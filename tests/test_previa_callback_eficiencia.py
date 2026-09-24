"""Testes da página Eficiência Acadêmica com fonte da prévia
(`previa-paginas-publicas`, T12): mesmo contrato `preview_id`/`State` de T11.
Com `preview_id`, KPIs e matriz leem a fonte candidata com o ano-base dela e
sem carimbo de publicação; contexto inválido devolve erro/vazio, nunca dados
públicos (PVP-01/PVP-02/PVP-04/PVP-06).
"""

import importlib
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arvore_dash import textos  # noqa: E402
from app import app as _app  # noqa: E402, F401
from app.data.ingest import preparar_versao  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec import execucoes  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402

eficiencia = importlib.import_module("pages.eficiencia")


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()
    yield
    execucoes._REGISTRO.clear()
    execucoes._REGISTRO_CAPTURAS.clear()


@pytest.fixture
def db_path(tmp_path):
    caminho = str(tmp_path / "previa.db")
    init_db(caminho)
    return caminho


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
        "DT_DATA_FIM_PREVISTO": "2025-12-31",
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


def _candidato(db_path):
    leitura = _leitura_envio()
    conjunto = consolidar([leitura["ciclo"][0][1]], [leitura["matricula"][0][1]])
    return preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)


def _envio_com_previa(db_path, monkeypatch):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO campus (co_unidade, cidade, nome_unidade) VALUES ('U1', 'Santa Maria', 'Campus SM')"
        )
        conn.commit()
    finally:
        conn.close()

    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id="sessao-A"
    )
    execucoes.registrar_leitura(envio, _leitura_envio())
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)
    monkeypatch.setattr(eficiencia, "sessao_id_atual", lambda: "sessao-A")
    return envio


def _df_publico():
    return pd.DataFrame([{"cidade": "Santa Maria", "modalidade_ensino": "PRESENCIAL"}])


def test_layout_publico_sem_preview_inalterado(monkeypatch):
    monkeypatch.setattr(eficiencia, "dataset_disponivel", lambda: True)
    monkeypatch.setattr(eficiencia, "carregar_eficiencia", _df_publico)
    monkeypatch.setattr(eficiencia, "ano_base_ativo", lambda: 2026)
    monkeypatch.setattr(eficiencia, "data_ultima_publicacao", lambda: "2026-09-22")

    layout = eficiencia.layout()

    assert layout.className == "painel-dashboard"
    assert "Atualizado em 22/09/2026" in textos(layout)
    # CPR-02: o `Store` da prévia fica no layout também no caminho público,
    # com `data=None` — o callback o declara como `State` sempre.
    store = [c for c in layout.children if getattr(c, "id", None) == "eficiencia-preview"]
    assert len(store) == 1
    assert store[0].data is None


def test_layout_previa_sem_publicacao_inicial(monkeypatch, db_path):
    # banco sem publicação: a prévia renderiza sem a mensagem pública de vazio
    envio = _envio_com_previa(db_path, monkeypatch)

    layout = eficiencia.layout(preview_id=envio.id)

    assert layout.className == "painel-dashboard"
    assert "Ainda não há dados publicados." not in textos(layout)
    assert "Atualizado em" not in textos(layout)
    assert "Ano PNP 2026" in textos(layout)
    assert any(getattr(c, "id", None) == "eficiencia-preview" for c in layout.children)


def test_callback_previa_valida_le_a_fonte(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)

    kpis, matriz = eficiencia.atualizar("com_fic", ["campus"], "__todos__", "__todos__", preview_id=envio.id)

    assert "IEA" in textos(kpis)
    assert "Sem dados" not in textos(matriz)


def test_callback_previa_forjado_devolve_erro(monkeypatch, db_path):
    _envio_com_previa(db_path, monkeypatch)

    kpis, matriz = eficiencia.atualizar("com_fic", ["campus"], "__todos__", "__todos__", preview_id="forjado")

    assert "Prévia indisponível" in textos(matriz)
    assert "IEA" not in textos(kpis)
