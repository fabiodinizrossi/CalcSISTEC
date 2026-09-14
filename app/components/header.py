"""BC-04 (Apresentação): cabeçalho comum às 5 páginas públicas do Dash
(`PageHeader`), feature `001-govbr-design-system` (T016).

Mostra o logotipo vigente, com texto alternativo fixo "Instituto Federal
Farroupilha" (RF-02), e os títulos "Painel de Acompanhamento Sistec"/
"Pesquisa Institucional". Deliberadamente sem a barra de identidade do
Governo Federal (RF-02): este não é um sistema gov.br oficial, apenas adota
o Design System.

O `<img>` aponta para a rota pública `GET /branding/logo` (T037), que resolve
`config_store.get_logo_path` no momento da requisição — indireção necessária
porque o logotipo enviado pelo administrador fica em `app/data/uploads/branding/`
(fora da pasta `assets/` que o Dash serve estaticamente).
"""

from dash import html


def make_header():
    return html.Header(
        className="app-header",
        role="banner",
        children=[
            html.Div(
                className="app-header-inner",
                children=[
                    html.Img(
                        src="/branding/logo",
                        alt="Instituto Federal Farroupilha",
                        className="app-header-logo",
                    ),
                    html.Div(
                        className="app-header-text",
                        children=[
                            html.Span("Painel de Acompanhamento Sistec", className="app-header-title"),
                            html.Span("Pesquisa Institucional", className="app-header-subtitle"),
                        ],
                    ),
                ],
            ),
        ],
    )
