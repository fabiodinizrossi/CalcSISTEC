"""Testes de `app/data/config_store.py` (Tarefa `001-govbr-design-system`, T008).

Cobre os pares get/set/reset de e-mail de contato e logotipo sobre a tabela
`config` existente (`app/data/schema.py`), incluindo o padrão de fábrica e a
ausência de cache em processo (RF-20/RF-21/RF-22, RN-12/RN-13/RN-14).
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.schema import get_connection, init_db  # noqa: E402


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.remove(path)


def test_get_contato_email_retorna_padrao_quando_config_nao_tem_a_chave(db_path):
    from app.data.config_store import DEFAULT_CONTATO_EMAIL, get_contato_email

    assert get_contato_email(db_path) == DEFAULT_CONTATO_EMAIL


def test_get_logo_path_retorna_padrao_quando_config_nao_tem_a_chave(db_path):
    from app.data.config_store import DEFAULT_LOGO_PATH, get_logo_path

    assert get_logo_path(db_path) == DEFAULT_LOGO_PATH


def test_set_contato_email_grava_e_get_reflete(db_path):
    from app.data.config_store import get_contato_email, set_contato_email

    set_contato_email("contato.pi@iffarroupilha.edu.br", db_path)
    assert get_contato_email(db_path) == "contato.pi@iffarroupilha.edu.br"


def test_reset_contato_email_volta_ao_padrao(db_path):
    from app.data.config_store import (
        DEFAULT_CONTATO_EMAIL,
        get_contato_email,
        reset_contato_email,
        set_contato_email,
    )

    set_contato_email("contato.pi@iffarroupilha.edu.br", db_path)
    reset_contato_email(db_path)
    assert get_contato_email(db_path) == DEFAULT_CONTATO_EMAIL


def test_set_logo_grava_e_get_reflete(db_path):
    from app.data.config_store import get_logo_path, set_logo

    set_logo("app/data/uploads/branding/logo-novo.png", db_path)
    assert get_logo_path(db_path) == "app/data/uploads/branding/logo-novo.png"


def test_reset_logo_volta_ao_padrao(db_path):
    from app.data.config_store import DEFAULT_LOGO_PATH, get_logo_path, reset_logo, set_logo

    set_logo("app/data/uploads/branding/logo-novo.png", db_path)
    reset_logo(db_path)
    assert get_logo_path(db_path) == DEFAULT_LOGO_PATH


def test_leitura_nao_usa_cache_em_processo(db_path):
    """Duas leituras após uma escrita externa direta no banco (sem passar
    pelos setters de `config_store`) devem refletir o valor novo — nenhuma
    função de leitura pode manter estado em memória entre chamadas."""
    from app.data.config_store import get_contato_email

    assert get_contato_email(db_path) is not None

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO config (chave, valor) VALUES ('contato_email', ?)",
            ("escrita.externa@iffarroupilha.edu.br",),
        )
        conn.commit()
    finally:
        conn.close()

    assert get_contato_email(db_path) == "escrita.externa@iffarroupilha.edu.br"
    assert get_contato_email(db_path) == "escrita.externa@iffarroupilha.edu.br"
