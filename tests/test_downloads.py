"""Testes da coleta pelo navegador da pessoa (`app/sistec/downloads.py` e
`app/sistec/navegador.py`), que repete a mecânica do script R, e da lista de
campi cadastrada à mão (`app/data/campi.py`).

O "navegador da pessoa" é simulado por um `abrir()` que busca a URL com
cookies próprios e grava o arquivo numa pasta, como o Chrome faria. Nenhum
teste vigia a pasta de Downloads real da máquina (`pastas_extras=[]`)."""

import os
import sys
import threading
import time
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data import campi  # noqa: E402
from app.data.schema import init_db  # noqa: E402
from app.sistec import downloads, execucoes, navegador  # noqa: E402
from scripts import sistec_simulado  # noqa: E402

ADMIN = "teste-downloads@iffarroupilha.edu.br"
PERFIS = [
    {"id_perfil": "8278857", "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - 101 - IFFAR - CAMPUS ALEGRETE", "ordem": 0},
    {
        "id_perfil": "8278858",
        "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - INSTITUTO FEDERAL FARROUPILHA - CÂMPUS JÚLIO DE CASTILHOS",
        "ordem": 1,
    },
]


@pytest.fixture
def sistec():
    servidor = sistec_simulado.criar_servidor(0, login_automatico=False)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()
    servidor.server_close()


@pytest.fixture(autouse=True)
def limpar_registros():
    yield
    execucoes._REGISTRO.pop(ADMIN, None)
    navegador._SESSOES.pop(ADMIN, None)


class NavegadorFalso:
    """Faz o papel do navegador da pessoa: mantém os cookies da sessão e grava
    o CSV baixado na pasta que o navegador usaria, com o nome que o Sistec dá."""

    def __init__(self, pasta_destino, base):
        self.pasta_destino = Path(pasta_destino)
        self.base = base.rstrip("/")
        self.abertas = []
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def __call__(self, url):
        self.abertas.append(url)
        if url.rstrip("/") == self.base:
            self.opener.open(url).read()  # página de login
            self.opener.open(f"{self.base}/entrar", data=b"").read()  # a pessoa entra
            return
        conteudo = self.opener.open(url).read()
        if "exportar-ciclo-turmas" in url:
            nome = "ciclo-matricula.csv"
        elif "gerar-csv" in url:
            nome = "sistec.csv"
        else:
            return  # troca de perfil não baixa arquivo
        destino = self.pasta_destino / nome
        if destino.exists():  # o Chrome não sobrescreve: acrescenta " (1)"
            destino = self.pasta_destino / f"{destino.stem} (1).csv"
        destino.write_bytes(conteudo)


def _confirmar_login_quando_pedir(sessao, vezes=1):
    """A tela mostra "Já entrei no Sistec"; aqui o clique é automático."""

    def _rodar():
        for _ in range(vezes):
            for _tentativa in range(600):
                if not sessao.ativa():
                    return
                if sessao.fase == "aguardando_login":
                    navegador.confirmar_login(ADMIN)
                    break
                time.sleep(0.05)
            time.sleep(0.2)

    threading.Thread(target=_rodar, daemon=True).start()


def test_pasta_downloads_respeita_a_variavel_de_ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCSISTEC_PASTA_DOWNLOADS", str(tmp_path))
    assert downloads.pasta_downloads() == tmp_path


def test_pasta_de_coleta_e_fixa_e_criada_sozinha(tmp_path, monkeypatch):
    alvo = tmp_path / "CalcSISTEC" / "coleta"
    monkeypatch.setenv("CALCSISTEC_PASTA_COLETA", str(alvo))

    assert downloads.pasta_coleta() == alvo
    assert alvo.is_dir()


@pytest.mark.skipif(os.name != "nt", reason="caminho padrão do Windows")
def test_pasta_de_coleta_padrao_fica_no_appdata(tmp_path, monkeypatch):
    monkeypatch.delenv("CALCSISTEC_PASTA_COLETA", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert downloads.pasta_coleta() == tmp_path / "CalcSISTEC" / "coleta"


def test_esperar_arquivo_ignora_antigo_e_espera_download_terminar(tmp_path):
    antigo = tmp_path / "sistec.csv"
    antigo.write_bytes(b"velho")
    os.utime(antigo, (time.time() - 3600, time.time() - 3600))

    desde = time.time()
    parcial = tmp_path / "sistec (1).csv"
    parcial.write_bytes(b"a")
    (tmp_path / "sistec (1).csv.crdownload").write_bytes(b"")

    def _terminar_download():
        time.sleep(1.0)
        parcial.write_bytes(b"conteudo completo")
        (tmp_path / "sistec (1).csv.crdownload").unlink()

    threading.Thread(target=_terminar_download, daemon=True).start()
    achado = downloads.esperar_arquivo(tmp_path, "sistec", desde, tempo_max_s=20)

    assert achado == parcial


def test_esperar_arquivo_devolve_none_no_tempo_esgotado(tmp_path):
    assert downloads.esperar_arquivo(tmp_path, "sistec", time.time(), tempo_max_s=1) is None


def test_esperar_arquivo_avisa_uma_vez_quando_nada_chega(tmp_path, monkeypatch):
    """Caso do navegador com "perguntar onde salvar cada arquivo": a pessoa
    precisa saber disso em 1 minuto, não depois dos 15 de tempo máximo."""
    monkeypatch.setattr(downloads, "TEMPO_AVISO_SEM_ARQUIVO_S", 0.2)
    chamadas = []

    downloads.esperar_arquivo(tmp_path, "sistec", time.time(), tempo_max_s=2, aviso=lambda: chamadas.append(1))

    assert chamadas == [1]


def test_esperar_arquivo_olha_todas_as_pastas_vigiadas(tmp_path):
    coleta = tmp_path / "coleta"
    baixados = tmp_path / "Downloads"
    coleta.mkdir()
    baixados.mkdir()
    desde = time.time()
    arquivo = baixados / "ciclo-matricula.csv"
    arquivo.write_bytes(b"conteudo")

    achado = downloads.esperar_arquivo([coleta, baixados], "ciclo-matricula", desde, tempo_max_s=10)

    assert achado == arquivo


def test_arquivo_salvo_em_downloads_e_movido_para_a_pasta_de_coleta(tmp_path):
    coleta = tmp_path / "coleta"
    baixados = tmp_path / "Downloads"
    coleta.mkdir()
    baixados.mkdir()
    arquivo = baixados / "sistec.csv"
    arquivo.write_bytes(b"conteudo")

    destino = downloads.mover_para(coleta, arquivo)

    assert destino == coleta / "sistec.csv"
    assert destino.read_bytes() == b"conteudo"
    assert not arquivo.exists()


def test_apagar_remove_o_csv_com_dado_pessoal(tmp_path):
    arquivo = tmp_path / "sistec.csv"
    arquivo.write_bytes(b"x")
    assert downloads.apagar(arquivo) is True
    assert not arquivo.exists()


def test_coleta_baixa_todos_os_campi_e_nao_deixa_arquivo_no_disco(sistec, tmp_path):
    """O navegador salva na pasta dele; o CalcSISTEC move para a pasta fixa,
    lê e apaga."""
    db_path = str(tmp_path / "downloads.db")
    init_db(db_path)
    campi.salvar_captura(PERFIS, db_path)  # lista cadastrada, com identificador válido
    coleta = tmp_path / "coleta"
    baixados = tmp_path / "Downloads"
    coleta.mkdir()
    baixados.mkdir()

    sessao = navegador.Sessao(ADMIN, None, db_path, sistec)
    navegador._SESSOES[ADMIN] = sessao
    falso = NavegadorFalso(baixados, sistec)
    _confirmar_login_quando_pedir(sessao)

    thread = threading.Thread(
        target=lambda: navegador._coletar(sessao, abrir=falso, pasta=coleta, pastas_extras=[baixados]),
        daemon=True,
    )
    thread.start()
    thread.join(timeout=120)
    assert not thread.is_alive(), f"travou em: {sessao.fase} — {sessao.mensagem}"

    execucao = sessao.execucao
    assert [p.status for p in execucao.fila] == ["baixado"] * 4
    assert execucao.estado == "previa"
    assert sorted(execucao.previa["ciclos"]["CO_UNIDADE"].unique()) == ["101", "102"]
    assert list(coleta.iterdir()) == []  # nada com CPF fica no disco
    assert list(baixados.iterdir()) == []
    assert sessao.progresso == {"feitos": 4, "total": 4}
    assert any("Pasta de trabalho" in passo["texto"] for passo in sessao.passos)


def test_coleta_se_recusa_a_rodar_com_identificador_da_extensao_antiga(sistec, tmp_path):
    """A extensão MV3 gravava a posição do item ("0", "1", …) no lugar do
    identificador do Sistec: a troca de campus não acontecia e a baixa inteira
    vinha vazia, com o progresso parado em 0%. Agora a coleta para antes de
    tentar e diz o que corrigir."""
    db_path = str(tmp_path / "ids_velhos.db")
    init_db(db_path)
    campi.salvar_captura(
        [
            {"id_perfil": "0", "nome_perfil": PERFIS[0]["nome_perfil"], "ordem": 0},
            {"id_perfil": "1", "nome_perfil": PERFIS[1]["nome_perfil"], "ordem": 1},
        ],
        db_path,
    )
    coleta = tmp_path / "coleta"
    coleta.mkdir()

    sessao = navegador.Sessao(ADMIN, None, db_path, sistec)
    navegador._SESSOES[ADMIN] = sessao
    falso = NavegadorFalso(coleta, sistec)
    _confirmar_login_quando_pedir(sessao)

    with pytest.raises(navegador.FalhaNavegador, match="identificador de perfil válido"):
        navegador._coletar(sessao, abrir=falso, pasta=coleta, pastas_extras=[])

    assert sessao.execucao is None  # nenhuma fila chegou a ser montada
    assert list(coleta.iterdir()) == []


def test_coleta_sem_campi_cadastrados_explica_o_que_fazer(sistec, tmp_path):
    db_path = str(tmp_path / "vazio.db")
    init_db(db_path)
    sessao = navegador.Sessao(ADMIN, None, db_path, sistec)
    navegador._SESSOES[ADMIN] = sessao
    _confirmar_login_quando_pedir(sessao)

    with pytest.raises(navegador.FalhaNavegador, match="Configurações"):
        navegador._coletar(sessao, abrir=lambda url: None, pasta=tmp_path, pastas_extras=[])


def test_campi_suspeitos_aponta_so_os_identificadores_invalidos(tmp_path):
    db_path = str(tmp_path / "suspeitos.db")
    init_db(db_path)
    assert campi.campi_suspeitos(db_path) == []

    campi.salvar_captura(
        [
            {"id_perfil": "0", "nome_perfil": PERFIS[0]["nome_perfil"], "ordem": 0},
            {"id_perfil": "8278858", "nome_perfil": PERFIS[1]["nome_perfil"], "ordem": 1},
        ],
        db_path,
    )

    assert [c["id_perfil"] for c in campi.campi_suspeitos(db_path)] == ["0"]
    assert campi.id_suspeito("0") is True
    assert campi.id_suspeito("1234") is True  # curto demais para ser do Sistec
    assert campi.id_suspeito("abcdefg") is True
    assert campi.id_suspeito("8278860") is False


def test_salvar_campus_manual_corrige_o_identificador_preservando_o_resto(tmp_path):
    """É assim que uma lista gravada pela extensão antiga é consertada sem
    perder código da unidade, cidade e nome já preenchidos."""
    db_path = str(tmp_path / "crud.db")
    init_db(db_path)
    campi.salvar_captura([{"id_perfil": "0", "nome_perfil": PERFIS[0]["nome_perfil"], "ordem": 0}], db_path)
    campi.salvar_campus_manual("0", "13478", "Alegrete", "Campus Alegrete", db_path)

    campi.salvar_campus_manual("0", "13478", "Alegrete", "Campus Alegrete", db_path, novo_id_perfil="8278857")

    (salvo,) = campi.listar_campi(db_path)
    assert salvo["id_perfil"] == "8278857"
    assert (salvo["co_unidade"], salvo["cidade"], salvo["nome_unidade"]) == ("13478", "Alegrete", "Campus Alegrete")
    assert campi.campi_suspeitos(db_path) == []


def test_salvar_campus_manual_recusa_identificador_ja_usado(tmp_path):
    db_path = str(tmp_path / "duplicado.db")
    init_db(db_path)
    campi.salvar_captura(PERFIS, db_path)

    with pytest.raises(campi.CampusInvalido, match="identificador"):
        campi.salvar_campus_manual("8278857", None, None, None, db_path, novo_id_perfil="8278858")


def test_lista_de_perfis_colada_substitui_ids_antigos_preservando_edicoes(tmp_path):
    """Caminho mais rápido do cadastro: a pessoa cola a lista da instituição
    dela (nada fixo no código)."""
    from app.sistec.perfis import perfis_de_texto

    db_path = str(tmp_path / "importar.db")
    init_db(db_path)
    campi.salvar_captura(
        [{"id_perfil": "0", "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS SANTA ROSA", "ordem": 0}],
        db_path,
    )
    campi.salvar_campus_manual("0", "13478", "Santa Rosa", "Campus Santa Rosa", db_path)

    perfis, invalidas = perfis_de_texto(
        "8278860 ; ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS SANTA ROSA\n"
        "8278864 ; ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS SÃO BORJA\n"
    )
    campi.salvar_captura([{**p, "ordem": i} for i, p in enumerate(perfis)], db_path)

    assert invalidas == []
    lista = campi.listar_campi(db_path)
    assert [c["id_perfil"] for c in lista] == ["8278860", "8278864"]
    santa_rosa = next(c for c in lista if "SANTA ROSA" in c["nome_perfil"].upper())
    assert santa_rosa["co_unidade"] == "13478"  # o que já estava salvo continua
