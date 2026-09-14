"""Schema do banco alvo (SQLite) — Tarefa 02 do plano de reconstrução.

DDL e inicialização do armazenamento local definido em
`_reversa_sdd/migration/target_data_model.md` (AD-01 de `target_architecture.md`).
Nenhuma tabela contém coluna de dado pessoal identificável (BR-DESCARTAR-001).
"""

import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "sistec.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS campus (
    co_unidade         TEXT PRIMARY KEY,
    cidade             TEXT NOT NULL,
    nome_unidade       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cursos (
    codigo_portfolio           TEXT PRIMARY KEY,
    nome_curso_ajustado        TEXT NOT NULL,
    tipo_curso_pnp             TEXT NOT NULL,
    subtipo_curso              TEXT,
    modalidade_ensino          TEXT NOT NULL,
    eixo_tecnologico_ajustado  TEXT,
    fec                        REAL,
    fech                       REAL,
    carga_horaria_total        REAL,
    co_unidade                 TEXT NOT NULL REFERENCES campus(co_unidade),
    -- Tarefa 11: colunas adicionadas após divergência encontrada em
    -- parity_tests/06-eixo-dinamico-e-fic.feature.
    -- tipo_oferta_curso: coluna de origem do eixo "oferta" (BR-MIGRAR-020) —
    -- ausente do schema original da Tarefa 02 (GAP nunca implementado; o eixo
    -- aparecia desabilitado na UI da Tarefa 09).
    tipo_oferta_curso          TEXT,
    -- categoria_origem_curso: TIPO_CURSO cru, antes do colapso de
    -- BR-MIGRAR-017 em tipo_curso_pnp — necessário para o toggle FIC
    -- (BR-MIGRAR-021) distinguir Formação Inicial/Continuada de Mulheres
    -- Mil, distinção que o colapso de tipo_curso_pnp por si só destrói.
    categoria_origem_curso     TEXT
);

CREATE TABLE IF NOT EXISTS ciclos (
    codigo_ciclo_matricula   TEXT PRIMARY KEY,
    codigo_portfolio         TEXT NOT NULL REFERENCES cursos(codigo_portfolio),
    dt_data_inicio           DATE,
    dt_data_fim_previsto     DATE,
    tipo_programa_curso      TEXT,
    status_ciclo             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matriculas (
    co_matricula             TEXT PRIMARY KEY,
    codigo_ciclo_matricula   TEXT NOT NULL REFERENCES ciclos(codigo_ciclo_matricula),
    status_corrigido         TEXT NOT NULL,
    mes_ocorrencia_corrigido DATE,
    ano_base                 INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS matriculas_eficiencia (
    co_matricula             TEXT PRIMARY KEY,
    codigo_ciclo_matricula   TEXT NOT NULL REFERENCES ciclos(codigo_ciclo_matricula),
    status_corrigido2        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS config (
    chave  TEXT PRIMARY KEY,
    valor  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS uploads_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    uploaded_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uploaded_by     TEXT NOT NULL,
    filename        TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('valido', 'invalido')),
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_matriculas_status_corrigido
    ON matriculas (status_corrigido);

CREATE INDEX IF NOT EXISTS idx_ciclos_codigo_portfolio
    ON ciclos (codigo_portfolio);
"""

# Linha obrigatória em `config` (BR-MIGRAR-016).
DEFAULT_CONFIG = {"ano_base": "2026"}


def get_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        for chave, valor in DEFAULT_CONFIG.items():
            conn.execute(
                "INSERT OR IGNORE INTO config (chave, valor) VALUES (?, ?)",
                (chave, valor),
            )
        conn.commit()
    finally:
        conn.close()
    return db_path


if __name__ == "__main__":
    init_db()
