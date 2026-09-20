"""Componentes públicos em Dash no padrão do gov.br DS (DS-13, DS-14, DS-15, DS-17, DS-27)."""

import pytest
from dash import html

from app.components.kpi import kpi_card
from arvore_dash import classes, com_classe, exigir_sem_componente_do_ds_que_precisa_de_js, textos

CLASSES_DO_BOOTSTRAP = {"card", "card-body", "kpi-card"}


def test_kpi_card_e_um_br_card_com_o_valor_formatado():
    cartao = kpi_card("Matrículas", 1234, "0")
    assert "br-card" in classes(cartao)
    assert "1.234" in textos(cartao)
    assert "Matrículas" in textos(cartao)


def test_kpi_card_sem_valor_mostra_travessao():
    assert "—" in textos(kpi_card("Matrículas", None, "0"))


def test_empty_state_substitui_o_valor_none_sem_virar_zero():
    texto = textos(kpi_card("Eficiência", None, "0", empty_state="Fatores ausentes"))
    assert "Fatores ausentes" in texto
    assert "0" not in texto
    assert "—" not in texto


def test_empty_state_nao_esconde_um_valor_zero_real():
    assert "0" in textos(kpi_card("Evasão", 0, "0", empty_state="Fatores ausentes"))
    assert "Fatores ausentes" not in textos(kpi_card("Evasão", 0, "0", empty_state="Fatores ausentes"))


def test_kpi_card_nao_usa_classe_de_card_do_bootstrap():
    assert not (classes(kpi_card("Matrículas", 1234, "0")) & CLASSES_DO_BOOTSTRAP)


def test_kpi_card_nao_usa_componente_do_ds_que_precisa_de_js():
    exigir_sem_componente_do_ds_que_precisa_de_js(kpi_card("Matrículas", 1234, "0"))


@pytest.mark.parametrize("classe", ["br-select", "br-tab", "br-modal", "br-tooltip", "br-accordion", "br-dropdown", "br-carousel", "br-upload"])
def test_o_helper_falha_com_componente_do_ds_que_precisa_de_js(classe):
    arvore = html.Div([html.Div("ok"), html.Div(html.Span("x", className=f"algo {classe}"))])
    with pytest.raises(AssertionError):
        exigir_sem_componente_do_ds_que_precisa_de_js(arvore)


def test_o_helper_acha_componentes_por_classe_em_arvore_aninhada():
    arvore = html.Div([html.Div(className="a"), html.Div(html.Div(className="a b"))])
    assert len(com_classe(arvore, "a")) == 2


from app.components.tabela import tabela_ds
from arvore_dash import componentes


def _tabela(**kwargs):
    return tabela_ds(["Campus", "Total"], [["Alegrete", 120], ["Jaguari", 80]], "Matrículas por campus", **kwargs)


def test_tabela_e_br_table_com_conteiner_de_rolagem_e_table_dentro():
    raiz = _tabela()
    assert raiz.className == "br-table"
    assert raiz.children.className == "responsive"
    assert type(raiz.children.children).__name__ == "Table"


def test_tabela_tem_legenda_em_caption_e_cabecalhos_com_scope_col():
    raiz = _tabela()
    legendas = [c for c in componentes(raiz) if type(c).__name__ == "Caption"]
    assert [textos(c) for c in legendas] == ["Matrículas por campus"]
    cabecalhos = [c for c in componentes(raiz) if type(c).__name__ == "Th"]
    assert [(textos(c), c.scope) for c in cabecalhos] == [("Campus", "col"), ("Total", "col")]


def test_valores_das_celulas_chegam_iguais_aos_passados():
    linhas = [
        [textos(c) for c in componentes(tr) if type(c).__name__ == "Td"]
        for tr in componentes(_tabela())
        if type(tr).__name__ == "Tr"
    ]
    assert linhas == [[], ["Alegrete", "120"], ["Jaguari", "80"]]


def test_celula_com_classe_recebe_a_classe_e_a_sem_classe_nao():
    raiz = tabela_ds(["Taxa"], [[{"valor": "12,3%", "classe": "evasao-media"}], ["5,0%"]], "Evasão")
    celulas = [c for c in componentes(raiz) if type(c).__name__ == "Td"]
    assert [(textos(c), getattr(c, "className", None)) for c in celulas] == [("12,3%", "evasao-media"), ("5,0%", None)]


def test_tabela_nao_usa_classe_de_tabela_do_bootstrap_nem_componente_dbc():
    raiz = _tabela()
    assert not (classes(raiz) & {"table", "table-striped", "table-bordered", "table-hover"})
    assert not [c for c in componentes(raiz) if type(c).__module__.startswith("dash_bootstrap_components")]


def test_tabela_nao_usa_componente_do_ds_que_precisa_de_js():
    exigir_sem_componente_do_ds_que_precisa_de_js(_tabela())


from app.components.filters import EIXOS, axis_selector, fic_toggle


def _radio(raiz):
    radios = [c for c in componentes(raiz) if type(c).__name__ == "RadioItems"]
    assert len(radios) == 1
    return radios[0]


def test_fic_toggle_tem_com_fic_e_sem_fic_com_padrao_com_fic_e_id_preservado():
    radio = _radio(fic_toggle("matriculas-fic"))
    assert radio.id == "matriculas-fic"
    assert radio.options == [{"label": "Com FIC", "value": "com_fic"}, {"label": "Sem FIC", "value": "sem_fic"}]
    assert radio.value == "com_fic"


def test_axis_selector_tem_os_6_eixos_com_padrao_campus_e_id_preservado():
    radio = _radio(axis_selector("matriculas-eixo"))
    assert radio.id == "matriculas-eixo"
    assert [o["value"] for o in radio.options] == ["campus", "tipo_curso", "nome_curso", "modalidade", "oferta", "ciclo"]
    assert radio.options == EIXOS
    assert radio.value == "campus"


@pytest.mark.parametrize("componente", [fic_toggle("x"), axis_selector("y")])
def test_filtros_de_opcao_exclusiva_sao_br_radio_sem_classe_btn_do_bootstrap(componente):
    radio = _radio(componente)
    assert "br-radio" in radio.className.split()
    assert not [c for c in classes(componente) if c == "btn" or c.startswith("btn-")]
    exigir_sem_componente_do_ds_que_precisa_de_js(componente)
