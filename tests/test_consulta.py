"""Testes da consulta com conexão explícita (`previa-paginas-publicas`, T9):
`dataset_disponivel`, `ano_base_ativo` e `data_ultima_publicacao` aceitam
`conn=None` — sem conexão continuam lendo o banco publicado; com conexão não
abrem nem fecham conexão própria nem tocam `DEFAULT_DB_PATH` (PVP-04/PVP-05).
"""

import os
import sqlite3
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data import consulta  # noqa: E402
from app.data.schema import init_db  # noqa: E402


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
