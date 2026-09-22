"""BC-04 (Apresentação): página Taxa de Evasão Anual.

Implementado na Tarefa 09 do plano de reconstrução, a partir do contrato em
`_reversa_sdd/migration/target_screens.md` §"Tela: Taxa de Evasão Anual".
"""

import dash
from dash import Input, Output, State, callback, dcc, html

from app.components.filters import EIXOS, axis_selector, clear_filters_button, fic_toggle, ordenar_eixos, select_filter
from app.components.mensagem import mensagem_ds
from app.components.painel_publico import cabecalho_pagina, cartao_indicador, cartoes_indicadores
from app.components.tabela import tabela_hierarquica_ds
from app.data.consulta import ano_base_ativo, carregar_matriculas, data_ultima_publicacao, dataset_disponivel
from app.domain.contrato import FiltrosAtivos
from app.domain.matriculas import filtrar_fic, taxa_evasao
from app.domain.shared import coluna_para_eixo

dash.register_page(__name__, path="/evasao", title="Taxa de Evasão Anual - Pesquisa Institucional - SISTEC")


def _data_curta(valor):
    if not valor:
        return None
    texto = str(valor)[:10]
    return "/".join(reversed(texto.split("-"))) if "-" in texto else texto


def layout():
    if not dataset_disponivel():
        return mensagem_ds("info", "Ainda não há dados publicados.")

    df = carregar_matriculas()
    filtros = html.Div(
        [
            select_filter("evasao-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
            select_filter("evasao-filtro-tipo-curso", "Tipo de Curso", sorted(df["tipo_curso_pnp"].dropna().unique())),
            fic_toggle("evasao-fic", default="sem_fic"),
            clear_filters_button("evasao-limpar"),
        ],
        className="card-filtros",
    )
    return html.Div(
        [
            cabecalho_pagina("Taxa de Evasão Anual", ano_base_ativo() or 2026, _data_curta(data_ultima_publicacao())),
            dcc.Loading(html.Div(id="evasao-kpi", className="kpis-figma")),
            axis_selector("evasao-eixo", default="campus"),
            dcc.Store(id="evasao-eixos-ordenados", data=["campus"]),
            dcc.Loading(html.Div(id="evasao-heatmap")),
            filtros,
        ],
        className="painel-dashboard",
    )


def _filtrar(df, campus, tipo_curso, incluir_fic):
    if campus and campus != "__todos__":
        df = df[df["cidade"] == campus]
    if tipo_curso and tipo_curso != "__todos__":
        df = df[df["tipo_curso_pnp"] == tipo_curso]
    return filtrar_fic(df, incluir_fic)


# `color_scale` de `target_screens.md` (verde/amarelo/vermelho) — o ponto
# médio é sinalizado no próprio contrato como "revisar, hoje 16% fixo no
# legado"; mantido aqui como constante nomeada (nunca literal solto), até que
# vire configurável.
LIMIAR_EVASAO_MEDIO = 0.16


def _classe_evasao(taxa):
    if taxa is None:
        return ""
    if taxa >= LIMIAR_EVASAO_MEDIO * 1.5:
        return "evasao-alta"
    if taxa >= LIMIAR_EVASAO_MEDIO:
        return "evasao-media"
    return "evasao-baixa"


# RN-08 (RF-09): cor nunca é o único indicador de estado — cada faixa tem um
# equivalente textual visível, para quem não distingue cor (daltonismo,
# leitor de tela, impressão em preto e branco).
_LABEL_EVASAO = {"evasao-alta": "Alta", "evasao-media": "Média", "evasao-baixa": "Baixa"}


@callback(
    Output("evasao-eixos-ordenados", "data"),
    Input("evasao-eixo", "value"),
    State("evasao-eixos-ordenados", "data"),
)
def atualizar_ordem_eixos(marcados, ordem_anterior):
    return ordenar_eixos(marcados, ordem_anterior)


@callback(
    Output("evasao-kpi", "children"),
    Output("evasao-heatmap", "children"),
    Input("evasao-fic", "value"),
    Input("evasao-eixos-ordenados", "data"),
    Input("evasao-filtro-campus", "value"),
    Input("evasao-filtro-tipo-curso", "value"),
)
def atualizar(fic, eixos, campus, tipo_curso):
    ano_base = ano_base_ativo() or 2026
    incluir_fic = fic == "com_fic"
    df = _filtrar(carregar_matriculas(), campus, tipo_curso, incluir_fic)
    filtros = FiltrosAtivos(ano_base=ano_base, incluir_fic=incluir_fic)

    if df.empty:
        return html.Div(), mensagem_ds("info", "Sem dados para os filtros selecionados.")

    eixos = ordenar_eixos(eixos if isinstance(eixos, list) else [eixos], eixos if isinstance(eixos, list) else [eixos])

    def metricas(grupo):
        taxa = taxa_evasao(grupo, filtros)
        classe = _classe_evasao(taxa)
        percentual = f"{taxa:.1%}".replace(".", ",")
        return [{"valor": f"{percentual} ({_LABEL_EVASAO.get(classe, '—')})", "classe": classe or None}]

    taxa_total = taxa_evasao(df, filtros)
    kpi = cartoes_indicadores([cartao_indicador("Taxa de evasão anual", taxa_total, formato="#,0.00", destaque=True)])
    colunas_eixos = {eixo: "cidade" if eixo == "campus" else coluna_para_eixo(eixo) for eixo in (opcao["value"] for opcao in EIXOS)}
    rotulos = {opcao["value"]: opcao["label"] for opcao in EIXOS}
    tabela = tabela_hierarquica_ds(
        df, eixos, colunas_eixos, rotulos, ["Taxa de Evasão"], "Taxa de evasão por recorte selecionado", metricas,
        metricas(df),
    )
    return kpi, tabela


@callback(
    Output("evasao-filtro-campus", "value"),
    Output("evasao-filtro-tipo-curso", "value"),
    Output("evasao-fic", "value"),
    Output("evasao-eixo", "value"),
    Input("evasao-limpar", "n_clicks"),
    prevent_initial_call=True,
)
def limpar_filtros(_n_clicks):
    return "__todos__", "__todos__", "sem_fic", ["campus"]
