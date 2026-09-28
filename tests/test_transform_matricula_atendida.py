"""Testes de `app.data.transform.t07_grao_matricula_atendida` (BR-MIGRAR-001,
MAT-01) — a regra "matrícula atendida".

Causa raiz da divergência contra o painel legado: a coluna
`mes_ocorrencia_corrigido` chega do Sistec como texto em português
("JUNHO 2026"), que `pd.to_datetime` não reconhece; com `errors="coerce"` o
parse falhava em 100% das linhas, e toda matrícula que não estava `EM_CURSO` só
era contada pelo ciclo. A regra real é: `EM_CURSO` sempre conta; qualquer outra
situação conta se o mês de ocorrência é do ano-base, mesmo com ciclo de outro
ano.

Rodar com: `pytest tests/test_transform_matricula_atendida.py -v`
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.transform import t07_grao_matricula_atendida  # noqa: E402

ANO_BASE = 2026


def _df(*linhas):
    """Uma linha por matrícula: `dt_data_inicio` do ciclo, status corrigido e
    `mes_ocorrencia_corrigido` como o Sistec exporta (texto em português)."""
    return pd.DataFrame(
        [
            {
                "dt_data_inicio": dt_inicio,
                "status_corrigido": status,
                "mes_ocorrencia_corrigido": mes_ocorrencia,
            }
            for dt_inicio, status, mes_ocorrencia in linhas
        ]
    )


def test_concluida_com_mes_de_ocorrencia_no_ano_base_conta_com_ciclo_antigo():
    """MAT-01 AC1: o caso que hoje quebra — ciclo de 2024, conclusão em 2026.
    Sem o parse do mês em português esta linha era descartada."""
    df = _df(("2024-03-10", "CONCLUÍDA", "JUNHO 2026"))

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 1


def test_mes_de_ocorrencia_de_ano_anterior_nao_conta_fora_de_em_curso():
    """MAT-01 AC1: a via do mês é do ano-base, não "a partir do ano-base"."""
    df = _df(("2024-03-10", "CONCLUÍDA", "DEZEMBRO 2025"))

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 0


def test_em_curso_conta_sempre_independente_de_ciclo_e_mes():
    """MAT-01 AC3: comportamento já existente, não muda."""
    df = _df(
        ("2019-03-10", "EM_CURSO", "DEZEMBRO 2025"),
        ("2019-03-10", "EM_CURSO", None),
        ("2019-03-10", "EM_CURSO", "LIXO"),
    )

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 3


def test_ciclo_iniciado_no_ano_base_conta_com_status_nao_em_curso():
    """MAT-01: a via do ciclo continua valendo (abandono com ciclo de 2026)."""
    df = _df(
        ("2026-02-01", "ABANDONO", "DEZEMBRO 2025"),
        ("2026-02-01", "ABANDONO", None),
    )

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 2


def test_mes_com_cedilha_e_sem_cedilha_contam_igual():
    """Edge case de `spec.md`: exportações do Sistec variam na acentuação."""
    df = _df(
        ("2024-03-10", "CONCLUÍDA", "MARÇO 2026"),
        ("2024-03-10", "CONCLUÍDA", "MARCO 2026"),
    )

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 2


def test_mes_no_ano_base_com_ciclo_de_data_nula_conta():
    """Edge case de `spec.md`: a via do mês não depende do ciclo."""
    df = _df((None, "CONCLUÍDA", "JANEIRO 2026"))

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 1


def test_todas_em_curso_mantem_o_total():
    """Edge case de `spec.md`: nenhuma via de mês/ciclo muda o resultado."""
    df = _df(
        ("2019-03-10", "EM_CURSO", "DEZEMBRO 2025"),
        ("2024-03-10", "EM_CURSO", "JUNHO 2026"),
        (None, "EM_CURSO", None),
    )

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 3


@pytest.mark.parametrize("mes_ocorrencia", [None, pd.NA, "", "LIXO", "2026", "JUNHO", "06/2026"])
def test_mes_invalido_com_ciclo_de_outro_ano_nao_conta_sem_excecao(mes_ocorrencia):
    """MAT-01 AC4 e `RISK-002`: entrada ruim não levanta exceção — a matrícula
    simplesmente não conta por essa via."""
    df = _df(("2024-03-10", "CONCLUÍDA", mes_ocorrencia))

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert len(resultado) == 0


def test_ano_base_diferente_so_reconhece_o_proprio_ano():
    """MAT-01 AC1: o ano-base é parâmetro explícito (BR-MIGRAR-016)."""
    df = _df(
        ("2024-03-10", "CONCLUÍDA", "JUNHO 2026"),
        ("2024-03-10", "CONCLUÍDA", "JUNHO 2025"),
    )

    resultado = t07_grao_matricula_atendida(df, 2025)

    assert len(resultado) == 1


def test_dataframe_vazio_devolve_vazio():
    """Edge case de `spec.md`: lote vazio não quebra a ingestão. O DataFrame
    chega com as colunas tipadas (como `montar_matriculas_e_eficiencia` o
    devolve quando o lote não tem matrícula nenhuma)."""
    vazio = pd.DataFrame(columns=["dt_data_inicio", "status_corrigido", "mes_ocorrencia_corrigido"])

    resultado = t07_grao_matricula_atendida(vazio, ANO_BASE)

    assert len(resultado) == 0
    assert list(resultado.columns) == ["dt_data_inicio", "status_corrigido", "mes_ocorrencia_corrigido"]


def test_mes_de_ocorrencia_nulo_nao_vira_linha_de_ano_zero():
    """`NaT.dt.year` é NaN/0: se a comparação de ano fosse ingênua, um mês
    inválido entraria como "ano-base 0" ou quebraria. Aqui não conta."""
    df = _df(("2000-03-10", "TRANSF_EXT", None), ("2000-03-10", "TRANSF_EXT", "JUNHO 2026"))

    resultado = t07_grao_matricula_atendida(df, ANO_BASE)

    assert list(resultado["mes_ocorrencia_corrigido"]) == ["JUNHO 2026"]
