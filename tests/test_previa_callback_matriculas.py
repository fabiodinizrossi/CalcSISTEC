"""Testes da página Matrículas com fonte da prévia (`previa-paginas-publicas`,
T11): `layout(preview_id)` e o callback `atualizar` distinguem o caminho
público do privado. Com `preview_id`, leem pela conexão da fonte candidata e
usam o ano-base do candidato; contexto inválido devolve erro/vazio, nunca
dados públicos (PVP-01/PVP-02/PVP-04/PVP-06).
"""

import importlib
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arvore_dash import textos  # noqa: E402
from app import app as _app  # noqa: E402, F401  (instancia e registra as páginas)
from app.data.ingest import preparar_versao  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec import execucoes  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402

matriculas = importlib.import_module("pages.matriculas")


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


def _candidato(db_path):
    leitura = _leitura_envio()
    conjunto = consolidar([leitura["ciclo"][0][1]], [leitura["matricula"][0][1]])
    return preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)


def _envio_com_previa(db_path, monkeypatch):
    """Cria um envio em `previa`, abre a fonte candidata e faz
    `sessao_id_atual` devolver a sessão dona."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO interna_campus (co_unidade, cidade, nome_unidade) VALUES ('U1', 'Santa Maria', 'Campus SM')"
        )
        conn.commit()
    finally:
        conn.close()

    envio = execucoes.criar_execucao_envio(
        "pi@iffarroupilha.edu.br", ["ciclos.csv"], ["matriculas.csv"], sessao_id="sessao-A"
    )
    execucoes.registrar_leitura(envio, _leitura_envio())
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)
    monkeypatch.setattr(matriculas, "sessao_id_atual", lambda: "sessao-A")
    return envio


def _df_publico():
    return pd.DataFrame(
        [{"cidade": "Santa Maria", "tipo_curso_pnp": "TECNICO", "tipo_programa_curso": "REGULAR"}]
    )


def test_layout_publico_sem_preview_inalterado(monkeypatch):
    monkeypatch.setattr(matriculas, "dataset_disponivel", lambda: True)
    monkeypatch.setattr(matriculas, "carregar_matriculas", _df_publico)
    monkeypatch.setattr(matriculas, "ano_base_ativo", lambda: 2026)
    monkeypatch.setattr(matriculas, "data_ultima_publicacao", lambda: "2026-09-22")

    layout = matriculas.layout()

    assert layout.className == "painel-landing"
    assert "Atualizado em 22/09/2026" in textos(layout)
    # CPR-02: o `Store` da prévia fica no layout também no caminho público,
    # com `data=None` — o callback o declara como `State` sempre.
    store = [c for c in layout.children if getattr(c, "id", None) == "matriculas-preview"]
    assert len(store) == 1
    assert store[0].data is None


def test_layout_previa_le_a_fonte(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)

    layout = matriculas.layout(preview_id=envio.id)

    assert layout.className == "painel-landing"
    # omite o carimbo de publicação e usa o ano-base do candidato
    assert "Atualizado em" not in textos(layout)
    assert "Ano PNP 2026" in textos(layout)
    assert any(getattr(c, "id", None) == "matriculas-preview" for c in layout.children)


def test_callback_previa_valida_le_a_fonte(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)

    kpis, matriz = matriculas.atualizar(
        "com_fic", ["campus"], "__todos__", "__todos__", "__todos__", preview_id=envio.id
    )

    assert "Matrículas 1" in textos(kpis)
    assert "Sem dados" not in textos(matriz)


def test_callback_previa_forjado_devolve_erro(monkeypatch, db_path):
    _envio_com_previa(db_path, monkeypatch)

    kpis, matriz = matriculas.atualizar(
        "com_fic", ["campus"], "__todos__", "__todos__", "__todos__", preview_id="forjado"
    )

    assert "Prévia indisponível" in textos(matriz)
    # nunca dados públicos por engano
    assert "Matrículas" not in textos(kpis)


def test_callback_previa_filtro_vazio(monkeypatch, db_path):
    envio = _envio_com_previa(db_path, monkeypatch)

    kpis, matriz = matriculas.atualizar(
        "com_fic", ["campus"], "Inexistente", "__todos__", "__todos__", preview_id=envio.id
    )

    assert "Sem dados para o eixo selecionado." in textos(matriz)


def test_callback_publico_filtro_vazio(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "co_matricula": "M1",
                "status_corrigido": "EM_CURSO",
                "ano_base": 2026,
                "mes_ocorrencia_corrigido": "JUNHO 2026",
                "codigo_ciclo_matricula": "C1",
                "tipo_programa_curso": "REGULAR",
                "dt_data_inicio": "2026-01-01",
                "codigo_portfolio": "P1",
                "nome_curso_ajustado": "X",
                "tipo_curso_pnp": "TECNICO",
                "subtipo_curso": "Técnico",
                "modalidade_ensino": "PRESENCIAL",
                "eixo_tecnologico_ajustado": "EIXO1",
                "carga_horaria_total": 1200,
                "fec": 1.0,
                "fech": 1.0,
                "co_unidade": "U1",
                "tipo_oferta_curso": "ANUAL",
                "categoria_origem_curso": "TECNICO",
                "cidade": "Santa Maria",
            }
        ]
    )
    monkeypatch.setattr(matriculas, "carregar_matriculas", lambda: df)
    monkeypatch.setattr(matriculas, "ano_base_ativo", lambda: 2026)

    _kpis, matriz = matriculas.atualizar("com_fic", ["campus"], "Inexistente", "__todos__", "__todos__")

    assert "Sem dados para o eixo selecionado." in textos(matriz)
