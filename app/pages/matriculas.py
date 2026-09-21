"""BC-04 (Apresentação): página inicial (Matrículas).

Conteúdo renderizado conforme o design "09 - Página inicial (Matrículas)" do
Figma. Nenhuma regra de negócio é calculada aqui — apenas consumo de
`app/domain/*` (invariante de `AGG-Apresentacao`).
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

from app.components.filters import EIXOS, clear_filters_button, select_filter
from app.components.kpi import formatar_valor
from app.components.mensagem import mensagem_ds
from app.data.consulta import ano_base_ativo, carregar_matriculas, data_ultima_publicacao, dataset_disponivel
from app.domain.contrato import FiltrosAtivos
from app.domain.matriculas import contar_cursos_ativos, contar_evadidos, contar_matriculas, contar_por_status, filtrar_fic
from app.domain.shared import coluna_para_eixo, eh_evadido, matricula_equivalente

dash.register_page(__name__, path="/", title="Matrículas - Pesquisa Institucional - SISTEC")

STATUS_CONCLUIDA = "CONCLUÍDA"
STATUS_INTEGRALIZADA = "INTEGRALIZADA"
STATUS_EM_CURSO = "EM_CURSO"


def _data_curta(valor):
    if not valor:
        return None
    texto = str(valor)[:10]
    return "/".join(reversed(texto.split("-"))) if "-" in texto else texto


def _kpi(label, valor, formato="0", empty_state=None):
    texto = empty_state if (empty_state is not None and valor is None) else formatar_valor(valor, formato)
    return html.Div(
        [html.Div(texto, className="valor"), html.Div(label, className="rotulo")],
        className="kpi-figma",
    )


def _chip_selector(id_):
    """"Ver tabela por" como chips (pílulas), seleção única."""
    return html.Div(
        [
            html.Span("Ver tabela por:", className="rotulo-chips"),
            dbc.RadioItems(
                id=id_,
                options=EIXOS,
                value="campus",
                inline=True,
                labelClassName="chip",
                labelCheckedClassName="chip chip--ativo",
                inputClassName="chip-input",
            ),
        ],
        className="card-chips",
    )


def _fic_selector(id_):
    """Toggle FIC como controle segmentado Com FIC / Sem FIC."""
    return html.Div(
        [
            html.Label("Filtro FIC", className="filter-label"),
            dbc.RadioItems(
                id=id_,
                options=[{"label": "Com FIC", "value": "com_fic"}, {"label": "Sem FIC", "value": "sem_fic"}],
                value="com_fic",
                inline=True,
                labelClassName="seg",
                labelCheckedClassName="seg seg--ativo",
                inputClassName="seg-input",
            ),
        ],
        className="fic-segmentado",
    )


def layout():
    if not dataset_disponivel():
        return mensagem_ds("info", "Ainda não há dados publicados.")

    df = carregar_matriculas()
    ano_base = ano_base_ativo() or 2026
    atualizado = _data_curta(data_ultima_publicacao())

    cabecalho = html.Div(
        [
            html.Div(
                [
                    html.H1("Matrículas"),
                    html.Span(f"Acompanhamento Sistec | Ano PNP {ano_base}", className="subtitulo"),
                ],
                className="titulo-bloco",
            ),
            html.Span(f"Atualizado em {atualizado}", className="atualizado") if atualizado else None,
        ],
        className="cabecalho-pagina",
    )

    filtros = html.Div(
        [
            select_filter("matriculas-filtro-campus", "Campus", sorted(df["cidade"].dropna().unique())),
            select_filter("matriculas-filtro-tipo-curso", "Tipo de Curso", sorted(df["tipo_curso_pnp"].dropna().unique())),
            select_filter("matriculas-filtro-programa", "Tipo de Programa", sorted(df["tipo_programa_curso"].dropna().unique())),
            _fic_selector("matriculas-fic"),
            clear_filters_button("matriculas-limpar"),
        ],
        className="card-filtros",
    )

    return html.Div(
        [
            cabecalho,
            dcc.Loading(html.Div(id="matriculas-kpis", className="kpis-figma")),
            _chip_selector("matriculas-eixo"),
            dcc.Loading(html.Div(id="matriculas-matriz")),
            filtros,
        ],
        className="painel-landing",
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


def _tabela_matriculas(df, filtros):
    """Tabela do Figma: quebra por campus com Ano PNP / Total de Matrículas,
    Concluídas, Integralizadas, Em Curso e Evasões, e linha de total."""
    coluna = "cidade" if filtros.eixo == "campus" else coluna_para_eixo(filtros.eixo)
    rotulo_eixo = {o["value"]: o["label"] for o in EIXOS}.get(filtros.eixo, filtros.eixo)
    linhas = []
    for chave, grupo in df.groupby(coluna, dropna=False):
        total = len(grupo)
        concluidas = int((grupo["status_corrigido"] == STATUS_CONCLUIDA).sum())
        integralizadas = int((grupo["status_corrigido"] == STATUS_INTEGRALIZADA).sum())
        em_curso = int((grupo["status_corrigido"] == STATUS_EM_CURSO).sum())
        evasoes = int(grupo["status_corrigido"].apply(eh_evadido).sum())
        linhas.append(
            {
                "eixo": chave,
                "total": total,
                "concluidas": concluidas,
                "integralizadas": integralizadas,
                "em_curso": em_curso,
                "evasoes": evasoes,
            }
        )
    linhas.sort(key=lambda l: str(l["eixo"]))

    def _td(valor, classe="num"):
        return html.Td(formatar_valor(valor, "#,0"), className=classe)

    corpo = [
        html.Tr(
            [
                html.Td(linha["eixo"], className="campus"),
                _td(linha["total"]),
                _td(linha["concluidas"]),
                _td(linha["integralizadas"], "num" if linha["integralizadas"] else "num zero"),
                _td(linha["em_curso"]),
                html.Td(formatar_valor(linha["evasoes"], "#,0"), className="evasao"),
            ]
        )
        for linha in linhas
    ]

    total = sum(l["total"] for l in linhas)
    concluidas = sum(l["concluidas"] for l in linhas)
    integralizadas = sum(l["integralizadas"] for l in linhas)
    em_curso = sum(l["em_curso"] for l in linhas)
    evasoes = sum(l["evasoes"] for l in linhas)
    rodape = html.Tr(
        [
            html.Td("Total", className="campus"),
            _td(total),
            _td(concluidas),
            _td(integralizadas),
            _td(em_curso),
            html.Td(formatar_valor(evasoes, "#,0"), className="evasao"),
        ]
    )

    cabecalho = html.Thead(
        [
            html.Tr(
                [
                    html.Th(rotulo_eixo, rowSpan=2, scope="col"),
                    html.Th("Ano PNP", scope="col"),
                    html.Th("Concluintes", colSpan=2, scope="colgroup"),
                    html.Th("Em Curso", rowSpan=2, scope="col", className="negrito"),
                    html.Th("Evasões", rowSpan=2, scope="col", className="negrito"),
                ]
            ),
            html.Tr(
                [
                    html.Th("Total de Matrículas", scope="col", className="negrito"),
                    html.Th("Concluídas", scope="col", className="negrito"),
                    html.Th("Integralizadas", scope="col", className="negrito"),
                ]
            ),
        ]
    )

    return html.Div(
        html.Table([cabecalho, html.Tbody(corpo), html.Tfoot(rodape)], className="tabela-landing"),
        className="matriz-figma",
    )


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
            matricula_equivalente(linha.tipo_curso_pnp, linha.carga_horaria_total, linha.fec, 1, linha.fech)
            for linha in df_ano_base.itertuples()
        )

    kpis = [
        _kpi("Cursos", cursos_ativos),
        _kpi("Matrículas", total, formato="#,0"),
        _kpi("Matrículas equivalentes", equivalentes, formato="#,0.00", empty_state="dado incompleto"),
        _kpi("Matrículas concluídas", concluidas),
        _kpi("Ingressantes", ingressantes),
    ]

    if df.empty:
        matriz = mensagem_ds("info", "Sem dados para o eixo selecionado.")
    else:
        matriz = _tabela_matriculas(df, filtros)

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
