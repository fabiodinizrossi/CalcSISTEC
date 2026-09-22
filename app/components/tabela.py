"""Tabela das páginas públicas no padrão do gov.br DS (`br-table`)."""

from dash import html


def _celula(celula, numerica=False):
    """Uma célula é o valor ou `{"valor": ..., "classe": ...}` quando precisa de classe (faixas de evasão)."""
    if isinstance(celula, dict):
        classes = [celula.get("classe"), "num" if numerica else None]
        return html.Td(celula["valor"], className=" ".join(c for c in classes if c) or None)
    return html.Td(celula, className="num" if numerica else None)


def tabela_ds(colunas, linhas, legenda, *, quadro=False, total=None, ordenavel=True):
    """`div.br-table > div.responsive > table`: a rolagem horizontal fica dentro do
    quadro da tabela (RF-07), e a legenda vai em `<caption>`."""
    corpo = html.Tbody(
        [
            html.Tr([_celula(celula, quadro and indice > 0) for indice, celula in enumerate(linha)])
            for linha in linhas
        ]
    )
    tabela = html.Table(
        [
            html.Caption(legenda),
            html.Thead(html.Tr([html.Th(coluna, scope="col") for coluna in colunas])),
            corpo,
            html.Tfoot(html.Tr([_celula(celula, quadro and indice > 0) for indice, celula in enumerate(total)]))
            if total is not None
            else None,
        ],
        className="tabela-publica" if quadro else None,
        **{"data-sortable": "true" if ordenavel else "false"},
    )
    if not quadro:
        return html.Div(html.Div(tabela, className="responsive"), className="br-table")
    return html.Div(
        [
            html.Div(tabela, className="rolagem-tabela", tabIndex="0", role="region", **{"aria-label": legenda}),
            html.P("Deslize a tabela para o lado para ver todas as colunas.", className="dica-rolagem"),
        ],
        className="matriz-figma tabela-publica-quadro",
    )
