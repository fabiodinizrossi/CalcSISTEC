"""Testes de `scripts/sintetico.py` (o simulador do Sistec).

O módulo promete "a estrutura exata que o Sistec exporta". `MES_DE_OCORRENCIA`
saía como `"06/2026"` — formato que a extração real nunca traz (o Sistec exporta
`"JUNHO 2026"`) e que `app.domain.shared.parsear_mes_ocorrencia` não reconhece.
Dado sintético fora do formato real escondia a regra do mês de ocorrência
(MAT-01) do próprio modo de teste.

Rodar com: `pytest tests/test_sintetico.py -v`
"""

import io
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts import sintetico  # noqa: E402

from app.domain.shared import parsear_mes_ocorrencia  # noqa: E402
from app.sistec.colunas import COLUNAS_CICLO, COLUNAS_MATRICULA, aplicar_permissao  # noqa: E402
from app.sistec.consolidacao import consolidar, montar_matriculas_e_eficiencia  # noqa: E402

CO_UNIDADE = "101"
NOME_UNIDADE = "Alegrete"


def _ler(texto, mapa, tipo):
    df_bruto = pd.read_csv(
        io.BytesIO(texto.encode("cp1252")), sep=";", encoding="cp1252", dtype=str, usecols=list(mapa.keys())
    )
    return aplicar_permissao(df_bruto, tipo)


@pytest.fixture
def conjuntos():
    ciclos = _ler(sintetico.csv_ciclo(CO_UNIDADE, NOME_UNIDADE), COLUNAS_CICLO, "ciclo")
    matriculas = _ler(sintetico.csv_matricula(CO_UNIDADE, NOME_UNIDADE), COLUNAS_MATRICULA, "matricula")
    return consolidar([ciclos], [matriculas])


def test_mes_de_ocorrencia_gerado_no_formato_real_do_sistec(conjuntos):
    """Todo valor gerado é reconhecido pelo parse do domínio, e o ano-base
    aparece — sem isso o modo de teste não exercita a regra real."""
    ocorrencias = conjuntos["matriculas"]["MES_OCORRENCIA_CORRIGIDO"]

    analisadas = parsear_mes_ocorrencia(ocorrencias)

    assert len(ocorrencias) > 0
    assert int(analisadas.isna().sum()) == 0
    assert sintetico.ANO_BASE in set(analisadas.dt.year)


def test_mes_de_ocorrencia_sai_por_extenso_como_no_sistec(conjuntos):
    """Formato literal: `<NOME DO MÊS> <ano de 4 dígitos>`, em maiúsculas."""
    valores = conjuntos["matriculas"]["MES_OCORRENCIA_CORRIGIDO"].unique()

    for valor in valores:
        nome, ano = valor.split(" ")
        assert nome in set(sintetico.MESES_PT.values())
        assert len(ano) == 4 and ano.isdigit()


def test_corpus_sintetico_exercita_a_via_do_mes_de_ocorrencia(conjuntos):
    """MAT-01 AC1 com o dado sintético: matrícula fora de `EM_CURSO` com ciclo
    começado antes do ano-base entra pela via do mês de ocorrência."""
    atendidas, _eficiencia = montar_matriculas_e_eficiencia(
        conjuntos["matriculas"], conjuntos["ciclos"], sintetico.ANO_BASE
    )
    juncao = conjuntos["matriculas"].rename(columns={"MES_OCORRENCIA_CORRIGIDO": "mes_ocorrencia_corrigido"}).merge(
        conjuntos["ciclos"].rename(
            columns={"DT_DATA_INICIO": "dt_data_inicio", "DT_DATA_FIM_PREVISTO": "dt_data_fim_previsto"}
        ),
        on="CODIGO_CICLO_MATRICULA",
        how="inner",
    )

    so_pelo_mes = (
        (juncao["status_corrigido"] != "EM_CURSO")
        & (pd.to_datetime(juncao["dt_data_inicio"], errors="coerce").dt.year != sintetico.ANO_BASE)
        & (parsear_mes_ocorrencia(juncao["mes_ocorrencia_corrigido"]).dt.year == sintetico.ANO_BASE)
    )

    assert int(so_pelo_mes.sum()) > 0
    esperadas = set(juncao.loc[so_pelo_mes, "CO_MATRICULA"])
    assert esperadas <= set(atendidas["CO_MATRICULA"])
