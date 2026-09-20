"""Contexto do shell (DS-11, DS-12, DS-19, DS-39, DS-41, DS-56, DS-61): menu, breadcrumb e
identidade que cabeçalho, menu e rodapé recebem."""

import pytest

from app import shell
from app.shell import contexto_shell

PUBLICAS = [
    ("Início", "/"),
    ("Matrículas", "/matriculas"),
    ("Eficiência Acadêmica", "/eficiencia"),
    ("Taxa de Evasão Anual", "/evasao"),
    ("Percentuais Legais", "/percentuais-legais"),
]


@pytest.fixture(autouse=True)
def instituicao_configurada(monkeypatch):
    monkeypatch.setattr(
        shell,
        "dados_instituicao",
        lambda: {"nome": "Instituto Teste", "sigla": "IT", "site": "https://it.edu.br", "contato_email": "pi@it.edu.br"},
    )
    monkeypatch.setattr(shell, "get_contato_email", lambda: "pi@it.edu.br")


def test_menu_publico_tem_5_itens_na_ordem_da_spec():
    menu = contexto_shell("/")["menu"]
    assert [(i["rotulo"], i["href"]) for i in menu] == PUBLICAS


@pytest.mark.parametrize("rotulo,caminho", PUBLICAS)
def test_so_o_item_da_pagina_atual_fica_ativo(rotulo, caminho):
    menu = contexto_shell(caminho)["menu"]
    assert [i["rotulo"] for i in menu if i["ativo"]] == [rotulo]


def test_capa_nao_tem_breadcrumb():
    assert contexto_shell("/")["breadcrumb"] == []


@pytest.mark.parametrize("rotulo,caminho", PUBLICAS[1:])
def test_pagina_publica_tem_breadcrumb_inicio_e_titulo(rotulo, caminho):
    assert contexto_shell(caminho)["breadcrumb"] == [
        {"rotulo": "Início", "href": "/"},
        {"rotulo": rotulo, "href": None},
    ]


def test_breadcrumb_das_rotas_de_campi():
    assert contexto_shell("/admin/campi")["breadcrumb"] == [
        {"rotulo": "Configurações", "href": "/admin/config"},
        {"rotulo": "Campi", "href": None},
    ]
    assert contexto_shell("/admin/campi/8278857/editar")["breadcrumb"] == [
        {"rotulo": "Configurações", "href": "/admin/config"},
        {"rotulo": "Campi", "href": "/admin/campi"},
        {"rotulo": "Editar", "href": None},
    ]
    assert contexto_shell("/admin/campi/novo")["breadcrumb"] == [
        {"rotulo": "Configurações", "href": "/admin/config"},
        {"rotulo": "Campi", "href": "/admin/campi"},
        {"rotulo": "Incluir", "href": None},
    ]


@pytest.mark.parametrize(
    "rotulo,caminho",
    [
        ("Atualizar dados", "/admin/atualizar"),
        ("Histórico de atualizações", "/admin/historico"),
        ("Configurações", "/admin/config"),
    ],
)
def test_pagina_administrativa_tem_menu_proprio_e_breadcrumb_inicio_e_titulo(rotulo, caminho):
    contexto = contexto_shell(caminho)
    assert [i["rotulo"] for i in contexto["menu"]] == ["Atualizar dados", "Histórico de atualizações", "Configurações"]
    assert [i["rotulo"] for i in contexto["menu"] if i["ativo"]] == [rotulo]
    assert contexto["breadcrumb"] == [{"rotulo": "Início", "href": "/"}, {"rotulo": rotulo, "href": None}]


@pytest.mark.parametrize("caminho", ["/admin/login", "/recuperar-acesso", "/admin/instalacao"])
def test_login_recuperar_acesso_e_instalacao_ficam_sem_menu_e_sem_breadcrumb(caminho):
    contexto = contexto_shell(caminho)
    assert contexto["com_menu"] is False
    assert contexto["breadcrumb"] == []


@pytest.mark.parametrize("caminho", ["/", "/matriculas", "/admin/historico", "/admin/campi"])
def test_demais_paginas_ficam_com_menu(caminho):
    assert contexto_shell(caminho)["com_menu"] is True


def test_identidade_vem_da_configuracao_e_nao_de_literal():
    contexto = contexto_shell("/")
    assert contexto["instituicao"]["nome"] == "Instituto Teste"
    assert contexto["instituicao"]["sigla"] == "IT"
    assert contexto["instituicao"]["site"] == "https://it.edu.br"
    assert contexto["contato_email"] == "pi@it.edu.br"


def test_email_e_site_em_branco_chegam_como_vazios(monkeypatch):
    monkeypatch.setattr(
        shell,
        "dados_instituicao",
        lambda: {"nome": "Instituto Teste", "sigla": "", "site": "   ", "contato_email": None},
    )
    monkeypatch.setattr(shell, "get_contato_email", lambda: "  ")
    contexto = contexto_shell("/")
    assert contexto["contato_email"] == ""
    assert contexto["instituicao"]["site"] == ""
    assert contexto["instituicao"]["nome"] == "Instituto Teste"
