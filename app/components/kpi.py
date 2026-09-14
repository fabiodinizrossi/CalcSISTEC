"""BC-04 (Apresentação): cartão de KPI (`KpiCard`), reusado por todas as
páginas de dashboard.

Implementado na Tarefa 09 do plano de reconstrução, a partir de
`_reversa_sdd/migration/target_screens.md` (componente `KpiCard`).
"""

import dash_bootstrap_components as dbc
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
    """`empty_state` (RF-08 `pagina-matriculas`): mensagem exibida em vez de
    "0" quando o valor está incompleto (ex.: FEC/FECH ausente, `BR-MIGRAR-008`)
    — nunca "0" enganoso escondendo dado ausente."""
    texto = empty_state if (empty_state is not None and valor is None) else formatar_valor(valor, formato)
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(label, className="kpi-label"),
                html.Div(texto, className="kpi-value"),
            ]
        ),
        className="kpi-card",
    )
