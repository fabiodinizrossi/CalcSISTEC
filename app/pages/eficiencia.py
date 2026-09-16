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
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dcc, html

from app.components.filters import axis_selector, clear_filters_button, fic_toggle, filter_panel, select_filter
from app.components.kpi import kpi_card
from app.data.consulta import ano_base_ativo, carregar_eficiencia, dataset_disponivel
from app.domain.contrato import FiltrosAtivos
from app.domain.eficiencia import iea
from app.domain.matriculas import filtrar_fic
from app.domain.shared import coluna_para_eixo

dash.register_page(__name__, path="/eficiencia", title="Eficiência Acadêmica - Pesquisa Institucional - SISTEC")


def layout():
    if not dataset_disponivel():
        return html.Div("Ainda não há dados publicados.", className="empty-state")

    df = carregar_eficiencia()
    return html.Div(
        [
            html.H1("Eficiência Acadêmica"),
            # BR-MIGRAR-021: estado inicial SEM FIC nesta página, intencional (não alterar).
            fic_toggle("eficiencia-fic", default="sem_fic"),
            axis_selector("eficiencia-eixo", default="campus"),
            dcc.Loading(html.Div(id="eficiencia-kpi")),
            dcc.Loading(html.Div(id="eficiencia-matriz")),
            filter_panel(
                select_filter("eficiencia-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
                select_filter("eficiencia-filtro-modalidade", "Modalidade", sorted(df["modalidade_ensino"].dropna().unique())),
            ),
            clear_filters_button("eficiencia-limpar"),
        ]
    )


def _filtrar(df, campus, modalidade):
    if campus and campus != "__todos__":
        df = df[df["cidade"] == campus]
    if modalidade and modalidade != "__todos__":
        df = df[df["modalidade_ensino"] == modalidade]
    return df


@callback(
    Output("eficiencia-kpi", "children"),
    Output("eficiencia-matriz", "children"),
    Input("eficiencia-fic", "value"),
    Input("eficiencia-eixo", "value"),
    Input("eficiencia-filtro-campus", "value"),
    Input("eficiencia-filtro-modalidade", "value"),
)
def atualizar(fic, eixo, campus, modalidade):
    ano_base = ano_base_ativo() or 2026
    incluir_fic = fic == "com_fic"
    df = filtrar_fic(_filtrar(carregar_eficiencia(), campus, modalidade), incluir_fic)
    filtros = FiltrosAtivos(ano_base=ano_base, eixo=eixo or "campus", incluir_fic=incluir_fic)

    if df.empty:
        return kpi_card("IEA", None, empty_state="0"), html.Div("Sem dados para o eixo selecionado.")

    valor_iea = iea(df, filtros)

    # "campus" usa `cidade` (legível), os demais eixos usam a coluna real de
    # `app/domain/shared.COLUNA_POR_EIXO` (fonte única — BR-MIGRAR-019/020).
    coluna_eixo = "cidade" if eixo == "campus" else coluna_para_eixo(eixo or "campus")
    linhas = []
    for chave, grupo in df.groupby(coluna_eixo, dropna=False):
        linhas.append({coluna_eixo: chave, "IEA": round(iea(grupo, filtros), 4)})
    tabela = dbc.Table.from_dataframe(pd.DataFrame(linhas), striped=True, bordered=True, hover=True)
    matriz = html.Div(tabela, className="table-scroll-wrapper")

    # BR-MIGRAR-013/BR-HUMANA-001: 0, nunca NaN, quando pC+pE=0 — já garantido
    # por `app.domain.eficiencia.calcular_iea`.
    return kpi_card("IEA (Índice de Eficiência Acadêmica)", valor_iea, formato="#,0.00"), matriz


@callback(
    Output("eficiencia-filtro-campus", "value"),
    Output("eficiencia-filtro-modalidade", "value"),
    Output("eficiencia-fic", "value"),
    Output("eficiencia-eixo", "value"),
    Input("eficiencia-limpar", "n_clicks"),
    prevent_initial_call=True,
)
def limpar_filtros(_n_clicks):
    return "__todos__", "__todos__", "sem_fic", "campus"
