import dash
from dash import html, dcc

dash.register_page(__name__, path="/")

layout = html.Div(
    [
        html.Div(
            className="header",
            children=[
                html.H2("Pesquisa Institucional"),
                html.Div("Acompanhamento SISTEC"),
                html.Div(
                    "O arquivo será processado automaticamente após ser arrastado ou selecionado.",
                    className="small-note",
                ),
            ],
        ),
        html.Div(
            className="panel",
            children=[
                html.H3("Upload do arquivo SISTEC"),
                html.P(
                    "Selecione o arquivo Excel contendo as abas 'matriculas' e 'ciclos'."
                ),
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(
                        [
                            html.Div("Arraste o arquivo aqui"),
                            html.Div("ou"),
                            html.B("clique para selecionar"),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "minHeight": "140px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "12px",
                        "textAlign": "center",
                        "background": "white",
                        "cursor": "pointer",
                        "padding": "20px",
                    },
                    multiple=False,
                ),
                html.Div(
                    id="upload-filename",
                    style={"marginTop": "12px", "fontWeight": "700"},
                ),
                html.Div(
                    id="upload-status",
                    style={"marginTop": "16px", "fontWeight": "700"},
                ),
            ],
        ),
    ]
)
