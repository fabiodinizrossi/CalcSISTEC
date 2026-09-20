"""Páginas públicas em Dash no padrão do gov.br DS (DS-06, DS-13, DS-14, DS-17, DS-35, DS-43, DS-44)."""

import importlib

import pytest

from app import app as _app  # noqa: F401  (carrega e registra as páginas)
from arvore_dash import classes, com_classe, componentes, exigir_sem_componente_do_ds_que_precisa_de_js, textos

SEM_DADOS = "Ainda não há dados publicados."


def pagina(nome):
    return importlib.import_module(f"pages.{nome}")


@pytest.fixture
def home_com_dados(monkeypatch):
    home = pagina("home")
    monkeypatch.setattr(home, "dataset_disponivel", lambda: True)
    monkeypatch.setattr(home, "data_ultimo_upload_valido", lambda: "01/09/2026")
    return home


def test_inicio_com_dados_tem_4_cartoes_de_navegacao_com_os_links_e_rotulos_atuais(home_com_dados):
    cartoes = com_classe(home_com_dados.layout(), "br-card")
    assert [(c.href, textos(c)) for c in cartoes] == [
        ("/matriculas", "Matrículas"),
        ("/eficiencia", "Eficiência Acadêmica"),
        ("/evasao", "Taxa de Evasão Anual"),
        ("/percentuais-legais", "Percentuais Legais"),
    ]


def test_inicio_poe_os_cartoes_numa_row_com_colunas_col_12_col_md_6_col_xl_3(home_com_dados):
    linhas = com_classe(home_com_dados.layout(), "row")
    assert len(linhas) == 1
    colunas = linhas[0].children
    assert len(colunas) == 4
    for coluna in colunas:
        assert {"col-12", "col-md-6", "col-xl-3"} <= set(coluna.className.split())


def test_inicio_mostra_a_data_de_atualizacao(home_com_dados):
    assert "Atualizado em 01/09/2026" in textos(home_com_dados.layout())


def test_inicio_sem_dados_mostra_br_message_info_e_nenhum_cartao(monkeypatch):
    home = pagina("home")
    monkeypatch.setattr(home, "dataset_disponivel", lambda: False)
    layout = home.layout()
    mensagens = com_classe(layout, "br-message")
    assert len(mensagens) == 1
    assert {"br-message", "info"} <= set(mensagens[0].className.split())
    assert SEM_DADOS in textos(mensagens[0])
    assert not com_classe(layout, "br-card")


def test_inicio_nao_usa_classes_proprias_antigas_nem_componente_do_ds_que_precisa_de_js(home_com_dados, monkeypatch):
    for layout in (home_com_dados.layout(),):
        assert not (classes(layout) & {"nav-card", "hero", "landing-cards", "updated-at-badge"})
        exigir_sem_componente_do_ds_que_precisa_de_js(layout)
    monkeypatch.setattr(home_com_dados, "dataset_disponivel", lambda: False)
    assert not (classes(home_com_dados.layout()) & {"nav-card", "hero", "empty-state"})
