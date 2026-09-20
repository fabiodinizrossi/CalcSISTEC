"""Tabela das páginas públicas no padrão do gov.br DS (`br-table`)."""

from dash import html


def _celula(celula):
    """Uma célula é o valor ou `{"valor": ..., "classe": ...}` quando precisa de classe (faixas de evasão)."""
    if isinstance(celula, dict):
        return html.Td(celula["valor"], className=celula.get("classe"))
    return html.Td(celula)


def tabela_ds(colunas, linhas, legenda):
    """`div.br-table > div.responsive > table`: a rolagem horizontal fica dentro do
    quadro da tabela (RF-07), e a legenda vai em `<caption>`."""
    return html.Div(
        html.Div(
            html.Table(
                [
                    html.Caption(legenda),
                    html.Thead(html.Tr([html.Th(coluna, scope="col") for coluna in colunas])),
                    html.Tbody([html.Tr([_celula(celula) for celula in linha]) for linha in linhas]),
                ]
            ),
            className="responsive",
        ),
        className="br-table",
    )
