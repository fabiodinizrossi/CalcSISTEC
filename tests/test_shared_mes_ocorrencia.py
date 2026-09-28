"""Testes de `app.domain.shared.parsear_mes_ocorrencia` (MAT-01, AC2/AC4).

O Sistec exporta `MES_DE_OCORRENCIA` por extenso em português ("JUNHO 2026").
`pd.to_datetime(..., errors="coerce")` devolvia `NaT` para 100% dessas linhas —
é a causa raiz da divergência de contagem de matrículas atendidas contra o
painel legado. Estes testes fixam o contrato: 12 meses reconhecidos (com e sem
cedilha em MARÇO/MARCO), mesmo índice da entrada, e `NaT` — nunca exceção —
para qualquer valor fora do padrão (`RISK-002`).

Rodar com: `pytest tests/test_shared_mes_ocorrencia.py -v`
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.domain.shared import MESES_PT, parsear_mes_ocorrencia  # noqa: E402

# MAT-01 AC2: os 12 nomes de mês como o Sistec exporta.
NOMES_PT = [
    "JANEIRO",
    "FEVEREIRO",
    "MARÇO",
    "ABRIL",
    "MAIO",
    "JUNHO",
    "JULHO",
    "AGOSTO",
    "SETEMBRO",
    "OUTUBRO",
    "NOVEMBRO",
    "DEZEMBRO",
]


@pytest.mark.parametrize("numero, nome", list(enumerate(NOMES_PT, start=1)))
def test_reconhece_os_doze_meses_em_portugues(numero, nome):
    """MAT-01 AC2: o mês vira o dia 1 daquele mês, e o ano do texto é o ano
    extraído (AC1: o ano é o que decide "cai no ano-base")."""
    resultado = parsear_mes_ocorrencia(pd.Series([f"{nome} 2026"]))

    assert resultado.iloc[0] == pd.Timestamp(year=2026, month=numero, day=1)
    assert int(resultado.dt.year.iloc[0]) == 2026


def test_marco_sem_cedilha_e_reconhecido_como_marco():
    """Edge case de `spec.md`: exportações do Sistec variam na acentuação."""
    resultado = parsear_mes_ocorrencia(pd.Series(["MARCO 2026"]))

    assert resultado.iloc[0] == pd.Timestamp(year=2026, month=3, day=1)


def test_marco_com_cedilha_e_reconhecido_como_marco():
    resultado = parsear_mes_ocorrencia(pd.Series(["MARÇO 2026"]))

    assert resultado.iloc[0] == pd.Timestamp(year=2026, month=3, day=1)


def test_mes_minusculo_com_espacos_e_reconhecido():
    """O Sistec exporta em maiúsculas, mas normalizar antes evita depender disso."""
    resultado = parsear_mes_ocorrencia(pd.Series(["  junho 2026  "]))

    assert resultado.iloc[0] == pd.Timestamp(year=2026, month=6, day=1)


def test_ano_de_ocorrencia_e_o_do_texto_nao_o_do_indice():
    """MAT-01 AC1: a decisão de "cai no ano-base" depende só do ano do texto."""
    serie = pd.Series(["DEZEMBRO 2025", "JANEIRO 2020", "AGOSTO 2031"])

    resultado = parsear_mes_ocorrencia(serie)

    assert list(resultado.dt.year) == [2025, 2020, 2031]


def test_indice_da_entrada_e_preservado():
    """O chamador (`t07`, `contar_ingressantes`) faz `&`/`|` com máscaras da
    mesma linha — índice desalinhado corromperia a contagem."""
    serie = pd.Series(["JUNHO 2026", "DEZEMBRO 2025"], index=[42, 7])

    resultado = parsear_mes_ocorrencia(serie)

    assert list(resultado.index) == [42, 7]


@pytest.mark.parametrize(
    "valor",
    [
        None,
        pd.NA,
        float("nan"),
        "",
        "   ",
        "LIXO",
        "2026",
        "JUNHO",
        "JUNHO 26",
        "06/2026",
        "2026-06-01",
        "JUNHO 2026 DEZEMBRO",
        13,
    ],
)
def test_valor_fora_do_padrao_vira_nat_sem_excecao(valor):
    """MAT-01 AC4 e `RISK-002`: entrada ruim não levanta exceção nem inventa
    data — vira `NaT` e a matrícula simplesmente não conta por essa via."""
    resultado = parsear_mes_ocorrencia(pd.Series([valor]))

    assert resultado.iloc[0] is pd.NaT


def test_serie_vazia_devolve_serie_vazia():
    """Edge case de `spec.md`: lote vazio não pode quebrar a ingestão."""
    resultado = parsear_mes_ocorrencia(pd.Series([], dtype=object))

    assert len(resultado) == 0
    assert resultado.dtype.kind == "M"


def test_serie_mista_mantem_posicao_dos_invalidos():
    """Válidos e inválidos na mesma série: cada linha decide por si."""
    serie = pd.Series(["JUNHO 2026", "LIXO", "DEZEMBRO 2025", None])

    resultado = parsear_mes_ocorrencia(serie)

    assert list(resultado) == [
        pd.Timestamp(year=2026, month=6, day=1),
        pd.NaT,
        pd.Timestamp(year=2025, month=12, day=1),
        pd.NaT,
    ]


def test_meses_pt_cobre_doze_meses_com_a_variante_sem_cedilha():
    """O dicionário é a fonte única do parse: 12 meses + `MARCO`."""
    assert sorted(set(MESES_PT.values())) == list(range(1, 13))
    assert MESES_PT["MARÇO"] == MESES_PT["MARCO"] == 3
    assert len(MESES_PT) == 13
