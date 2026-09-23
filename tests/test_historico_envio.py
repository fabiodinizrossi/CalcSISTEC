"""Histórico das atualizações por envio de pastas (UPL-14).

O tipo `envio` distingue a atualização por arquivos enviados da baixa ao
vivo do Sistec; os desfechos são os já existentes.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.historico import encerrar, iniciar, listar  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402

# Forma da tabela antes do tipo `envio` existir (CHECK sem 'envio').
_SCHEMA_HISTORICO_ANTIGO = """
CREATE TABLE historico (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo                  TEXT NOT NULL CHECK (tipo IN ('captura','baixa')),
    admin_email           TEXT NOT NULL,
    inicio                TIMESTAMP NOT NULL,
    fim                   TIMESTAMP,
    desfecho              TEXT,
    sucessos              INTEGER,
    falhas                INTEGER,
    pausas                INTEGER,
    linhas_consolidadas   INTEGER,
    campi_mantidos        TEXT,
    detalhe               TEXT
);

CREATE INDEX IF NOT EXISTS idx_historico_inicio ON historico (inicio DESC);
"""


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.remove(path)


def test_iniciar_envio_cria_linha_e_devolve_id(db_path):
    historico_id = iniciar("envio", "admin@iffar.edu.br", db_path=db_path)
    assert historico_id

    linhas = listar(db_path=db_path)
    assert len(linhas) == 1
    assert linhas[0]["tipo"] == "envio"
    assert linhas[0]["admin_email"] == "admin@iffar.edu.br"
    assert linhas[0]["desfecho"] is None


def test_tipo_invalido_continua_recusado(db_path):
    with pytest.raises(ValueError):
        iniciar("exportacao", "admin@iffar.edu.br", db_path=db_path)


@pytest.mark.parametrize("desfecho", ["salva", "descartada", "cancelada", "falhou", "falhou_consolidacao"])
def test_desfechos_encerram_linha_de_envio(db_path, desfecho):
    historico_id = iniciar("envio", "admin@iffar.edu.br", db_path=db_path)
    encerrar(historico_id, desfecho, db_path=db_path)

    linha = listar(db_path=db_path)[0]
    assert linha["id"] == historico_id
    assert linha["desfecho"] == desfecho
    assert linha["fim"] is not None


def test_banco_anterior_ganha_o_tipo_envio_sem_perder_linhas():
    """`CREATE TABLE IF NOT EXISTS` não muda o CHECK de um banco já migrado:
    `init_db` reconstrói `historico` preservando as linhas existentes."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = get_connection(path)
        conn.executescript(_SCHEMA_HISTORICO_ANTIGO)
        conn.execute(
            "INSERT INTO historico (tipo, admin_email, inicio, desfecho) VALUES ('baixa', 'antigo@iffar.edu.br', '2026-01-01T00:00:00', 'salva')"
        )
        conn.commit()
        conn.close()

        init_db(path)

        conn = get_connection(path)
        try:
            indices = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
            }
            antigas = conn.execute("SELECT tipo, admin_email, desfecho FROM historico").fetchall()
        finally:
            conn.close()

        assert "idx_historico_inicio" in indices
        assert antigas == [("baixa", "antigo@iffar.edu.br", "salva")]
        assert iniciar("envio", "admin@iffar.edu.br", db_path=path)
        assert {linha["tipo"] for linha in listar(db_path=path)} == {"baixa", "envio"}
    finally:
        os.remove(path)
