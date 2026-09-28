"""Blocos de apresentação compartilhados pelos dashboards públicos."""

from dash import html

from app.components.kpi import formatar_valor


def cabecalho_pagina(titulo, ano_base, data_publicacao=None):
    """Monta o contexto visual, sem consultar dados ou calcular indicadores."""
    atualizado = (
        html.Span(f"Atualizado em {data_publicacao}", className="atualizado")
        if data_publicacao
        else None
    )
    return html.Div(
        [
            html.Div(
                [
                    html.H1(titulo),
                    html.Span(
                        f"Acompanhamento Sistec | Ano PNP {ano_base}",
                        className="subtitulo",
                    ),
                ],
                className="titulo-bloco",
            ),
            atualizado,
        ],
        className="cabecalho-pagina",
    )


def cartao_indicador(label, valor, formato="0", empty_state=None, destaque=False):
    """Exibe um valor já calculado, preservando zero como valor válido."""
    estado_textual = empty_state is not None and valor is None
    texto = empty_state if estado_textual else formatar_valor(valor, formato)
    classes = "kpi-figma kpi-figma--destaque" if destaque else "kpi-figma"
    classe_valor = "valor valor--texto" if estado_textual else "valor"
    return html.Div(
        [html.Div(label, className="rotulo"), html.Div(texto, className=classe_valor)],
        className=classes,
    )


def cartoes_indicadores(cartoes):
    """Agrupa cartões no grid visual dos dashboards, sem alterar sua ordem."""
    return html.Div(cartoes, className="kpis-figma")
