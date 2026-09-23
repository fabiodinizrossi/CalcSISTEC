"""Testes de `app/sistec/execucoes.py` (`002-baixador-planilhas-sistec`,
T023): transições de estado (roadmap §5.1), watchdog de par (900 s + 60 s),
pausa de 4 h — com relógio injetável, sem `sleep` real."""

import os
import sys
from datetime import datetime, timedelta

import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.sistec import execucoes  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402


class RelogioFalso:
    def __init__(self, inicio=None):
        self.agora = inicio or datetime(2026, 9, 15, 10, 0, 0)

    def __call__(self):
        return self.agora

    def avancar(self, **kwargs):
        self.agora += timedelta(**kwargs)


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()
    yield
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()


def _campi():
    return [{"id_perfil": "1", "nome_perfil": "Campus A"}, {"id_perfil": "2", "nome_perfil": "Campus B"}]


def _leitura_envio(ciclos=None):
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
    return {"ciclo": ciclos or [("ciclos.csv", pd.DataFrame([ciclo]))], "matricula": [("matriculas.csv", pd.DataFrame([matricula]))]}


def test_criar_execucao_monta_fila_ciclos_depois_matriculas():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    tipos = [p.tipo for p in execucao.fila]
    assert tipos == ["ciclo", "ciclo", "matricula", "matricula"]
    assert execucao.estado == "aguardando_login"


def test_rn11_recusa_segunda_execucao_nao_terminal():
    relogio = RelogioFalso()
    execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    with pytest.raises(execucoes.ExecucaoInvalida):
        execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)


def test_obter_por_token_recusa_token_errado():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    with pytest.raises(execucoes.ExecucaoInvalida):
        execucoes.obter_por_token(execucao.id, "token-errado")


def test_iniciar_baixa_muda_estado():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    assert execucao.estado == "baixando"


def test_proximo_aguardando_login_pede_aguardar():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    assert execucoes.proximo(execucao) == {"acao": "aguardar"}


def test_proximo_e_idempotente_no_par_em_andamento():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    primeiro = execucoes.proximo(execucao)
    segundo = execucoes.proximo(execucao)
    assert primeiro == segundo
    assert primeiro["par"]["n"] == 1


def test_reportar_sessao_expirada_pausa_execucao_e_par_volta_a_pendente():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    execucoes.proximo(execucao)

    execucoes.reportar_falha(execucao, 1, "sessao_expirada")

    assert execucao.estado == "pausada"
    assert execucao.pausas == 1
    assert execucao.par_por_n(1).status == "pendente"


def test_retomar_volta_a_baixando():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    execucoes.proximo(execucao)
    execucoes.reportar_falha(execucao, 1, "sessao_expirada")

    execucoes.retomar(execucao)
    assert execucao.estado == "baixando"
    assert execucao.pausada_desde is None


def test_reportar_tempo_esgotado_falha_o_par_e_segue_fila():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    execucoes.proximo(execucao)

    execucoes.reportar_falha(execucao, 1, "tempo_esgotado")

    assert execucao.estado == "baixando"
    assert execucao.par_por_n(1).status == "falhou"
    assert execucao.par_por_n(1).motivo == "tempo_esgotado"
    assert "1" in execucao.campi_falhos


def test_watchdog_falha_par_parado_ha_mais_de_900_mais_60s():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    execucoes.proximo(execucao)

    relogio.avancar(seconds=900 + 60 + 1)
    execucoes.varrer(execucao)

    assert execucao.par_por_n(1).status == "falhou"
    assert execucao.par_por_n(1).motivo == "tempo_esgotado"


def test_watchdog_nao_falha_par_dentro_do_prazo():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    execucoes.proximo(execucao)

    relogio.avancar(seconds=900 + 30)
    execucoes.varrer(execucao)

    assert execucao.par_por_n(1).status == "em_andamento"


def test_pausa_encerra_apos_4_horas():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    execucoes.proximo(execucao)
    execucoes.reportar_falha(execucao, 1, "sessao_expirada")

    relogio.avancar(hours=4, seconds=1)
    execucoes.varrer(execucao)

    assert execucao.estado == "encerrada_pausa"


def test_pausa_nao_encerra_antes_de_4_horas():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.iniciar_baixa(execucao)
    execucoes.proximo(execucao)
    execucoes.reportar_falha(execucao, 1, "sessao_expirada")

    relogio.avancar(hours=3, minutes=59)
    execucoes.varrer(execucao)

    assert execucao.estado == "pausada"


def test_cancelar_a_partir_de_qualquer_estado_nao_terminal():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.cancelar(execucao)
    assert execucao.estado == "cancelada"


def test_cancelar_estado_terminal_falha():
    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    execucoes.cancelar(execucao)
    with pytest.raises(execucoes.ExecucaoInvalida):
        execucoes.cancelar(execucao)


def test_fila_vazia_consolida_e_vai_para_previa(monkeypatch):
    import pandas as pd

    relogio = RelogioFalso()
    execucao = execucoes.criar_execucao("pi@iffarroupilha.edu.br", [{"id_perfil": "1", "nome_perfil": "Campus A"}], relogio=relogio)
    execucoes.iniciar_baixa(execucao)

    def _preencher(n, tipo):
        par = execucao.par_por_n(n)
        par.status = "baixado"
        if tipo == "ciclo":
            par.df = pd.DataFrame(
                [
                    {
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
                ]
            )
        else:
            par.df = pd.DataFrame(
                [
                    {
                        "CO_MATRICULA": "M1",
                        "CODIGO_CICLO_MATRICULA": "C1",
                        "STATUS_MATRICULA_SISTEC": "EM_CURSO",
                        "MES_OCORRENCIA_CORRIGIDO": "2026-01-01",
                    }
                ]
            )

    _preencher(1, "ciclo")
    _preencher(2, "matricula")

    resultado = execucoes.proximo(execucao)
    assert resultado == {"acao": "encerrar"}
    assert execucao.estado == "previa"
    assert execucao.previa is not None


def test_criar_execucao_envio_recusa_admin_com_execucao_nao_terminal():
    relogio = RelogioFalso()
    execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)

    with pytest.raises(execucoes.ExecucaoInvalida):
        execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], relogio=relogio)


def test_criar_execucao_envio_aceita_admin_apos_execucao_terminal():
    relogio = RelogioFalso()
    anterior = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi(), relogio=relogio)
    anterior.estado = "cancelada"

    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], relogio=relogio)

    assert envio is execucoes.obter_do_admin("pi@iffarroupilha.edu.br")


def test_criar_execucao_envio_monta_um_par_por_arquivo_e_define_origem():
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["c1.csv", "c2.csv"], ["m1.csv"])

    assert envio.origem == "envio"
    assert envio.estado == "consolidando"
    assert [(par.tipo, par.id_perfil, par.nome_perfil) for par in envio.fila] == [
        ("ciclo", None, "c1.csv"), ("ciclo", None, "c2.csv"), ("matricula", None, "m1.csv")
    ]


def test_criar_execucao_de_baixa_mantem_origem_padrao():
    baixa = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi())

    assert baixa.origem == "baixa"


def test_registrar_leitura_preenche_pares_e_leva_envio_para_previa():
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"])

    execucoes.registrar_leitura(envio, _leitura_envio())

    assert [(par.status, par.linhas, par.df is not None) for par in envio.fila] == [("baixado", 1, True), ("baixado", 1, True)]
    assert envio.estado == "previa"
    assert envio.previa is not None


def test_registrar_leitura_marca_falha_de_consolidacao_sem_previa():
    primeiro = _leitura_envio()["ciclo"][0][1].iloc[0].to_dict()
    segundo = {**primeiro, "NOME_CURSO": "DIVERGENTE"}
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["c1.csv", "c2.csv"], ["matriculas.csv"])

    execucoes.registrar_leitura(envio, _leitura_envio([("c1.csv", pd.DataFrame([primeiro])), ("c2.csv", pd.DataFrame([segundo]))]))

    assert envio.estado == "falhou_consolidacao"
    assert envio.previa is None


def test_definir_campi_preservados_grava_codigos_na_execucao():
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"])

    execucoes.definir_campi_preservados(envio, ["U2", "U1", "U2"])

    assert envio.campi_falhos == {"U1", "U2"}


def test_salvar_envio_com_campi_preservados_exige_confirmacao(tmp_path):
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"])
    execucoes.registrar_leitura(envio, _leitura_envio())
    execucoes.definir_campi_preservados(envio, ["U2"])

    with pytest.raises(execucoes.ConfirmacaoNecessaria):
        execucoes.salvar(envio, str(tmp_path / "interna.db"), 2026)

    assert envio.estado == "previa"


def test_salvar_envio_confirmado_preserva_linhas_do_campus_ausente(tmp_path):
    from app.data.ingest import montar_versao_interna
    from app.data.schema import get_connection, init_db

    db_path = str(tmp_path / "interna.db")
    init_db(db_path)
    anterior = consolidar([_leitura_envio()["ciclo"][0][1]], [_leitura_envio()["matricula"][0][1]])
    montar_versao_interna(anterior, set(), db_path=db_path, ano_base=2026)

    ciclo_novo = _leitura_envio()["ciclo"][0][1].assign(CO_UNIDADE="U2", CODIGO_CICLO_MATRICULA="C2", **{"CÓDIGO DO PORTFÓLIO": "P2"})
    matricula_nova = _leitura_envio()["matricula"][0][1].assign(CO_MATRICULA="M2", CODIGO_CICLO_MATRICULA="C2")
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"])
    execucoes.registrar_leitura(envio, {"ciclo": [("ciclos.csv", ciclo_novo)], "matricula": [("matriculas.csv", matricula_nova)]})
    execucoes.definir_campi_preservados(envio, ["U1"])

    resultado = execucoes.salvar(envio, db_path, 2026, confirmado=True)

    conn = get_connection(db_path)
    try:
        linhas = conn.execute("SELECT codigo_ciclo_matricula, co_unidade FROM interna_ciclos ORDER BY codigo_ciclo_matricula").fetchall()
    finally:
        conn.close()
    assert resultado["campi_mantidos"] == ["U1"]
    assert linhas == [("C1", "U1"), ("C2", "U2")]


def test_salvar_envio_sem_campi_preservados_nao_exige_confirmacao(monkeypatch):
    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"])
    envio.estado = "previa"
    envio.previa = {"valor": "previa"}
    monkeypatch.setattr("app.data.ingest.montar_versao_interna", lambda *args, **kwargs: {"salva": True})

    assert execucoes.salvar(envio, "qualquer.db", 2026) == {"salva": True}
    assert envio.estado == "salva"


def test_salvar_baixa_mantem_comportamento_sem_confirmacao(monkeypatch):
    baixa = execucoes.criar_execucao("pi@iffarroupilha.edu.br", _campi())
    baixa.estado = "previa"
    baixa.previa = {"valor": "previa"}
    baixa.campi_falhos = {"U1"}
    monkeypatch.setattr("app.data.ingest.montar_versao_interna", lambda *args, **kwargs: {"salva": True})

    assert execucoes.salvar(baixa, "qualquer.db", 2026) == {"salva": True}
    assert baixa.estado == "salva"


# ===================== Captura de perfis (roadmap §5.1) =====================


def test_criar_captura_e_receber_perfis_vai_para_revisao():
    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.receber_perfis(captura, [{"id_perfil": "1", "nome_perfil": "Campus A", "co_unidade": "U1"}])
    assert captura.estado == "revisao"


def test_receber_perfis_vazio_vai_para_sem_resultado():
    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.receber_perfis(captura, [])
    assert captura.estado == "sem_resultado"


def test_salvar_lista_captura_grava_via_campi(tmp_path):
    from app.data.schema import get_connection, init_db

    db_path = str(tmp_path / "captura.db")
    init_db(db_path)

    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.receber_perfis(captura, [{"id_perfil": "1", "nome_perfil": "Campus A", "co_unidade": "U1"}])
    execucoes.salvar_lista_captura(captura, db_path)

    assert captura.estado == "salva"
    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM campi_sistec").fetchone()[0]
    finally:
        conn.close()
    assert total == 1


def test_receber_perfis_deduplica_por_co_unidade():
    """Sistec real lista um perfil por papel (Assessor/Gestor) para o mesmo
    campus, repetindo o código da unidade (achado 2 da F0) — `co_unidade` é
    `UNIQUE` em `campi_sistec`, então dois perfis com o mesmo código não
    podem ir ambos para a revisão/gravação (IntegrityError do SQLite)."""
    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.receber_perfis(
        captura,
        [
            {"id_perfil": "1", "nome_perfil": "Assessor - Campus A", "co_unidade": "U1"},
            {"id_perfil": "2", "nome_perfil": "Gestor - Campus A", "co_unidade": "U1"},
            {"id_perfil": "3", "nome_perfil": "Assessor - Campus B", "co_unidade": "U2"},
        ],
    )
    assert captura.estado == "revisao"
    assert [p["id_perfil"] for p in captura.perfis] == ["1", "3"]


def test_receber_perfis_nao_deduplica_perfis_sem_co_unidade():
    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.receber_perfis(
        captura,
        [
            {"id_perfil": "1", "nome_perfil": "Campus sem código A", "co_unidade": None},
            {"id_perfil": "2", "nome_perfil": "Campus sem código B", "co_unidade": None},
        ],
    )
    assert [p["id_perfil"] for p in captura.perfis] == ["1", "2"]


def test_salvar_lista_captura_com_perfis_duplicados_por_co_unidade(tmp_path):
    from app.data.schema import get_connection, init_db

    db_path = str(tmp_path / "captura.db")
    init_db(db_path)

    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.receber_perfis(
        captura,
        [
            {"id_perfil": "1", "nome_perfil": "Assessor - Campus A", "co_unidade": "U1"},
            {"id_perfil": "2", "nome_perfil": "Gestor - Campus A", "co_unidade": "U1"},
        ],
    )
    execucoes.salvar_lista_captura(captura, db_path)

    assert captura.estado == "salva"
    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM campi_sistec").fetchone()[0]
    finally:
        conn.close()
    assert total == 1


def test_cancelar_captura_a_partir_de_revisao():
    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.receber_perfis(captura, [{"id_perfil": "1", "nome_perfil": "Campus A", "co_unidade": "U1"}])
    execucoes.cancelar_captura(captura)
    assert captura.estado == "cancelada"


def test_criar_captura_descarta_automaticamente_captura_presa_do_mesmo_admin():
    """Emenda E001 (`002-baixador-planilhas-sistec`, RN-05, clarify
    2026-09-15 Q2): uma captura anterior presa em `aguardando_login` não
    bloqueia nem fica órfã — é marcada `cancelada` e some das consultas por
    captura ativa, para uma nova poder ser iniciada sem intervenção manual."""
    relogio = RelogioFalso()
    presa = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    assert presa.estado == "aguardando_login"

    nova = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)

    assert presa.estado == "cancelada"
    assert nova.id != presa.id
    assert execucoes.obter_captura_do_admin("pi@iffarroupilha.edu.br").id == nova.id


def test_criar_captura_nao_descarta_captura_presa_de_outro_admin():
    relogio = RelogioFalso()
    presa = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    execucoes.criar_captura("outro@iffarroupilha.edu.br", relogio=relogio)

    assert presa.estado == "aguardando_login"


def test_obter_captura_por_token_recusa_token_errado():
    relogio = RelogioFalso()
    captura = execucoes.criar_captura("pi@iffarroupilha.edu.br", relogio=relogio)
    with pytest.raises(execucoes.ExecucaoInvalida):
        execucoes.obter_captura_por_token(captura.id, "errado")
