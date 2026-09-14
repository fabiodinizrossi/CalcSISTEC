"""BC-04 (Apresentação): componentes de filtro reusados pelas páginas de
dashboard — `FicToggle`, `AxisSelector`, `Select` (dentro de `FilterPanel`) e
o botão "Limpar Filtros".

Implementado na Tarefa 09 do plano de reconstrução, a partir de
`_reversa_sdd/migration/target_screens.md`. Substitui o antigo filtro único
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
    {"label": "Nome do Curso", "value": "nome_curso"},
    {"label": "Modalidade", "value": "modalidade"},
    {"label": "Oferta (Técnico)", "value": "oferta"},
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
            ),
        ],
        className="filter-item",
    )


def axis_selector(id_, default="campus"):
    """BR-MIGRAR-020: "Ver tabela por:" — seleção única por construção
    (`dbc.RadioItems`, nunca um componente multi-select), corrigindo o bug
    M-D3 do legado (`DEV-002`)."""
    return html.Div(
        [
            html.Label("Ver tabela por:", className="filter-label"),
            dbc.RadioItems(id=id_, options=EIXOS, value=default, inline=True),
        ],
        className="filter-item",
    )


def select_filter(id_, label, opcoes):
    return html.Div(
        [
            html.Label(label, className="filter-label"),
            dcc.Dropdown(
                id=id_,
                options=[{"label": "Todos", "value": TODOS}] + [{"label": str(o), "value": str(o)} for o in opcoes],
                value=TODOS,
                clearable=False,
            ),
        ],
        className="filter-item",
    )


def filter_panel(*campos):
    return html.Div(list(campos), className="filter-panel")


def clear_filters_button(id_):
    """BR-MIGRAR-023: callback "Limpar Filtros" por página."""
    return dbc.Button("Limpar Filtros", id=id_, className="btn-primary-gov")
