"""Filtros de FIC, eixo e seleção usados pelas páginas do dashboard.

Cada página monta seus próprios filtros e botão "Limpar Filtros".
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

TODOS = "__todos__"

# Os seis eixos de quebra seguem EixoQuebra (`app/domain/contrato.py`).
# "oferta" mapeia para `cursos.tipo_oferta_curso`.
EIXOS = [
    {"label": "Campus", "value": "campus"},
    {"label": "Tipo de Curso", "value": "tipo_curso"},
    {"label": "Oferta (Técnico)", "value": "oferta"},
    {"label": "Nome do Curso", "value": "nome_curso"},
    {"label": "Modalidade", "value": "modalidade"},
    {"label": "Ciclo", "value": "ciclo"},
]


def fic_toggle(id_, default="com_fic"):
    """Cria o controle Com FIC / Sem FIC com seleção nos dois sentidos."""
    return html.Div(
        [
            html.Label("Filtro FIC", className="filter-label"),
            dbc.RadioItems(
                id=id_,
                options=[{"label": "Com FIC", "value": "com_fic"}, {"label": "Sem FIC", "value": "sem_fic"}],
                value=default,
                inline=True,
                className="br-radio",
            ),
        ],
        className="filter-item",
    )


def axis_selector(id_, default="campus"):
    """"Ver tabela por" como chips; a ordem dos cliques forma a hierarquia."""
    return html.Div(
        [
            html.Span("Ver tabela por:", className="rotulo-chips"),
            dbc.Checklist(
                id=id_,
                options=EIXOS,
                value=[default] if default else [],
                inline=True,
                className="chips-grupo",
                labelClassName="chip",
                labelCheckedClassName="chip--ativo",
                inputClassName="chip-input",
            ),
        ],
        className="card-chips",
    )


def ordenar_eixos(marcados, ordem_anterior):
    """Mantém os campos ativos na ordem em que foram marcados."""
    marcados = list(dict.fromkeys(marcados or []))
    ordem = [eixo for eixo in (ordem_anterior or []) if eixo in marcados]
    ordem.extend(eixo for eixo in marcados if eixo not in ordem)
    return ordem


def select_filter(id_, label, opcoes):
    return html.Div(
        [
            html.Label(label, className="filter-label"),
            dcc.Dropdown(
                id=id_,
                options=[{"label": "Todos", "value": TODOS}] + [{"label": str(o), "value": str(o)} for o in opcoes],
                value=TODOS,
                clearable=False,
                className="filtro-dropdown",
            ),
        ],
        className="filter-item",
    )


def filter_panel(*campos):
    return html.Div([html.Div(campo, className="col-12 col-md-6 col-lg-4") for campo in campos], className="row filter-panel")


def clear_filters_button(id_):
    """Cria o botão "Limpar Filtros" da página."""
    return html.Button("Limpar Filtros", id=id_, n_clicks=0, className="br-button primary")
