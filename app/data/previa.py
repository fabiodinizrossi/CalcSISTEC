"""Fonte candidata da prévia (`previa-paginas-publicas`, T2): SQLite nomeado
em memória (`file:previa-<id>?mode=memory&cache=shared`) com as tabelas que
`app.data.consulta` lê nas páginas públicas — as quatro tabelas do candidato
(T1), o `campus` publicado, a `config` (ano-base) e `estado_versoes` sem data
de publicação.

Um banco nomeado em memória morre quando a última conexão fecha; a conexão
âncora o mantém vivo enquanto a fonte existir. `abrir_leitura` devolve uma
conexão nova somente leitura (`query_only=ON`). Nenhum arquivo em disco e
nenhuma coluna pessoal (as tabelas vêm do candidato, já sem PII — PVP-03,
`RISK-008`).

A âncora é criada com `check_same_thread=False` (T21): o Flask atende cada
requisição numa thread, então a fonte aberta no envio é fechada por outra
thread no Salvar/Descartar. A serialização continua sendo a de
`execucoes.com_trava`, não a do `sqlite3` — a flag só remove a checagem de
identidade de thread, não introduz concorrência.
"""

import secrets
import sqlite3

import pandas as pd

from app.data.schema import (
    DEFAULT_DB_PATH,
    SCHEMA_CONFIG_SQL,
    SCHEMA_ESTADO_VERSOES_SQL,
    SCHEMA_PUBLICAS_SQL,
    get_connection,
)

# FKs: ciclos -> cursos; matriculas(_eficiencia) -> ciclos. INSERT vai do pai
# para o filho (mesma ordem de `app/data/versoes.py`).
_ORDEM_INSERT = ("cursos", "ciclos", "matriculas", "matriculas_eficiencia")


class FontePrevia:
    """Banco nomeado em memória com as tabelas de leitura da prévia. A
    conexão âncora mantém o banco vivo; `abrir_leitura` devolve conexões
    novas somente leitura para os callbacks/páginas. `fechar` pode rodar numa
    thread diferente da que criou a fonte (requisições distintas do Flask)."""

    def __init__(self, nome, ancora):
        self.nome = nome
        self._ancora = ancora

    def abrir_leitura(self):
        """Conexão nova, somente leitura, sem arquivos auxiliares em disco."""
        conn = sqlite3.connect(self.nome, uri=True)
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA query_only = ON")
        return conn

    def fechar(self):
        """Fecha a conexão âncora (idempotente). Sem a âncora, o banco
        nomeado em memória deixa de existir ao fechar a última conexão."""
        if self._ancora is not None:
            self._ancora.close()
            self._ancora = None


def abrir_fonte_previa(candidato, campus_publico=None, db_path=DEFAULT_DB_PATH):
    """Cria a fonte em memória a partir do `candidato` (T1: dict com
    `tabelas` e `ano_base`). `campus_publico`: DataFrame de campus (colunas
    `co_unidade`, `cidade`, `nome_unidade`); se None, o fallback lê
    `interna_campus` de `db_path` (CPR-06: é o que o Publicar leva ao ar).
    Não toca nem grava no banco publicado."""
    tabelas = candidato["tabelas"]
    ano_base = candidato["ano_base"]

    if campus_publico is None:
        conn = get_connection(db_path)
        try:
            campus_publico = pd.read_sql_query(
                "SELECT co_unidade, cidade, nome_unidade FROM interna_campus", conn
            )
        finally:
            conn.close()

    nome = f"file:previa-{secrets.token_urlsafe(16)}?mode=memory&cache=shared"
    # `check_same_thread=False` (T21): o Flask atende cada requisição numa
    # thread, então a fonte aberta no envio é fechada por outra thread no
    # Salvar/Descartar. Todo acesso à âncora já é serializado por
    # `execucoes.com_trava`, então nunca há duas threads na conexão ao mesmo
    # tempo — a flag só remove a checagem de identidade de thread do Python.
    ancora = sqlite3.connect(nome, uri=True, check_same_thread=False)
    try:
        ancora.execute("PRAGMA foreign_keys = ON")
        ancora.executescript(SCHEMA_PUBLICAS_SQL)
        ancora.executescript(SCHEMA_CONFIG_SQL)
        ancora.executescript(SCHEMA_ESTADO_VERSOES_SQL)

        for tabela in _ORDEM_INSERT:
            df = tabelas.get(tabela)
            if df is not None and not df.empty:
                df.to_sql(tabela, ancora, if_exists="append", index=False)

        if not campus_publico.empty:
            campus_publico.to_sql("campus", ancora, if_exists="append", index=False)

        ancora.execute(
            "INSERT INTO config (chave, valor) VALUES ('ano_base', ?)", (str(ano_base),)
        )
        # `publicada_em` vazio: as páginas da prévia não exibem a data da
        # publicação antiga (PVP-05).
        ancora.execute(
            "INSERT INTO estado_versoes (id, rev_interna, rev_publicada, rev_anterior, publicada_em, publicada_por) "
            "VALUES (1, 0, NULL, NULL, NULL, NULL)"
        )
        ancora.commit()
    except Exception:
        ancora.close()
        raise

    return FontePrevia(nome, ancora)
