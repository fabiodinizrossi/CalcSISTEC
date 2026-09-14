import base64
import io

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

from app.components.sidebar import make_sidebar
from app.components.filters import render_filters
from app.components.utils import clean_str, clean_sorted

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Pesquisa Institucional - SISTEC",
)

server = app.server
server.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

app.layout = dbc.Container(
    fluid=True,
    children=[
        dcc.Store(id="store-data", storage_type="session"),
        dcc.Store(id="store-meta", storage_type="session"),
        dcc.Store(id="store-filters", storage_type="session"),
        dbc.Row(
            [
                dbc.Col(
                    make_sidebar(),
                    width=3,
                    className="sidebar-col",
                ),
                dbc.Col(
                    dash.page_container,
                    width=9,
                    className="content-col",
                ),
            ]
        ),
    ],
)


@app.callback(
    Output("filters-container", "children"),
    Output("filters-status", "children"),
    Input("store-meta", "data"),
)
def render_sidebar_filters(meta):
    if not meta:
        return (
            html.Div(
                "Faça upload na Home para habilitar os filtros.",
                style={"fontSize": "12px"},
            ),
            "",
        )

    return render_filters(meta), "Arquivo carregado: {}".format(
        meta.get("filename", "")
    )


@app.callback(
    Output("store-filters", "data"),
    Input("filt-ano-ingresso", "value"),
    Input("filt-campus", "value"),
    Input("filt-subtipo", "value"),
    Input("filt-modalidade", "value"),
    Input("filt-oferta", "value"),
    Input("filt-curso", "value"),
    Input("filt-programa", "value"),
    Input("filt-fic-mode", "value"),
    Input("filt-ano-ocorrencia", "value"),
    prevent_initial_call=True,
)
def sync_filters(
    ano_ingresso,
    campus,
    subtipo,
    modalidade,
    oferta,
    curso,
    programa,
    fic_mode,
    ano_ocorrencia,
):
    return {
        "ano_ingresso": ano_ingresso,
        "campus": campus,
        "subtipo": subtipo,
        "modalidade": modalidade,
        "oferta": oferta,
        "curso": curso,
        "programa": programa,
        "fic_mode": fic_mode,
        "ano_ocorrencia": ano_ocorrencia,
    }


@app.callback(
    Output("filt-ano-ingresso", "value"),
    Output("filt-campus", "value"),
    Output("filt-subtipo", "value"),
    Output("filt-modalidade", "value"),
    Output("filt-oferta", "value"),
    Output("filt-curso", "value"),
    Output("filt-programa", "value"),
    Output("filt-fic-mode", "value"),
    Output("filt-ano-ocorrencia", "value"),
    Input("btn-clear-filters", "n_clicks"),
    State("store-meta", "data"),
    prevent_initial_call=True,
)
def clear_filters(n_clicks, meta):
    if not meta:
        raise dash.exceptions.PreventUpdate

    years_ingresso = meta.get("years_ingresso", [2010, 2025])
    years_ocorrencia = meta.get("years_ocorrencia", [])
    ano_oc = years_ocorrencia[-1] if years_ocorrencia else None

    return (
        [int(years_ingresso[0]), int(years_ingresso[1])],
        "Todos",
        "Todos",
        "Todos",
        "Todos",
        "Todos",
        "Todos",
        "SEM_FIC",
        ano_oc,
    )


@app.callback(
    Output("upload-filename", "children"),
    Input("upload-data", "filename"),
    prevent_initial_call=True,
)
def show_filename(filename):
    if not filename:
        return ""
    return "Arquivo selecionado: {}".format(filename)


@app.callback(
    Output("store-data", "data"),
    Output("store-meta", "data"),
    Output("upload-status", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def process_file(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update, ""

    try:
        _, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        xls = pd.ExcelFile(io.BytesIO(decoded))

        if "matriculas" not in xls.sheet_names or "ciclos" not in xls.sheet_names:
            return (
                dash.no_update,
                dash.no_update,
                "Erro: o arquivo precisa conter as abas 'matriculas' e 'ciclos'.",
            )

        df_m = pd.read_excel(xls, sheet_name="matriculas")
        df_c = pd.read_excel(xls, sheet_name="ciclos")

        rename_map = {
            "CÓDIGO CICLO DE MATRÍCULA": "CO_CICLO_MATRICULA",
            "NOME UNIDADE DE ENSINO": "NOME_UNIDADE",
            "NOME DO CURSO": "NOME_CURSO",
            "SUBTIPO CURSOS": "SUBTIPO_CURSO",
            "MODALIDADE ENSINO": "MODALIDADE",
            "OFERTA": "OFERTA",
            "TIPO PROGRAMA DO CURSO": "PROGRAMA",
            "CARGA HORÁRIA TOTAL": "CARGA_TOTAL",
        }

        df_c = df_c.rename(columns=rename_map)

        if "CO_CICLO_MATRICULA" not in df_m.columns:
            return (
                dash.no_update,
                dash.no_update,
                "Erro: a aba 'matriculas' não possui a coluna 'CO_CICLO_MATRICULA'.",
            )

        if "CO_CICLO_MATRICULA" not in df_c.columns:
            return (
                dash.no_update,
                dash.no_update,
                "Erro: a aba 'ciclos' não possui a coluna 'CO_CICLO_MATRICULA' após o renomeamento.",
            )

        df_c = df_c.drop_duplicates(subset=["CO_CICLO_MATRICULA"])

        fact = df_m.merge(df_c, on="CO_CICLO_MATRICULA", how="left")

        if "DT_DATA_INICIO" in fact.columns:
            fact["DT_DATA_INICIO"] = pd.to_datetime(
                fact["DT_DATA_INICIO"], errors="coerce"
            )
            fact["ANO_INGRESSO"] = fact["DT_DATA_INICIO"].dt.year

        if "MES_DE_OCORRENCIA" in fact.columns:
            fact["MES_DE_OCORRENCIA"] = pd.to_datetime(
                fact["MES_DE_OCORRENCIA"], errors="coerce"
            )
            fact["ANO_OCORRENCIA"] = fact["MES_DE_OCORRENCIA"].dt.year
            fact["MES_OCORRENCIA"] = fact["MES_DE_OCORRENCIA"].dt.month

        if "NOME_UNIDADE" in fact.columns:
            fact["CAMPUS"] = fact["NOME_UNIDADE"]
        elif "CO_UNIDADE_ENSINO" in fact.columns:
            fact["CAMPUS"] = fact["CO_UNIDADE_ENSINO"]
        else:
            fact["CAMPUS"] = "N/D"

        if "NOME_CURSO" in fact.columns:
            fact["CURSO"] = fact["NOME_CURSO"]
        elif "CO_CURSO" in fact.columns:
            fact["CURSO"] = fact["CO_CURSO"]
        else:
            fact["CURSO"] = "N/D"

        if "SUBTIPO_CURSO" not in fact.columns:
            fact["SUBTIPO_CURSO"] = "N/D"

        if "MODALIDADE" not in fact.columns:
            fact["MODALIDADE"] = "N/D"

        if "OFERTA" not in fact.columns:
            fact["OFERTA"] = "N/D"

        if "PROGRAMA" not in fact.columns:
            fact["PROGRAMA"] = "N/D"

        fact["CAMPUS"] = clean_str(fact["CAMPUS"])
        fact["CURSO"] = clean_str(fact["CURSO"])
        fact["SUBTIPO_CURSO"] = clean_str(fact["SUBTIPO_CURSO"])
        fact["MODALIDADE"] = clean_str(fact["MODALIDADE"])
        fact["OFERTA"] = clean_str(fact["OFERTA"])
        fact["PROGRAMA"] = clean_str(fact["PROGRAMA"])

        if "NU_CARGA_HORARIA" in fact.columns and "CARGA_TOTAL" in fact.columns:
            numerador = pd.to_numeric(fact["NU_CARGA_HORARIA"], errors="coerce")
            denominador = pd.to_numeric(fact["CARGA_TOTAL"], errors="coerce").replace(
                0, pd.NA
            )
            fact["EQ_MATRICULA"] = (numerador / denominador).fillna(1.0).clip(lower=0)
        else:
            fact["EQ_MATRICULA"] = 1.0

        options = {
            "campus": clean_sorted(fact["CAMPUS"]),
            "subtipo": clean_sorted(fact["SUBTIPO_CURSO"]),
            "modalidade": clean_sorted(fact["MODALIDADE"]),
            "oferta": clean_sorted(fact["OFERTA"]),
            "programa": clean_sorted(fact["PROGRAMA"]),
            "curso": clean_sorted(fact["CURSO"]),
        }

        if "ANO_INGRESSO" in fact.columns and fact["ANO_INGRESSO"].notna().any():
            years_ingresso = [
                int(fact["ANO_INGRESSO"].dropna().min()),
                int(fact["ANO_INGRESSO"].dropna().max()),
            ]
        else:
            years_ingresso = [2010, 2025]

        if "ANO_OCORRENCIA" in fact.columns and fact["ANO_OCORRENCIA"].notna().any():
            years_ocorrencia = sorted(
                pd.to_numeric(
                    fact["ANO_OCORRENCIA"].dropna(), errors="coerce"
                ).dropna().astype(int).unique().tolist()
            )
        else:
            years_ocorrencia = []

        meta = {
            "filename": filename,
            "years_ingresso": years_ingresso,
            "years_ocorrencia": years_ocorrencia,
            "options": options,
        }

        payload = {"fact": fact.to_json(orient="split", date_format="iso")}

        return (
            payload,
            meta,
            "Arquivo carregado e processado com sucesso ({} registros).".format(len(fact)),
        )

    except Exception as e:
        return (
            dash.no_update,
            dash.no_update,
            "Erro ao processar: {}".format(str(e)),
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
