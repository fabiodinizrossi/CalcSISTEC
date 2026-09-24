"""BC-04 (Apresentação): página Eficiência Acadêmica.

Implementado na Tarefa 09 do plano de reconstrução, a partir do contrato em
`_reversa_sdd/migration/target_screens.md` §"Tela: Eficiência Acadêmica".
`DEV-003`: link de Percentuais Legais mantido no menu (já liberada).

Tarefa 11: corrigido bug em que o toggle FIC não tinha nenhum efeito sobre os
dados (a Tarefa 09 calculava `filtros.incluir_fic` mas nunca aplicava
`filtrar_fic` ao `df`); e o eixo "Oferta" passou a funcionar com a coluna
`tipo_oferta_curso` adicionada ao schema nesta mesma tarefa.
"""

import dash
import pandas as pd
from dash import Input, Output, State, callback, dcc, html

from app.auth import sessao_id_atual
from app.components.filters import EIXOS, axis_selector, clear_filters_button, fic_toggle, ordenar_eixos, select_filter
from app.components.mensagem import mensagem_ds
from app.components.painel_publico import cabecalho_pagina, cartao_indicador, cartoes_indicadores
from app.components.tabela import tabela_hierarquica_ds
from app.data.consulta import ano_base_ativo, carregar_eficiencia, data_ultima_publicacao, dataset_disponivel
from app.domain.contrato import FiltrosAtivos
from app.domain.eficiencia import iea
from app.domain.matriculas import filtrar_fic
from app.domain.shared import coluna_para_eixo
from app.sistec.execucoes import PreviaIndisponivel, abrir_leitura_previa

dash.register_page(__name__, path="/eficiencia", title="Eficiência Acadêmica - Pesquisa Institucional - SISTEC")


def _data_curta(valor):
    if not valor:
        return None
    texto = str(valor)[:10]
    return "/".join(reversed(texto.split("-"))) if "-" in texto else texto


def _carregar(preview_id):
    """`(df, ano_base)` — banco publicado (`preview_id=None`) ou fonte candidata
    validada (PVP-04/PVP-07). Levanta `PreviaIndisponivel` em contexto inválido."""
    if preview_id is None:
        return carregar_eficiencia(), ano_base_ativo() or 2026

    contexto = abrir_leitura_previa(preview_id, sessao_id_atual())
    try:
        return carregar_eficiencia(conn=contexto.conn), contexto.ano_base
    finally:
        contexto.conn.close()


def _filtros(df):
    return html.Div(
        [
            select_filter("eficiencia-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
            select_filter("eficiencia-filtro-modalidade", "Modalidade", sorted(df["modalidade_ensino"].dropna().unique())),
            # BR-MIGRAR-021: estado inicial SEM FIC nesta página, intencional.
            fic_toggle("eficiencia-fic", default="sem_fic"),
            clear_filters_button("eficiencia-limpar"),
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
        cabecalho_pagina("Eficiência Acadêmica", ano_base, atualizado),
        dcc.Loading(html.Div(id="eficiencia-kpi", className="kpis-figma")),
        axis_selector("eficiencia-eixo", default="campus"),
        dcc.Store(id="eficiencia-eixos-ordenados", data=["campus"]),
        dcc.Loading(html.Div(id="eficiencia-matriz")),
        _filtros(df),
        # CPR-02: o `Store` entra sempre — o callback o declara como `State`
        # também no caminho público (`data=None`), e um `State` apontando para
        # id inexistente trava a página com ReferenceError no navegador.
        dcc.Store(id="eficiencia-preview", data=preview_id),
    ]

    return html.Div(filhos, className="painel-dashboard")


def _filtrar(df, campus, modalidade):
    if campus and campus != "__todos__":
        df = df[df["cidade"] == campus]
    if modalidade and modalidade != "__todos__":
        df = df[df["modalidade_ensino"] == modalidade]
    return df


@callback(
    Output("eficiencia-eixos-ordenados", "data"),
    Input("eficiencia-eixo", "value"),
    State("eficiencia-eixos-ordenados", "data"),
)
def atualizar_ordem_eixos(marcados, ordem_anterior):
    return ordenar_eixos(marcados, ordem_anterior)


@callback(
    Output("eficiencia-kpi", "children"),
    Output("eficiencia-matriz", "children"),
    Input("eficiencia-fic", "value"),
    Input("eficiencia-eixos-ordenados", "data"),
    Input("eficiencia-filtro-campus", "value"),
    Input("eficiencia-filtro-modalidade", "value"),
    State("eficiencia-preview", "data"),
)
def atualizar(fic, eixos, campus, modalidade, preview_id=None):
    try:
        df, ano_base = _carregar(preview_id)
    except PreviaIndisponivel:
        return html.Div(), mensagem_ds("warning", "Prévia indisponível.")
    incluir_fic = fic == "com_fic"
    df = filtrar_fic(_filtrar(df, campus, modalidade), incluir_fic)
    eixos = ordenar_eixos(eixos if isinstance(eixos, list) else [eixos], eixos if isinstance(eixos, list) else [eixos])
    filtros = FiltrosAtivos(ano_base=ano_base, eixo=(eixos[-1] if eixos else "campus"), incluir_fic=incluir_fic)

    if df.empty:
        return html.Div(), mensagem_ds("info", "Sem dados para o eixo selecionado.")

    valor_iea = iea(df, filtros)

    colunas_eixos = {eixo: "cidade" if eixo == "campus" else coluna_para_eixo(eixo) for eixo in (opcao["value"] for opcao in EIXOS)}
    rotulos = {opcao["value"]: opcao["label"] for opcao in EIXOS}
    matriz = tabela_hierarquica_ds(
        df, eixos, colunas_eixos, rotulos, ["IEA"], "IEA por recorte selecionado",
        lambda grupo: [f"{iea(grupo, filtros):.2f}".replace(".", ",")],
        [f"{valor_iea:.2f}".replace(".", ",")],
    )

    # BR-MIGRAR-013/BR-HUMANA-001: 0, nunca NaN, quando pC+pE=0 — já garantido
    # por `app.domain.eficiencia.calcular_iea`.
    return cartoes_indicadores([cartao_indicador("IEA (Índice de Eficiência Acadêmica)", valor_iea, formato="#,0.00", destaque=True)]), matriz


@callback(
    Output("eficiencia-filtro-campus", "value"),
    Output("eficiencia-filtro-modalidade", "value"),
    Output("eficiencia-fic", "value"),
    Output("eficiencia-eixo", "value"),
    Input("eficiencia-limpar", "n_clicks"),
    prevent_initial_call=True,
)
def limpar_filtros(_n_clicks):
    return "__todos__", "__todos__", "sem_fic", ["campus"]
