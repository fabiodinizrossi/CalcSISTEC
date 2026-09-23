"""Rota de Salvar de um envio com conferência da origem (`previa-paginas-publicas`,
T22): 409 para conferência desatualizada e para página com falha, 404 para
execução inexistente, e o caminho feliz gravando o candidato conferido
(PVP-04/PVP-09/PVP-10).
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as app_module  # noqa: E402
from app.data.ingest import preparar_versao  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec import execucoes  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402

ADMIN = "pi@ife.edu.br"


@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    execucoes._REGISTRO.clear()
    monkeypatch.setattr(app_module, "historico_iniciar", lambda tipo, email: 1)
    monkeypatch.setattr(app_module, "historico_encerrar", lambda *a, **k: None)
    yield
    execucoes._REGISTRO.clear()


@pytest.fixture
def sessao():
    cliente = app_module.server.test_client()
    with cliente.session_transaction() as s:
        s["admin_usuario"] = ADMIN
        s["admin_autenticado"] = True
    return cliente


def _execucao_envio_previa():
    execucao = execucoes.criar_execucao_envio(ADMIN, ["ciclos.csv"], ["matriculas.csv"])
    execucao.estado = "previa"
    return execucao


def test_salvar_previa_desatualizada_responde_409(sessao, monkeypatch):
    execucao = _execucao_envio_previa()

    def _desatualizada(*a, **k):
        raise execucoes.PreviaDesatualizada("desatualizada")

    monkeypatch.setattr(execucoes, "salvar", _desatualizada)

    resposta = sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={"confirmar_preservacao": True})

    assert resposta.status_code == 409
    corpo = resposta.get_json()
    assert corpo["erro"] == "previa_desatualizada"
    assert "reenviar" in corpo["mensagem"]


def test_salvar_previa_incompleta_responde_409(sessao, monkeypatch):
    execucao = _execucao_envio_previa()

    def _incompleta(*a, **k):
        raise execucoes.PreviaIncompleta(["matriculas", "evasao"])

    monkeypatch.setattr(execucoes, "salvar", _incompleta)

    resposta = sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={})

    assert resposta.status_code == 409
    corpo = resposta.get_json()
    assert corpo["erro"] == "previa_incompleta"
    assert corpo["paginas"] == ["matriculas", "evasao"]


def test_salvar_confirmacao_necessaria_continua_409(sessao):
    execucao = _execucao_envio_previa()
    execucoes.definir_campi_preservados(execucao, ["U2"])

    resposta = sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={})

    assert resposta.status_code == 409
    assert resposta.get_json() == {"erro": "confirmacao_necessaria", "campi_preservados": ["U2"]}


def test_salvar_execucao_inexistente_404(sessao):
    resposta = sessao.post("/admin/atualizar/execucoes/nao-existe/salvar", json={})

    assert resposta.status_code == 404
    assert resposta.get_json() == {"erro": "execucao_nao_encontrada"}


def _linha_ciclo():
    return {
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


def _linha_matricula():
    return {
        "CO_MATRICULA": "M1",
        "CODIGO_CICLO_MATRICULA": "C1",
        "STATUS_MATRICULA_SISTEC": "EM_CURSO",
        "MES_OCORRENCIA_CORRIGIDO": "2026-01-01",
    }


def test_salvar_envio_caminho_feliz(sessao, monkeypatch, tmp_path):
    db_path = str(tmp_path / "salvar.db")
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO campus (co_unidade, cidade, nome_unidade) VALUES ('U1', 'Santa Maria', 'Campus SM')")
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(app_module, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(app_module, "ano_base_ativo", lambda: 2026)

    conjunto = consolidar([pd.DataFrame([_linha_ciclo()])], [pd.DataFrame([_linha_matricula()])])
    candidato = preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)

    execucao = _execucao_envio_previa()
    execucoes.abrir_previa(execucao, candidato, db_path=db_path)

    resposta = sessao.post(f"/admin/atualizar/execucoes/{execucao.id}/salvar", json={})

    assert resposta.status_code == 200
    assert execucao.estado == "salva"
    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
    finally:
        conn.close()
    assert total == 1
