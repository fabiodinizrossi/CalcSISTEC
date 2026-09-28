"""Mensagem `br-message` das páginas públicas, com a mesma marcação e os mesmos
papéis ARIA do macro `mensagem` dos templates Jinja."""

from dash import html

_ICONES = {
    "success": "fa-check-circle",
    "danger": "fa-times-circle",
    "info": "fa-info-circle",
    "warning": "fa-exclamation-triangle",
}


def mensagem_ds(tipo, texto):
    """`success` e `danger` anunciam de imediato (`role="alert"`); `info` e `warning` não interrompem (`role="status"`)."""
    return html.Div(
        [
            html.Div(html.I(className=f"fas {_ICONES[tipo]} fa-lg", **{"aria-hidden": "true"}), className="icon"),
            html.Div(html.Span(texto, className="message-body"), className="content"),
        ],
        className=f"br-message {tipo}",
        role="alert" if tipo in ("success", "danger") else "status",
    )
