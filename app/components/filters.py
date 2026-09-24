"""BC-04 (Apresentação): componentes de filtro reusados pelas páginas de
dashboard — `FicToggle`, `AxisSelector`, `Select` (dentro de `FilterPanel`) e
o botão "Limpar Filtros".

Implementado na Tarefa 09 do plano de reconstrução. Substitui o antigo filtro único
de sidebar global (compartilhado entre páginas) por um `FilterPanel` por
página, conforme o contrato de cada tela.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

TODOS = "__todos__"

# BR-MIGRAR-020: os 6 eixos de quebra definidos em EixoQuebra
# (`app/domain/contrato.py`). "oferta" mapeia para `cursos.tipo_oferta_curso`
# (coluna adicionada ao schema na Tarefa 11, após divergência encontrada em
# parity_tests/06-eixo-dinamico-e-fic.feature).
EIXOS = [
    {"label": "Campus", "value": "campus"},
    {"label": "Tipo de Curso", "value": "tipo_curso"},
    {"label": "Oferta (Técnico)", "value": "oferta"},
    {"label": "Nome do Curso", "value": "nome_curso"},
    {"label": "Modalidade", "value": "modalidade"},
    {"label": "Ciclo", "value": "ciclo"},
]


def fic_toggle(id_, default="com_fic"):
    """BR-MIGRAR-021: toggle COM FIC / SEM FIC — bidirecional por
    construção (`dbc.RadioItems` não tem o bug de estado unidirecional do
    legado nesta página)."""
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
    """BR-MIGRAR-023: callback "Limpar Filtros" por página."""
    return html.Button("Limpar Filtros", id=id_, n_clicks=0, className="br-button primary")
