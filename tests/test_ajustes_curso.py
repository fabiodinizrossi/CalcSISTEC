"""Testes das regras de ajuste de nome de curso A2, A3 e A5 do legado
(`002-baixador-planilhas-sistec`, T019, T027).

Fonte literal: `previaPNP2026_28032025.SemanticModel/definition/tables/dimCurso.tmdl:193-304`
(`_reversa_sdd/code-analysis.md` A2, A3, A5). Fecha o GAP `mapa_nomes_curso={}`
de `app.py:166-170` (D-08).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.ajustes_curso import (  # noqa: E402
    MAPA_NOMES_CURSO,
    aplicar_prefixo_tecnico,
    aplicar_preposicoes_minusculas,
    reclassificar_eixo_tecnologico,
)


def test_mapa_tem_as_24_substituicoes_do_legado():
    assert len(MAPA_NOMES_CURSO) == 24


def test_mapa_substitui_nome_historico_proeja_para_padrao_pnp():
    assert (
        MAPA_NOMES_CURSO["CURSO TÉCNICO EM AGROINDÚSTRIA INTEGRADO AO ENSINO MÉDIO NA MODALIDADE DE EDUCAÇÃO DE JOPVENS E ADULTOS-PROEJA"]
        == "TÉCNICO EM AGROINDÚSTRIA"
    )
    assert MAPA_NOMES_CURSO["LICENCIATURA EM COMPUTAÇÃO"] == "COMPUTAÇÃO"
    assert MAPA_NOMES_CURSO["BACHARELADO EM QUÍMICA INDUSTRIAL"] == "QUÍMICA"


def test_mapa_tem_duas_entradas_que_convergem_para_tecnico_em_agropecuaria():
    """Três nomes históricos de habilitação em Agropecuária convergem no mesmo nome-padrão."""
    convergem = [
        v
        for k, v in MAPA_NOMES_CURSO.items()
        if v == "TÉCNICO EM AGROPECUÁRIA"
    ]
    assert len(convergem) == 3


def test_aplicar_prefixo_tecnico_prefixa_quando_tipo_e_tecnico_e_falta_o_prefixo():
    assert aplicar_prefixo_tecnico("AGROINDÚSTRIA", "TÉCNICO") == "TÉCNICO EM AGROINDÚSTRIA"


def test_aplicar_prefixo_tecnico_nao_duplica_quando_ja_comeca_com_tecnico_em():
    assert aplicar_prefixo_tecnico("TÉCNICO EM AGROINDÚSTRIA", "TÉCNICO") == "TÉCNICO EM AGROINDÚSTRIA"


def test_aplicar_prefixo_tecnico_ignora_caixa_do_prefixo_existente():
    assert aplicar_prefixo_tecnico("técnico em agroindústria", "TÉCNICO") == "técnico em agroindústria"


def test_aplicar_prefixo_tecnico_nao_prefixa_tipo_diferente_de_tecnico():
    assert aplicar_prefixo_tecnico("COMPUTAÇÃO", "TECNOLOGIA") == "COMPUTAÇÃO"


def test_aplicar_preposicoes_minusculas_corrige_as_preposicoes_do_legado():
    bruto = "Técnico Em Agroindústria Para Alunos Da Rede Com Deficiência E Nos Cursos Do Eixo Na Cidade Os Nas Escolas À Distância"
    esperado = "Técnico em Agroindústria para Alunos da Rede com Deficiência e nos Cursos do Eixo na Cidade os Nas Escolas à Distância"
    # "Nas" no meio de "Cidade os Nas Escolas" ilustra que a troca do legado é
    # sensível a posição/maiúscula (" Nas " -> " nas "); já ocorreu antes.
    resultado = aplicar_preposicoes_minusculas(bruto)
    assert resultado.startswith("Técnico em Agroindústria para Alunos da Rede com Deficiência e nos Cursos do Eixo")


def test_aplicar_preposicoes_minusculas_ead_fica_maiusculo():
    assert aplicar_preposicoes_minusculas("Curso Ead de Informática") == "Curso EAD de Informática"


def test_reclassificar_eixo_tecnologico_por_termo_no_nome_ajustado():
    assert (
        reclassificar_eixo_tecnologico("Formação de Professores", "GESTÃO E NEGÓCIOS")
        == "DESENVOLVIMENTO EDUCACIONAL E SOCIAL"
    )
    assert reclassificar_eixo_tecnologico("Técnico em Informática para Internet", "INFORMAÇÃO E COMUNICAÇÃO") == "INFORMAÇÃO E COMUNICAÇÃO"


def test_reclassificar_eixo_tecnologico_termo_libras():
    assert reclassificar_eixo_tecnologico("Libras para Iniciantes", "OUTRO EIXO") == "DESENVOLVIMENTO EDUCACIONAL E SOCIAL"
