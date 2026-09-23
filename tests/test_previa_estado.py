"""Suíte de estado, invalidação e falhas da prévia (`previa-paginas-publicas`,
T26): abrir/recarregar não altera revisões nem tabelas; alterar a configuração
antes do Salvar devolve conflito; falha de página bloqueia; filtro vazio não
bloqueia; Descartar libera a fonte sem alterar revisões (PVP-03/PVP-06/PVP-09/
PVP-10).
"""

import importlib
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

from arvore_dash import textos  # noqa: E402

matriculas = importlib.import_module("pages.matriculas")
previa = importlib.import_module("pages.previa")


@pytest.fixture(autouse=True)
def limpar_registro():
    execucoes._REGISTRO.clear()
    yield
    execucoes._REGISTRO.clear()


@pytest.fixture
def db_path(tmp_path):
    caminho = str(tmp_path / "estado.db")
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
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO campus (co_unidade, cidade, nome_unidade) VALUES ('U1', 'Santa Maria', 'Campus SM')")
        conn.commit()
    finally:
        conn.close()

    envio = execucoes.criar_execucao_envio("pi@iffarroupilha.edu.br", ["c.csv"], ["m.csv"], sessao_id="sessao-A")
    execucoes.registrar_leitura(envio, _leitura_envio())
    execucoes.abrir_previa(envio, _candidato(db_path), db_path=db_path)
    for pagina in (previa, matriculas):
        monkeypatch.setattr(pagina, "sessao_id_atual", lambda: "sessao-A")
    return envio


def _estado_versoes(db_path):
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT rev_interna, rev_publicada FROM estado_versoes WHERE id = 1").fetchone()
    finally:
        conn.close()


def test_abrir_recarregar_nao_altera_revisoes(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    antes = _estado_versoes(db_path)

    # abre leitura várias vezes e navega pelas quatro páginas
    for pagina_slug in ("matriculas", "eficiencia", "evasao", "percentuais-legais"):
        importlib.import_module("pages.previa").layout(execucao_id=envio.id, pagina=pagina_slug)
        execucoes.abrir_leitura_previa(envio.id, "sessao-A").conn.close()

    assert _estado_versoes(db_path) == antes


def test_alterar_interna_fatores_invalida_o_salvar(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO interna_fatores (tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome) VALUES ('X', 'Y', 2.0, 1.0, 'X', 'Y')")
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(execucoes.PreviaDesatualizada):
        execucoes.salvar(envio, db_path, 2026)


def test_alterar_campus_publicado_invalida_o_salvar(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO campus (co_unidade, cidade, nome_unidade) VALUES ('U9', 'Outro', 'Campus Outro')")
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(execucoes.PreviaDesatualizada):
        execucoes.salvar(envio, db_path, 2026)


def test_alterar_ano_base_invalida_o_salvar(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE config SET valor = '2030' WHERE chave = 'ano_base'")
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(execucoes.PreviaDesatualizada):
        execucoes.salvar(envio, db_path, 2026)


def test_alterar_rev_interna_invalida_o_salvar(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE estado_versoes SET rev_interna = rev_interna + 1 WHERE id = 1")
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(execucoes.PreviaDesatualizada):
        execucoes.salvar(envio, db_path, 2026)


def test_pagina_com_falha_bloqueia_o_salvar(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    execucoes.registrar_falha_pagina(envio, "matriculas")

    with pytest.raises(execucoes.PreviaIncompleta):
        execucoes.salvar(envio, db_path, 2026)
    assert envio.estado == "previa"


def test_filtro_vazio_nao_bloqueia_o_salvar(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)

    # filtro sem linhas: o callback devolve "Sem dados", mas não registra falha
    _kpis, matriz = matriculas.atualizar("com_fic", ["campus"], "Inexistente", "__todos__", "__todos__", preview_id=envio.id)
    assert "Sem dados para o eixo selecionado." in textos(matriz)

    assert execucoes.salvar(envio, db_path, 2026)["matriculas"] == 1
    assert envio.estado == "salva"


def test_descartar_libera_a_fonte_sem_alterar_revisoes(db_path, monkeypatch):
    envio = _envio_com_previa(db_path, monkeypatch)
    antes = _estado_versoes(db_path)
    assert envio.previa_fonte is not None

    execucoes.descartar(envio)

    assert envio.estado == "descartada"
    assert envio.previa_fonte is None  # fonte liberada
    assert _estado_versoes(db_path) == antes  # revisões intactas
