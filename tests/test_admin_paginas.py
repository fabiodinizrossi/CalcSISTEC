"""Páginas administrativas (Flask/Jinja) no padrão do gov.br DS."""

import re

import pytest

from app import app as app_module


@pytest.fixture
def cliente():
    return app_module.server.test_client()


@pytest.fixture
def cliente_autenticado(cliente, monkeypatch):
    with cliente.session_transaction() as sessao:
        sessao["admin_usuario"] = "pi@ife.edu.br"
        sessao["admin_autenticado"] = True
    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: True)
    return cliente


def test_base_compoe_o_shell_do_ds(cliente):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert '<html lang="pt-BR"' in html
    assert len(re.findall(r'<link[^>]+href="/ds/govbr-ds/dist/core\.min\.css"', html)) == 1
    assert len(re.findall(r'<script[^>]+src="/ds/govbr-ds/dist/core\.min\.js"', html)) == 1
    assert 'class="br-header"' in html
    assert 'class="br-footer"' in html
    assert "container-fluid" in html
    for antigo in ("app-header", "app-footer", "admin-nav"):
        assert antigo not in html


def test_base_nao_carrega_folha_do_bootstrap(cliente):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert "bootstrap" not in html.lower()


def test_pagina_administrativa_autenticada_mostra_menu_e_breadcrumb(cliente_autenticado):
    html = cliente_autenticado.get("/admin/historico").get_data(as_text=True)
    assert 'class="br-menu"' in html
    assert 'class="br-breadcrumb"' in html
    assert "admin-nav" not in html


def test_login_nao_mostra_menu_nem_breadcrumb(cliente):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert 'class="br-menu"' not in html
    assert 'class="br-breadcrumb"' not in html
