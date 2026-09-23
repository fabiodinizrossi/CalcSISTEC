"""Schema do banco alvo (SQLite) — Tarefa 02 do plano de reconstrução.

DDL e inicialização do armazenamento local definido em
`_reversa_sdd/migration/target_data_model.md` (AD-01 de `target_architecture.md`).
Nenhuma tabela contém coluna de dado pessoal identificável (BR-DESCARTAR-001).

Schema v2 (`002-baixador-planilhas-sistec`, ver
`_reversa_forward/002-baixador-planilhas-sistec/data-delta.md`): versionamento
interna/publicada/anterior, fatores por versão, lista de campi do Sistec,
estado de versões e histórico de execuções.
"""

import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "sistec.db")
FATORES_PADRAO_PATH = os.path.join(os.path.dirname(__file__), "padroes", "dados_FEC_PNP.xlsx")

SCHEMA_VERSAO_ATUAL = "2"

# Conversão de tipos do arquivo de fatores (D-09): normalizar(tipo) -> tipo gravado.
CONVERSAO_TIPO_FATORES = {
    "ESPECIALIZAÇÃO (LATO SENSU/PROFISSIONAL TECNOLÓGICA)": "ESPECIALIZAÇÃO (LATO SENSU)",
    "MESTRADO (ACADÊMICO/PROFISSIONAL)": "MESTRADO PROFISSIONAL",
}

# Tipos cuja chave é só o tipo (D-07, D-10): sem casamento por nome do curso.
TIPOS_SO_PELO_TIPO = {
    "ESPECIALIZAÇÃO (LATO SENSU)",
    "QUALIFICAÇÃO PROFISSIONAL",
    "MESTRADO PROFISSIONAL",
}


def normalizar(texto):
    """RN-36: maiúsculas, espaços das pontas e repetidos no meio removidos, acentos preservados."""
    return " ".join(str(texto).split()).upper()


def _ddl_conjunto(prefixo, fk_campus=True):
    """DDL das 5 tabelas de um conjunto (publicada/interna/anterior), mesmo índice, prefixo no nome.

    `fk_campus`: mantido só por simetria de assinatura; nenhum conjunto tem
    FK `cursos.co_unidade -> campus` (RN-16, sai na v2).
    """
    p = prefixo
    return f"""
CREATE TABLE IF NOT EXISTS {p}campus (
    co_unidade         TEXT PRIMARY KEY,
    cidade             TEXT NOT NULL,
    nome_unidade       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS {p}cursos (
    codigo_portfolio           TEXT PRIMARY KEY,
    nome_curso_ajustado        TEXT NOT NULL,
    tipo_curso_pnp             TEXT NOT NULL,
    subtipo_curso              TEXT,
    modalidade_ensino          TEXT NOT NULL,
    eixo_tecnologico_ajustado  TEXT,
    fec                        REAL,
    fech                       REAL,
    carga_horaria_total        REAL,
    co_unidade                 TEXT NOT NULL,
    tipo_oferta_curso          TEXT,
    categoria_origem_curso     TEXT,
    fator_nao_encontrado       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS {p}ciclos (
    codigo_ciclo_matricula   TEXT PRIMARY KEY,
    codigo_portfolio         TEXT NOT NULL REFERENCES {p}cursos(codigo_portfolio),
    co_unidade               TEXT NOT NULL,
    dt_data_inicio           DATE,
    dt_data_fim_previsto     DATE,
    tipo_programa_curso      TEXT,
    status_ciclo             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS {p}matriculas (
    co_matricula             TEXT PRIMARY KEY,
    codigo_ciclo_matricula   TEXT NOT NULL REFERENCES {p}ciclos(codigo_ciclo_matricula),
    status_corrigido         TEXT NOT NULL,
    mes_ocorrencia_corrigido DATE,
    ano_base                 INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS {p}matriculas_eficiencia (
    co_matricula             TEXT PRIMARY KEY,
    codigo_ciclo_matricula   TEXT NOT NULL REFERENCES {p}ciclos(codigo_ciclo_matricula),
    status_corrigido2        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_{p}matriculas_status_corrigido
    ON {p}matriculas (status_corrigido);

CREATE INDEX IF NOT EXISTS idx_{p}ciclos_codigo_portfolio
    ON {p}ciclos (codigo_portfolio);
"""


def _ddl_fatores(tabela):
    return f"""
CREATE TABLE IF NOT EXISTS {tabela} (
    tipo_curso   TEXT NOT NULL,
    nome_curso   TEXT NOT NULL,
    fec          REAL NOT NULL,
    fech         REAL NOT NULL,
    chave_tipo   TEXT NOT NULL,
    chave_nome   TEXT NOT NULL,
    PRIMARY KEY (chave_tipo, chave_nome)
);
"""


# Tabelas públicas (vazias na migração, RN-30). Sem FK cursos.co_unidade -> campus (RN-16).
SCHEMA_PUBLICAS_SQL = _ddl_conjunto("")

# `interna_*` e `anterior_*`: mesmo DDL, prefixo no nome (data-delta.md §1).
SCHEMA_INTERNA_SQL = _ddl_conjunto("interna_")
SCHEMA_ANTERIOR_SQL = _ddl_conjunto("anterior_")

SCHEMA_FATORES_SQL = _ddl_fatores("fatores") + _ddl_fatores("interna_fatores") + _ddl_fatores("anterior_fatores")

SCHEMA_CAMPI_SISTEC_SQL = """
CREATE TABLE IF NOT EXISTS campi_sistec (
    id_perfil      TEXT PRIMARY KEY,
    nome_perfil    TEXT NOT NULL,
    ordem          INTEGER NOT NULL,
    co_unidade     TEXT UNIQUE,
    cidade         TEXT,
    nome_unidade   TEXT,
    capturado_em   TIMESTAMP NOT NULL,
    ativo          INTEGER NOT NULL DEFAULT 1,
    origem         TEXT NOT NULL DEFAULT 'sistec'
);
"""

SCHEMA_ESTADO_VERSOES_SQL = """
CREATE TABLE IF NOT EXISTS estado_versoes (
    id                     INTEGER PRIMARY KEY CHECK (id = 1),
    rev_interna            INTEGER NOT NULL DEFAULT 0,
    rev_publicada          INTEGER,
    rev_anterior           INTEGER,
    interna_gravada_em     TIMESTAMP,
    publicada_em           TIMESTAMP,
    publicada_por          TEXT
);
"""

SCHEMA_HISTORICO_SQL = """
CREATE TABLE IF NOT EXISTS historico (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo                  TEXT NOT NULL CHECK (tipo IN (
                              'captura','baixa','envio','publicacao','desfazer_publicacao',
                              'configuracao_aplicada_publico','fatores_arquivo','fatores_restaurar_padrao')),
    admin_email           TEXT NOT NULL,
    inicio                TIMESTAMP NOT NULL,
    fim                   TIMESTAMP,
    desfecho              TEXT CHECK (desfecho IN (
                              'salva','descartada','cancelada','interrompida','encerrada_pausa',
                              'falhou_consolidacao','sem_resultado','falhou',
                              'publicada','publicacao_desfeita','aplicada')),
    sucessos              INTEGER,
    falhas                INTEGER,
    pausas                INTEGER,
    linhas_consolidadas   INTEGER,
    campi_mantidos        TEXT,
    detalhe               TEXT
);

CREATE INDEX IF NOT EXISTS idx_historico_inicio ON historico (inicio DESC);
"""

SCHEMA_CONFIG_SQL = """
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
"""

# Linha obrigatória em `config` (BR-MIGRAR-016).
DEFAULT_CONFIG = {"ano_base": "2026"}

# Ordem de DROP respeitando as FKs internas do conjunto público (T005).
_TABELAS_PUBLICAS_EM_ORDEM_DE_DROP = (
    "matriculas_eficiencia",
    "matriculas",
    "ciclos",
    "cursos",
    "campus",
)


def get_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _config_get(conn, chave):
    row = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
    return row[0] if row else None


def _config_set(conn, chave, valor):
    conn.execute(
        "INSERT INTO config (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, valor),
    )


def _converter_tipo_fator(tipo_bruto):
    tipo_normalizado = normalizar(tipo_bruto)
    for origem, destino in CONVERSAO_TIPO_FATORES.items():
        if normalizar(origem) == tipo_normalizado:
            return destino
    return str(tipo_bruto).strip()


def _linhas_fatores_padrao(caminho=FATORES_PADRAO_PATH):
    """Lê `dados_FEC_PNP.xlsx` e devolve linhas prontas para `fatores`/`interna_fatores` (D-09, D-11)."""
    import openpyxl

    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    aba = None
    for nome in wb.sheetnames:
        ws = wb[nome]
        cabecalho = [normalizar(c.value) for c in next(ws.iter_rows(max_row=1))[:6]]
        if {"TIPO DE CURSO", "CURSO", "FEC", "FECH"}.issubset(set(cabecalho)):
            aba = ws
            indices = {nome_col: i for i, nome_col in enumerate(cabecalho)}
            break
    if aba is None:
        raise ValueError("Arquivo de fatores padrão sem aba com as colunas TIPO DE CURSO, CURSO, FEC, FECH")

    linhas = []
    vistas = set()
    for row in aba.iter_rows(min_row=2, values_only=True):
        tipo_bruto = row[indices["TIPO DE CURSO"]]
        nome_bruto = row[indices["CURSO"]]
        fec = row[indices["FEC"]]
        fech = row[indices["FECH"]]
        if tipo_bruto is None or nome_bruto is None or fec is None or fech is None:
            continue
        tipo_curso = _converter_tipo_fator(tipo_bruto)
        chave_tipo = normalizar(tipo_curso)
        so_pelo_tipo = chave_tipo in TIPOS_SO_PELO_TIPO
        nome_curso = "TODOS" if so_pelo_tipo else str(nome_bruto).strip()
        chave_nome = "" if so_pelo_tipo else normalizar(nome_curso)
        chave = (chave_tipo, chave_nome)
        if chave in vistas:
            continue
        vistas.add(chave)
        linhas.append((tipo_curso, nome_curso, float(fec), float(fech), chave_tipo, chave_nome))
    return linhas


def _carregar_fatores_padrao(conn, caminho=FATORES_PADRAO_PATH):
    linhas = _linhas_fatores_padrao(caminho)
    for tabela in ("fatores", "interna_fatores"):
        conn.executemany(
            f"INSERT OR REPLACE INTO {tabela} "
            "(tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome) VALUES (?, ?, ?, ?, ?, ?)",
            linhas,
        )


def _garantir_colunas_campi_sistec(conn):
    """Bancos criados antes de `ativo`/`origem` (lista de campi editável em
    Configurações) ganham as colunas com os valores padrão."""
    colunas = {linha[1] for linha in conn.execute("PRAGMA table_info(campi_sistec)")}
    if "ativo" not in colunas:
        conn.execute("ALTER TABLE campi_sistec ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")
    if "origem" not in colunas:
        conn.execute("ALTER TABLE campi_sistec ADD COLUMN origem TEXT NOT NULL DEFAULT 'sistec'")


_COLUNAS_HISTORICO = (
    "id", "tipo", "admin_email", "inicio", "fim", "desfecho",
    "sucessos", "falhas", "pausas", "linhas_consolidadas", "campi_mantidos", "detalhe",
)


def _garantir_tipo_envio_historico(conn):
    """Bancos v2 criados antes da atualização por envio têm o `CHECK` de
    `historico.tipo` sem 'envio' (`CREATE TABLE IF NOT EXISTS` não altera a
    restrição existente). Reconstrói a tabela preservando as linhas."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'historico'"
    ).fetchone()
    if row is None or "'envio'" in row[0]:
        return

    colunas = ", ".join(_COLUNAS_HISTORICO)
    conn.execute("DROP INDEX IF EXISTS idx_historico_inicio")
    conn.execute("ALTER TABLE historico RENAME TO historico_sem_envio")
    conn.executescript(SCHEMA_HISTORICO_SQL)
    conn.execute(f"INSERT INTO historico ({colunas}) SELECT {colunas} FROM historico_sem_envio")
    conn.execute("DROP TABLE historico_sem_envio")


def init_db(db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_CONFIG_SQL)
        for chave, valor in DEFAULT_CONFIG.items():
            conn.execute(
                "INSERT OR IGNORE INTO config (chave, valor) VALUES (?, ?)",
                (chave, valor),
            )

        schema_versao = _config_get(conn, "schema_versao")
        if schema_versao is None:
            for tabela in _TABELAS_PUBLICAS_EM_ORDEM_DE_DROP:
                conn.execute(f"DROP TABLE IF EXISTS {tabela}")
            conn.executescript(SCHEMA_PUBLICAS_SQL)
        else:
            conn.executescript(SCHEMA_PUBLICAS_SQL)

        conn.executescript(SCHEMA_INTERNA_SQL)
        conn.executescript(SCHEMA_ANTERIOR_SQL)
        conn.executescript(SCHEMA_FATORES_SQL)
        conn.executescript(SCHEMA_CAMPI_SISTEC_SQL)
        _garantir_colunas_campi_sistec(conn)
        conn.executescript(SCHEMA_ESTADO_VERSOES_SQL)
        conn.execute("INSERT OR IGNORE INTO estado_versoes (id, rev_interna) VALUES (1, 0)")
        conn.executescript(SCHEMA_HISTORICO_SQL)
        _garantir_tipo_envio_historico(conn)

        if _config_get(conn, "fatores_carga_inicial_em") is None:
            _carregar_fatores_padrao(conn)
            _config_set(conn, "fatores_carga_inicial_em", _now_iso())

        _config_set(conn, "schema_versao", SCHEMA_VERSAO_ATUAL)

        conn.execute(
            "UPDATE historico SET desfecho = 'interrompida', fim = ? "
            "WHERE desfecho IS NULL",
            (_now_iso(),),
        )

        conn.commit()
    finally:
        conn.close()
    return db_path


def _now_iso():
    import datetime

    return datetime.datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    init_db()
