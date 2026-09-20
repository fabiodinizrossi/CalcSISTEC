"""BC-04 (Apresentação): aviso "sem correção PNP" (`002-baixador-planilhas-
sistec`, T043, D-17, RN-30, RN-31, RF-27, RF-28).

Esta feature baixa os dados direto do Sistec, sem a correção que antes vinha
dos microdados do PNP (`STATUS_MATRICULA_PNP` sempre nulo, RN-23). O aviso
fica visível nas 5 páginas públicas enquanto `CORRECAO_PNP_ATIVA` for
`False` — um único ponto a desligar quando a feature de microdados PNP for
implementada, controlando também o aviso na prévia e na confirmação de
"Publicar" (D-17).
"""

from dash import html

CORRECAO_PNP_ATIVA = False

_MENSAGEM = (
    "Os dados exibidos vêm direto do Sistec, sem a correção de status pelos "
    "microdados do PNP — os números podem divergir dos publicados oficialmente "
    "pelo PNP até essa correção ser reintroduzida."
)


def make_aviso_sem_pnp():
    """`None` quando `CORRECAO_PNP_ATIVA` for `True` (aviso desligado) —
    quem chama deve tratar esse caso (não inserir o componente no layout)."""
    if CORRECAO_PNP_ATIVA:
        return None
    return html.Div(
        [
            html.Div(html.I(className="fas fa-exclamation-triangle fa-lg", **{"aria-hidden": "true"}), className="icon"),
            html.Div(html.Span(_MENSAGEM, className="message-body"), className="content"),
        ],
        className="br-message warning",
        role="status",
    )
