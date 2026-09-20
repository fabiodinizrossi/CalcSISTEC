"""BC-04 (Apresentação): página Percentuais Legais.

Implementado na Tarefa 09 do plano de reconstrução, a partir do contrato em
`_reversa_sdd/migration/target_screens.md` §"Tela: Percentuais Legais".
`BR-MIGRAR-022`: página já liberada — nunca retida/oculta.
"""

import dash
from dash import Input, Output, callback, dcc, html

from app.components.filters import axis_selector, clear_filters_button, filter_panel, select_filter
from app.components.kpi import kpi_card, kpi_colunas
from app.components.mensagem import mensagem_ds
from app.data.consulta import ano_base_ativo, carregar_matriculas, dataset_disponivel
from app.domain.percentuais_legais import (
    META_PROEJA,
    META_PROFESSORES,
    META_TECNICO,
    cor_medidor,
    matriculas_equivalentes,
    percentual_proeja,
    percentual_professores,
    percentual_tecnico,
)

dash.register_page(__name__, path="/percentuais-legais", title="Percentuais Legais - Pesquisa Institucional - SISTEC")


def layout():
    if not dataset_disponivel():
        return mensagem_ds("info", "Ainda não há dados publicados.")

    df = carregar_matriculas()
    return html.Div(
        [
            html.H1("Percentuais Legais"),
            axis_selector("percentuais-eixo", default="campus"),
            dcc.Loading(html.Div(id="percentuais-medidores", className="row")),
            dcc.Loading(html.Div(id="percentuais-kpi", className="row")),
            filter_panel(
                select_filter("percentuais-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
                select_filter("percentuais-filtro-programa", "Programa Associado", sorted(df["tipo_programa_curso"].dropna().unique())),
            ),
            html.Div(id="percentuais-aviso-proeja"),
            clear_filters_button("percentuais-limpar"),
        ]
    )


def _base_percentuais(df):
    """Adapta a base consolidada de `carregar_matriculas` para o formato
    esperado por `app/domain/percentuais_legais.py` (uma linha por matrícula,
    `quantidade_matriculas=1` — a soma equivale à agregação por curso, já que
    `matricula_equivalente` é linear em `matriculas`)."""
    return df.assign(quantidade_matriculas=1)


@callback(
    Output("percentuais-medidores", "children"),
    Output("percentuais-kpi", "children"),
    Output("percentuais-aviso-proeja", "children"),
    Input("percentuais-eixo", "value"),
    Input("percentuais-filtro-campus", "value"),
    Input("percentuais-filtro-programa", "value"),
)
def atualizar(_eixo, campus, programa):
    ano_base_ativo()
    df = carregar_matriculas()
    if campus and campus != "__todos__":
        df = df[df["cidade"] == campus]

    aviso = None
    if programa and programa != "__todos__":
        df = df[df["tipo_programa_curso"] == programa]
        # BR-MIGRAR-026: avisa quando o filtro de programa distorce o % PROEJA
        # (denominador filtrado deixa de representar o universo de referência).
        aviso = mensagem_ds("warning", "Atenção: o filtro de Programa Associado pode distorcer o percentual PROEJA.")

    base = _base_percentuais(df)
    if base.empty:
        medidores = html.Div(mensagem_ds("info", "Sem dados para os filtros selecionados."), className="col-12")
        kpi = kpi_colunas([kpi_card("Matrículas equivalentes", None, empty_state="dado incompleto")])
        return medidores, kpi, aviso

    pt = percentual_tecnico(base)
    pp = percentual_professores(base)
    pj = percentual_proeja(base)
    equivalentes_total = matriculas_equivalentes(base).sum()

    def gauge(label, valor, meta):
        cor = cor_medidor(valor, meta)
        # RF-09/RN-08: a cor do medidor nunca é o único sinal de estado — o
        # texto "Acima da meta"/"Abaixo da meta" vale mesmo sem distinguir cor.
        situacao = "Acima da meta" if valor >= meta else "Abaixo da meta"
        return html.Div(
            html.Div(
                [
                    html.Div(label, className="kpi-label"),
                    html.Div(f"{valor:.1%}", className=f"gauge-value gauge-{cor}"),
                    html.Div(situacao, className=f"gauge-situacao gauge-situacao-{cor}"),
                    html.Div(f"Meta: {meta:.0%}", className="gauge-meta"),
                ],
                className="card-content",
            ),
            className="br-card",
        )

    medidores = kpi_colunas(
        [
            gauge("Técnico", pt, META_TECNICO),
            gauge("Formação de Professores", pp, META_PROFESSORES),
            gauge("PROEJA", pj, META_PROEJA),
        ]
    )
    kpi = kpi_colunas([kpi_card("Matrículas equivalentes", equivalentes_total, formato="#,0.00")])

    return medidores, kpi, aviso


@callback(
    Output("percentuais-filtro-campus", "value"),
    Output("percentuais-filtro-programa", "value"),
    Output("percentuais-eixo", "value"),
    Input("percentuais-limpar", "n_clicks"),
    prevent_initial_call=True,
)
def limpar_filtros(_n_clicks):
    return "__todos__", "__todos__", "campus"
