"""BC-04 (Apresentação): menu de navegação, comum a todas as páginas.

Reescrito na feature `001-govbr-design-system` (T017): a barra lateral fixa
vira um `NavigationMenu` horizontal no topo, recolhível por um botão abaixo
do breakpoint médio (`app/assets/style.css` `.nav-menu`/`.nav-open`,
alternado por `app/assets/nav-toggle.js` — Dash carrega qualquer `.js` de
`assets/` automaticamente, sem precisar de callback Python).

`dbc.NavLink(active="exact")` é mantido deliberadamente: é o único jeito
simples de marcar a página atual (`aria-current="page"`, adicionado pelo
próprio Dash Bootstrap Components no lado do cliente) sem um callback
server-side lendo `dcc.Location` — as classes visuais é que mudam para o
padrão DS (`nav-menu-link`), não o mecanismo de ativação. As 5 páginas
continuam sempre no menu, sem retenção (`BR-MIGRAR-022`).
"""

import dash_bootstrap_components as dbc
from dash import html

PAGINAS = [
    ("Início", "/"),
    ("Matrículas", "/matriculas"),
    ("Eficiência Acadêmica", "/eficiencia"),
    ("Taxa de Evasão Anual", "/evasao"),
    ("Percentuais Legais", "/percentuais-legais"),
]


def make_navigation():
    return html.Nav(
        className="nav-menu",
        id="nav-menu",
        **{"aria-label": "Navegação principal"},
        children=[
            html.Button(
                "Menu",
                id="nav-toggle",
                type="button",
                className="nav-toggle",
                **{"aria-expanded": "false", "aria-controls": "nav-menu-list"},
            ),
            dbc.Nav(
                id="nav-menu-list",
                className="nav-menu-list",
                vertical=False,
                children=[
                    dbc.NavLink(label, href=href, active="exact", className="nav-menu-link")
                    for label, href in PAGINAS
                ],
            ),
        ],
    )
