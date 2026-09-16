"""Transformações T-01 a T-08 do pipeline de ingestão — Tarefa 03 do plano de reconstrução.

Reimplementa em pandas o pipeline descrito em
`_reversa_sdd/migration/data_migration_plan.md` §"Transformações", produzindo
DataFrames prontos para gravação no schema alvo (`app/data/schema.py` /
`_reversa_sdd/migration/target_data_model.md`).

Cada função é pura (mesma entrada -> mesma saída), conforme
`AGG-Ingestao`/`AGG-NucleoMatriculas` no paradigma alvo (sem estado global).

GAP sinalizado (🔴): `data_migration_plan.md` não especifica os nomes exatos
das colunas cruas de status Sistec/PNP (T-02) nem da planilha de fatores
FEC/FECH (T-05) na fonte real do Sistec. Este módulo assume os nomes abaixo
como convenção provisória; confirmar com a usuária ou com a planilha real de
teste antes da Tarefa 05 (BC-01), que conecta este pipeline ao upload real:
- Status Sistec: `STATUS_MATRICULA_SISTEC`
- Status PNP: `STATUS_MATRICULA_PNP`
- Planilha de fatores: colunas `CÓDIGO DO PORTFÓLIO`, `FEC`, `FECH`
"""

import pandas as pd

# Domínio fechado de StatusMatricula (T-02). PNP "terminativo" é qualquer
# status != EM_CURSO e != nulo.
#
# Correção da Tarefa 11 (parity_tests/05-eficiencia-academica-iea.feature,
# "nenhum status some do total"): o conjunto original da Tarefa 03 era um
# placeholder provisório ({"CONCLUINTE", "EVADIDO", "TRANCADO",
# "TRANSFERIDO", ...}) que não batia com o value object `StatusMatricula`
# canônico definido em `target_domain_model.md` §"Value objects" (8 valores,
# usado por `app/domain/shared.STATUS_EVADIDO` e
# `app/domain/eficiencia.STATUS_CONCLUIDO`). Um status válido segundo o
# domínio antigo (ex.: "CONCLUINTE") não pertencia a nenhum bucket de
# eficiência (nem concluído, nem evadido, nem retido) — divergência
# encontrada ao rodar o cenário de paridade.
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

# Colunas de PII a descartar incondicionalmente (T-01).
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
    # `_reversa_forward/002-baixador-planilhas-sistec/f0-resultado.md`, achado 4):
    # nome e CPF do responsável, não previstos na versão anterior desta lista.
    "NOME_RESPONSAVEL",
    "CPF",
]


def t01_remover_pii(df):
    """T-01: descarta colunas de PII, se presentes, antes de qualquer outra transformação."""
    colunas_presentes = [c for c in COLUNAS_PII if c in df.columns]
    return df.drop(columns=colunas_presentes)


def t02_corrigir_status(df, col_sistec="STATUS_MATRICULA_SISTEC", col_pnp="STATUS_MATRICULA_PNP"):
    """T-02: PNP terminativo prevalece; PNP EM_CURSO/nulo -> vale o Sistec.

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
    """T-03: aplica mapa de nomes históricos -> padrão PNP e colapsa
    FORMAÇÃO INICIAL / FORMAÇÃO CONTINUADA / MULHERES MIL em QUALIFICAÇÃO PROFISSIONAL.

    Nome não encontrado no mapa mantém o original e é sinalizado em `aviso_qualidade`.
    """
    df = df.copy()
    nomes_ajustados = df[col_nome].map(mapa_nomes)
    df["nome_curso_ajustado"] = nomes_ajustados.fillna(df[col_nome])
    df["aviso_qualidade_nome"] = nomes_ajustados.isna()

    # Tarefa 11 (parity_tests/06-eixo-dinamico-e-fic.feature): preserva o
    # tipo cru ANTES do colapso — BR-MIGRAR-021 exige distinguir Formação
    # Inicial/Continuada de Mulheres Mil no toggle FIC, distinção que o
    # colapso abaixo, sozinho, destruiria.
    df["categoria_origem_curso"] = df[col_tipo].str.upper()

    colapso = {
        "FORMAÇÃO INICIAL": "QUALIFICAÇÃO PROFISSIONAL",
        "FORMAÇÃO CONTINUADA": "QUALIFICAÇÃO PROFISSIONAL",
        "MULHERES MIL": "QUALIFICAÇÃO PROFISSIONAL",
    }
    df["tipo_curso_pnp"] = df[col_tipo].replace(colapso)

    return df


def t04_chave_curso_unica(df, col_portfolio="CÓDIGO DO PORTFÓLIO"):
    """T-04: usa CÓDIGO DO PORTFÓLIO como chave real; rejeita linhas sem esse código."""
    tem_chave = df[col_portfolio].notna() & (df[col_portfolio] != "")

    df_valido = df.loc[tem_chave].copy()
    df_valido["codigo_portfolio"] = df_valido[col_portfolio]

    df_rejeitado = df.loc[~tem_chave].copy()
    df_rejeitado["motivo_rejeicao"] = "sem_codigo_portfolio"

    return df_valido, df_rejeitado


def t05_default_fec_fech(df_cursos, df_fatores, col_portfolio="codigo_portfolio"):
    """T-05: merge com a planilha de fatores; ausência de par -> fec=fech=1 (default
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
    """T-06: descarta ciclos com status EXCLUÍDO."""
    return df.loc[df[col_status] != "EXCLUÍDO"].copy()


def t07_grao_matricula_atendida(
    df,
    ano_base,
    col_dt_inicio="dt_data_inicio",
    col_status="status_corrigido",
    col_mes_ocorrencia="mes_ocorrencia_corrigido",
):
    """T-07: inclui a matrícula se iniciou no ano-base OU status=EM_CURSO OU mês de
    ocorrência >= início do ano-base — incluindo o caso de `dt_data_inicio` nula
    (BR-HUMANA-010: o campo pertence ao ciclo, não à matrícula; nulo não exclui)."""
    dt_inicio = pd.to_datetime(df[col_dt_inicio], errors="coerce")
    mes_ocorrencia = pd.to_datetime(df[col_mes_ocorrencia], errors="coerce")
    inicio_ano_base = pd.Timestamp(year=ano_base, month=1, day=1)

    iniciou_no_ano_base = dt_inicio.dt.year == ano_base
    em_curso = df[col_status] == "EM_CURSO"
    ocorreu_apos_inicio = mes_ocorrencia >= inicio_ano_base

    incluir = iniciou_no_ano_base | em_curso | ocorreu_apos_inicio | dt_inicio.isna() & em_curso
    return df.loc[incluir].copy()


def t08_grao_eficiencia_academica(df, ano_base, col_dt_fim_previsto="dt_data_fim_previsto"):
    """T-08: inclui apenas matrículas cujo DT_DATA_FIM_PREVISTO do ciclo cai em
    ano_base - 1. DT_DATA_FIM_PREVISTO nulo -> excluída (sem decisão em contrário)."""
    dt_fim = pd.to_datetime(df[col_dt_fim_previsto], errors="coerce")
    incluir = dt_fim.dt.year == (ano_base - 1)
    return df.loc[incluir].copy()
