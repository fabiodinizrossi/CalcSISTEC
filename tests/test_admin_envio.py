"""Rota de atualização por envio de pastas (`/admin/atualizar/envio`, T7/UPL-02,
UPL-05, UPL-06, UPL-10, UPL-11, UPL-12, UPL-13).

Integração com o `test_client` do Flask: nada aqui toca o Sistec real nem o
banco do repositório — a lista de campi e as linhas de histórico são
substituídas por dublês, e o registro de execuções em memória é limpo a cada
teste.
"""

import io
import json
import os
import re
import sys
import tempfile

import pandas as pd
import pytest
from werkzeug.datastructures import FileStorage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as app_module  # noqa: E402
from app.sistec import envio, execucoes  # noqa: E402
from app.sistec.colunas import COLUNAS_CICLO, COLUNAS_MATRICULA  # noqa: E402

ADMIN = "pi@ife.edu.br"
CELULA_SENSIVEL = "SEGREDO-DE-CELULA"

CAMPI = [
    {"id_perfil": "1", "nome_perfil": "Assessor A", "co_unidade": "U1"},
    {"id_perfil": "2", "nome_perfil": "Assessor B", "co_unidade": "U2"},
    {"id_perfil": "3", "nome_perfil": "Assessor C", "co_unidade": "U3"},
]

HISTORICO = []


def _linha_ciclo(co_unidade, codigo):
    return {
        "CÓDIGO CICLO DE MATRÍCULA": codigo,
        "CÓDIGO UNIDADE DE ENSINO": co_unidade,
        "CÓDIGO DO PORTFÓLIO": f"P-{co_unidade}",
        "NOME DO CURSO": "TÉCNICO EM X",
        "SUBTIPO CURSOS": "TECNICO",
        "CARGA HORÁRIA TOTAL": "1200",
        "MODALIDADE ENSINO": "PRESENCIAL",
        "TIPO OFERTA DO CURSO": "ANUAL",
        "EIXO TECNOLÓGICO": "EIXO1",
        "TIPO PROGRAMA DO CURSO": "REGULAR",
        "DATA INÍCIO DO CURSO": "2026-01-01",
        "DATA FIM PREVISTO DO CURSO": "2027-01-01",
        "STATUS DO CICLO DE MATRÍCULA": "ATIVO",
        "SITUAÇÃO DO CICLO ": "ATIVO",
    }


def _linha_matricula(co_unidade, codigo, co_matricula):
    return {
        "CO_MATRICULA": co_matricula,
        "CO_CICLO_MATRICULA": codigo,
        "NO_STATUS_MATRICULA": "EM_CURSO",
        "MES_DE_OCORRENCIA": "2026-01-01",
    }


def _bytes(linhas, colunas_esperadas):
    """CSV `;`/`cp1252` com as colunas externas do Sistec, na ordem do mapa."""
    nomes = [nome for nome in colunas_esperadas if nome in linhas[0]]
    df = pd.DataFrame([{nome: linha[nome] for nome in nomes} for linha in linhas], columns=nomes)
    return df.to_csv(sep=";", index=False).encode("cp1252")


def _ciclo(codigo, co_unidade, nome="ciclos-U1.csv", **overrides):
    linha = {**_linha_ciclo(co_unidade, codigo), **overrides}
    return FileStorage(io.BytesIO(_bytes([linha], COLUNAS_CICLO)), filename=nome)


def _matricula(codigo, co_matricula, co_unidade="U1", nome="matriculas-U1.csv"):
    linha = _linha_matricula(co_unidade, codigo, co_matricula)
    return FileStorage(io.BytesIO(_bytes([linha], COLUNAS_MATRICULA)), filename=nome)


def _envio_valido(co_unidades=("U1", "U2", "U3")):
    """Pastas de ciclos e matrículas cobrindo as unidades pedidas."""
    ciclos = [_ciclo(f"C{i}", co_unidade, nome=f"ciclos-{co_unidade}.csv") for i, co_unidade in enumerate(co_unidades, 1)]
    matriculas = [
        _matricula(f"C{i}", f"M{i}", co_unidade, nome=f"matriculas-{co_unidade}.csv")
        for i, co_unidade in enumerate(co_unidades, 1)
    ]
    return ciclos, matriculas


@pytest.fixture
def cliente():
    return app_module.server.test_client()


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    """Dublês de campi e histórico + registro de execuções limpo."""
    HISTORICO.clear()
    execucoes._REGISTRO.clear()
    monkeypatch.setattr(app_module, "listar_campi", lambda *a, **k: CAMPI)
    monkeypatch.setattr(app_module, "historico_iniciar", lambda tipo, email: _iniciar(tipo, email))
    monkeypatch.setattr(app_module, "historico_encerrar", _encerrar)
    yield
    execucoes._REGISTRO.clear()


def _iniciar(tipo, email):
    HISTORICO.append({"tipo": tipo, "admin_email": email, "desfecho": None, "detalhe": None})
    return len(HISTORICO)


def _encerrar(historico_id, desfecho, **kwargs):
    HISTORICO[historico_id - 1]["desfecho"] = desfecho
    HISTORICO[historico_id - 1]["detalhe"] = kwargs.get("detalhe")


@pytest.fixture
def sessao(cliente):
    """Cliente com sessão administrativa ativa."""
    with cliente.session_transaction() as s:
        s["admin_usuario"] = ADMIN
        s["admin_autenticado"] = True
    return cliente


def test_rota_sem_sessao_redireciona_para_o_login(cliente):
    resposta = cliente.post("/admin/atualizar/envio", data={})
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/admin/login"


def test_envio_valido_chega_a_previa_com_desfecho_por_arquivo(sessao):
    ciclos, matriculas = _envio_valido()
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["estado"] == "previa"
    assert corpo["previa"] == {"ciclos": 3, "matriculas": 3}
    assert [(item["nome"], item["status"], item["linhas"]) for item in corpo["arquivos"]] == [
        ("ciclos-U1.csv", "baixado", 1),
        ("ciclos-U2.csv", "baixado", 1),
        ("ciclos-U3.csv", "baixado", 1),
        ("matriculas-U1.csv", "baixado", 1),
        ("matriculas-U2.csv", "baixado", 1),
        ("matriculas-U3.csv", "baixado", 1),
    ]


def test_envio_lista_os_arquivos_ignorados_sem_processar(sessao):
    ciclos, matriculas = _envio_valido(("U1",))
    resposta = sessao.post(
        "/admin/atualizar/envio",
        data={"ciclos": ciclos + [_ciclo("C9", "U1", nome="LEIA-ME.txt")], "matriculas": matriculas},
    )
    corpo = resposta.get_json()
    assert corpo["ignorados"] == ["LEIA-ME.txt"]
    assert [item["nome"] for item in corpo["arquivos"]].count("LEIA-ME.txt") == 0


def test_pasta_vazia_devolve_400_nomeando_a_pasta_sem_criar_execucao(sessao):
    _, matriculas = _envio_valido(("U1",))
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": [], "matriculas": matriculas})

    corpo = resposta.get_json()
    assert resposta.status_code == 400
    assert corpo == {"erro": "envio_invalido", "arquivo": "ciclos", "motivo": "pasta_vazia"}
    assert execucoes.obter_do_admin(ADMIN) is None
    assert HISTORICO == []


def test_arquivo_sem_colunas_obrigatorias_devolve_400_e_nao_grava_nada(sessao):
    _, matriculas = _envio_valido(("U1",))
    quebrado = FileStorage(
        io.BytesIO(f"CÓDIGO UNIDADE DE ENSINO\n{CELULA_SENSIVEL}\n".encode("cp1252")), filename="quebrado.csv"
    )
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": [quebrado], "matriculas": matriculas})

    corpo = resposta.get_json()
    assert resposta.status_code == 400
    assert corpo == {"erro": "envio_invalido", "arquivo": "quebrado.csv", "motivo": "colunas_ausentes"}
    assert execucoes.obter_do_admin(ADMIN) is None


def test_mensagem_de_erro_nao_carrega_conteudo_de_celula(sessao):
    """RN-13/UPL-12: a resposta nomeia o arquivo e o motivo, nunca a célula."""
    _, matriculas = _envio_valido(("U1",))
    linha_matricula = {nome: CELULA_SENSIVEL for nome in COLUNAS_MATRICULA}
    df = pd.DataFrame([linha_matricula], columns=list(COLUNAS_MATRICULA))
    quebrado = FileStorage(io.BytesIO(df.to_csv(sep=";", index=False).encode("cp1252")), filename="quebrado.csv")

    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": [quebrado], "matriculas": matriculas})

    assert resposta.status_code == 400
    assert CELULA_SENSIVEL not in resposta.get_data(as_text=True)


def test_consolidacao_invalida_encerra_em_falhou_consolidacao_sem_gravar(sessao):
    """UPL-11: chave repetida com conteúdo divergente falha o envio inteiro."""
    matriculas = [_matricula("C1", "M1")]
    ciclos = [
        _ciclo("C1", "U1", nome="ciclos-a.csv"),
        _ciclo("C1", "U1", nome="ciclos-b.csv", **{"NOME DO CURSO": "OUTRO CURSO"}),
    ]
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["estado"] == "falhou_consolidacao"
    assert corpo["erro_consolidacao"]
    assert corpo["previa"] is None
    assert execucoes.obter_do_admin(ADMIN).previa is None
    assert HISTORICO[0]["desfecho"] == "falhou_consolidacao"


def test_falha_de_consolidacao_nao_poe_conteudo_de_planilha_no_detalhe(sessao):
    matriculas = [_matricula("C1", "M1")]
    ciclos = [
        _ciclo("C1", "U1", nome="ciclos-a.csv"),
        _ciclo("C1", "U1", nome="ciclos-b.csv", **{"NOME DO CURSO": CELULA_SENSIVEL}),
    ]
    sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    detalhe = json.dumps(HISTORICO[0]["detalhe"], ensure_ascii=False)
    assert CELULA_SENSIVEL not in detalhe
    assert "TÉCNICO EM X" not in detalhe


def test_historico_abre_com_tipo_envio(sessao):
    ciclos, matriculas = _envio_valido(("U1",))
    sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    assert [(linha["tipo"], linha["admin_email"]) for linha in HISTORICO] == [("envio", ADMIN)]


def test_previa_pendente_recusa_um_segundo_envio(sessao):
    ciclos, matriculas = _envio_valido(("U1",))
    primeira = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})
    assert primeira.status_code == 200

    ciclos, matriculas = _envio_valido(("U1",))
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})
    assert resposta.status_code == 409
    assert resposta.get_json() == {"erro": "previa_pendente"}

    execucao_id = primeira.get_json()["execucao_id"]
    descarte = sessao.post(f"/admin/atualizar/execucoes/{execucao_id}/descartar")
    assert descarte.status_code == 204

    ciclos, matriculas = _envio_valido(("U1",))
    novo_envio = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})
    assert novo_envio.status_code == 200
    assert novo_envio.get_json()["estado"] == "previa"


def test_baixa_em_andamento_recusa_o_envio(sessao, monkeypatch):
    monkeypatch.setattr(app_module.navegador, "status", lambda email: {"ativa": True})
    ciclos, matriculas = _envio_valido(("U1",))
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    assert resposta.status_code == 409
    assert resposta.get_json() == {"erro": "execucao_em_andamento"}


def test_envio_em_andamento_faz_a_baixa_do_sistec_devolver_409(sessao, monkeypatch):
    monkeypatch.setattr(app_module.navegador, "status", lambda email: None)
    ciclos, matriculas = _envio_valido(("U1",))
    sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    resposta = sessao.post("/admin/atualizar/sistec")
    assert resposta.status_code == 409


def test_payload_acima_do_limite_devolve_413(sessao, monkeypatch):
    monkeypatch.setitem(app_module.server.config, "MAX_CONTENT_LENGTH", 50)
    ciclos, matriculas = _envio_valido(("U1",))
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    assert resposta.status_code == 413


def test_arquivo_grande_nao_deixa_buffer_temporario_legivel(tmp_path, monkeypatch):
    """UPL-06: acima de 512 KB o parser entrega o arquivo num spool em disco
    (e não num `BytesIO`); `ler_pastas` precisa fechá-lo, o que apaga o
    arquivo antes de a requisição terminar."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    _, matriculas = _envio_valido(("U1",))
    conteudo = (b"\n".join(b"linha %d" % i for i in range(120000))) + b"\n"

    spool = tempfile.SpooledTemporaryFile(max_size=1024, mode="rb+")
    spool.write(conteudo)
    arquivo = FileStorage(spool, filename="grande.csv")

    with pytest.raises(envio.EnvioInvalido):
        envio.ler_pastas([arquivo], matriculas)

    assert arquivo.stream.closed is True
    assert list(tmp_path.iterdir()) == []


def test_rota_fecha_os_arquivos_recebidos_antes_de_responder(sessao, monkeypatch):
    """UPL-06 na rota: o envio fecha cada arquivo recebido do parser."""
    recebidos = []
    ler_pastas_original = envio.ler_pastas

    def espiao(ciclos, matriculas):
        recebidos.extend(list(ciclos) + list(matriculas))
        return ler_pastas_original(ciclos, matriculas)

    monkeypatch.setattr(envio, "ler_pastas", espiao)
    ciclos, matriculas = _envio_valido(("U1",))
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    assert resposta.status_code == 200
    assert recebidos
    assert all(arquivo.stream.closed for arquivo in recebidos)


@pytest.fixture
def banco_temporario(tmp_path, monkeypatch):
    """Banco vazio para o cadastro automático (AFE-03), no lugar do do repositório."""
    from app.data.schema import init_db

    caminho = str(tmp_path / "envio.db")
    init_db(caminho)
    monkeypatch.setattr(app_module, "DEFAULT_DB_PATH", caminho)
    return caminho


def test_campus_ausente_do_envio_fica_preservado(sessao, banco_temporario):
    """UPL-07/UPL-09: U3 fica ausente do envio e preservado."""
    ciclos = [_ciclo("C1", "U1", nome="ciclos-U1.csv"), _ciclo("C9", "U9", nome="ciclos-U9.csv")]
    matriculas = [_matricula("C1", "M1", "U1")]
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert corpo["campi_preservados"] == ["U2", "U3"]
    assert execucoes.obter_do_admin(ADMIN).campi_falhos == {"U2", "U3"}


def test_unidade_fora_do_cadastro_e_cadastrada_automaticamente(sessao, banco_temporario):
    """AFE-03: U9 vem nos ciclos mas não está em `campi_sistec`; a rota cadastra
    a unidade sozinha, em vez de só avisar que ela ficou de fora."""
    from app.data import campi as dados_campi

    ciclos = [_ciclo("C1", "U1", nome="ciclos-U1.csv"), _ciclo("C9", "U9", nome="ciclos-U9.csv")]
    matriculas = [_matricula("C1", "M1", "U1")]
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert corpo["campi_cadastrados_automaticamente"] == ["U9"]
    assert "campi_nao_cadastrados" not in corpo

    cadastrados = {c["co_unidade"]: c for c in dados_campi.listar_campi(banco_temporario)}
    assert "U9" in cadastrados
    unidade = cadastrados["U9"]
    assert unidade["id_perfil"] == "envio-U9"
    assert unidade["nome_perfil"] == "Unidade U9 (cadastrada pelo envio de pastas)"
    assert unidade["origem"] == "manual"
    # O CSV não traz o identificador de perfil real: o prefixo textual faz o
    # aviso de identificador inválido aparecer em Configurações.
    assert dados_campi.id_suspeito(unidade["id_perfil"]) is True


def test_colisao_no_cadastro_automatico_nao_derruba_o_envio(sessao, banco_temporario):
    """AFE-03 AC3: se `incluir_campus` colidir numa unidade (aqui "U9", cujo
    identificador `envio-U9` já pertence a outro campus), o envio não falha por
    causa disso — aquela unidade fica de fora do cadastro e as demais do mesmo
    envio entram normalmente."""
    from app.data import campi as dados_campi

    dados_campi.incluir_campus("envio-U9", "Campus de outro código", "U7", db_path=banco_temporario)
    ciclos = [
        _ciclo("C1", "U1", nome="ciclos-U1.csv"),
        _ciclo("C9", "U9", nome="ciclos-U9.csv"),
        _ciclo("C8", "U8", nome="ciclos-U8.csv"),
    ]
    matriculas = [_matricula("C1", "M1", "U1")]
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["estado"] == "previa"
    assert corpo["campi_cadastrados_automaticamente"] == ["U8"]

    cadastrados = {c["co_unidade"]: c for c in dados_campi.listar_campi(banco_temporario)}
    assert cadastrados["U8"]["id_perfil"] == "envio-U8"
    # A linha que já ocupava o identificador "envio-U9" segue intacta.
    assert cadastrados["U7"]["id_perfil"] == "envio-U9"
    assert "U9" not in cadastrados


def test_unidade_cadastrada_pelo_envio_aparece_nas_paginas_de_cadastro(sessao, banco_temporario, monkeypatch):
    """AFE-03 AC4: a unidade cadastrada pelo envio aparece em `/admin/campi` e
    conta nos totais de Configurações — a tela, não só o banco.

    As duas páginas chegam ao cadastro por caminhos próprios: `admin_config`
    usa o `listar_campi` do `app.py`, e `/admin/campi` usa um `DB_PATH` próprio
    (`app/admin_campi.py:25`, cópia do valor de `DEFAULT_DB_PATH` feita no
    import). O teste aponta os dois para o banco temporário — sem isso as
    chamadas leriam o banco do repositório e o teste não provaria nada."""
    from app import admin_campi
    from app.data import campi as dados_campi

    monkeypatch.setattr(admin_campi, "DB_PATH", banco_temporario)
    monkeypatch.setattr(app_module, "listar_campi", lambda *a, **k: dados_campi.listar_campi(banco_temporario))
    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: True)

    ciclos = [_ciclo("C9", "U9", nome="ciclos-U9.csv")]
    matriculas = [_matricula("C9", "M9", "U9")]
    sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    pagina_campi = sessao.get("/admin/campi").get_data(as_text=True)
    assert "Unidade U9 (cadastrada pelo envio de pastas)" in pagina_campi
    assert re.search(r"<td>\s*U9\s*</td>", pagina_campi)

    config = sessao.get("/admin/config").get_data(as_text=True)
    assert "1 campi cadastrados, 1 ativos." in config
    assert "1 campus com identificador inválido" in config


def test_unidade_ja_cadastrada_nao_e_cadastrada_de_novo(sessao, banco_temporario, monkeypatch):
    """Edge case AFE-03: dois envios reais contra o mesmo banco. O primeiro
    cadastra U9; no segundo ela já está em `campi_sistec`, então
    `campi_nao_cadastrados` a exclui e nada é incluído de novo — nem duplicado."""
    from app.data import campi as dados_campi

    monkeypatch.setattr(app_module, "listar_campi", lambda *a, **k: dados_campi.listar_campi(banco_temporario))

    def enviar():
        # Cada POST recebe arquivos novos: o `FileStorage` do primeiro foi lido
        # (e fechado) pelo `ler_pastas`.
        ciclos = [_ciclo("C9", "U9", nome="ciclos-U9.csv")]
        matriculas = [_matricula("C9", "M9", "U9")]
        resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})
        return resposta.get_json()

    primeiro = enviar()
    assert primeiro["campi_cadastrados_automaticamente"] == ["U9"]

    sessao.post(f"/admin/atualizar/execucoes/{primeiro['execucao_id']}/descartar")

    segundo = enviar()
    assert segundo["campi_cadastrados_automaticamente"] == []
    assert [c["co_unidade"] for c in dados_campi.listar_campi(banco_temporario)] == ["U9"]


def test_unidade_cadastrada_pelo_envio_sobrevive_a_uma_leitura_do_sistec(sessao, banco_temporario):
    """AFE-03: `origem='manual'` — uma recaptura de perfis pelo Sistec não apaga
    a unidade que o envio cadastrou."""
    from app.data import campi as dados_campi

    ciclos = [_ciclo("C9", "U9", nome="ciclos-U9.csv")]
    matriculas = [_matricula("C9", "M9", "U9")]
    sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    dados_campi.salvar_captura(
        [{"id_perfil": "8278860", "nome_perfil": "Assessor A", "ordem": 0, "co_unidade": "U1"}],
        banco_temporario,
    )

    assert "U9" in {c["co_unidade"] for c in dados_campi.listar_campi(banco_temporario)}


def test_matriculas_de_ciclo_ausente_entram_na_contagem_de_orfas(sessao):
    ciclos = [_ciclo("C1", "U1", nome="ciclos-U1.csv")]
    matriculas = [_matricula("C1", "M1", "U1"), _matricula("C9", "M9", "U1", nome="matriculas-U1-b.csv")]
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert corpo["matriculas_orfas"] == 1
    assert corpo["previa"]["matriculas"] == 2


# ===================== previa-paginas-publicas, T17 =====================


def test_envio_valido_abre_a_fonte_e_vincula_sessao(sessao, banco_temporario):
    ciclos, matriculas = _envio_valido(("U1",))
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert resposta.status_code == 200
    assert corpo["estado"] == "previa"
    execucao = execucoes.obter_do_admin(ADMIN)
    assert execucao.previa_fonte is not None
    assert execucao.sessao_dona is not None


def test_envio_valido_libera_os_dataframes_e_conserva_resumo(sessao, banco_temporario):
    ciclos, matriculas = _envio_valido(("U1",))
    sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    execucao = execucoes.obter_do_admin(ADMIN)
    assert execucao.previa is None  # consolidado pesado liberado
    assert all(par.df is None for par in execucao.fila)  # DataFrames por arquivo liberados
    assert execucao.previa_resumo is not None
    assert execucao.previa_resumo["ciclos"] == 1
    assert execucao.previa_resumo["matriculas"] == 1


def test_consolidacao_invalida_nao_cria_fonte(sessao, banco_temporario):
    matriculas = [_matricula("C1", "M1")]
    ciclos = [
        _ciclo("C1", "U1", nome="ciclos-a.csv"),
        _ciclo("C1", "U1", nome="ciclos-b.csv", **{"NOME DO CURSO": "OUTRO CURSO"}),
    ]
    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})

    corpo = resposta.get_json()
    assert corpo["estado"] == "falhou_consolidacao"
    execucao = execucoes.obter_do_admin(ADMIN)
    assert execucao.previa_fonte is None


def test_falha_de_memoria_devolve_erro_sem_gravar(sessao, banco_temporario, monkeypatch):
    def _sem_memoria(*a, **k):
        raise MemoryError("sem memória")

    monkeypatch.setattr(execucoes, "abrir_previa", _sem_memoria)
    ciclos, matriculas = _envio_valido(("U1",))

    resposta = sessao.post("/admin/atualizar/envio", data={"ciclos": ciclos, "matriculas": matriculas})
    corpo = resposta.get_json()

    assert resposta.status_code == 200
    assert corpo["estado"] == "previa"
    assert corpo["erro_previa"] == "sem_memoria"
    assert corpo["previa"] is None
    execucao = execucoes.obter_do_admin(ADMIN)
    assert execucao.estado == "previa"
    assert execucao.previa_fonte is None
