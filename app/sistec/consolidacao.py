"""Consolidação das planilhas baixadas do Sistec (`002-baixador-planilhas-
sistec`, T036, D-18).

Empilha as planilhas do mesmo tipo (ciclo/matrícula) já lidas com a lista de
permissão aplicada (`app/sistec/colunas.aplicar_permissao` — os DataFrames de
entrada já chegam com os nomes internos de `data-delta.md` §4), confere a
assinatura de cabeçalho (RN-16), deduplica por `CODIGO_CICLO_MATRICULA` e
cria `STATUS_MATRICULA_PNP` nulo (RN-23: sem PNP, o corrigido vale o
Sistec, via `app/data/transform.t02_corrigir_status`).

Cada linha da planilha de ciclo traz, junto do ciclo, os atributos do curso
(RN-16 do Sistec: um ciclo pertence a um único portfólio). A separação em
`cursos` (por `codigo_portfolio`) e `ciclos` (por `codigo_ciclo_matricula`),
os ajustes de nome/eixo (A2/A3/A5, `app/data/ajustes_curso.py`), o casamento
de fatores (D-07, `app/data/fatores.py`) e o mapeamento final para os nomes
de coluna do schema (`app/data/schema.py`) ficam em
`app/data/ingest.montar_versao_interna` (T037/T038), que consome o
`conjunto` devolvido por `consolidar`.
"""

import pandas as pd

from app.data.correction import corrigir_status_sistec_pnp
from app.data.transform import t06_filtrar_ciclos_excluidos, t07_grao_matricula_atendida, t08_grao_eficiencia_academica

COL_CICLO_CHAVE = "CODIGO_CICLO_MATRICULA"
COL_PORTFOLIO = "CÓDIGO DO PORTFÓLIO"
COL_UNIDADE = "CO_UNIDADE"


class ConsolidacaoInvalida(Exception):
    """RNF Robustez: assinatura de cabeçalho divergente entre pares do mesmo
    tipo, `codigo_ciclo_matricula` repetido com conteúdo divergente, ou
    `codigo_portfolio` com `co_unidade` divergente entre campi (P-07)."""


def _assinatura(df):
    return tuple(sorted(df.columns))


def empilhar(dfs, tipo):
    """Empilha os DataFrames (já com a permissão de colunas aplicada) do
    mesmo `tipo` ('ciclo' ou 'matricula'). RN-16: todos precisam ter a mesma
    assinatura de cabeçalho; caso contrário, a consolidação falha por inteiro
    com erro explícito."""
    if not dfs:
        return pd.DataFrame()

    assinatura_base = _assinatura(dfs[0])
    for df in dfs[1:]:
        if _assinatura(df) != assinatura_base:
            raise ConsolidacaoInvalida(f"assinatura de cabeçalho diferente entre pares do tipo '{tipo}'")

    return pd.concat(dfs, ignore_index=True)


def _checar_portfolio_sem_unidade_divergente(df_ciclo):
    """P-07: `codigo_portfolio` não pode ter mais de um `CO_UNIDADE` — a
    consolidação falha com erro explícito (a chave de `cursos` é
    `codigo_portfolio`, um único `co_unidade`)."""
    if COL_PORTFOLIO not in df_ciclo.columns or COL_UNIDADE not in df_ciclo.columns:
        return
    divergentes = df_ciclo.groupby(COL_PORTFOLIO)[COL_UNIDADE].nunique().loc[lambda s: s > 1]
    if not divergentes.empty:
        raise ConsolidacaoInvalida(
            f"{COL_PORTFOLIO} repetido com {COL_UNIDADE} divergente entre campi: {list(divergentes.index)}"
        )


def _deduplicar_por_chave(df, coluna_chave):
    """data-delta.md §6.4: chave repetida com conteúdo idêntico é
    deduplicada; com conteúdo divergente, a consolidação falha explícita."""
    duplicadas = df[df.duplicated(subset=[coluna_chave], keep=False)]
    if duplicadas.empty:
        return df

    for _chave, grupo in duplicadas.groupby(coluna_chave):
        primeira = grupo.iloc[0]
        for _, linha in grupo.iloc[1:].iterrows():
            if not primeira.equals(linha):
                raise ConsolidacaoInvalida(f"'{coluna_chave}' repetido com conteúdo divergente: {_chave}")
    return df.drop_duplicates(subset=[coluna_chave], keep="first")


def consolidar(pares_ciclo, pares_matricula):
    """Consolida os pares já lidos com permissão aplicada. Retorna um dict
    com `ciclos` e `matriculas`, ainda nos nomes internos de colunas
    (`data-delta.md` §4), prontos para `app/data/ingest.montar_versao_interna`.

    `pares_ciclo`/`pares_matricula`: listas de DataFrames, um por par
    (campus) baixado com sucesso.
    """
    df_ciclo = empilhar(pares_ciclo, "ciclo")
    df_matricula = empilhar(pares_matricula, "matricula")

    if df_ciclo.empty:
        raise ConsolidacaoInvalida("nenhum par de ciclo consolidado")

    _checar_portfolio_sem_unidade_divergente(df_ciclo)
    df_ciclo = _deduplicar_por_chave(df_ciclo, COL_CICLO_CHAVE)

    # T-06 (status EXCLUÍDO do ciclo) + SITUAÇÃO DO CICLO (RN filtro adicional).
    df_ciclo = t06_filtrar_ciclos_excluidos(df_ciclo, col_status="STATUS_CICLO")
    if "SITUACAO_CICLO" in df_ciclo.columns:
        df_ciclo = df_ciclo.loc[df_ciclo["SITUACAO_CICLO"] != "EXCLUÍDO"].copy()

    if not df_matricula.empty:
        df_matricula = _deduplicar_por_chave(df_matricula, COL_CICLO_CHAVE)
        # RN-23: sem correção PNP nesta feature — STATUS_MATRICULA_PNP nulo,
        # o corrigido vale sempre o Sistec (t02_corrigir_status já cobre isso).
        df_matricula = df_matricula.assign(STATUS_MATRICULA_PNP=pd.NA)
        df_matricula, _rejeitadas_status = corrigir_status_sistec_pnp(
            df_matricula, col_sistec="STATUS_MATRICULA_SISTEC", col_pnp="STATUS_MATRICULA_PNP"
        )

    return {"ciclos": df_ciclo.reset_index(drop=True), "matriculas": df_matricula.reset_index(drop=True)}


def montar_matriculas_e_eficiencia(df_matriculas, df_ciclos, ano_base):
    """Junta matrículas ao ciclo (para expor `dt_data_inicio`/
    `dt_data_fim_previsto`) e aplica T-07/T-08, reaproveitando o núcleo já
    coberto pela suíte de paridade."""
    colunas_matriculas = ["CO_MATRICULA", COL_CICLO_CHAVE, "status_corrigido", "mes_ocorrencia_corrigido"]
    colunas_eficiencia = ["CO_MATRICULA", COL_CICLO_CHAVE, "status_corrigido"]
    if df_matriculas.empty or df_ciclos.empty:
        return pd.DataFrame(columns=colunas_matriculas), pd.DataFrame(columns=colunas_eficiencia)

    df_ciclos_join = df_ciclos.rename(
        columns={"DT_DATA_INICIO": "dt_data_inicio", "DT_DATA_FIM_PREVISTO": "dt_data_fim_previsto"}
    )
    df_matriculas = df_matriculas.rename(columns={"MES_OCORRENCIA_CORRIGIDO": "mes_ocorrencia_corrigido"})
    df_join = df_matriculas.merge(df_ciclos_join, on=COL_CICLO_CHAVE, how="inner")

    df_matriculas_final = t07_grao_matricula_atendida(df_join, ano_base)
    df_eficiencia_final = t08_grao_eficiencia_academica(df_join, ano_base)
    return df_matriculas_final, df_eficiencia_final
