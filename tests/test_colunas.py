"""Testes da lista de permissão de colunas do Sistec (`002-baixador-planilhas-sistec`, T020, T026).

RN-17: só as colunas de interesse entram no conjunto consolidado; qualquer
coluna fora da lista de permissão é descartada antes da prévia, e isso inclui
obrigatoriamente todas as colunas de dado pessoal (defesa em profundidade,
D-04, `data-delta.md` §4).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.transform import COLUNAS_PII  # noqa: E402
from app.sistec.colunas import (  # noqa: E402
    COLUNAS_CICLO,
    COLUNAS_MATRICULA,
    aplicar_permissao,
)


def test_lista_de_permissao_nao_intersecta_colunas_pii():
    nomes = set(COLUNAS_CICLO) | set(COLUNAS_CICLO.values()) | set(COLUNAS_MATRICULA) | set(COLUNAS_MATRICULA.values())
    assert nomes.isdisjoint(COLUNAS_PII)


def test_permissao_do_ciclo_cobre_as_14_colunas_de_data_delta():
    assert len(COLUNAS_CICLO) == 14
    assert COLUNAS_CICLO["CÓDIGO CICLO DE MATRÍCULA"] == "CODIGO_CICLO_MATRICULA"
    assert COLUNAS_CICLO["CÓDIGO UNIDADE DE ENSINO"] == "CO_UNIDADE"
    assert "SITUAÇÃO DO CICLO " in COLUNAS_CICLO  # espaço final confirmado em data-delta.md §4.1


def test_permissao_da_matricula_cobre_as_4_colunas_de_data_delta():
    assert COLUNAS_MATRICULA == {
        "CO_MATRICULA": "CO_MATRICULA",
        "CO_CICLO_MATRICULA": "CODIGO_CICLO_MATRICULA",
        "NO_STATUS_MATRICULA": "STATUS_MATRICULA_SISTEC",
        "MES_DE_OCORRENCIA": "MES_OCORRENCIA_CORRIGIDO",
    }


def test_ciclo_e_matricula_convergem_para_a_mesma_chave_de_juncao():
    """RN-16: a chave de junção tem o mesmo nome interno nos dois tipos de planilha."""
    assert COLUNAS_CICLO["CÓDIGO CICLO DE MATRÍCULA"] == COLUNAS_MATRICULA["CO_CICLO_MATRICULA"]


def test_aplicar_permissao_descarta_nome_responsavel_e_cpf_da_planilha_de_ciclo():
    """Achado 4 da F0: a planilha de ciclo real também tem NOME_RESPONSAVEL e CPF
    do responsável. A lista de permissão já os descarta, mesmo sem estarem em
    COLUNAS_PII."""
    import pandas as pd

    df = pd.DataFrame(
        {
            "CÓDIGO CICLO DE MATRÍCULA": ["1"],
            "CÓDIGO UNIDADE DE ENSINO": ["9001"],
            "NOME_RESPONSAVEL": ["Fulana da Silva"],
            "CPF": ["000.000.000-00"],
        }
    )

    resultado = aplicar_permissao(df, tipo="ciclo")

    assert "NOME_RESPONSAVEL" not in resultado.columns
    assert "CPF" not in resultado.columns
    assert list(resultado.columns) == ["CODIGO_CICLO_MATRICULA", "CO_UNIDADE"]


def test_aplicar_permissao_mantem_so_colunas_presentes_e_permitidas_e_renomeia():
    import pandas as pd

    df = pd.DataFrame(
        {
            "CO_MATRICULA": ["10"],
            "CO_CICLO_MATRICULA": ["1"],
            "NU_CPF": ["11111111111"],
            "COLUNA_DESCONHECIDA_NOVA_DO_SISTEC": ["x"],
        }
    )

    resultado = aplicar_permissao(df, tipo="matricula")

    assert list(resultado.columns) == ["CO_MATRICULA", "CODIGO_CICLO_MATRICULA"]


def test_aplicar_permissao_tipo_invalido_levanta_erro():
    import pandas as pd

    df = pd.DataFrame({"x": [1]})
    try:
        aplicar_permissao(df, tipo="outro")
    except ValueError:
        pass
    else:
        raise AssertionError("esperava ValueError para tipo desconhecido")
