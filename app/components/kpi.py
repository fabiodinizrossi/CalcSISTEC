"""Cartão de KPI usado pelas páginas do dashboard."""

from dash import html


def formatar_valor(valor, formato="0"):
    if valor is None:
        return "—"
    if formato == "0" or formato == "#,0":
        return f"{int(round(valor)):,}".replace(",", ".")
    if formato == "#,0.00":
        texto = f"{valor:,.2f}"
        return texto.replace(",", "@").replace(".", ",").replace("@", ".")
    return str(valor)


def kpi_card(label, valor, formato="0", empty_state=None):
    """Mostra `empty_state` em vez de zero quando o valor está incompleto,
    como no caso de FEC/FECH ausente."""
    texto = empty_state if (empty_state is not None and valor is None) else formatar_valor(valor, formato)
    return html.Div(
        html.Div(
            [
                html.Div(label, className="kpi-label"),
                html.Div(texto, className="kpi-value"),
            ],
            className="card-content",
        ),
        className="br-card",
    )
