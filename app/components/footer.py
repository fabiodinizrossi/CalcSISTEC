"""BC-04 (Apresentação): rodapé comum às 5 páginas públicas do Dash
(`Footer`), feature `001-govbr-design-system` (T018).

Mostra "Instituto Federal Farroupilha", o link institucional e o e-mail de
contato vigente (`config_store.get_contato_email` — RF-04, RF-15, RN-12) e o
link "Área administrativa" (RF-18) para `/admin/login`.
"""

from dash import html

from app.data.config_store import get_contato_email


def make_footer():
    return html.Footer(
        className="app-footer",
        role="contentinfo",
        children=[
            html.Span("Instituto Federal Farroupilha"),
            html.A(
                "www.iffarroupilha.edu.br",
                href="https://www.iffarroupilha.edu.br",
                target="_blank",
                rel="noopener",
            ),
            html.Span(get_contato_email()),
            html.A("Área administrativa", href="/admin/login", className="app-footer-admin-link"),
        ],
    )
