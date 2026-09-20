"""BC-04 (Apresentação): página Início (capa).

Implementado na Tarefa 09 do plano de reconstrução, a partir do contrato em
`_reversa_sdd/migration/target_screens.md` §"Tela: Início (capa)".

O widget de upload que existia aqui (herdado do app pré-migração) foi
removido — o upload agora é uma função administrativa autenticada em
`/admin/upload` (BC-05, Tarefa 08, `BR-MIGRAR-027`/`AD-04`: o painel público
nunca exige login). `DEV-001`: fundo de imagem ad-hoc do legado substituído
por estilização CSS/gov.br (nenhum componente de imagem aqui).
"""

import dash
from dash import html

from app.components.mensagem import mensagem_ds
from app.data.consulta import data_ultimo_upload_valido, dataset_disponivel

dash.register_page(__name__, path="/", title="Início - Pesquisa Institucional - SISTEC")

NAV_CARDS = [
    ("Matrículas", "/matriculas"),
    ("Eficiência Acadêmica", "/eficiencia"),
    ("Taxa de Evasão Anual", "/evasao"),
    # BR-MIGRAR-022: já liberada, sempre visível — nunca omitida do menu/capa.
    ("Percentuais Legais", "/percentuais-legais"),
]


def layout():
    titulo = html.H1("Painel de Acompanhamento Sistec")
    if not dataset_disponivel():
        # Estado Idle (`target_screens.md`): nenhum dataset carregado ainda.
        return html.Div([titulo, mensagem_ds("info", "Ainda não há dados publicados.")])

    data_atualizacao = data_ultimo_upload_valido()
    cartoes = [
        html.Div(
            html.A(html.Div(label, className="card-content"), href=href, className="br-card"),
            className="col-12 col-md-6 col-xl-3 mb-3",
        )
        for label, href in NAV_CARDS
    ]
    return html.Div(
        [
            titulo,
            html.P("Pesquisa Institucional"),
            html.P(f"Atualizado em {data_atualizacao}") if data_atualizacao else None,
            html.Div(cartoes, className="row"),
        ]
    )
