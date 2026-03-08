from dash import html
import dash_bootstrap_components as dbc


def make_sidebar():
    return html.Div(
        className="sidebar",
        children=[
            html.Div(
                [
                    html.Div(
                        "Pesquisa Institucional",
                        style={"fontWeight": "900", "fontSize": "16px"},
                    ),
                    html.Div(
                        "Acompanhamento SISTEC",
                        style={"fontWeight": "700", "fontSize": "12px", "opacity": "0.9"},
                    ),
                    html.Hr(className="sidebar-hr"),
                ]
            ),
            dbc.Nav(
                vertical=True,
                pills=True,
                children=[
                    dbc.NavLink("Home (Upload)", href="/", active="exact"),
                    dbc.NavLink("Matrículas", href="/matriculas", active="exact"),
                    dbc.NavLink("Eficiência Acadêmica", href="/eficiencia", active="exact"),
                    dbc.NavLink("Taxa de Evasão", href="/evasao", active="exact"),
                    dbc.NavLink("Percentuais Legais", href="/percentuais", active="exact"),
                ],
            ),
            html.Hr(className="sidebar-hr"),
            html.Div("Filtros", style={"fontWeight": "900"}),
            html.Div(
                "Aplicam-se a todas as páginas.",
                style={"fontSize": "12px", "opacity": "0.9"},
            ),
            html.Div(id="filters-container"),
            html.Hr(className="sidebar-hr"),
            dbc.Button(
                "Limpar filtros",
                id="btn-clear-filters",
                className="btn-accent",
                style={"width": "100%"},
            ),
            html.Div(
                id="filters-status",
                style={"marginTop": "10px", "fontSize": "12px", "opacity": "0.9"},
            ),
        ],
    )
