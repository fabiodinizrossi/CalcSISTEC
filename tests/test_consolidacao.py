"""Testes de `app/sistec/consolidacao.py` (`002-baixador-planilhas-sistec`,
T021): assinatura de cabeçalho, junção pelo código do ciclo,
`STATUS_MATRICULA_PNP` nulo, renomeio para nomes internos."""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.sistec.consolidacao import (  # noqa: E402
    ConsolidacaoInvalida,
    consolidar,
    empilhar,
    montar_matriculas_e_eficiencia,
)


def _linha_ciclo(**overrides):
    base = {
        "CODIGO_CICLO_MATRICULA": "C1",
        "CO_UNIDADE": "U1",
        "CÓDIGO DO PORTFÓLIO": "P1",
        "NOME_CURSO": "TÉCNICO EM X",
        "TIPO_CURSO": "TECNICO",
        "CARGA_HORARIA_TOTAL": 1200,
        "MODALIDADE_ENSINO": "PRESENCIAL",
        "OFERTA": "ANUAL",
        "EIXO_TECNOLOGICO": "EIXO1",
        "TIPO_PROGRAMA_CURSO": "REGULAR",
        "DT_DATA_INICIO": "2026-01-01",
        "DT_DATA_FIM_PREVISTO": "2027-01-01",
        "STATUS_CICLO": "ATIVO",
        "SITUACAO_CICLO": "ATIVO",
    }
    base.update(overrides)
    return base


def _linha_matricula(**overrides):
    base = {
        "CO_MATRICULA": "M1",
        "CODIGO_CICLO_MATRICULA": "C1",
        "STATUS_MATRICULA_SISTEC": "EM_CURSO",
        "MES_OCORRENCIA_CORRIGIDO": "2026-01-01",
    }
    base.update(overrides)
    return base


def test_empilhar_junta_pares_com_mesma_assinatura():
    df1 = pd.DataFrame([_linha_ciclo(CODIGO_CICLO_MATRICULA="C1")])
    df2 = pd.DataFrame([_linha_ciclo(CODIGO_CICLO_MATRICULA="C2", CO_UNIDADE="U2")])
    resultado = empilhar([df1, df2], "ciclo")
    assert len(resultado) == 2


def test_empilhar_recusa_assinatura_diferente():
    df1 = pd.DataFrame([_linha_ciclo()])
    df2 = pd.DataFrame([{"OUTRA_COLUNA": 1}])
    with pytest.raises(ConsolidacaoInvalida):
        empilhar([df1, df2], "ciclo")


def test_consolidar_cria_status_matricula_pnp_nulo_e_corrige_pelo_sistec():
    ciclos = pd.DataFrame([_linha_ciclo()])
    matriculas = pd.DataFrame([_linha_matricula(STATUS_MATRICULA_SISTEC="EM_CURSO")])
    resultado = consolidar([ciclos], [matriculas])
    assert resultado["matriculas"].loc[0, "status_corrigido"] == "EM_CURSO"


def test_consolidar_mantem_varias_matriculas_do_mesmo_ciclo():
    ciclos = pd.DataFrame([_linha_ciclo()])
    matriculas = pd.DataFrame(
        [
            _linha_matricula(CO_MATRICULA="M1"),
            _linha_matricula(CO_MATRICULA="M2"),
            _linha_matricula(CO_MATRICULA="M3"),
        ]
    )
    resultado = consolidar([ciclos], [matriculas])
    assert sorted(resultado["matriculas"]["CO_MATRICULA"]) == ["M1", "M2", "M3"]


def test_consolidar_filtra_ciclo_excluido():
    ciclos = pd.DataFrame([_linha_ciclo(STATUS_CICLO="EXCLUÍDO")])
    resultado = consolidar([ciclos], [])
    assert resultado["ciclos"].empty


def test_consolidar_filtra_situacao_excluida():
    ciclos = pd.DataFrame([_linha_ciclo(SITUACAO_CICLO="EXCLUÍDO")])
    resultado = consolidar([ciclos], [])
    assert resultado["ciclos"].empty


def test_consolidar_deduplica_ciclo_repetido_com_conteudo_identico():
    ciclos = pd.DataFrame([_linha_ciclo(), _linha_ciclo()])
    resultado = consolidar([ciclos], [])
    assert len(resultado["ciclos"]) == 1


def test_consolidar_falha_ciclo_repetido_com_conteudo_divergente():
    ciclos = pd.DataFrame([_linha_ciclo(NOME_CURSO="A"), _linha_ciclo(NOME_CURSO="B")])
    with pytest.raises(ConsolidacaoInvalida):
        consolidar([ciclos], [])


def test_consolidar_falha_portfolio_com_unidade_divergente():
    """P-07: mesmo CÓDIGO DO PORTFÓLIO em campi diferentes."""
    ciclos = pd.DataFrame(
        [
            _linha_ciclo(CODIGO_CICLO_MATRICULA="C1", CO_UNIDADE="U1"),
            _linha_ciclo(CODIGO_CICLO_MATRICULA="C2", CO_UNIDADE="U2"),
        ]
    )
    with pytest.raises(ConsolidacaoInvalida):
        consolidar([ciclos], [])


def test_consolidar_sem_par_de_ciclo_falha():
    with pytest.raises(ConsolidacaoInvalida):
        consolidar([], [])


def test_montar_matriculas_e_eficiencia_junta_pelo_ciclo():
    ciclos = pd.DataFrame([_linha_ciclo()])
    matriculas = pd.DataFrame(
        [_linha_matricula(STATUS_MATRICULA_SISTEC="EM_CURSO")]
    ).assign(status_corrigido="EM_CURSO")

    matriculas_final, eficiencia_final = montar_matriculas_e_eficiencia(matriculas, ciclos, ano_base=2026)
    assert len(matriculas_final) == 1  # EM_CURSO sempre entra em T-07
    assert eficiencia_final.empty  # dt_data_fim_previsto=2027, ano_base-1=2025
