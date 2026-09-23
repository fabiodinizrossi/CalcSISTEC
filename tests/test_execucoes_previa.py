"""Testes do guardião de posse, origem, estado e ciclo de vida da prévia
(`previa-paginas-publicas`, T4–T8) em `app/sistec/execucoes.py`.

Cobrem PVP-07/PVP-08: `obter_previa` só autoriza a sessão dona de um envio em
estado `previa`; a fonte candidata abre/libera; leitura e transição de estado
são serializadas por trava; e falhas de página bloqueiam o Salvar.
"""

import os
import sys
import threading
import time
from datetime import datetime

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.sistec import execucoes  # noqa: E402


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()
    yield
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()


def _leitura_envio():
    ciclo = {
        "CODIGO_CICLO_MATRICULA": "C1",
        "CO_UNIDADE": "U1",
        "CÓDIGO DO PORTFÓLIO": "P1",
        "NOME_CURSO": "TÉCNICO EM X",
        "TIPO_CURSO": "TECNICO",
        "CARGA_HORARIA_TOTAL": 1200,
        "MODALIDADE_ENSINO": "PRESENCIAL",
        "OFERTA": "ANUAL",
        "EIXO_TECNOLOGICO": "EIXO1",
        "TIPO_PROGRAMA_CURSO": "REGULAR",
        "DT_DATA_INICIO": "2026-01-01",
        "DT_DATA_FIM_PREVISTO": "2027-01-01",
        "STATUS_CICLO": "ATIVO",
        "SITUACAO_CICLO": "ATIVO",
    }
    matricula = {
        "CO_MATRICULA": "M1",
        "CODIGO_CICLO_MATRICULA": "C1",
        "STATUS_MATRICULA_SISTEC": "EM_CURSO",
        "MES_OCORRENCIA_CORRIGIDO": "2026-01-01",
    }
    return {
        "ciclo": [("ciclos.csv", pd.DataFrame([ciclo]))],
        "matricula": [("matriculas.csv", pd.DataFrame([matricula]))],
    }


def _envio_em_previa(sessao_id="sessao-A"):
    """Cria um envio consolidado em estado `previa`, dono da `sessao_id`."""
    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id=sessao_id
    )
    execucoes.registrar_leitura(envio, _leitura_envio())
    return envio


# ===================== T4: guardião de posse, origem e estado =====================


def test_obter_previa_autoriza_a_sessao_dona():
    envio = _envio_em_previa()
    assert execucoes.obter_previa(envio.id, "sessao-A") is envio


def test_obter_previa_recusa_execucao_inexistente():
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa("nao-existe", "sessao-A")


def test_obter_previa_recusa_sessao_alheia_do_mesmo_email():
    envio = _envio_em_previa(sessao_id="sessao-A")
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, "sessao-B")


def test_obter_previa_recusa_sessao_ausente_quando_dona_exigida():
    envio = _envio_em_previa(sessao_id="sessao-A")
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, None)


def test_obter_previa_recusa_origem_baixa():
    from app.sistec.execucoes import criar_execucao

    baixa = criar_execucao(
        "pi@iffarroupilha.edu.br", [{"id_perfil": "1", "nome_perfil": "Campus A"}]
    )
    baixa.estado = "previa"
    baixa.sessao_dona = "sessao-A"
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(baixa.id, "sessao-A")


def test_obter_previa_recusa_estado_terminal():
    envio = _envio_em_previa()
    envio.estado = "salva"
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, "sessao-A")


def test_obter_previa_recusa_estado_diferente_de_previa():
    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id="sessao-A"
    )
    # ainda em `consolidando`, antes de registrar a leitura
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa(envio.id, "sessao-A")


def test_obter_previa_registro_limpo_devolve_indisponivel():
    # registro vazio (reinício do processo): execução pendente deixou de existir
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.obter_previa("qualquer-id", "sessao-A")


# ===================== T5: trava por execução =====================


def test_execucao_cria_trava_na_construcao_e_nao_substitui():
    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id="sessao-A"
    )
    assert isinstance(envio.lock, type(threading.Lock()))
    # a mesma instância persiste durante a vida da execução (não é recriada)
    assert envio.lock is envio.lock


def test_com_trava_serializa_leitura_contra_descar():
    envio = _envio_em_previa()
    leitor_entrou = threading.Event()
    liberar = threading.Event()
    ordem = []

    def leitor():
        with execucoes.com_trava(envio):
            ordem.append("leitor-entra")
            leitor_entrou.set()
            liberar.wait(timeout=5)
            ordem.append("leitor-sai")

    resultado = {"descartou": False}

    def descartar():
        execucoes.descartar(envio)
        resultado["descartou"] = True
        ordem.append("descartou")

    t_leitor = threading.Thread(target=leitor)
    t_leitor.start()
    assert leitor_entrou.wait(timeout=5)

    t_descar = threading.Thread(target=descartar)
    t_descar.start()
    time.sleep(0.05)  # deixa o descartar tentar e bloquear na trava
    assert resultado["descartou"] is False  # ainda esperando o leitor liberar

    liberar.set()
    t_leitor.join(timeout=5)
    t_descar.join(timeout=5)

    assert ordem == ["leitor-entra", "leitor-sai", "descartou"]
    assert envio.estado == "descartada"


def test_sem_deadlock_entre_registro_e_execucao():
    envio = _envio_em_previa()
    # Segurando a trava da execução, uma operação de registro (que toma
    # `_LOCK`) conclui — a ordem execução -> registro não trava.
    with execucoes.com_trava(envio):
        nova = execucoes.criar_execucao(
            "outro@iffarroupilha.edu.br", [{"id_perfil": "1", "nome_perfil": "Campus A"}]
        )
        assert nova is not None
    assert envio.estado == "previa"


# ===================== T6: abrir e liberar a fonte da prévia =====================


@pytest.fixture
def db_path(tmp_path):
    from app.data.schema import init_db

    caminho = str(tmp_path / "previa.db")
    init_db(caminho)
    return caminho


def _candidato(db_path):
    from app.data.ingest import preparar_versao
    from app.sistec.consolidacao import consolidar

    leitura = _leitura_envio()
    conjunto = consolidar([leitura["ciclo"][0][1]], [leitura["matricula"][0][1]])
    return preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)


def test_abrir_previa_cria_fonte_e_nao_duplica(db_path):
    envio = _envio_em_previa()
    candidato = _candidato(db_path)

    fonte = execucoes.abrir_previa(envio, candidato, db_path=db_path)
    assert fonte is not None
    assert envio.previa_fonte is fonte
    assert envio.candidato is candidato

    fonte_2 = execucoes.abrir_previa(envio, candidato, db_path=db_path)
    assert fonte_2 is fonte  # chamadas repetidas não criam segunda fonte

    execucoes.liberar_previa(envio)


def test_abrir_previa_libera_dataframes_e_conserva_resumo(db_path):
    envio = _envio_em_previa()
    assert all(p.df is not None for p in envio.fila)
    assert envio.previa is not None

    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)

    assert all(p.df is None for p in envio.fila)
    assert envio.previa is None
    assert envio.previa_resumo["ciclos"] == 1
    assert envio.previa_resumo["matriculas"] == 1
    execucoes.liberar_previa(envio)


def test_abrir_previa_preserva_campi_falhos(db_path):
    envio = _envio_em_previa()
    execucoes.definir_campi_preservados(envio, ["U1", "U2"])

    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)

    assert envio.campi_falhos == {"U1", "U2"}
    execucoes.liberar_previa(envio)


def test_liberar_previa_fecha_fonte_e_e_idempotente(db_path):
    envio = _envio_em_previa()
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)

    execucoes.liberar_previa(envio)
    assert envio.previa_fonte is None

    execucoes.liberar_previa(envio)  # idempotente: não lança


def test_descar_libera_fonte_antes_de_marcar_descartada(db_path):
    envio = _envio_em_previa()
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)
    assert envio.previa_fonte is not None

    execucoes.descartar(envio)

    assert envio.estado == "descartada"
    assert envio.previa_fonte is None


def test_descar_fora_de_previa_recusa(db_path):
    envio = _envio_em_previa()
    envio.estado = "salva"
    with pytest.raises(execucoes.ExecucaoInvalida):
        execucoes.descartar(envio)


# ===================== T7: contexto de leitura da prévia =====================


def test_abrir_leitura_previa_contexto_valido(db_path):
    envio = _envio_em_previa()
    candidato = _candidato(db_path)
    execucoes.abrir_previa(envio, candidato, db_path=db_path)

    contexto = execucoes.abrir_leitura_previa(envio.id, "sessao-A")
    try:
        assert contexto.execucao is envio
        assert contexto.ano_base == 2026
        # a conexão lê a fonte candidata (1 curso), não o banco publicado (vazio)
        total = contexto.conn.execute("SELECT COUNT(*) FROM cursos").fetchone()[0]
        assert total == 1
    finally:
        contexto.conn.close()
    execucoes.liberar_previa(envio)


def test_abrir_leitura_previa_sessao_alheia(db_path):
    envio = _envio_em_previa()
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)

    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.abrir_leitura_previa(envio.id, "sessao-B")

    execucoes.liberar_previa(envio)


def test_abrir_leitura_previa_estado_terminal(db_path):
    envio = _envio_em_previa()
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)
    envio.estado = "salva"

    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.abrir_leitura_previa(envio.id, "sessao-A")

    execucoes.liberar_previa(envio)


def test_abrir_leitura_previa_fonte_fechada(db_path):
    envio = _envio_em_previa()
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)
    execucoes.liberar_previa(envio)  # fecha a fonte; estado continua `previa`

    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.abrir_leitura_previa(envio.id, "sessao-A")


def test_abrir_leitura_previa_execucao_inexistente():
    with pytest.raises(execucoes.PreviaIndisponivel):
        execucoes.abrir_leitura_previa("nao-existe", "sessao-A")


# ===================== T8: falha de página e bloqueio do Salvar =====================


def test_falhas_paginas_comeca_vazio():
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"])
    assert envio.falhas_paginas == set()
    assert execucoes.paginas_com_falha(envio) == []


def test_registrar_e_limpar_falha_pagina():
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"])
    execucoes.registrar_falha_pagina(envio, "eficiencia")
    assert execucoes.paginas_com_falha(envio) == ["eficiencia"]

    # renderização bem-sucedida da mesma página limpa a falha anterior
    execucoes.limpar_falha_pagina(envio, "eficiencia")
    assert execucoes.paginas_com_falha(envio) == []


def test_salvar_bloqueado_por_uma_falha():
    envio = _envio_em_previa()
    execucoes.registrar_falha_pagina(envio, "matriculas")

    with pytest.raises(execucoes.PreviaIncompleta) as exc:
        execucoes.salvar(envio, "qualquer.db", 2026)

    assert exc.value.paginas == ["matriculas"]
    assert envio.estado == "previa"


def test_salvar_bloqueado_por_duas_falhas():
    envio = _envio_em_previa()
    execucoes.registrar_falha_pagina(envio, "matriculas")
    execucoes.registrar_falha_pagina(envio, "evasao")

    with pytest.raises(execucoes.PreviaIncompleta) as exc:
        execucoes.salvar(envio, "qualquer.db", 2026)

    assert exc.value.paginas == ["evasao", "matriculas"]  # ordem estável


def test_salvar_baixa_nao_afetado_por_falha(monkeypatch):
    baixa = execucoes.criar_execucao(
        "pi@iffarroupilha.edu.br", [{"id_perfil": "1", "nome_perfil": "Campus A"}]
    )
    baixa.estado = "previa"
    baixa.previa = {"valor": "previa"}
    execucoes.registrar_falha_pagina(baixa, "matriculas")
    monkeypatch.setattr("app.data.ingest.montar_versao_interna", lambda *a, **k: {"salva": True})

    assert execucoes.salvar(baixa, "qualquer.db", 2026) == {"salva": True}
    assert baixa.estado == "salva"


def test_descar_libera_previa_mesmo_com_falha(db_path):
    envio = _envio_em_previa()
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)
    execucoes.registrar_falha_pagina(envio, "matriculas")

    execucoes.descartar(envio)

    assert envio.estado == "descartada"
    assert envio.previa_fonte is None


# ===================== T21: salvar aproveita o candidato conferido =====================


def test_salvar_envio_grava_o_candidato_e_encerra_a_previa(db_path):
    from app.data.schema import get_connection

    envio = _envio_em_previa()
    candidato = _candidato(db_path)
    execucoes.abrir_previa(envio, candidato, db_path=db_path)
    assert envio.previa_fonte is not None

    resultado = execucoes.salvar(envio, db_path, 2026)

    assert envio.estado == "salva"
    assert envio.previa_fonte is None  # fonte liberada no sucesso
    assert resultado["matriculas"] == 1
    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
    finally:
        conn.close()
    assert total == 1


def test_salvar_envio_conflito_levanta_previa_desatualizada(db_path, monkeypatch):
    from app.data import versoes as mod_versoes

    envio = _envio_em_previa()
    candidato = _candidato(db_path)
    execucoes.abrir_previa(envio, candidato, db_path=db_path)

    def _conflito(*a, **k):
        raise mod_versoes.ConflitoDeConferencia("desatualizada")

    monkeypatch.setattr(mod_versoes, "salvar_interna", _conflito)

    with pytest.raises(execucoes.PreviaDesatualizada):
        execucoes.salvar(envio, db_path, 2026)

    assert envio.estado == "previa"  # continua pendente
    assert envio.previa_fonte is not None  # fonte continua viva


def test_salvar_envio_previa_incompleta_antes_de_gravar(db_path):
    from app.data.schema import get_connection

    envio = _envio_em_previa()
    candidato = _candidato(db_path)
    execucoes.abrir_previa(envio, candidato, db_path=db_path)
    execucoes.registrar_falha_pagina(envio, "matriculas")

    with pytest.raises(execucoes.PreviaIncompleta):
        execucoes.salvar(envio, db_path, 2026)

    assert envio.estado == "previa"
    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
    finally:
        conn.close()
    assert total == 0


def test_salvar_baixa_direta_nao_usa_salvar_interna(monkeypatch):
    baixa = execucoes.criar_execucao("pi@iffarroupilha.edu.br", [{"id_perfil": "1", "nome_perfil": "Campus A"}])
    baixa.estado = "previa"
    baixa.previa = {"valor": "previa"}
    monkeypatch.setattr("app.data.ingest.montar_versao_interna", lambda *a, **k: {"salva": True})
    monkeypatch.setattr(
        "app.data.versoes.salvar_interna",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("baixa não deve usar salvar_interna")),
    )

    assert execucoes.salvar(baixa, "qualquer.db", 2026) == {"salva": True}
    assert baixa.estado == "salva"
