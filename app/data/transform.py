"""Transformações do pipeline de ingestão (`t02` a `t08`).

Reimplementa em pandas o pipeline de transformações do painel legado,
produzindo DataFrames prontos para gravação no schema alvo
(`app/data/schema.py`).

Cada função é pura (mesma entrada -> mesma saída), sem estado global.

Nomes de coluna crus esperados da fonte real do Sistec:
- Status Sistec: `STATUS_MATRICULA_SISTEC`
- Status PNP: `STATUS_MATRICULA_PNP`
- Planilha de fatores: colunas `CÓDIGO DO PORTFÓLIO`, `FEC`, `FECH`
"""

import pandas as pd

from app.domain.shared import parsear_mes_ocorrencia

# Domínio fechado de StatusMatricula. PNP "terminativo" é qualquer
# status != EM_CURSO e != nulo.
#
# O conjunto é o value object `StatusMatricula` canônico, o mesmo usado por
# `app/domain/shared.STATUS_EVADIDO` e `app/domain/eficiencia.STATUS_CONCLUIDO`:
# um status aceito aqui que não pertencesse a nenhum bucket de eficiência
# (nem concluído, nem evadido, nem retido) sumiria dos totais.
STATUS_MATRICULA_VALIDOS = {
    "EM_CURSO",
    "CONCLUÍDA",
    "INTEGRALIZADA",
    "ABANDONO",
    "DESLIGADO",
    "DESLIGADA",
    "REPROVADO",
    "REPROVADA",
    "TRANSF_EXT",
    "TRANSF_INT",
}

# Colunas de PII a descartar incondicionalmente.
COLUNAS_PII = [
    "DS_SENHA",
    "DS_EMAIL",
    "CO_PESSOA_FISICA_ALUNO",
    "NO_ALUNO",
    "NO_MAE_ALUNO",
    "SG_SEXO",
    "DT_DATA_NASCIMENTO",
    "NU_CPF",
    # Confirmadas na planilha de CICLO pela investigação ao vivo F0 (2026-09-14,
    # achado 4): nome e CPF do responsável, não previstos na versão anterior
    # desta lista.
    "NOME_RESPONSAVEL",
    "CPF",
]


def t02_corrigir_status(df, col_sistec="STATUS_MATRICULA_SISTEC", col_pnp="STATUS_MATRICULA_PNP"):
    """PNP terminativo prevalece; PNP EM_CURSO/nulo -> vale o Sistec.

    Linhas cujo status corrigido não pertence a STATUS_MATRICULA_VALIDOS são
    rejeitadas (retornadas em separado) em vez de passar silenciosamente.
    """
    pnp = df[col_pnp]
    sistec = df[col_sistec]

    pnp_terminativo = pnp.notna() & (pnp != "EM_CURSO")
    status_corrigido = pnp.where(pnp_terminativo, sistec)

    valido = status_corrigido.isin(STATUS_MATRICULA_VALIDOS)

    df_valido = df.loc[valido].copy()
    df_valido["status_corrigido"] = status_corrigido.loc[valido]

    df_rejeitado = df.loc[~valido].copy()
    df_rejeitado["motivo_rejeicao"] = "status_fora_do_dominio"

    return df_valido, df_rejeitado


def t03_normalizar_curso(df, mapa_nomes, col_nome="NOME_CURSO", col_tipo="TIPO_CURSO"):
    """Aplica mapa de nomes históricos -> padrão PNP e colapsa
    FORMAÇÃO INICIAL / FORMAÇÃO CONTINUADA / MULHERES MIL em QUALIFICAÇÃO PROFISSIONAL.

    Nome não encontrado no mapa mantém o original e é sinalizado em `aviso_qualidade`.
    """
    df = df.copy()
    nomes_ajustados = df[col_nome].map(mapa_nomes)
    df["nome_curso_ajustado"] = nomes_ajustados.fillna(df[col_nome])
    df["aviso_qualidade_nome"] = nomes_ajustados.isna()

    # Preserva o tipo cru ANTES do colapso: o toggle FIC exige distinguir
    # Formação Inicial/Continuada de Mulheres Mil, distinção que o colapso
    # abaixo, sozinho, destruiria.
    df["categoria_origem_curso"] = df[col_tipo].str.upper()

    colapso = {
        "FORMAÇÃO INICIAL": "QUALIFICAÇÃO PROFISSIONAL",
        "FORMAÇÃO CONTINUADA": "QUALIFICAÇÃO PROFISSIONAL",
        "MULHERES MIL": "QUALIFICAÇÃO PROFISSIONAL",
    }
    df["tipo_curso_pnp"] = df[col_tipo].replace(colapso)

    return df


def t04_chave_curso_unica(df, col_portfolio="CÓDIGO DO PORTFÓLIO"):
    """Usa CÓDIGO DO PORTFÓLIO como chave real; rejeita linhas sem esse código."""
    tem_chave = df[col_portfolio].notna() & (df[col_portfolio] != "")

    df_valido = df.loc[tem_chave].copy()
    df_valido["codigo_portfolio"] = df_valido[col_portfolio]

    df_rejeitado = df.loc[~tem_chave].copy()
    df_rejeitado["motivo_rejeicao"] = "sem_codigo_portfolio"

    return df_valido, df_rejeitado


def t05_default_fec_fech(df_cursos, df_fatores, col_portfolio="codigo_portfolio"):
    """Merge com a planilha de fatores; ausência de par -> fec=fech=1 (default
    explícito) e sinalização em `fator_nao_encontrado`, nunca NULL silencioso."""
    merged = df_cursos.merge(
        df_fatores[[col_portfolio, "FEC", "FECH"]],
        on=col_portfolio,
        how="left",
        suffixes=("", "_fator"),
    )
    merged["fator_nao_encontrado"] = merged["FEC"].isna()
    merged["fec"] = merged["FEC"].fillna(1.0)
    merged["fech"] = merged["FECH"].fillna(1.0)
    return merged.drop(columns=["FEC", "FECH"])


def t06_filtrar_ciclos_excluidos(df, col_status="STATUS_CICLO"):
    """Descarta ciclos com status EXCLUÍDO."""
    return df.loc[df[col_status] != "EXCLUÍDO"].copy()


def t07_grao_matricula_atendida(
    df,
    ano_base,
    col_dt_inicio="dt_data_inicio",
    col_status="status_corrigido",
    col_mes_ocorrencia="mes_ocorrencia_corrigido",
):
    """Inclui a matrícula se o ciclo iniciou no
    ano-base, OU se o status é EM_CURSO, OU se o mês de ocorrência é do
    ano-base — independente de quando o ciclo começou.

    `mes_ocorrencia_corrigido` (vindo de `MES_DE_OCORRENCIA`) chega do Sistec
    como texto em português ("JUNHO 2026"), que `pd.to_datetime` não reconhece;
    por isso a coluna passa por `shared.parsear_mes_ocorrencia`, e o teste é de
    ano exato (`== ano_base`), não "a partir do ano-base".

    `dt_data_inicio` é ISO ("2010-02-22 00:00:00") e continua com
    `pd.to_datetime` direto. `dt_data_inicio` nula não exclui por si só (o
    campo pertence ao ciclo, não à matrícula) — a matrícula ainda pode entrar
    por EM_CURSO ou pelo mês de ocorrência.
    """
    dt_inicio = pd.to_datetime(df[col_dt_inicio], errors="coerce")
    mes_ocorrencia = parsear_mes_ocorrencia(df[col_mes_ocorrencia])

    iniciou_no_ano_base = dt_inicio.dt.year == ano_base
    em_curso = df[col_status] == "EM_CURSO"
    ocorreu_no_ano_base = mes_ocorrencia.dt.year == ano_base

    incluir = iniciou_no_ano_base | em_curso | ocorreu_no_ano_base
    return df.loc[incluir].copy()


def t08_grao_eficiencia_academica(df, ano_base, col_dt_fim_previsto="dt_data_fim_previsto"):
    """Inclui apenas matrículas cujo DT_DATA_FIM_PREVISTO do ciclo cai em
    ano_base - 1. DT_DATA_FIM_PREVISTO nulo -> excluída (sem decisão em contrário)."""
    dt_fim = pd.to_datetime(df[col_dt_fim_previsto], errors="coerce")
    incluir = dt_fim.dt.year == (ano_base - 1)
    return df.loc[incluir].copy()
