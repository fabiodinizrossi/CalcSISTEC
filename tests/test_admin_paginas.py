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


@pytest.fixture
def login_configurado(monkeypatch):
    monkeypatch.setattr(app_module, "credenciais_configuradas", lambda: True)


def test_login_tem_titulo_campos_com_rotulo_e_apoio_e_link_depois_da_senha(cliente, login_configurado):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert re.search(r"<h1[^>]*>\s*Acesso ao sistema\s*</h1>", html)
    assert len(re.findall(r'<label for="(email|senha)">', html)) == 2
    assert "Mínimo de 8 caracteres." in html
    assert 'id="email-ajuda"' in html
    assert html.index('id="senha"') < html.index("Esqueci minha senha")


def test_botao_entrar_ocupa_a_largura_do_formulario(cliente, login_configurado):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert re.search(r'<button\b[^>]*class="br-button primary block"[^>]*>\s*Entrar\s*</button>', html)


def test_login_com_campo_invalido_devolve_o_campo_em_danger_ligado_ao_erro(cliente, login_configurado):
    resposta = cliente.post("/admin/login", data={"email": "nao-e-email", "senha": "curta"})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"', html)
    descrito = re.search(r'<input\b[^>]*id="email"[^>]*aria-describedby="([^"]+)"', html).group(1)
    assert f'id="{descrito.split()[-1]}"' in html


def test_login_recusado_mostra_mensagem_danger_com_role_alert(cliente, login_configurado, monkeypatch):
    monkeypatch.setattr(app_module, "autenticar_sessao", lambda email, senha: False)
    html = cliente.post("/admin/login", data={"email": "pi@ife.edu.br", "senha": "12345678"}).get_data(as_text=True)
    assert re.search(r'class="br-message danger"[^>]*role="alert"', html)
    assert "E-mail ou senha incorretos." in html


def test_recuperar_acesso_tem_titulo_shell_sem_menu_e_sem_breadcrumb(cliente):
    resposta = cliente.get("/recuperar-acesso")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r"<h1[^>]*>\s*Recuperação de acesso\s*</h1>", html)
    assert 'class="br-header"' in html
    assert 'class="br-footer"' in html
    assert 'class="br-menu"' not in html
    assert 'class="br-breadcrumb"' not in html


def test_recuperar_acesso_volta_ao_login_por_um_br_button(cliente):
    html = cliente.get("/recuperar-acesso").get_data(as_text=True)
    assert re.search(r'<a\b[^>]*class="br-button[^"]*"[^>]*href="/admin/login"[^>]*>\s*Voltar ao login\s*</a>', html)


def test_instalacao_tem_rotulo_e_br_input_para_todo_campo_de_texto(cliente_autenticado):
    resposta = cliente_autenticado.get("/admin/instalacao")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    ids = re.findall(r'<input\b[^>]*type="(?:text|email)"[^>]*id="([^"]+)"', html)
    assert sorted(ids) == ["contato_email", "nome", "sigla", "site"]
    for campo_id in ids:
        assert f'<label for="{campo_id}">' in html
    assert len(re.findall(r'class="br-input\b', html)) == len(ids)


def test_instalacao_nao_mostra_menu_nem_breadcrumb_e_nao_usa_confirm_nativo(cliente_autenticado):
    html = cliente_autenticado.get("/admin/instalacao").get_data(as_text=True)
    assert 'class="br-menu"' not in html
    assert 'class="br-breadcrumb"' not in html
    assert "confirm(" not in html


def test_instalacao_com_nome_vazio_marca_o_campo_em_danger_ligado_a_mensagem(cliente_autenticado):
    resposta = cliente_autenticado.post("/admin/instalacao", data={"acao": "salvar_instituicao", "nome": "  "})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"[^>]*>\s*<label for="nome">', html)
    assert re.search(r'<input\b[^>]*id="nome"[^>]*aria-describedby="nome-erro[^"]*"', html)
    assert re.search(r'id="nome-erro"[^>]*>\s*<i[^>]*></i>Informe o nome da instituição\.', html)
