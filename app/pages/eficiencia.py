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
from dash import Input, Output, callback, dcc, html

from app.components.filters import axis_selector, clear_filters_button, fic_toggle, select_filter
from app.components.mensagem import mensagem_ds
from app.components.painel_publico import cabecalho_pagina, cartao_indicador, cartoes_indicadores
from app.components.tabela import tabela_ds
from app.data.consulta import ano_base_ativo, carregar_eficiencia, data_ultima_publicacao, dataset_disponivel
from app.domain.contrato import FiltrosAtivos
from app.domain.eficiencia import iea
from app.domain.matriculas import filtrar_fic
from app.domain.shared import coluna_para_eixo

dash.register_page(__name__, path="/eficiencia", title="Eficiência Acadêmica - Pesquisa Institucional - SISTEC")


def _data_curta(valor):
    if not valor:
        return None
    texto = str(valor)[:10]
    return "/".join(reversed(texto.split("-"))) if "-" in texto else texto


def layout():
    if not dataset_disponivel():
        return mensagem_ds("info", "Ainda não há dados publicados.")

    df = carregar_eficiencia()
    filtros = html.Div(
        [
            select_filter("eficiencia-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
            select_filter("eficiencia-filtro-modalidade", "Modalidade", sorted(df["modalidade_ensino"].dropna().unique())),
            # BR-MIGRAR-021: estado inicial SEM FIC nesta página, intencional.
            fic_toggle("eficiencia-fic", default="sem_fic"),
            clear_filters_button("eficiencia-limpar"),
        ],
        className="card-filtros",
    )
    return html.Div(
        [
            cabecalho_pagina("Eficiência Acadêmica", ano_base_ativo() or 2026, _data_curta(data_ultima_publicacao())),
            dcc.Loading(html.Div(id="eficiencia-kpi", className="kpis-figma")),
            axis_selector("eficiencia-eixo", default="campus"),
            dcc.Loading(html.Div(id="eficiencia-matriz")),
            filtros,
        ],
        className="painel-dashboard",
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
        return html.Div(), mensagem_ds("info", "Sem dados para o eixo selecionado.")

    valor_iea = iea(df, filtros)

    # "campus" usa `cidade` (legível), os demais eixos usam a coluna real de
    # `app/domain/shared.COLUNA_POR_EIXO` (fonte única — BR-MIGRAR-019/020).
    coluna_eixo = "cidade" if eixo == "campus" else coluna_para_eixo(eixo or "campus")
    linhas = []
    for chave, grupo in df.groupby(coluna_eixo, dropna=False):
        linhas.append([chave, f"{iea(grupo, filtros):.2f}".replace(".", ",")])
    rotulo_eixo = "Campus" if eixo == "campus" else eixo.replace("_", " ").title()
    matriz = tabela_ds([rotulo_eixo, "IEA"], linhas, f"IEA por {rotulo_eixo.lower()}", quadro=True)

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
    return "__todos__", "__todos__", "sem_fic", "campus"
