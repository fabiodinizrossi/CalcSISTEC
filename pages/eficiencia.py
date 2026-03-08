import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from components.utils import apply_filters, classify_status

dash.register_page(__name__, path="/eficiencia")

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
                html.H2("Eficiência Acadêmica"),
                html.Div("Concluídos, evadidos e retidos"),
            ],
        ),
        html.Div(
            className="panel",
            children=[
                html.Div(id="eficiencia-alerta"),
                dbc.Row(
                    [
                        dbc.Col(html.Div(id="kpi-efi-total"), md=3),
                        dbc.Col(html.Div(id="kpi-efi-concl"), md=3),
                        dbc.Col(html.Div(id="kpi-efi-evad"), md=3),
                        dbc.Col(html.Div(id="kpi-efi-indice"), md=3),
                    ],
                    className="g-3",
                ),
                html.Br(),
                dcc.Tabs(
                    id="eficiencia-groupby",
                    value="Campus",
                    children=[dcc.Tab(label=k, value=k) for k in GROUP_MAP.keys()],
                ),
                html.Br(),
                dcc.Graph(id="grafico-eficiencia"),
                html.Div(id="tabela-eficiencia"),
            ],
        ),
    ]
)


@callback(
    Output("eficiencia-alerta", "children"),
    Output("kpi-efi-total", "children"),
    Output("kpi-efi-concl", "children"),
    Output("kpi-efi-evad", "children"),
    Output("kpi-efi-indice", "children"),
    Output("grafico-eficiencia", "figure"),
    Output("tabela-eficiencia", "children"),
    Input("store-data", "data"),
    Input("store-filters", "data"),
    Input("eficiencia-groupby", "value"),
)
def atualizar_eficiencia(store_data, filtros, group_label):
    if not store_data or "fact" not in store_data:
        empty_fig = px.bar(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
        alerta = dbc.Alert("Faça upload do arquivo na Home.", color="warning")
        return alerta, "", "", "", "", empty_fig, ""

    df = pd.read_json(store_data["fact"], orient="split")
    df = apply_filters(df, filtros)
    df["STATUS_GRUPO"] = classify_status(df["NO_STATUS_MATRICULA"])

    if len(df) == 0:
        empty_fig = px.bar(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
        alerta = dbc.Alert("Nenhum registro encontrado para os filtros selecionados.", color="info")
        return alerta, "", "", "", "", empty_fig, ""

    total = len(df)
    concl = int((df["STATUS_GRUPO"] == "CONCLUIDO").sum())
    evad = int(df["STATUS_GRUPO"].isin(["ABANDONO", "TRANSF_EXT", "DESLIGADO", "TRANSF_INT"]).sum())
    retidos = int((df["STATUS_GRUPO"] == "RETIDO").sum())
    indice = round((concl / total) * 100, 2) if total > 0 else 0.0

    col = GROUP_MAP.get(group_label, "CAMPUS")
    if col not in df.columns:
        col = "CAMPUS"

    tabela = (
        df.groupby(col)
        .apply(
            lambda x: pd.Series(
                {
                    "Total": len(x),
                    "Concluídos": int((x["STATUS_GRUPO"] == "CONCLUIDO").sum()),
                    "Evadidos": int(x["STATUS_GRUPO"].isin(["ABANDONO", "TRANSF_EXT", "DESLIGADO", "TRANSF_INT"]).sum()),
                    "Retidos": int((x["STATUS_GRUPO"] == "RETIDO").sum()),
                }
            )
        )
        .reset_index()
    )

    tabela["Índice de Eficiência (%)"] = (
        (tabela["Concluídos"] / tabela["Total"]) * 100
    ).fillna(0).round(2)

    fig = px.bar(
        tabela.sort_values("Índice de Eficiência (%)", ascending=False),
        x=col,
        y="Índice de Eficiência (%)",
        title="Índice de Eficiência por {}".format(group_label),
    )

    table_component = dbc.Table.from_dataframe(
        tabela.sort_values("Índice de Eficiência (%)", ascending=False),
        striped=True,
        bordered=False,
        hover=True,
        size="sm",
    )

    return (
        "",
        dbc.Card(dbc.CardBody([html.Div("Total"), html.H4(f"{total:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Concluídos"), html.H4(f"{concl:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Evadidos"), html.H4(f"{evad:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Índice"), html.H4(f"{indice:.2f}%".replace(".", ","))]), className="kpi-card"),
        fig,
        table_component,
    )
