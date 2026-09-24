"""BC-04 (Apresentação): página Percentuais Legais.

Implementado na Tarefa 09 do plano de reconstrução, a partir do contrato em
`_reversa_sdd/migration/target_screens.md` §"Tela: Percentuais Legais".
`BR-MIGRAR-022`: página já liberada — nunca retida/oculta.
"""

import dash
from dash import Input, Output, State, callback, dcc, html

from app.auth import sessao_id_atual
from app.components.filters import EIXOS, axis_selector, clear_filters_button, ordenar_eixos, select_filter
from app.components.mensagem import mensagem_ds
from app.components.painel_publico import cabecalho_pagina, cartao_indicador, cartoes_indicadores
from app.components.tabela import tabela_hierarquica_ds
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
from app.sistec.execucoes import PreviaIndisponivel, abrir_leitura_previa

dash.register_page(__name__, path="/percentuais-legais", title="Percentuais Legais - Pesquisa Institucional - SISTEC")


def _data_curta(valor):
    if not valor:
        return None
    texto = str(valor)[:10]
    return "/".join(reversed(texto.split("-"))) if "-" in texto else texto


def _formatar_percentual(valor):
    return f"{valor:.1%}".replace(".", ",")


def _formatar_equivalentes(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _carregar(preview_id):
    """`(df, ano_base)` — banco publicado (`preview_id=None`) ou fonte candidata
    validada (PVP-04/PVP-07). Levanta `PreviaIndisponivel` em contexto inválido."""
    if preview_id is None:
        return carregar_matriculas(), ano_base_ativo() or 2026

    contexto = abrir_leitura_previa(preview_id, sessao_id_atual())
    try:
        return carregar_matriculas(conn=contexto.conn), contexto.ano_base
    finally:
        contexto.conn.close()


def _filtros(df):
    return html.Div(
        [
            select_filter("percentuais-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
            select_filter("percentuais-filtro-programa", "Programa Associado", sorted(df["tipo_programa_curso"].dropna().unique())),
            html.Div(id="percentuais-aviso-proeja"),
            clear_filters_button("percentuais-limpar"),
        ],
        className="card-filtros",
    )


def layout(preview_id=None):
    """PVP-01/PVP-02/PVP-04: caminho público fica idêntico; com `preview_id`,
    lê a fonte candidata, omite o carimbo de publicação e injeta o `dcc.Store`
    que leva o identificador aos callbacks."""
    if preview_id is not None:
        try:
            df, ano_base = _carregar(preview_id)
        except PreviaIndisponivel:
            return mensagem_ds("warning", "Prévia indisponível.")
        atualizado = None
    else:
        if not dataset_disponivel():
            return mensagem_ds("info", "Ainda não há dados publicados.")
        df, ano_base = _carregar(None)
        atualizado = _data_curta(data_ultima_publicacao())

    filhos = [
        cabecalho_pagina("Percentuais Legais", ano_base, atualizado),
        dcc.Loading(html.Div(id="percentuais-cartoes", className="kpis-figma")),
        axis_selector("percentuais-eixo", default="campus"),
        dcc.Store(id="percentuais-eixos-ordenados", data=["campus"]),
        dcc.Loading(html.Div(id="percentuais-tabela")),
        _filtros(df),
        # CPR-02: o `Store` entra sempre — o callback o declara como `State`
        # também no caminho público (`data=None`), e um `State` apontando para
        # id inexistente trava a página com ReferenceError no navegador.
        dcc.Store(id="percentuais-preview", data=preview_id),
    ]

    return html.Div(filhos, className="painel-dashboard")


def _base_percentuais(df):
    """Adapta a base consolidada de `carregar_matriculas` para o formato
    esperado por `app/domain/percentuais_legais.py` (uma linha por matrícula,
    `quantidade_matriculas=1` — a soma equivale à agregação por curso, já que
    `matricula_equivalente` é linear em `matriculas`)."""
    return df.assign(quantidade_matriculas=1)


@callback(
    Output("percentuais-eixos-ordenados", "data"),
    Input("percentuais-eixo", "value"),
    State("percentuais-eixos-ordenados", "data"),
)
def atualizar_ordem_eixos(marcados, ordem_anterior):
    return ordenar_eixos(marcados, ordem_anterior)


@callback(
    Output("percentuais-cartoes", "children"),
    Output("percentuais-tabela", "children"),
    Output("percentuais-aviso-proeja", "children"),
    Input("percentuais-eixos-ordenados", "data"),
    Input("percentuais-filtro-campus", "value"),
    Input("percentuais-filtro-programa", "value"),
    State("percentuais-preview", "data"),
)
def atualizar(eixos, campus, programa, preview_id=None):
    try:
        df, ano_base = _carregar(preview_id)
    except PreviaIndisponivel:
        return mensagem_ds("warning", "Prévia indisponível."), html.Div(), None
    df = df[df["ano_base"] == ano_base]
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
    eixos = ordenar_eixos(eixos if isinstance(eixos, list) else [eixos], eixos if isinstance(eixos, list) else [eixos])
    colunas_eixos = {eixo: "cidade" if eixo == "campus" else coluna_para_eixo(eixo) for eixo in (opcao["value"] for opcao in EIXOS)}
    rotulos = {opcao["value"]: opcao["label"] for opcao in EIXOS}
    def metricas(grupo):
        return [_formatar_percentual(percentual_tecnico(grupo)), _formatar_percentual(percentual_professores(grupo)), _formatar_percentual(percentual_proeja(grupo)), _formatar_equivalentes(matriculas_equivalentes(grupo).sum())]
    tabela = tabela_hierarquica_ds(
        base, eixos, colunas_eixos, rotulos,
        ["Técnico", "Formação de Professores", "PROEJA", "Matrículas equivalentes"],
        "Recorte exploratório. Os percentuais não avaliam o cumprimento da meta por grupo.", metricas,
        [_formatar_percentual(pt), _formatar_percentual(pp), _formatar_percentual(pj), _formatar_equivalentes(equivalentes_total)],
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
    return "__todos__", "__todos__", ["campus"]
