from dash import html

def kpi(title: str, value: str, subtitle=None):
    children = [
        html.Div(title, style={"fontSize": "12px", "opacity": "0.8", "fontWeight": "800"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": "900"}),
    ]
    if subtitle:
        children.append(html.Div(subtitle, style={"fontSize": "11px", "opacity": "0.75"}))
    return html.Div(className="kpi-card", children=children)
