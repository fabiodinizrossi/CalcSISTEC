"""Configurações administráveis do painel — e-mail de contato e logotipo
(`001-govbr-design-system`, T012).

Sobre a tabela `config` (chave/valor) já existente em `app/data/schema.py`
(mesmo padrão de `app/data/consulta.ano_base_ativo`), sem cache em processo:
cada leitura consulta o SQLite diretamente, para que uma escrita feita em
outra requisição/processo seja vista de imediato (RN-12/RN-13/RN-14).
"""

from app.data.schema import DEFAULT_DB_PATH, get_connection

DEFAULT_CONTATO_EMAIL = "pesquisainstitucional@iffarroupilha.edu.br"
DEFAULT_LOGO_PATH = "app/assets/branding/iffar-horizontal-colorida.svg"

_CHAVE_CONTATO_EMAIL = "contato_email"
_CHAVE_LOGO_PATH = "logo_path"


def _get(chave, padrao, db_path):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
        return row[0] if row else padrao
    finally:
        conn.close()


def _set(chave, valor, db_path):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO config (chave, valor) VALUES (?, ?) "
            "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
            (chave, valor),
        )
        conn.commit()
    finally:
        conn.close()


def _reset(chave, db_path):
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM config WHERE chave=?", (chave,))
        conn.commit()
    finally:
        conn.close()


def get_contato_email(db_path=DEFAULT_DB_PATH):
    return _get(_CHAVE_CONTATO_EMAIL, DEFAULT_CONTATO_EMAIL, db_path)


def set_contato_email(email, db_path=DEFAULT_DB_PATH):
    _set(_CHAVE_CONTATO_EMAIL, email, db_path)


def reset_contato_email(db_path=DEFAULT_DB_PATH):
    _reset(_CHAVE_CONTATO_EMAIL, db_path)


def get_logo_path(db_path=DEFAULT_DB_PATH):
    return _get(_CHAVE_LOGO_PATH, DEFAULT_LOGO_PATH, db_path)


def set_logo(caminho, db_path=DEFAULT_DB_PATH):
    _set(_CHAVE_LOGO_PATH, caminho, db_path)


def reset_logo(db_path=DEFAULT_DB_PATH):
    _reset(_CHAVE_LOGO_PATH, db_path)
