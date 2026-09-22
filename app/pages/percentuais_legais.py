"""BC-04 (Apresentação): página Percentuais Legais.

Implementado na Tarefa 09 do plano de reconstrução, a partir do contrato em
`_reversa_sdd/migration/target_screens.md` §"Tela: Percentuais Legais".
`BR-MIGRAR-022`: página já liberada — nunca retida/oculta.
"""

import dash
from dash import Input, Output, callback, dcc, html

from app.components.filters import axis_selector, clear_filters_button, select_filter
from app.components.mensagem import mensagem_ds
from app.components.painel_publico import cabecalho_pagina, cartao_indicador, cartoes_indicadores
from app.components.tabela import tabela_ds
from app.data.consulta import ano_base_ativo, carregar_matriculas, data_ultima_publicacao, dataset_disponivel
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
from app.domain.shared import coluna_para_eixo

dash.register_page(__name__, path="/percentuais-legais", title="Percentuais Legais - Pesquisa Institucional - SISTEC")


def _data_curta(valor):
    if not valor:
        return None
    texto = str(valor)[:10]
    return "/".join(reversed(texto.split("-"))) if "-" in texto else texto


def _rotulo_eixo(eixo):
    return {
        "campus": "Campus",
        "tipo_curso": "Tipo de Curso",
        "oferta": "Oferta (Técnico)",
        "nome_curso": "Nome do Curso",
        "modalidade": "Modalidade",
        "ciclo": "Ciclo",
    }.get(eixo, "Campus")


def _formatar_percentual(valor):
    return f"{valor:.1%}".replace(".", ",")


def _formatar_equivalentes(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def layout():
    if not dataset_disponivel():
        return mensagem_ds("info", "Ainda não há dados publicados.")

    df = carregar_matriculas()
    filtros = html.Div(
        [
                select_filter("percentuais-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
                select_filter("percentuais-filtro-programa", "Programa Associado", sorted(df["tipo_programa_curso"].dropna().unique())),
                html.Div(id="percentuais-aviso-proeja"),
                clear_filters_button("percentuais-limpar"),
        ],
        className="card-filtros",
    )
    return html.Div(
        [
            cabecalho_pagina("Percentuais Legais", ano_base_ativo() or 2026, _data_curta(data_ultima_publicacao())),
            dcc.Loading(html.Div(id="percentuais-cartoes", className="kpis-figma")),
            axis_selector("percentuais-eixo", default="campus"),
            dcc.Loading(html.Div(id="percentuais-tabela")),
            filtros,
        ],
        className="painel-dashboard",
    )


def _base_percentuais(df):
    """Adapta a base consolidada de `carregar_matriculas` para o formato
    esperado por `app/domain/percentuais_legais.py` (uma linha por matrícula,
    `quantidade_matriculas=1` — a soma equivale à agregação por curso, já que
    `matricula_equivalente` é linear em `matriculas`)."""
    return df.assign(quantidade_matriculas=1)


@callback(
    Output("percentuais-cartoes", "children"),
    Output("percentuais-tabela", "children"),
    Output("percentuais-aviso-proeja", "children"),
    Input("percentuais-eixo", "value"),
    Input("percentuais-filtro-campus", "value"),
    Input("percentuais-filtro-programa", "value"),
)
def atualizar(eixo, campus, programa):
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
        return html.Div(mensagem_ds("info", "Sem dados para os filtros selecionados.")), html.Div(), aviso

    pt = percentual_tecnico(base)
    pp = percentual_professores(base)
    pj = percentual_proeja(base)
    equivalentes_total = matriculas_equivalentes(base).sum()

    def gauge(label, valor, meta, destaque=False):
        cor = cor_medidor(valor, meta)
        # RF-09/RN-08: a cor do medidor nunca é o único sinal de estado — o
        # texto "Acima da meta"/"Abaixo da meta" vale mesmo sem distinguir cor.
        situacao = "Acima da meta" if valor >= meta else "Abaixo da meta"
        return html.Div(
            html.Div(
                [
                    html.Div(label, className="kpi-label"),
                    html.Div(_formatar_percentual(valor), className=f"gauge-value gauge-{cor}"),
                    html.Div(situacao, className=f"gauge-situacao gauge-situacao-{cor}"),
                    html.Div(f"Meta: {meta:.0%}", className="gauge-meta"),
                ],
                className="card-content",
            ),
            className="br-card kpi-figma kpi-figma--destaque" if destaque else "br-card kpi-figma",
        )

    cartoes = cartoes_indicadores(
        [
            gauge("Técnico", pt, META_TECNICO, destaque=True),
            gauge("Formação de Professores", pp, META_PROFESSORES),
            gauge("PROEJA", pj, META_PROEJA),
            cartao_indicador("Matrículas equivalentes", equivalentes_total, formato="#,0.00"),
        ]
    )
    eixo = eixo or "campus"
    coluna_eixo = "cidade" if eixo == "campus" else coluna_para_eixo(eixo)
    rotulo_eixo = _rotulo_eixo(eixo)
    linhas = []
    for chave, grupo in base.groupby(coluna_eixo, dropna=False):
        linhas.append(
            [
                chave,
                _formatar_percentual(percentual_tecnico(grupo)),
                _formatar_percentual(percentual_professores(grupo)),
                _formatar_percentual(percentual_proeja(grupo)),
                _formatar_equivalentes(matriculas_equivalentes(grupo).sum()),
            ]
        )
    tabela = tabela_ds(
        [rotulo_eixo, "Técnico", "Formação de Professores", "PROEJA", "Matrículas equivalentes"],
        linhas,
        f"Recorte exploratório por {rotulo_eixo}. Os percentuais não avaliam o cumprimento da meta por grupo.",
        quadro=True,
        total=[
            "Total",
            _formatar_percentual(pt),
            _formatar_percentual(pp),
            _formatar_percentual(pj),
            _formatar_equivalentes(equivalentes_total),
        ],
    )

    return cartoes, tabela, aviso


@callback(
    Output("percentuais-filtro-campus", "value"),
    Output("percentuais-filtro-programa", "value"),
    Output("percentuais-eixo", "value"),
    Input("percentuais-limpar", "n_clicks"),
    prevent_initial_call=True,
)
def limpar_filtros(_n_clicks):
    return "__todos__", "__todos__", "campus"
