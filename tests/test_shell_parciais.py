"""Parciais Jinja do shell (`app/templates/shell/`)."""

import re
from pathlib import Path

import pytest
from flask import render_template

from app import app as app_module
from app import shell as shell_modulo
from app.shell import PAGINAS_ADMIN, contexto_shell


@pytest.fixture(scope="module")
def servidor():
    return app_module.server


def renderizar(servidor, modelo, **contexto):
    with servidor.test_request_context("/"):
        return render_template(modelo, **contexto)


def test_head_tem_viewport_e_um_unico_core_min_css(servidor):
    html = renderizar(servidor, "shell/_head.html", titulo="Matrículas")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert len(re.findall(r'<link[^>]+href="/ds/govbr-ds/dist/core\.min\.css"', html)) == 1
    assert "<title>Matrículas</title>" in html


def test_head_nao_referencia_url_externa(servidor):
    html = renderizar(servidor, "shell/_head.html", titulo="Início")
    assert "http://" not in html
    assert "https://" not in html


def cabecalho(servidor, nome="Instituto Teste", com_menu=True):
    return renderizar(
        servidor,
        "shell/_header.html",
        shell={"com_menu": com_menu},
        instituicao={"nome": nome},
    )


def test_primeiro_link_do_cabecalho_salta_para_o_conteudo_principal(servidor):
    html = cabecalho(servidor)
    primeiro = re.search(r"<a\b([^>]*)>(.*?)</a>", html, re.S)
    assert 'href="#main-content"' in primeiro.group(1)
    assert primeiro.group(2).strip() == "Ir para o conteúdo principal"


def test_logotipo_tem_alt_nao_vazio_com_e_sem_nome_de_instituicao(servidor):
    com_nome = re.search(r'<img[^>]*alt="([^"]*)"', cabecalho(servidor, nome="Instituto Teste")).group(1)
    sem_nome = re.search(r'<img[^>]*alt="([^"]*)"', cabecalho(servidor, nome="")).group(1)
    assert "Instituto Teste" in com_nome
    assert sem_nome.strip() != ""


def test_logotipo_fica_em_involucro_de_superficie_clara(servidor):
    assert re.search(r'class="logo-superficie"[^>]*>\s*<img', cabecalho(servidor))


def test_cabecalho_mostra_titulo_do_painel_e_nome_da_instituicao(servidor):
    html = cabecalho(servidor)
    assert "Painel de Acompanhamento Sistec" in html
    assert "Instituto Teste" in html


def test_botao_de_tema_tem_rotulo_textual_e_aria_pressed_falso(servidor):
    botao = re.search(r'<button\b[^>]*id="botao-tema"[^>]*>(.*?)</button>', cabecalho(servidor), re.S)
    assert 'aria-pressed="false"' in botao.group(0)
    assert "Usar tema escuro" in botao.group(1)


def test_botao_hamburguer_declara_estado_e_alvo_e_some_sem_menu(servidor):
    botao = re.search(r'<button\b[^>]*id="botao-menu"[^>]*>', cabecalho(servidor, com_menu=True))
    assert 'aria-expanded="false"' in botao.group(0)
    assert 'aria-controls="main-navigation"' in botao.group(0)
    assert 'id="botao-menu"' not in cabecalho(servidor, com_menu=False)


def test_logotipo_sem_arquivo_enviado_cai_em_padrao_generico(servidor, monkeypatch):
    monkeypatch.setattr(app_module, "get_logo_path", lambda: "app/data/uploads/branding/nao-existe.png")
    resposta = servidor.test_client().get("/branding/logo")
    padrao = Path(app_module.DEFAULT_LOGO_PATH).read_bytes()
    assert resposta.status_code == 200
    assert resposta.mimetype == "image/svg+xml"
    assert resposta.data == padrao


def itens_do_menu(servidor, caminho):
    html = renderizar(servidor, "shell/_menu.html", shell=contexto_shell(caminho))
    return html, re.findall(r"<a\b([^>]*)>\s*<span class=\"content\">(.*?)</span>", html, re.S)


@pytest.fixture
def instituicao_configurada(monkeypatch):
    monkeypatch.setattr(shell_modulo, "dados_instituicao", lambda: {"nome": "Instituto Teste"})
    monkeypatch.setattr(shell_modulo, "get_contato_email", lambda: "")


def test_menu_publico_renderiza_5_links_na_ordem_da_spec(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/matriculas")
    assert [rotulo.strip() for _, rotulo in itens] == [
        "Início",
        "Matrículas",
        "Eficiência Acadêmica",
        "Taxa de Evasão Anual",
        "Percentuais Legais",
    ]


def test_so_o_link_da_pagina_atual_tem_aria_current_e_classe_ativa(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/matriculas")
    com_aria = [rotulo.strip() for atributos, rotulo in itens if 'aria-current="page"' in atributos]
    com_classe = [rotulo.strip() for atributos, rotulo in itens if re.search(r'class="[^"]*\bactive\b', atributos)]
    assert com_aria == ["Matrículas"]
    assert com_classe == ["Matrículas"]


def test_menu_administrativo_renderiza_os_itens_de_paginas_admin(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/admin/historico")
    assert [rotulo.strip() for _, rotulo in itens] == [rotulo for rotulo, _ in PAGINAS_ADMIN]


def test_todos_os_itens_do_menu_sao_links_com_href(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/")
    assert len(itens) == 5
    assert all(re.search(r'href="/[^"]*"', atributos) for atributos, _ in itens)


@pytest.mark.parametrize("caminho", ["/admin/login", "/recuperar-acesso", "/admin/instalacao"])
def test_sem_menu_o_parcial_nao_renderiza_nada(servidor, instituicao_configurada, caminho):
    html, _ = itens_do_menu(servidor, caminho)
    assert html.strip() == ""
