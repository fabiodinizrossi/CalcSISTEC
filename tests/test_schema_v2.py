"""Testes da migração de schema v2 (`002-baixador-planilhas-sistec`, T004-T012, T015).

Cobre idempotência (`init_db` chamado duas vezes não falha nem duplica dados),
criação das tabelas novas (`interna_*`, `anterior_*`, `fatores`, `campi_sistec`,
`estado_versoes`, `historico`) e a guarda por `config.schema_versao`.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.schema import (  # noqa: E402
    SCHEMA_VERSAO_ATUAL,
    get_connection,
    init_db,
    normalizar,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def _tabelas(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {r[0] for r in rows}


def test_init_db_cria_as_tabelas_publicas_internas_e_anteriores(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        tabelas = _tabelas(conn)
    finally:
        conn.close()

    esperado = set()
    for prefixo in ("", "interna_", "anterior_"):
        for nome in ("campus", "cursos", "ciclos", "matriculas", "matriculas_eficiencia"):
            esperado.add(f"{prefixo}{nome}")
    esperado |= {"fatores", "interna_fatores", "anterior_fatores"}
    esperado |= {"campi_sistec", "estado_versoes", "historico", "config"}

    assert esperado <= tabelas


def test_init_db_grava_schema_versao_atual(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT valor FROM config WHERE chave = 'schema_versao'").fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == SCHEMA_VERSAO_ATUAL


def test_init_db_e_idempotente(db_path):
    """Chamar `init_db` duas vezes não falha e não duplica linhas de `fatores`."""
    init_db(db_path)
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        (total,) = conn.execute("SELECT COUNT(*) FROM fatores").fetchone()
        (linhas_estado,) = conn.execute("SELECT COUNT(*) FROM estado_versoes").fetchone()
    finally:
        conn.close()

    assert total > 0
    assert linhas_estado == 1


def test_init_db_marca_historico_em_aberto_como_interrompida_no_startup(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO historico (tipo, admin_email, inicio, desfecho) "
            "VALUES ('baixa', 'pi@iffarroupilha.edu.br', '2026-09-14T10:00:00', NULL)"
        )
        conn.commit()
    finally:
        conn.close()

    init_db(db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT desfecho, fim FROM historico WHERE admin_email = 'pi@iffarroupilha.edu.br'"
        ).fetchone()
    finally:
        conn.close()

    assert row[0] == "interrompida"
    assert row[1] is not None


def test_init_db_carrega_fatores_padrao_uma_unica_vez(db_path):
    """A carga inicial de `fatores`/`interna_fatores` não se repete numa segunda migração,
    mesmo se o administrador já tiver editado a tabela (RN-33: edição vale na hora)."""
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM fatores WHERE chave_tipo = 'TÉCNICO'")
        conn.commit()
        (total_apos_delete,) = conn.execute("SELECT COUNT(*) FROM fatores").fetchone()
    finally:
        conn.close()

    init_db(db_path)

    conn = get_connection(db_path)
    try:
        (total_apos_segunda_migracao,) = conn.execute("SELECT COUNT(*) FROM fatores").fetchone()
    finally:
        conn.close()

    assert total_apos_segunda_migracao == total_apos_delete


def test_normalizar_maiusculas_espacos_das_pontas_e_repetidos_preserva_acentos():
    assert normalizar("  técnico   em  informática  ") == "TÉCNICO EM INFORMÁTICA"
