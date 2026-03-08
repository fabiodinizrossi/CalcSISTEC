from dash import html, dcc
import dash_bootstrap_components as dbc

def render_filters(meta: dict):
    # meta: {options: {campus:[], ...}, years:[min,max], years_ocorrencia:[...]}
    options = (meta or {}).get("options", {})
    years = (meta or {}).get("years_ingresso", [2010, 2025])
    years_oc = (meta or {}).get("years_ocorrencia", [])

    def dd(id_, opts, placeholder):
        return dcc.Dropdown(
            id=id_,
            options=[{"label": "Todos", "value": "Todos"}] + [{"label": o, "value": o} for o in opts],
            value="Todos",
            clearable=False,
            placeholder=placeholder,
            style={"fontSize": "12px"},
        )

    year_marks = {int(y): str(int(y)) for y in range(int(years[0]), int(years[1])+1, max(1, (int(years[1])-int(years[0]))//5 or 1))}
    year_marks[int(years[0])] = str(int(years[0]))
    year_marks[int(years[1])] = str(int(years[1]))

    oc_year_dd = dcc.Dropdown(
        id="filt-ano-ocorrencia",
        options=[{"label": str(y), "value": int(y)} for y in years_oc] if years_oc else [],
        value=int(years_oc[-1]) if years_oc else None,
        clearable=False,
        placeholder="Ano (ocorrência)",
        style={"fontSize": "12px"},
    )

    return html.Div(
        [
            html.Div("Ano de ingresso (range)", className="filter-label"),
            dcc.RangeSlider(
                id="filt-ano-ingresso",
                min=int(years[0]),
                max=int(years[1]),
                value=[int(years[0]), int(years[1])],
                marks=year_marks,
                step=1,
                tooltip={"placement": "bottom", "always_visible": False},
            ),

            html.Div("Campus", className="filter-label"),
            dd("filt-campus", options.get("campus", []), "Campus"),

            html.Div("Tipo/Subtipo do curso", className="filter-label"),
            dd("filt-subtipo", options.get("subtipo", []), "Subtipo"),

            html.Div("Modalidade", className="filter-label"),
            dd("filt-modalidade", options.get("modalidade", []), "Modalidade"),

            html.Div("Oferta", className="filter-label"),
            dd("filt-oferta", options.get("oferta", []), "Oferta"),

            html.Div("Programa", className="filter-label"),
            dd("filt-programa", options.get("programa", []), "Programa"),

            html.Div("Curso", className="filter-label"),
            dd("filt-curso", options.get("curso", []), "Curso"),

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

            html.Hr(className="sidebar-hr"),
            html.Div("Ano de referência (Evasão)", className="filter-label"),
            oc_year_dd,
        ]
    )
