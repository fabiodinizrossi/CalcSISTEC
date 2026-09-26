"""Regras comuns de evasão, matrícula equivalente e agrupamento por eixo.

As funções recebem os filtros ativos por parâmetro e não consultam estado global.
"""

import pandas as pd

from app.domain.contrato import EixoQuebra, FiltrosAtivos

# Estes sete status compõem a evasão em todos os indicadores.
STATUS_EVADIDO = {
    "ABANDONO",
    "DESLIGADO",
    "DESLIGADA",
    "REPROVADO",
    "REPROVADA",
    "TRANSF_EXT",
    "TRANSF_INT",
}

# Para Qualificação Profissional, FECH é carga horária total dividida por 800.
TIPO_CURSO_QUALIFICACAO_PROFISSIONAL = "QUALIFICAÇÃO PROFISSIONAL"
CARGA_HORARIA_REFERENCIA_FECH = 800

# O Sistec exporta meses por extenso em português, com ou sem cedilha em março.
MESES_PT = {
    "JANEIRO": 1,
    "FEVEREIRO": 2,
    "MARÇO": 3,
    "MARCO": 3,
    "ABRIL": 4,
    "MAIO": 5,
    "JUNHO": 6,
    "JULHO": 7,
    "AGOSTO": 8,
    "SETEMBRO": 9,
    "OUTUBRO": 10,
    "NOVEMBRO": 11,
    "DEZEMBRO": 12,
}

# Cada eixo seleciona uma coluna do conjunto consolidado para o agrupamento.
COLUNA_POR_EIXO = {
    "campus": "co_unidade",
    "tipo_curso": "subtipo_curso",
    "nome_curso": "nome_curso_ajustado",
    "modalidade": "modalidade_ensino",
    "oferta": "tipo_oferta_curso",
    "ciclo": "codigo_ciclo_matricula",
}


def eh_evadido(status):
    """Retorna se o status corrigido representa evasão.

    REPROVADO e REPROVADA contam como evasão sem remapeamento na ingestão.
    """
    return status in STATUS_EVADIDO


def matricula_equivalente(tipo_curso, carga_horaria_total, fec, matriculas, fech=1):
    """Calcula Mateq = matrículas × FECH × FEC (Portaria 146/2021, art. 2º).

    `fec` chega com o valor padrão aplicado pela ingestão, nunca nulo. Para
    cursos que não são de Qualificação Profissional, usa o `fech` recebido.
    Para Qualificação Profissional, ignora esse valor e divide a carga horária
    total por 800.
    """
    if tipo_curso == TIPO_CURSO_QUALIFICACAO_PROFISSIONAL:
        fech_efetivo = carga_horaria_total / CARGA_HORARIA_REFERENCIA_FECH
    else:
        fech_efetivo = fech
    return matriculas * fech_efetivo * fec


def coluna_para_eixo(eixo: EixoQuebra):
    """Resolve o eixo de quebra para sua coluna no conjunto consolidado."""
    return COLUNA_POR_EIXO[eixo]


def agrupar_por_eixo(df, filtros: FiltrosAtivos, coluna_valor, agregacao="sum"):
    """Agrega `coluna_valor` por um único eixo de quebra ativo."""
    coluna = coluna_para_eixo(filtros.eixo)
    return df.groupby(coluna, dropna=False)[coluna_valor].agg(agregacao).reset_index()


def modalidade(df):
    """Lê a modalidade de ensino consolidada pela ingestão."""
    return df["modalidade_ensino"]


def parsear_mes_ocorrencia(serie):
    """Interpreta o mês de ocorrência do Sistec como o dia 1 daquele mês.

    Devolve `pandas.Series` de `pandas.Timestamp` com o mesmo índice de
    `serie`. Qualquer valor que não seja `<nome de mês em português> <ano de 4
    dígitos>` (nulo, vazio, texto inesperado, outro formato de data) vira
    `pandas.NaT` sem levantar exceção. O resultado permite usar `.dt.year`.
    """
    texto = serie.astype("string").str.strip().str.upper()
    extraido = texto.str.extract(r"^([A-ZÇ]+)\s+(\d{4})$")
    mes = extraido[0].map(MESES_PT)
    ano = pd.to_numeric(extraido[1], errors="coerce")
    valido = mes.notna() & ano.notna()
    # `pd.to_datetime` não aceita ano/mês ausentes; preenche com um valor
    # qualquer e apaga depois com `where`, preservando o índice.
    datas = pd.to_datetime(
        {"year": ano.fillna(1970).astype("int64"), "month": mes.fillna(1).astype("int64"), "day": 1},
        errors="coerce",
    )
    return datas.where(valido, pd.NaT)
