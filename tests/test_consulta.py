"""Testes da consulta com conexão explícita (`previa-paginas-publicas`, T9):
`dataset_disponivel`, `ano_base_ativo` e `data_ultima_publicacao` aceitam
`conn=None` — sem conexão continuam lendo o banco publicado; com conexão não
abrem nem fecham conexão própria nem tocam `DEFAULT_DB_PATH` (PVP-04/PVP-05).
"""

import os
import sqlite3
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data import consulta, versoes  # noqa: E402
from app.data.previa import abrir_fonte_previa  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402


@pytest.fixture
def db_path():
    path = os.path.join(tempfile.mkdtemp(), "consulta.db")
    init_db(path)
    return path


def test_dataset_disponivel_sem_conn_le_banco_publicado(db_path):
    # banco recém-inicializado: nenhuma matrícula publicada
    assert consulta.dataset_disponivel(db_path) is False


def test_dataset_disponivel_com_conn_explicita():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE matriculas (co_matricula TEXT)")
    conn.execute("INSERT INTO matriculas VALUES ('M1')")

    assert consulta.dataset_disponivel(conn=conn) is True
    # a conexão do chamador continua aberta (não foi fechada pela função)
    assert conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0] == 1


def test_ano_base_ativo_sem_conn_le_config(db_path):
    # `init_db` grava o padrão `ano_base` = 2026 em `config`
    assert consulta.ano_base_ativo(db_path) == 2026


def test_ano_base_ativo_com_conn_explicita():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE config (chave TEXT, valor TEXT)")
    conn.execute("INSERT INTO config VALUES ('ano_base', '2027')")

    assert consulta.ano_base_ativo(conn=conn) == 2027
    assert conn.execute("SELECT valor FROM config").fetchone()[0] == "2027"


def test_data_ultima_publicacao_sem_conn(db_path):
    # `publicada_em` começa NULL
    assert consulta.data_ultima_publicacao(db_path) is None


def test_data_ultima_publicacao_com_conn_explicita():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE estado_versoes (id INTEGER, publicada_em TIMESTAMP)")
    conn.execute("INSERT INTO estado_versoes VALUES (1, '2026-09-22')")

    assert consulta.data_ultima_publicacao(conn=conn) == "2026-09-22"
    assert conn.execute("SELECT publicada_em FROM estado_versoes WHERE id = 1").fetchone()[0] == "2026-09-22"


# ===================== T10: cargas com conexão explícita =====================


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


def _campus():
    return pd.DataFrame([{"co_unidade": "U1", "cidade": "Santa Maria", "nome_unidade": "Campus SM"}])


def _candidato(db_path):
    from app.data.ingest import preparar_versao
    from app.sistec.consolidacao import consolidar

    conjunto = consolidar([pd.DataFrame([_linha_ciclo()])], [pd.DataFrame([_linha_matricula()])])
    return preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)


def _publicar_os_mesmos_dados(db_path, candidato):
    """Grava o `campus` publicado e publica as tabelas do candidato, para o
    banco público ter exatamente os mesmos dados da fonte da prévia."""
    conn = get_connection(db_path)
    try:
        _campus().to_sql("campus", conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()
    versoes.salvar_interna(candidato["tabelas"], db_path)
    versoes.publicar(db_path)


def test_carregar_matriculas_com_conn_igual_ao_publico(db_path):
    candidato = _candidato(db_path)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)
    _publicar_os_mesmos_dados(db_path, candidato)

    conn = fonte.abrir_leitura()
    try:
        da_fonte = consulta.carregar_matriculas(conn=conn)
    finally:
        conn.close()
    fonte.fechar()

    do_publico = consulta.carregar_matriculas(db_path)
    assert list(da_fonte.columns) == list(do_publico.columns)
    assert da_fonte.shape == do_publico.shape
    assert da_fonte["co_matricula"].tolist() == do_publico["co_matricula"].tolist()
    assert da_fonte["cidade"].tolist() == do_publico["cidade"].tolist()


def test_carregar_eficiencia_com_conn_igual_ao_publico(db_path):
    candidato = _candidato(db_path)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)
    _publicar_os_mesmos_dados(db_path, candidato)

    conn = fonte.abrir_leitura()
    try:
        da_fonte = consulta.carregar_eficiencia(conn=conn)
    finally:
        conn.close()
    fonte.fechar()

    do_publico = consulta.carregar_eficiencia(db_path)
    assert list(da_fonte.columns) == list(do_publico.columns)
    assert da_fonte.shape == do_publico.shape
    assert da_fonte["co_matricula"].tolist() == do_publico["co_matricula"].tolist()
    assert da_fonte["cidade"].tolist() == do_publico["cidade"].tolist()


def test_carregar_com_conn_nao_fecha_a_conexao_do_chamador(db_path):
    candidato = _candidato(db_path)
    fonte = abrir_fonte_previa(candidato, _campus(), db_path)

    conn = fonte.abrir_leitura()
    try:
        consulta.carregar_matriculas(conn=conn)
        # a conexão continua aberta para nova leitura — a função não a fecha
        assert conn.execute("SELECT COUNT(*) FROM matriculas").fetchone()[0] == 1
    finally:
        conn.close()
    fonte.fechar()
