"""BC-04 (Apresentação): observação sobre a origem dos dados (simulação).

A nota fica no rodapé do conteúdo das páginas públicas enquanto
`CORRECAO_PNP_ATIVA` for `False` — um único ponto a desligar quando a feature
de microdados PNP for implementada. É só uma observação discreta, sem o
destaque de aviso (`br-message warning`).
"""

from dash import html

CORRECAO_PNP_ATIVA = False

_MENSAGEM = (
    "Os dados exibidos vêm direto do Sistec e por isso, podem divergir dos "
    "publicados oficialmente na PNP. Trata-se de simulação para acompanhamento."
)


def make_aviso_sem_pnp():
    """`None` quando `CORRECAO_PNP_ATIVA` for `True` (observação desligada) —
    quem chama deve tratar esse caso (não inserir o componente no layout)."""
    if CORRECAO_PNP_ATIVA:
        return None
    return html.P(_MENSAGEM, className="aviso-simulacao")
