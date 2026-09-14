"""Variante simplificada de cartão de KPI, sem uso atual pelas páginas
(`app/components/kpi.py`/`kpi_card` é a usada em produção). Restilizada na
feature `001-govbr-design-system` (T022) para usar as mesmas classes DS de
`kpi.py`/`app/assets/style.css`, em vez de estilo inline."""

from dash import html


def kpi(title: str, value: str, subtitle=None):
    children = [
        html.Div(title, className="kpi-label"),
        html.Div(value, className="kpi-value"),
    ]
    if subtitle:
        children.append(html.Div(subtitle, className="kpi-meta"))
    return html.Div(className="kpi-card", children=children)
