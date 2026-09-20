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
