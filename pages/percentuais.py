import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from components.utils import apply_filters, matriculas_equivalentes

dash.register_page(__name__, path="/percentuais")


def make_gauge(title, value):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(value),
            number={"suffix": "%"},
            title={"text": title},
            gauge={"axis": {"range": [0, 100]}},
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


layout = html.Div(
    [
        html.Div(
            className="header",
            children=[
                html.H2("Percentuais Legais"),
                html.Div("Técnico, Formação de Professores e Proeja"),
            ],
        ),
        html.Div(
            className="panel",
            children=[
                html.Div(id="percentuais-alerta"),
                dbc.Row(
                    [
                        dbc.Col(html.Div(id="kpi-p-total"), md=3),
                        dbc.Col(html.Div(id="kpi-p-tecnico"), md=3),
                        dbc.Col(html.Div(id="kpi-p-formacao"), md=3),
                        dbc.Col(html.Div(id="kpi-p-proeja"), md=3),
                    ],
                    className="g-3",
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id="gauge-tecnico"), md=4),
                        dbc.Col(dcc.Graph(id="gauge-formacao"), md=4),
                        dbc.Col(dcc.Graph(id="gauge-proeja"), md=4),
                    ]
                ),
                html.Br(),
                html.Div(id="tabela-percentuais"),
            ],
        ),
    ]
)


@callback(
    Output("percentuais-alerta", "children"),
    Output("kpi-p-total", "children"),
    Output("kpi-p-tecnico", "children"),
    Output("kpi-p-formacao", "children"),
    Output("kpi-p-proeja", "children"),
    Output("gauge-tecnico", "figure"),
    Output("gauge-formacao", "figure"),
    Output("gauge-proeja", "figure"),
    Output("tabela-percentuais", "children"),
    Input("store-data", "data"),
    Input("store-filters", "data"),
)
def atualizar_percentuais(store_data, filtros):
    if not store_data or "fact" not in store_data:
        alerta = dbc.Alert("Faça upload do arquivo na Home.", color="warning")
        return alerta, "", "", "", "", make_gauge("Técnico", 0), make_gauge("Formação", 0), make_gauge("Proeja", 0), ""

    df = pd.read_json(store_data["fact"], orient="split")
    df = apply_filters(df, filtros)

    if len(df) == 0:
        alerta = dbc.Alert("Nenhum registro encontrado para os filtros selecionados.", color="info")
        return alerta, "", "", "", "", make_gauge("Técnico", 0), make_gauge("Formação", 0), make_gauge("Proeja", 0), ""

    total_eq = matriculas_equivalentes(df)

    subtipo_norm = (
        df["SUBTIPO_CURSO"]
        .astype(str)
        .str.upper()
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )

    programa_norm = (
        df["PROGRAMA"]
        .astype(str)
        .str.upper()
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )

    df_tecnico = df[subtipo_norm.str.contains("TECNICO", na=False)]
    df_formacao = df[subtipo_norm.str.contains("LICENCIATURA|FORMACAO DE PROFESSORES", na=False)]
    df_proeja = df[programa_norm.str.contains("PROEJA", na=False)]

    eq_tecnico = matriculas_equivalentes(df_tecnico)
    eq_formacao = matriculas_equivalentes(df_formacao)
    eq_proeja = matriculas_equivalentes(df_proeja)

    pct_tecnico = round((eq_tecnico / total_eq) * 100, 2) if total_eq > 0 else 0.0
    pct_formacao = round((eq_formacao / total_eq) * 100, 2) if total_eq > 0 else 0.0
    pct_proeja = round((eq_proeja / total_eq) * 100, 2) if total_eq > 0 else 0.0

    tabela = (
        df.groupby("CAMPUS")
        .apply(
            lambda x: pd.Series(
                {
                    "MatEq Total": round(matriculas_equivalentes(x), 2),
                    "MatEq Técnico": round(
                        matriculas_equivalentes(
                            x[
                                x["SUBTIPO_CURSO"]
                                .astype(str)
                                .str.upper()
                                .str.normalize("NFKD")
                                .str.encode("ascii", errors="ignore")
                                .str.decode("utf-8")
                                .str.contains("TECNICO", na=False)
                            ]
                        ),
                        2,
                    ),
                    "MatEq Formação": round(
                        matriculas_equivalentes(
                            x[
                                x["SUBTIPO_CURSO"]
                                .astype(str)
                                .str.upper()
                                .str.normalize("NFKD")
                                .str.encode("ascii", errors="ignore")
                                .str.decode("utf-8")
                                .str.contains("LICENCIATURA|FORMACAO DE PROFESSORES", na=False)
                            ]
                        ),
                        2,
                    ),
                    "MatEq Proeja": round(
                        matriculas_equivalentes(
                            x[
                                x["PROGRAMA"]
                                .astype(str)
                                .str.upper()
                                .str.normalize("NFKD")
                                .str.encode("ascii", errors="ignore")
                                .str.decode("utf-8")
                                .str.contains("PROEJA", na=False)
                            ]
                        ),
                        2,
                    ),
                }
            )
        )
        .reset_index()
    )

    table_component = dbc.Table.from_dataframe(
        tabela.sort_values("MatEq Total", ascending=False),
        striped=True,
        bordered=False,
        hover=True,
        size="sm",
    )

    return (
        "",
        dbc.Card(dbc.CardBody([html.Div("MatEq Total"), html.H4(f"{total_eq:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("MatEq Técnico"), html.H4(f"{eq_tecnico:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("MatEq Formação"), html.H4(f"{eq_formacao:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("MatEq Proeja"), html.H4(f"{eq_proeja:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))]), className="kpi-card"),
        make_gauge("Técnico", pct_tecnico),
        make_gauge("Formação", pct_formacao),
        make_gauge("Proeja", pct_proeja),
        table_component,
    )
