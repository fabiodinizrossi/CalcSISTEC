"""Lista de permissão de colunas do Sistec (`002-baixador-planilhas-sistec`, T026, D-04).

RN-17: do resultado da junção entram só as colunas de interesse para os
cálculos do painel. Qualquer coluna fora da lista de permissão é descartada
já na leitura (D-03), e isso é obrigatório para toda coluna de dado pessoal
(defesa em profundidade) — inclusive `NOME_RESPONSAVEL` e `CPF` do
responsável, confirmadas na planilha de ciclo pela investigação ao vivo F0
(`f0-resultado.md`, achado 4), que não estavam na versão anterior de
`app/data/transform.COLUNAS_PII`.

Cada mapa é {nome no Sistec: nome interno}. Nomes conforme
`_reversa_forward/002-baixador-planilhas-sistec/data-delta.md` §4 (P-03:
convenção provisória para a planilha de matrícula, ainda não confirmada em
exploração ao vivo — a de ciclo já foi, pela F0).
"""

import io

import pandas as pd

from app.data.transform import COLUNAS_PII

# §4.1 Planilha de ciclo (`ciclo-matricula.csv`).
COLUNAS_CICLO = {
    "CÓDIGO CICLO DE MATRÍCULA": "CODIGO_CICLO_MATRICULA",
    "CÓDIGO UNIDADE DE ENSINO": "CO_UNIDADE",
    "CÓDIGO DO PORTFÓLIO": "CÓDIGO DO PORTFÓLIO",
    "NOME DO CURSO": "NOME_CURSO",
    "SUBTIPO CURSOS": "TIPO_CURSO",
    "CARGA HORÁRIA TOTAL": "CARGA_HORARIA_TOTAL",
    "MODALIDADE ENSINO": "MODALIDADE_ENSINO",
    "TIPO OFERTA DO CURSO": "OFERTA",
    "EIXO TECNOLÓGICO": "EIXO_TECNOLOGICO",
    "TIPO PROGRAMA DO CURSO": "TIPO_PROGRAMA_CURSO",
    "DATA INÍCIO DO CURSO": "DT_DATA_INICIO",
    "DATA FIM PREVISTO DO CURSO": "DT_DATA_FIM_PREVISTO",
    "STATUS DO CICLO DE MATRÍCULA": "STATUS_CICLO",
    "SITUAÇÃO DO CICLO ": "SITUACAO_CICLO",  # espaço final confirmado em data-delta.md §4.1
}

# §4.2 Planilha de matrícula (`sistec.csv`).
COLUNAS_MATRICULA = {
    "CO_MATRICULA": "CO_MATRICULA",
    "CO_CICLO_MATRICULA": "CODIGO_CICLO_MATRICULA",
    "NO_STATUS_MATRICULA": "STATUS_MATRICULA_SISTEC",
    "MES_DE_OCORRENCIA": "MES_OCORRENCIA_CORRIGIDO",
}

_PERMISSAO_POR_TIPO = {
    "ciclo": COLUNAS_CICLO,
    "matricula": COLUNAS_MATRICULA,
}

# Defesa em profundidade (D-04): nem o nome no Sistec nem o nome interno de
# uma coluna permitida podem ser um nome de PII conhecido. Falha na
# importação do módulo, não em tempo de teste, para que um erro de edição
# futura nesta lista pare a aplicação imediatamente.
for _tipo, _mapa in _PERMISSAO_POR_TIPO.items():
    _intersecao = (set(_mapa.keys()) | set(_mapa.values())) & set(COLUNAS_PII)
    if _intersecao:
        raise AssertionError(
            f"Lista de permissão de '{_tipo}' contém coluna de PII: {_intersecao}"
        )


def aplicar_permissao(df, tipo):
    """Mantém só as colunas permitidas para `tipo` ('ciclo' ou 'matricula') que
    estiverem presentes em `df`, e as renomeia para o nome interno. Coluna
    nova que o Sistec passar a exportar nunca entra sem mudança de código
    (RN-17)."""
    try:
        mapa = _PERMISSAO_POR_TIPO[tipo]
    except KeyError:
        raise ValueError(f"tipo de planilha desconhecido: {tipo!r}") from None

    colunas_presentes = [c for c in mapa if c in df.columns]
    return df[colunas_presentes].rename(columns=mapa)


def ler_planilha(conteudo_bytes, tipo):
    """Lê uma exportação CSV do Sistec e mantém apenas colunas permitidas."""
    try:
        mapa = _PERMISSAO_POR_TIPO[tipo]
    except KeyError:
        raise ValueError(f"tipo de planilha desconhecido: {tipo!r}") from None

    try:
        cabecalho = pd.read_csv(
            io.BytesIO(conteudo_bytes), sep=";", encoding="cp1252", encoding_errors="replace", dtype=str, nrows=0
        )
    except Exception as exc:
        raise ValueError("leitura_csv") from exc

    if any(coluna not in cabecalho.columns for coluna in mapa):
        raise ValueError("colunas_ausentes")

    try:
        df_bruto = pd.read_csv(
            io.BytesIO(conteudo_bytes),
            sep=";",
            encoding="cp1252",
            encoding_errors="replace",
            dtype=str,
            usecols=list(mapa),
        )
    except Exception as exc:
        raise ValueError("leitura_csv") from exc

    return aplicar_permissao(df_bruto, tipo)
