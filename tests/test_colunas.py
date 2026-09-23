"""Testes da lista de permissão de colunas do Sistec (`002-baixador-planilhas-sistec`, T020, T026).

RN-17: só as colunas de interesse entram no conjunto consolidado; qualquer
coluna fora da lista de permissão é descartada antes da prévia, e isso inclui
obrigatoriamente todas as colunas de dado pessoal (defesa em profundidade,
D-04, `data-delta.md` §4).
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.transform import COLUNAS_PII  # noqa: E402
from app.sistec.colunas import (  # noqa: E402
    COLUNAS_CICLO,
    COLUNAS_MATRICULA,
    aplicar_permissao,
    ler_planilha,
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


@pytest.mark.parametrize(
    ("tipo", "colunas", "esperadas"),
    [
        ("ciclo", COLUNAS_CICLO, list(COLUNAS_CICLO.values())),
        ("matricula", COLUNAS_MATRICULA, list(COLUNAS_MATRICULA.values())),
    ],
)
def test_ler_planilha_le_os_dois_tipos_com_colunas_permitidas(tipo, colunas, esperadas):
    conteudo = pd.DataFrame([{coluna: "valor" for coluna in colunas}]).to_csv(sep=";", index=False).encode("cp1252")

    resultado = ler_planilha(conteudo, tipo)

    assert list(resultado.columns) == esperadas
    assert resultado.iloc[0].tolist() == ["valor"] * len(esperadas)


def test_ler_planilha_recusa_coluna_obrigatoria_ausente():
    conteudo = pd.DataFrame([{next(iter(COLUNAS_CICLO)): "C1"}]).to_csv(sep=";", index=False).encode("cp1252")

    with pytest.raises(ValueError, match="^colunas_ausentes$"):
        ler_planilha(conteudo, "ciclo")


def test_ler_planilha_recusa_csv_que_nao_pode_ser_lido():
    """Arquivo truncado/vazio continua sendo recusado como `leitura_csv`.

    Antes desta feature o caso era `b"\\x81"` (um byte sozinho), que falhava por
    `UnicodeDecodeError`. Com a decodificação tolerante esse byte vira `�` e o
    arquivo deixa de ser ilegível por codificação — então a entrada aqui passa a
    ser o que segue ilegível de fato: um arquivo sem nenhum conteúdo.
    """
    with pytest.raises(ValueError, match="^leitura_csv$"):
        ler_planilha(b"", "ciclo")


# --- Decodificação tolerante a bytes fora do cp1252 (CEP-04, CEP-05) ---------
#
# O defeito original foi reproduzido com um export real do Sistec de um único
# byte 0x81 (indefinido em cp1252) numa coluna descartada. O arquivo real
# contém nome de mãe de estudantes e não entra no repositório: os casos abaixo
# usam um CSV sintético de mesmo formato, com o byte inserido no lugar do
# arquivo real.

_BYTE_INVALIDO = b"\x81"

_CABECALHO_MATRICULA = "CO_MATRICULA;CO_CICLO_MATRICULA;NO_STATUS_MATRICULA;MES_DE_OCORRENCIA;NO_MAE_ALUNO"


def _matricula_sintetica(no_mae_aluno, status="MATRICULADO", cabecalho=_CABECALHO_MATRICULA):
    """CSV do Sistec em bytes crus, com `no_mae_aluno` como bytes (aceita 0x81)."""
    linha = b"10;1;" + status.encode("latin-1") + b";2024-01;" + no_mae_aluno
    return cabecalho.encode("cp1252") + b"\n" + linha + b"\n"


def test_ler_planilha_le_arquivo_com_byte_invalido_em_coluna_descartada():
    """CEP-04: o byte 0x81 numa coluna fora da lista de permissão não impede a
    leitura, e a coluna inteira continua descartada por `aplicar_permissao`."""
    conteudo = _matricula_sintetica(b"MARIA DA SIL" + _BYTE_INVALIDO + b"VA")

    resultado = ler_planilha(conteudo, "matricula")

    assert list(resultado.columns) == list(COLUNAS_MATRICULA.values())
    assert "NO_MAE_ALUNO" not in resultado.columns
    assert resultado.iloc[0]["CO_MATRICULA"] == "10"
    assert resultado.iloc[0]["STATUS_MATRICULA_SISTEC"] == "MATRICULADO"


def test_ler_planilha_troca_o_byte_invalido_por_caractere_de_substituicao_em_coluna_mantida():
    """CEP-04: byte inválido dentro de uma coluna mantida é lido com `�` no
    lugar do byte, sem lançar exceção (risco aceito por decisão da spec)."""
    conteudo = _matricula_sintetica(b"MARIA DA SILVA", status="MATRICULAD" + "\x81" + "O")

    resultado = ler_planilha(conteudo, "matricula")

    assert resultado.iloc[0]["STATUS_MATRICULA_SISTEC"] == "MATRICULAD�O"


def test_ler_planilha_com_byte_invalido_iguala_o_resultado_do_arquivo_sem_o_byte():
    """CEP-04 AC 2: o byte numa coluna descartada não muda nenhuma coluna usada."""
    com_byte = _matricula_sintetica(b"MARIA DA SIL" + _BYTE_INVALIDO + b"VA")
    sem_byte = _matricula_sintetica(b"MARIA DA SILVA")

    assert ler_planilha(com_byte, "matricula").equals(ler_planilha(sem_byte, "matricula"))


def test_ler_planilha_mantem_os_valores_de_arquivo_sem_byte_invalido():
    """Não regressão: arquivo todo em cp1252 válido sai igual ao de antes."""
    conteudo = _matricula_sintetica(b"MARIA DA SILVA")

    resultado = ler_planilha(conteudo, "matricula")

    esperado = pd.DataFrame(
        [{"CO_MATRICULA": "10", "CODIGO_CICLO_MATRICULA": "1", "STATUS_MATRICULA_SISTEC": "MATRICULADO", "MES_OCORRENCIA_CORRIGIDO": "2024-01"}]
    )
    assert list(resultado.columns) == list(esperado.columns)
    pd.testing.assert_frame_equal(resultado.reset_index(drop=True), esperado)


def test_ler_planilha_recusa_coluna_obrigatoria_ausente_mesmo_com_byte_invalido():
    """CEP-05: cabeçalho sem coluna obrigatória continua sendo `colunas_ausentes`,
    mesmo com byte fora do cp1252 em outra coluna do arquivo."""
    cabecalho = "CO_MATRICULA;CO_CICLO_MATRICULA;NO_STATUS_MATRICULA;NO_MAE_ALUNO"
    conteudo = _matricula_sintetica(b"MARIA DA SIL" + _BYTE_INVALIDO + b"VA", cabecalho=cabecalho)

    with pytest.raises(ValueError, match="^colunas_ausentes$"):
        ler_planilha(conteudo, "matricula")


def test_ler_planilha_recusa_arquivo_estruturalmente_quebrado_apos_decodificacao_tolerante():
    """CEP-05 AC 3: arquivo que continua impasseável depois da decodificação
    tolerante segue recusado como `leitura_csv`."""
    conteudo = _CABECALHO_MATRICULA.encode("cp1252") + b'\n10;1;"MATRICULADO;2024-01\n'

    with pytest.raises(ValueError, match="^leitura_csv$"):
        ler_planilha(conteudo, "matricula")


def test_ler_planilha_recusa_arquivo_com_delimitador_errado():
    """CEP-05: delimitador errado continua recusado — o arquivo inteiro vira uma
    única coluna, então as colunas obrigatórias não são encontradas."""
    conteudo = _CABECALHO_MATRICULA.replace(";", ",").encode("cp1252") + b"\n10,1,MATRICULADO,2024-01,MARIA DA SILVA\n"

    with pytest.raises(ValueError, match="^colunas_ausentes$"):
        ler_planilha(conteudo, "matricula")
