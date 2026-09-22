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


def tabela_hierarquica_ds(df, eixos, colunas_por_eixo, rotulos_por_eixo, colunas, legenda, metricas, total):
    """Tabela pública em árvore; a ordem de ``eixos`` define seus níveis."""
    linhas = []

    def visitar(grupo, nivel, pai, caminho):
        if nivel >= len(eixos):
            return
        eixo = eixos[nivel]
        coluna = colunas_por_eixo[eixo]
        for indice, (valor, subgrupo) in enumerate(grupo.groupby(coluna, dropna=False)):
            identificador = "-".join(map(str, caminho + (indice,)))
            tem_filhos = nivel + 1 < len(eixos)
            linhas.append((valor, subgrupo, nivel, identificador, pai, tem_filhos))
            if tem_filhos:
                visitar(subgrupo, nivel + 1, identificador, caminho + (indice,))

    if eixos:
        visitar(df, 0, "", ())

    corpo = []
    for valor, grupo, nivel, identificador, pai, tem_filhos in linhas:
        controle = (
            html.Button(
                html.I(className="fas fa-chevron-down", **{"aria-hidden": "true"}),
                className="matriz-expansor",
                type="button",
                title="Recolher grupo",
                **{"aria-expanded": "true", "aria-label": f"Recolher {valor}"},
            )
            if tem_filhos
            else html.Span(className="matriz-expansor-espaco", **{"aria-hidden": "true"})
        )
        corpo.append(
            html.Tr(
                [
                    html.Td(
                        html.Div([controle, html.Span(str(valor))], className="matriz-rotulo"),
                        className="campus",
                        style={"--nivel": str(nivel)},
                    ),
                    *[_celula(valor, numerica=True) for valor in metricas(grupo)],
                ],
                className=f"matriz-nivel-{nivel}",
                **{"data-group-id": identificador, "data-parent-id": pai, "data-level": nivel},
            )
        )

    rotulo = " › ".join(rotulos_por_eixo[eixo] for eixo in eixos) or "Total geral"
    tabela = html.Table(
        [
            html.Caption(legenda),
            html.Thead(html.Tr([html.Th(rotulo, scope="col"), *[html.Th(coluna, scope="col") for coluna in colunas]])),
            html.Tbody(corpo),
            html.Tfoot(html.Tr([_celula("Total"), *[_celula(valor, numerica=True) for valor in total]])),
        ],
        className="tabela-publica tabela-hierarquica",
        **{"data-sortable": "true"},
    )
    return html.Div(
        [
            html.Div(tabela, className="rolagem-tabela", tabIndex="0", role="region", **{"aria-label": legenda}),
            html.P("Deslize a tabela para o lado para ver todas as colunas.", className="dica-rolagem"),
        ],
        className="matriz-figma tabela-publica-quadro",
    )
