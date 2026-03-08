import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from components.utils import apply_filters, classify_status, matriculas_equivalentes

dash.register_page(__name__, path="/matriculas")

GROUP_MAP = {
    "Campus": "CAMPUS",
    "Curso": "CURSO",
    "Subtipo": "SUBTIPO_CURSO",
    "Modalidade": "MODALIDADE",
    "Oferta": "OFERTA",
    "Programa": "PROGRAMA",
}


layout = html.Div(
    [
        html.Div(
            className="header",
            children=[
                html.H2("Matrículas"),
                html.Div("Situação das matrículas"),
            ],
        ),
        html.Div(
            className="panel",
            children=[
                html.Div(id="matriculas-alerta"),
                dbc.Row(
                    [
                        dbc.Col(html.Div(id="kpi-mat-total"), md=2),
                        dbc.Col(html.Div(id="kpi-mat-cursos"), md=2),
                        dbc.Col(html.Div(id="kpi-mat-eq"), md=3),
                        dbc.Col(html.Div(id="kpi-mat-concl"), md=2),
                        dbc.Col(html.Div(id="kpi-mat-curso"), md=3),
                    ],
                    className="g-3",
                ),
                html.Br(),
                dcc.Tabs(
                    id="matriculas-groupby",
                    value="Campus",
                    children=[dcc.Tab(label=k, value=k) for k in GROUP_MAP.keys()],
                ),
                html.Br(),
                dcc.Graph(id="grafico-matriculas"),
                html.Div(id="tabela-matriculas"),
            ],
        ),
    ]
)


@callback(
    Output("matriculas-alerta", "children"),
    Output("kpi-mat-total", "children"),
    Output("kpi-mat-cursos", "children"),
    Output("kpi-mat-eq", "children"),
    Output("kpi-mat-concl", "children"),
    Output("kpi-mat-curso", "children"),
    Output("grafico-matriculas", "figure"),
    Output("tabela-matriculas", "children"),
    Input("store-data", "data"),
    Input("store-filters", "data"),
    Input("matriculas-groupby", "value"),
)
def atualizar_matriculas(store_data, filtros, group_label):
    if not store_data or "fact" not in store_data:
        empty_fig = px.bar(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
        alerta = dbc.Alert("Faça upload do arquivo na Home.", color="warning")
        return alerta, "", "", "", "", "", empty_fig, ""

    df = pd.read_json(store_data["fact"], orient="split")
    df = apply_filters(df, filtros)
    df["STATUS_GRUPO"] = classify_status(df["NO_STATUS_MATRICULA"])

    if len(df) == 0:
        empty_fig = px.bar(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
        alerta = dbc.Alert("Nenhum registro encontrado para os filtros selecionados.", color="info")
        return alerta, "", "", "", "", "", empty_fig, ""

    total = len(df)
    cursos = df["CURSO"].nunique() if "CURSO" in df.columns else 0
    eq = matriculas_equivalentes(df)
    concl = int((df["STATUS_GRUPO"] == "CONCLUIDO").sum())
    em_curso = int((df["STATUS_GRUPO"] == "EM_CURSO").sum())

    col = GROUP_MAP.get(group_label, "CAMPUS")
    if col not in df.columns:
        col = "CAMPUS"

    agrupado = (
        df.groupby([col, "STATUS_GRUPO"])
        .size()
        .reset_index(name="QTD")
    )

    fig = px.bar(
        agrupado,
        x=col,
        y="QTD",
        color="STATUS_GRUPO",
        barmode="stack",
        title="Matrículas por {}".format(group_label),
    )

    tabela = (
        df.groupby(col)
        .agg(
            Matriculas=("CO_MATRICULA", "count"),
            Cursos=("CURSO", "nunique"),
        )
        .reset_index()
        .sort_values("Matriculas", ascending=False)
    )

    table_component = dbc.Table.from_dataframe(
        tabela,
        striped=True,
        bordered=False,
        hover=True,
        size="sm",
    )

    alerta = ""

    return (
        alerta,
        dbc.Card(dbc.CardBody([html.Div("Matrículas"), html.H4(f"{total:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Cursos"), html.H4(f"{cursos:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Matrículas equivalentes"), html.H4(f"{eq:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Concluídas"), html.H4(f"{concl:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Em curso"), html.H4(f"{em_curso:,}".replace(",", "."))]), className="kpi-card"),
        fig,
        table_component,
    )
