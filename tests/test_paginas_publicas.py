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


import pandas as pd


def _matriculas_de_teste():
    return pd.DataFrame(
        {
            "co_matricula": [1, 2, 3],
            "status_corrigido": ["CONCLUÍDA", "EM_CURSO", "EM_CURSO"],
            "ano_base": [2026, 2026, 2026],
            "codigo_ciclo_matricula": [10, 10, 11],
            "tipo_programa_curso": ["Regular"] * 3,
            "dt_data_inicio": pd.to_datetime(["2026-02-01"] * 3),
            "codigo_portfolio": ["P1", "P1", "P2"],
            "nome_curso_ajustado": ["Curso A", "Curso A", "Curso B"],
            "tipo_curso_pnp": ["Técnico"] * 3,
            "subtipo_curso": ["Integrado"] * 3,
            "modalidade_ensino": ["Presencial"] * 3,
            "eixo_tecnologico_ajustado": ["Informação"] * 3,
            "carga_horaria_total": [1200, 1200, 800],
            "fec": [1.0, 1.0, 1.0],
            "fech": [1.0, 1.0, 1.0],
            "co_unidade": ["101", "101", "102"],
            "tipo_oferta_curso": ["Integrado"] * 3,
            "categoria_origem_curso": ["Regular"] * 3,
            "cidade": ["Alegrete", "Alegrete", "Jaguari"],
        }
    )


@pytest.fixture
def matriculas_com_dados(monkeypatch):
    pagina_matriculas = pagina("matriculas")
    monkeypatch.setattr(pagina_matriculas, "carregar_matriculas", _matriculas_de_teste)
    monkeypatch.setattr(pagina_matriculas, "ano_base_ativo", lambda: 2026)
    return pagina_matriculas


def _atualizar(pagina_matriculas):
    return pagina_matriculas.atualizar("com_fic", "campus", "__todos__", "__todos__", "__todos__")


def test_matriculas_mostra_os_kpis_em_br_card_com_os_mesmos_numeros(matriculas_com_dados):
    kpis, _ = _atualizar(matriculas_com_dados)
    cartoes = [textos(c) for coluna in kpis for c in com_classe(coluna, "br-card")]
    assert cartoes == [
        "Cursos 2",
        "Matrículas 3",
        "Matrículas equivalentes 3,00",
        "Matrículas concluídas 1",
        "Ingressantes 2",
    ]


def test_matriculas_poe_cada_kpi_em_coluna_que_comeca_em_col_12(matriculas_com_dados):
    kpis, _ = _atualizar(matriculas_com_dados)
    assert len(kpis) == 5
    for coluna in kpis:
        assert "col-12" in coluna.className.split()


def test_matriculas_mostra_a_matriz_em_br_table_com_os_mesmos_numeros(matriculas_com_dados):
    _, matriz = _atualizar(matriculas_com_dados)
    assert matriz.className == "br-table"
    celulas = [[textos(td) for td in componentes(tr) if type(td).__name__ == "Td"] for tr in componentes(matriz) if type(tr).__name__ == "Tr"]
    assert [linha for linha in celulas if linha] == [["101", "2"], ["102", "1"]]


def test_matriculas_nao_usa_classes_nem_componentes_de_tabela_ou_card_do_bootstrap(matriculas_com_dados):
    kpis, matriz = _atualizar(matriculas_com_dados)
    usadas = classes(kpis) | classes(matriz) | classes(matriculas_com_dados.layout())
    assert not (usadas & {"kpi-row", "table", "table-striped", "card", "card-body", "kpi-card", "table-scroll-wrapper"})
    for componente in (kpis, matriz):
        assert not [c for c in componentes(componente) if type(c).__name__ in ("Table", "Card", "CardBody") and type(c).__module__.startswith("dash_bootstrap_components")]
        exigir_sem_componente_do_ds_que_precisa_de_js(componente)


def test_matriculas_sem_dados_mostra_br_message_info(monkeypatch):
    pagina_matriculas = pagina("matriculas")
    monkeypatch.setattr(pagina_matriculas, "dataset_disponivel", lambda: False)
    layout = pagina_matriculas.layout()
    assert {"br-message", "info"} <= set(layout.className.split())
    assert SEM_DADOS in textos(layout)
    assert "empty-state" not in classes(layout)
