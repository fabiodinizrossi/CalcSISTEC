"""BC-04 (Apresentação): página inicial (Matrículas).

Conteúdo renderizado conforme o design "09 - Página inicial (Matrículas)" do
Figma. Nenhuma regra de negócio é calculada aqui — apenas consumo de
`app/domain/*` (invariante de `AGG-Apresentacao`).
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

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
    estado_textual = empty_state is not None and valor is None
    texto = empty_state if estado_textual else formatar_valor(valor, formato)
    classe_valor = "valor valor--texto" if estado_textual else "valor"
    return html.Div(
        [html.Div(label, className="rotulo"), html.Div(texto, className=classe_valor)],
        className="kpi-figma kpi-figma--destaque",
    )


def _chip_selector(id_):
    """"Ver tabela por" como chips; a ordem dos cliques forma a hierarquia."""
    return html.Div(
        [
            html.Span("Ver tabela por:", className="rotulo-chips"),
            dbc.Checklist(
                id=id_,
                options=EIXOS,
                value=["campus"],
                inline=True,
                className="chips-grupo",
                labelClassName="chip",
                labelCheckedClassName="chip--ativo",
                inputClassName="chip-input",
            ),
        ],
        className="card-chips",
    )


def _ordenar_eixos(marcados, ordem_anterior):
    """Mantém os campos ativos na ordem em que foram marcados."""
    marcados = list(dict.fromkeys(marcados or []))
    ordem = [eixo for eixo in (ordem_anterior or []) if eixo in marcados]
    ordem.extend(eixo for eixo in marcados if eixo not in ordem)
    return ordem


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
                className="seg-grupo",
                labelClassName="seg",
                labelCheckedClassName="seg--ativo",
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
            dcc.Store(id="matriculas-eixos-ordenados", data=["campus"]),
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


def _metricas(grupo):
    return {
        "total": len(grupo),
        "concluidas": int((grupo["status_corrigido"] == STATUS_CONCLUIDA).sum()),
        "integralizadas": int((grupo["status_corrigido"] == STATUS_INTEGRALIZADA).sum()),
        "em_curso": int((grupo["status_corrigido"] == STATUS_EM_CURSO).sum()),
        "evasoes": int(grupo["status_corrigido"].apply(eh_evadido).sum()),
    }


def _linhas_hierarquicas(df, eixos):
    """Cria uma pré-ordem da árvore, agregada novamente em cada nível."""
    linhas = []

    def visitar(grupo, nivel, caminho, pai=None):
        eixo = eixos[nivel]
        coluna = "cidade" if eixo == "campus" else coluna_para_eixo(eixo)
        grupos = list(grupo.groupby(coluna, dropna=False, sort=False))
        grupos.sort(key=lambda item: str(item[0]))
        for indice, (chave, subgrupo) in enumerate(grupos):
            id_grupo = "grupo-" + "-".join(map(str, caminho + (indice,)))
            linhas.append(
                {
                    "eixo": "Não informado" if chave is None or chave != chave else chave,
                    "nivel": nivel,
                    "id": id_grupo,
                    "pai": pai,
                    "tem_filhos": nivel + 1 < len(eixos),
                    **_metricas(subgrupo),
                }
            )
            if nivel + 1 < len(eixos):
                visitar(subgrupo, nivel + 1, caminho + (indice,), id_grupo)

    visitar(df, 0, ())
    return linhas


def _tabela_matriculas(df, eixos):
    """Matriz hierárquica com agregações em todos os campos selecionados."""
    eixos = _ordenar_eixos(eixos, eixos)
    rotulos = {o["value"]: o["label"] for o in EIXOS}
    rotulo_eixo = " › ".join(rotulos.get(eixo, eixo) for eixo in eixos) or "Total geral"
    linhas = _linhas_hierarquicas(df, eixos) if eixos else []

    def _td(valor, classe="num"):
        return html.Td(formatar_valor(valor, "#,0"), className=classe)

    def _td_integralizadas(valor):
        if valor == 0:
            return html.Td("—", className="num vazio")
        return html.Td(formatar_valor(valor, "#,0"), className="num")

    corpo = []
    for linha in linhas:
        controle = (
            html.Button(
                html.I(className="fas fa-chevron-down", **{"aria-hidden": "true"}),
                className="matriz-expansor",
                type="button",
                title="Recolher grupo",
                **{"aria-expanded": "true", "aria-label": f"Recolher {linha['eixo']}"},
            )
            if linha["tem_filhos"]
            else html.Span(className="matriz-expansor-espaco", **{"aria-hidden": "true"})
        )
        corpo.append(html.Tr(
            [
                html.Td(
                    html.Div([controle, html.Span(str(linha["eixo"]))], className="matriz-rotulo"),
                    className="campus",
                    style={"--nivel": str(linha["nivel"])},
                ),
                _td(linha["total"]),
                _td(linha["concluidas"]),
                _td_integralizadas(linha["integralizadas"]),
                _td(linha["em_curso"]),
                html.Td(formatar_valor(linha["evasoes"], "#,0"), className="evasao"),
            ],
            className=f"matriz-nivel-{linha['nivel']}",
            **{"data-group-id": linha["id"], "data-parent-id": linha["pai"] or "", "data-level": linha["nivel"]},
        ))

    totais = _metricas(df)
    rodape = html.Tr(
        [
            html.Td("Total", className="campus"),
            _td(totais["total"]),
            _td(totais["concluidas"]),
            _td_integralizadas(totais["integralizadas"]),
            _td(totais["em_curso"]),
            html.Td(formatar_valor(totais["evasoes"], "#,0"), className="evasao"),
        ]
    )

    cabecalho = html.Thead(
        [
            html.Tr(
                [
                    html.Th(rotulo_eixo, rowSpan=2, scope="col"),
                    html.Th("Ano PNP", scope="col", **{"data-no-sort": "true"}),
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

    colgroup = html.Colgroup([
        html.Col(className="col-eixo"),
        html.Col(className="col-total"),
        html.Col(className="col-concluidas"),
        html.Col(className="col-integralizadas"),
        html.Col(className="col-em-curso"),
        html.Col(className="col-evasoes"),
    ])
    return html.Div(
        [
            html.Div(
                html.Table(
                    [colgroup, cabecalho, html.Tbody(corpo), html.Tfoot(rodape)],
                    className="tabela-landing tabela-hierarquica",
                    **{"data-sortable": "true"},
                ),
                className="rolagem-tabela",
                tabIndex="0",
                role="region",
                **{"aria-label": f"Tabela de matrículas por {rotulo_eixo.lower()}"},
            ),
            html.P("Deslize a tabela para o lado para ver todas as colunas.", className="dica-rolagem"),
        ],
        className="matriz-figma",
    )


@callback(
    Output("matriculas-eixos-ordenados", "data"),
    Input("matriculas-eixo", "value"),
    State("matriculas-eixos-ordenados", "data"),
)
def atualizar_ordem_eixos(marcados, ordem_anterior):
    return _ordenar_eixos(marcados, ordem_anterior)


@callback(
    Output("matriculas-kpis", "children"),
    Output("matriculas-matriz", "children"),
    Input("matriculas-fic", "value"),
    Input("matriculas-eixos-ordenados", "data"),
    Input("matriculas-filtro-campus", "value"),
    Input("matriculas-filtro-tipo-curso", "value"),
    Input("matriculas-filtro-programa", "value"),
)
def atualizar(fic, eixos, campus, tipo_curso, programa):
    ano_base = ano_base_ativo() or 2026
    df = _filtrar(carregar_matriculas(), campus, tipo_curso, programa, fic)
    eixos = eixos or []
    filtros = FiltrosAtivos(ano_base=ano_base, eixo=eixos[0] if eixos else "campus", incluir_fic=(fic == "com_fic"))

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
        _kpi("Ingressantes", ingressantes),
        _kpi("Matrículas concluídas", concluidas),
        _kpi("Matrículas equivalentes", equivalentes, formato="#,0.00", empty_state="dado incompleto"),
    ]

    if df.empty:
        matriz = mensagem_ds("info", "Sem dados para o eixo selecionado.")
    else:
        matriz = _tabela_matriculas(df, eixos)

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
    return "__todos__", "__todos__", "__todos__", "com_fic", ["campus"]
