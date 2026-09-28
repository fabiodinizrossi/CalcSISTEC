"""Contagens de matrículas por status, taxa de evasão e filtro FIC.

As funções recebem os filtros ativos explicitamente. O filtro SEM FIC exclui
Formação Inicial e Formação Continuada e preserva Mulheres Mil.
"""

import pandas as pd

from app.domain.contrato import FiltrosAtivos
from app.domain.shared import eh_evadido, parsear_mes_ocorrencia

# A categoria de origem distingue Formação Inicial e Continuada de Mulheres Mil.
CATEGORIAS_FIC = {"FORMAÇÃO INICIAL", "FORMAÇÃO CONTINUADA"}


def _aplicar_filtros(df, filtros: FiltrosAtivos):
    """Aplica ano-base e, quando selecionados, campus e curso."""
    filtrado = df[df["ano_base"] == filtros.ano_base]
    if filtros.campus is not None:
        filtrado = filtrado[filtrado["co_unidade"] == filtros.campus]
    if filtros.curso is not None:
        filtrado = filtrado[filtrado["codigo_portfolio"] == filtros.curso]
    return filtrado


def contar_por_status(df, filtros: FiltrosAtivos, status):
    """Conta matrículas pelo status corrigido após aplicar os filtros."""
    filtrado = _aplicar_filtros(df, filtros)
    return int((filtrado["status_corrigido"] == status).sum())


def contar_evadidos(df, filtros: FiltrosAtivos):
    """Conta os sete status de evasão, incluindo REPROVADO e REPROVADA."""
    filtrado = _aplicar_filtros(df, filtros)
    return int(filtrado["status_corrigido"].apply(eh_evadido).sum())


def contar_matriculas(df, filtros: FiltrosAtivos):
    """Conta as matrículas atendidas preparadas pela ingestão nos filtros ativos."""
    return int(len(_aplicar_filtros(df, filtros)))


def contar_ingressantes(df, filtros: FiltrosAtivos):
    """Conta ingressantes pelo início do ciclo ou pela ocorrência no ano-base.

    O Sistec informa a data do ciclo, não a da matrícula. Uma matrícula EM_CURSO
    entra pelo mês de ocorrência apenas quando ele cai no ano-base; o status
    sozinho não indica ingresso.
    """
    filtrado = _aplicar_filtros(df, filtros)
    dt_inicio = pd.to_datetime(filtrado["dt_data_inicio"], errors="coerce")
    iniciou_no_ano_base = dt_inicio.dt.year == filtros.ano_base
    em_curso = filtrado["status_corrigido"] == "EM_CURSO"
    mes_ocorrencia = parsear_mes_ocorrencia(filtrado["mes_ocorrencia_corrigido"])
    ocorreu_no_ano_base = mes_ocorrencia.dt.year == filtros.ano_base
    return int((iniciou_no_ano_base | (em_curso & ocorreu_no_ano_base)).sum())


def taxa_evasao(df, filtros: FiltrosAtivos):
    """Divide evadidos pelo total e retorna zero quando não há matrículas."""
    total = contar_matriculas(df, filtros)
    if total == 0:
        return 0.0
    return contar_evadidos(df, filtros) / total


def filtrar_fic(df, incluir_fic):
    """Exclui Formação Inicial e Continuada quando SEM FIC está ativo.

    Mulheres Mil permanece no resultado.
    """
    if incluir_fic:
        return df
    return df[~df["categoria_origem_curso"].isin(CATEGORIAS_FIC)]


def contar_cursos_ativos(df_cursos, filtros: FiltrosAtivos):
    """Conta códigos de portfólio distintos, opcionalmente por campus.

    A ingestão rejeita cursos com código duplicado.
    """
    filtrado = df_cursos
    if filtros.campus is not None:
        filtrado = filtrado[filtrado["co_unidade"] == filtros.campus]
    return int(filtrado["codigo_portfolio"].nunique())
