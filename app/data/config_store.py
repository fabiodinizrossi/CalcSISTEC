"""Configurações administráveis do painel — identidade da instituição,
e-mail de contato e logotipo (`001-govbr-design-system`, T012).

Sobre a tabela `config` (chave/valor) já existente em `app/data/schema.py`
(mesmo padrão de `app/data/consulta.ano_base_ativo`), sem cache em processo:
cada leitura consulta o SQLite diretamente, para que uma escrita feita em
outra requisição/processo seja vista de imediato (RN-12/RN-13/RN-14).

Nada aqui é fixo numa instituição: os padrões de fábrica são vazios (ou
neutros, no caso do logotipo), e o assistente de instalação
(`app/data/instalacao.py`) é quem preenche na primeira vez. Assim o mesmo
programa serve qualquer instituto federal.
"""

from app.data.schema import DEFAULT_DB_PATH, get_connection

DEFAULT_CONTATO_EMAIL = ""
DEFAULT_LOGO_PATH = "app/assets/branding/padrao-generico.svg"
DEFAULT_INSTITUICAO_NOME = ""
DEFAULT_INSTITUICAO_SIGLA = ""
DEFAULT_INSTITUICAO_SITE = ""

DEFAULT_QTD_PERFIS = ""

_CHAVE_CONTATO_EMAIL = "contato_email"
# `qtdPerfis` da conta de quem acessa o Sistec, cadastrado em Configurações →
# Campi do Sistec. Vai na URL que troca o campus; na conta conferida em
# 2026-09-16 eram 22 (11 campi x 2 papéis), e não o 16 literal que o script R
# herdou de outra conta. Vazio: vale `urls.QTD_PERFIS_PADRAO`.
_CHAVE_QTD_PERFIS = "sistec_qtd_perfis"
_CHAVE_LOGO_PATH = "logo_path"
_CHAVE_INSTITUICAO_NOME = "instituicao_nome"
_CHAVE_INSTITUICAO_SIGLA = "instituicao_sigla"
_CHAVE_INSTITUICAO_SITE = "instituicao_site"


def get_valor(chave, padrao="", db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
        return row[0] if row else padrao
    finally:
        conn.close()


def set_valor(chave, valor, db_path=DEFAULT_DB_PATH):
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


def reset_valor(chave, db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM config WHERE chave=?", (chave,))
        conn.commit()
    finally:
        conn.close()


# Compatibilidade com o código anterior (aliases internos).
_get = get_valor
_set = set_valor
_reset = reset_valor


def get_contato_email(db_path=DEFAULT_DB_PATH):
    return get_valor(_CHAVE_CONTATO_EMAIL, DEFAULT_CONTATO_EMAIL, db_path)


def set_contato_email(email, db_path=DEFAULT_DB_PATH):
    set_valor(_CHAVE_CONTATO_EMAIL, email, db_path)


def reset_contato_email(db_path=DEFAULT_DB_PATH):
    reset_valor(_CHAVE_CONTATO_EMAIL, db_path)


def get_qtd_perfis(db_path=DEFAULT_DB_PATH):
    """String com o total de perfis da conta, ou `""` se ainda não foi lido."""
    valor = get_valor(_CHAVE_QTD_PERFIS, DEFAULT_QTD_PERFIS, db_path)
    return valor if str(valor).isdigit() else DEFAULT_QTD_PERFIS


def set_qtd_perfis(qtd, db_path=DEFAULT_DB_PATH):
    set_valor(_CHAVE_QTD_PERFIS, str(qtd), db_path)


def reset_qtd_perfis(db_path=DEFAULT_DB_PATH):
    reset_valor(_CHAVE_QTD_PERFIS, db_path)


def get_logo_path(db_path=DEFAULT_DB_PATH):
    return get_valor(_CHAVE_LOGO_PATH, DEFAULT_LOGO_PATH, db_path)


def set_logo(caminho, db_path=DEFAULT_DB_PATH):
    set_valor(_CHAVE_LOGO_PATH, caminho, db_path)


def reset_logo(db_path=DEFAULT_DB_PATH):
    reset_valor(_CHAVE_LOGO_PATH, db_path)


def get_instituicao_nome(db_path=DEFAULT_DB_PATH):
    return get_valor(_CHAVE_INSTITUICAO_NOME, DEFAULT_INSTITUICAO_NOME, db_path)


def get_instituicao_sigla(db_path=DEFAULT_DB_PATH):
    return get_valor(_CHAVE_INSTITUICAO_SIGLA, DEFAULT_INSTITUICAO_SIGLA, db_path)


def get_instituicao_site(db_path=DEFAULT_DB_PATH):
    return get_valor(_CHAVE_INSTITUICAO_SITE, DEFAULT_INSTITUICAO_SITE, db_path)


def set_instituicao(nome=None, sigla=None, site=None, db_path=DEFAULT_DB_PATH):
    """Grava só o que veio preenchido (o assistente e as Configurações usam o
    mesmo caminho)."""
    if nome is not None:
        set_valor(_CHAVE_INSTITUICAO_NOME, nome, db_path)
    if sigla is not None:
        set_valor(_CHAVE_INSTITUICAO_SIGLA, sigla, db_path)
    if site is not None:
        set_valor(_CHAVE_INSTITUICAO_SITE, site, db_path)


def reset_instituicao(db_path=DEFAULT_DB_PATH):
    for chave in (_CHAVE_INSTITUICAO_NOME, _CHAVE_INSTITUICAO_SIGLA, _CHAVE_INSTITUICAO_SITE):
        reset_valor(chave, db_path)


def dados_instituicao(db_path=DEFAULT_DB_PATH):
    """Tudo o que cabeçalho, rodapé e telas precisam mostrar."""
    return {
        "nome": get_instituicao_nome(db_path),
        "sigla": get_instituicao_sigla(db_path),
        "site": get_instituicao_site(db_path),
        "contato_email": get_contato_email(db_path),
    }
