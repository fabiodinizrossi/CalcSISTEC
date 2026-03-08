import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from components.utils import apply_filters, classify_status

dash.register_page(__name__, path="/evasao")

layout = html.Div(
    [
        html.Div(
            className="header",
            children=[
                html.H2("Taxa de Evasão"),
                html.Div("Evasões por mês e por campus"),
            ],
        ),
        html.Div(
            className="panel",
            children=[
                html.Div(id="evasao-alerta"),
                dbc.Row(
                    [
                        dbc.Col(html.Div(id="kpi-eva-aband"), md=3),
                        dbc.Col(html.Div(id="kpi-eva-transf"), md=3),
                        dbc.Col(html.Div(id="kpi-eva-deslig"), md=3),
                        dbc.Col(html.Div(id="kpi-eva-taxa"), md=3),
                    ],
                    className="g-3",
                ),
                html.Br(),
                dcc.Graph(id="grafico-evasao"),
                html.Div(id="tabela-evasao"),
            ],
        ),
    ]
)


@callback(
    Output("evasao-alerta", "children"),
    Output("kpi-eva-aband", "children"),
    Output("kpi-eva-transf", "children"),
    Output("kpi-eva-deslig", "children"),
    Output("kpi-eva-taxa", "children"),
    Output("grafico-evasao", "figure"),
    Output("tabela-evasao", "children"),
    Input("store-data", "data"),
    Input("store-filters", "data"),
)
def atualizar_evasao(store_data, filtros):
    if not store_data or "fact" not in store_data:
        empty_fig = px.line(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
        alerta = dbc.Alert("Faça upload do arquivo na Home.", color="warning")
        return alerta, "", "", "", "", empty_fig, ""

    df = pd.read_json(store_data["fact"], orient="split")
    df = apply_filters(df, filtros)
    df["STATUS_GRUPO"] = classify_status(df["NO_STATUS_MATRICULA"])

    if "ANO_OCORRENCIA" in df.columns and filtros and filtros.get("ano_ocorrencia") is not None:
        df = df[df["ANO_OCORRENCIA"] == int(filtros["ano_ocorrencia"])]

    if len(df) == 0:
        empty_fig = px.line(pd.DataFrame({"x": [], "y": []}), x="x", y="y")
        alerta = dbc.Alert("Nenhum registro encontrado para os filtros selecionados.", color="info")
        return alerta, "", "", "", "", empty_fig, ""

    abandonos = int((df["STATUS_GRUPO"] == "ABANDONO").sum())
    transferencias = int(df["STATUS_GRUPO"].isin(["TRANSF_EXT", "TRANSF_INT"]).sum())
    desligamentos = int((df["STATUS_GRUPO"] == "DESLIGADO").sum())

    total = len(df)
    evasoes = int(df["STATUS_GRUPO"].isin(["ABANDONO", "TRANSF_EXT", "DESLIGADO", "TRANSF_INT"]).sum())
    taxa = round((evasoes / total) * 100, 2) if total > 0 else 0.0

    if "MES_OCORRENCIA" in df.columns:
        mensal = (
            df[df["STATUS_GRUPO"].isin(["ABANDONO", "TRANSF_EXT", "DESLIGADO", "TRANSF_INT"])]
            .groupby("MES_OCORRENCIA")
            .size()
            .reset_index(name="Evasões")
            .sort_values("MES_OCORRENCIA")
        )
        fig = px.area(
            mensal,
            x="MES_OCORRENCIA",
            y="Evasões",
            title="Evasões por mês",
        )
    else:
        fig = px.line(pd.DataFrame({"x": [], "y": []}), x="x", y="y")

    if "CAMPUS" in df.columns:
        tabela = (
            df.groupby("CAMPUS")
            .apply(
                lambda x: pd.Series(
                    {
                        "Matrículas": len(x),
                        "Evasões": int(x["STATUS_GRUPO"].isin(["ABANDONO", "TRANSF_EXT", "DESLIGADO", "TRANSF_INT"]).sum()),
                    }
                )
            )
            .reset_index()
        )
        tabela["Taxa de Evasão (%)"] = (
            (tabela["Evasões"] / tabela["Matrículas"]) * 100
        ).fillna(0).round(2)

        table_component = dbc.Table.from_dataframe(
            tabela.sort_values("Taxa de Evasão (%)", ascending=False),
            striped=True,
            bordered=False,
            hover=True,
            size="sm",
        )
    else:
        table_component = ""

    return (
        "",
        dbc.Card(dbc.CardBody([html.Div("Abandonos"), html.H4(f"{abandonos:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Transferências"), html.H4(f"{transferencias:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Desligamentos"), html.H4(f"{desligamentos:,}".replace(",", "."))]), className="kpi-card"),
        dbc.Card(dbc.CardBody([html.Div("Taxa"), html.H4(f"{taxa:.2f}%".replace(".", ","))]), className="kpi-card"),
        fig,
        table_component,
    )
