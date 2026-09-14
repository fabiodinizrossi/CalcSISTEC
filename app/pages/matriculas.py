"""BC-04 (Apresentação): página Matrículas.

Implementado na Tarefa 09 do plano de reconstrução, a partir do contrato em
`_reversa_sdd/migration/target_screens.md` §"Tela: Matrículas". Nenhuma regra
de negócio é calculada aqui — apenas consumo de `app/domain/*` (invariante de
`AGG-Apresentacao`, `target_domain_model.md`).

Tarefa 11: toggle FIC e eixo "Oferta" corrigidos para usar
`app/domain/matriculas.filtrar_fic` e a coluna `tipo_oferta_curso`
(`app/data/schema.py`), respectivamente — ver `_reversa_sdd/reconstruction-
plan.md` Tarefa 11 para o detalhe das divergências encontradas e corrigidas.
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

from app.components.filters import axis_selector, clear_filters_button, fic_toggle, filter_panel, select_filter
from app.components.kpi import kpi_card
from app.data.consulta import ano_base_ativo, carregar_matriculas, dataset_disponivel
from app.domain.contrato import FiltrosAtivos
from app.domain.matriculas import contar_cursos_ativos, contar_matriculas, contar_por_status, filtrar_fic
from app.domain.shared import agrupar_por_eixo, matricula_equivalente

dash.register_page(__name__, path="/matriculas", title="Matrículas - Pesquisa Institucional - SISTEC")

STATUS_CONCLUIDA = "CONCLUÍDA"
STATUS_EM_CURSO = "EM_CURSO"


def layout():
    if not dataset_disponivel():
        return html.Div("Nenhum dado disponível ainda. Aguarde o próximo upload.", className="empty-state")

    df = carregar_matriculas()
    return html.Div(
        [
            html.H1("Matrículas"),
            dcc.Loading(html.Div(id="matriculas-kpis", className="kpi-row")),
            fic_toggle("matriculas-fic", default="com_fic"),
            axis_selector("matriculas-eixo", default="campus"),
            dcc.Loading(html.Div(id="matriculas-matriz")),
            filter_panel(
                select_filter("matriculas-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
                select_filter("matriculas-filtro-tipo-curso", "Tipo de Curso", sorted(df["tipo_curso_pnp"].dropna().unique())),
                select_filter("matriculas-filtro-programa", "Tipo de Programa", sorted(df["tipo_programa_curso"].dropna().unique())),
            ),
            clear_filters_button("matriculas-limpar"),
        ]
    )


def _filtrar(df, campus, tipo_curso, programa, fic):
    if campus and campus != "__todos__":
        df = df[df["cidade"] == campus]
    if tipo_curso and tipo_curso != "__todos__":
        df = df[df["tipo_curso_pnp"] == tipo_curso]
    if programa and programa != "__todos__":
        df = df[df["tipo_programa_curso"] == programa]
    df = filtrar_fic(df, incluir_fic=(fic == "com_fic"))
    return df


@callback(
    Output("matriculas-kpis", "children"),
    Output("matriculas-matriz", "children"),
    Input("matriculas-fic", "value"),
    Input("matriculas-eixo", "value"),
    Input("matriculas-filtro-campus", "value"),
    Input("matriculas-filtro-tipo-curso", "value"),
    Input("matriculas-filtro-programa", "value"),
)
def atualizar(fic, eixo, campus, tipo_curso, programa):
    ano_base = ano_base_ativo() or 2026
    df = _filtrar(carregar_matriculas(), campus, tipo_curso, programa, fic)
    filtros = FiltrosAtivos(ano_base=ano_base, eixo=eixo or "campus", incluir_fic=(fic == "com_fic"))

    df_ano_base = df[df["ano_base"] == ano_base]
    total = contar_matriculas(df, filtros)
    concluidas = contar_por_status(df, filtros, STATUS_CONCLUIDA)
    ingressantes = contar_por_status(df, filtros, STATUS_EM_CURSO)
    cursos_ativos = contar_cursos_ativos(df, filtros)

    if df_ano_base.empty:
        equivalentes = None
    else:
        equivalentes = sum(
            matricula_equivalente(linha.tipo_curso_pnp, linha.carga_horaria_total, linha.fec, 1)
            for linha in df_ano_base.itertuples()
        )

    kpis = [
        kpi_card("Cursos", cursos_ativos),
        kpi_card("Matrículas", total, formato="#,0"),
        kpi_card("Matrículas equivalentes", equivalentes, formato="#,0.00", empty_state="dado incompleto"),
        kpi_card("Matrículas concluídas", concluidas),
        kpi_card("Ingressantes", ingressantes),
    ]

    if df.empty:
        matriz = html.Div("Sem dados para o eixo selecionado.")
    else:
        agregado = agrupar_por_eixo(df.assign(total=1), filtros, "total", agregacao="sum")
        tabela = dbc.Table.from_dataframe(agregado, striped=True, bordered=True, hover=True)
        # RF-07 (320 px): a tabela rola na horizontal dentro do próprio
        # quadro — a página inteira não rola.
        matriz = html.Div(tabela, className="table-scroll-wrapper")

    return kpis, matriz


@callback(
    Output("matriculas-filtro-campus", "value"),
    Output("matriculas-filtro-tipo-curso", "value"),
    Output("matriculas-filtro-programa", "value"),
    Output("matriculas-fic", "value"),
    Output("matriculas-eixo", "value"),
    Input("matriculas-limpar", "n_clicks"),
    prevent_initial_call=True,
)
def limpar_filtros(_n_clicks):
    """BR-MIGRAR-023."""
    return "__todos__", "__todos__", "__todos__", "com_fic", "campus"
