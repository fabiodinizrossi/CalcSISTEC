from dash import html, dcc
import dash_bootstrap_components as dbc


def render_filters(meta):
    options = meta.get("options", {})
    years = meta.get("years_ingresso", [2010, 2025])
    years_oc = meta.get("years_ocorrencia", [])

    def make_dropdown(component_id, values):
        return dcc.Dropdown(
            id=component_id,
            options=[{"label": "Todos", "value": "Todos"}]
            + [{"label": str(v), "value": str(v)} for v in values],
            value="Todos",
            clearable=False,
            style={"fontSize": "12px"},
        )

    slider_marks = {
        int(years[0]): str(int(years[0])),
        int(years[1]): str(int(years[1])),
    }

    return html.Div(
        [
            html.Div("Ano de ingresso", className="filter-label"),
            dcc.RangeSlider(
                id="filt-ano-ingresso",
                min=int(years[0]),
                max=int(years[1]),
                step=1,
                value=[int(years[0]), int(years[1])],
                marks=slider_marks,
                tooltip={"placement": "bottom"},
            ),

            html.Div("Campus", className="filter-label"),
            make_dropdown("filt-campus", options.get("campus", [])),

            html.Div("Subtipo do curso", className="filter-label"),
            make_dropdown("filt-subtipo", options.get("subtipo", [])),

            html.Div("Modalidade", className="filter-label"),
            make_dropdown("filt-modalidade", options.get("modalidade", [])),

            html.Div("Oferta", className="filter-label"),
            make_dropdown("filt-oferta", options.get("oferta", [])),

            html.Div("Curso", className="filter-label"),
            make_dropdown("filt-curso", options.get("curso", [])),

            html.Div("Programa", className="filter-label"),
            make_dropdown("filt-programa", options.get("programa", [])),

            html.Div("FIC", className="filter-label"),
            dbc.RadioItems(
                id="filt-fic-mode",
                options=[
                    {"label": "Sem FIC", "value": "SEM_FIC"},
                    {"label": "Com FIC", "value": "COM_FIC"},
                ],
                value="SEM_FIC",
                inline=True,
                style={"fontSize": "12px"},
            ),

            html.Div("Ano de ocorrência", className="filter-label"),
            dcc.Dropdown(
                id="filt-ano-ocorrencia",
                options=[{"label": str(v), "value": int(v)} for v in years_oc],
                value=years_oc[-1] if years_oc else None,
                clearable=False,
                style={"fontSize": "12px"},
            ),
        ]
    )
