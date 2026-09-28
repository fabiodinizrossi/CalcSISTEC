"""Testes de `app/data/fatores.py` (`002-baixador-planilhas-sistec`, T016-T018).

T016: casamento por tipo+nome (D-07), os 3 tipos só-pelo-tipo, curso sem
casamento vira `fator_nao_encontrado`.
T017: conversão de tipos do arquivo de fatores (D-09), tipos sem
correspondência mantidos com aviso.
T018: validação do arquivo (RN-34/RN-35): aba certa por cabeçalho, campos
obrigatórios, duplicidade por chave, tipo só-pelo-tipo com mais de uma linha
recusa o arquivo (D-10).
"""

import os
import sys
import tempfile

import openpyxl
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.fatores import (  # noqa: E402
    ArquivoFatoresInvalido,
    casar_fatores,
    diferenca_fatores,
    ler_e_validar,
)
from app.data.schema import normalizar  # noqa: E402


def _escrever_xlsx(linhas, cabecalho=("TIPO DE CURSO", "CURSO", "FEC", "FECH"), aba="Fatores"):
    fd, caminho = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = aba
    ws.append(list(cabecalho))
    for linha in linhas:
        ws.append(list(linha))
    wb.save(caminho)
    return caminho


# ===================== T018: validação (RN-34/RN-35/D-10) =====================


def test_le_e_valida_arquivo_bem_formado():
    caminho = _escrever_xlsx([("TÉCNICO", "TÉCNICO EM INFORMÁTICA", 1.0, 1.0)])
    try:
        linhas, avisos = ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert len(linhas) == 1
    assert linhas[0][0] == "TÉCNICO"
    assert avisos == []


def test_recusa_arquivo_sem_aba_com_as_4_colunas():
    caminho = _escrever_xlsx([("a", "b", "c", "d")], cabecalho=("X", "Y", "Z", "W"))
    try:
        with pytest.raises(ArquivoFatoresInvalido) as exc:
            ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert "nenhuma aba" in exc.value.erros[0]


def test_recusa_tipo_de_curso_vazio():
    caminho = _escrever_xlsx([(None, "CURSO X", 1.0, 1.0)])
    try:
        with pytest.raises(ArquivoFatoresInvalido) as exc:
            ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert "TIPO DE CURSO vazio" in exc.value.erros[0]


def test_recusa_fec_nao_numerico():
    caminho = _escrever_xlsx([("TÉCNICO", "CURSO X", "abc", 1.0)])
    try:
        with pytest.raises(ArquivoFatoresInvalido) as exc:
            ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert "FEC" in exc.value.erros[0]


def test_recusa_linhas_repetidas_por_chave_apos_conversao():
    caminho = _escrever_xlsx(
        [
            ("TÉCNICO", "TÉCNICO EM INFORMÁTICA", 1.0, 1.0),
            ("técnico", "  técnico   em  informática  ", 1.1, 1.0),
        ]
    )
    try:
        with pytest.raises(ArquivoFatoresInvalido) as exc:
            ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert "chave repetida" in exc.value.erros[0]


def test_tipo_so_pelo_tipo_com_mais_de_uma_linha_recusa_arquivo():
    """D-10: dois nomes diferentes do mesmo tipo só-pelo-tipo colapsam para a
    mesma chave (chave_nome='') e violam a mesma regra de RN-35."""
    caminho = _escrever_xlsx(
        [
            ("QUALIFICAÇÃO PROFISSIONAL", "CURSO A", 1.0, 1.0),
            ("QUALIFICAÇÃO PROFISSIONAL", "CURSO B", 1.2, 1.0),
        ]
    )
    try:
        with pytest.raises(ArquivoFatoresInvalido) as exc:
            ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert "chave repetida" in exc.value.erros[0]


# ===================== T017: conversão de tipos (D-09) =====================


def test_conversao_especializacao_lato_sensu_profissional_tecnologica():
    caminho = _escrever_xlsx(
        [("ESPECIALIZAÇÃO (LATO SENSU/PROFISSIONAL TECNOLÓGICA)", "QUALQUER", 1.0, 1.0)]
    )
    try:
        linhas, _avisos = ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert linhas[0][0] == "ESPECIALIZAÇÃO (LATO SENSU)"
    assert linhas[0][1] == "TODOS"  # só-pelo-tipo
    assert linhas[0][5] == ""  # chave_nome


def test_conversao_mestrado_academico_profissional():
    caminho = _escrever_xlsx([("MESTRADO (ACADÊMICO/PROFISSIONAL)", "QUALQUER", 1.0, 1.0)])
    try:
        linhas, _avisos = ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert linhas[0][0] == "MESTRADO PROFISSIONAL"


def test_tipo_sem_correspondencia_no_sistec_e_mantido_com_aviso():
    caminho = _escrever_xlsx([("ENSINO MÉDIO", "CURSO X", 1.0, 1.0)])
    try:
        linhas, avisos = ler_e_validar(caminho)
    finally:
        os.remove(caminho)
    assert len(linhas) == 1  # mantido
    assert "ENSINO MÉDIO" in avisos


# ===================== T016: casamento por tipo+nome (D-07) =====================


def _df_fatores(linhas):
    return pd.DataFrame(linhas, columns=["tipo_curso", "nome_curso", "fec", "fech", "chave_tipo", "chave_nome"])


def test_casar_fatores_por_tipo_e_nome():
    df_cursos = pd.DataFrame(
        {
            "tipo_curso_pnp": ["TÉCNICO"],
            "nome_curso_ajustado": ["Técnico em Informática"],
        }
    )
    df_fatores = _df_fatores(
        [("TÉCNICO", "TÉCNICO EM INFORMÁTICA", 1.5, 1.2, normalizar("TÉCNICO"), normalizar("TÉCNICO EM INFORMÁTICA"))]
    )
    resultado = casar_fatores(df_cursos, df_fatores)
    assert resultado.loc[0, "fec"] == 1.5
    assert resultado.loc[0, "fech"] == 1.2
    assert resultado.loc[0, "fator_nao_encontrado"] == 0


def test_casar_fatores_tipos_so_pelo_tipo_ignoram_o_nome():
    df_cursos = pd.DataFrame(
        {
            "tipo_curso_pnp": ["QUALIFICAÇÃO PROFISSIONAL"],
            "nome_curso_ajustado": ["Qualquer Nome de Curso FIC"],
        }
    )
    df_fatores = _df_fatores([("QUALIFICAÇÃO PROFISSIONAL", "TODOS", 2.0, 1.0, normalizar("QUALIFICAÇÃO PROFISSIONAL"), "")])
    resultado = casar_fatores(df_cursos, df_fatores)
    assert resultado.loc[0, "fec"] == 2.0
    assert resultado.loc[0, "fator_nao_encontrado"] == 0


def test_casar_fatores_sem_casamento_usa_default_e_sinaliza():
    df_cursos = pd.DataFrame(
        {
            "tipo_curso_pnp": ["TÉCNICO"],
            "nome_curso_ajustado": ["Curso Inexistente Na Tabela"],
        }
    )
    df_fatores = _df_fatores([("TÉCNICO", "OUTRO CURSO", 1.5, 1.2, normalizar("TÉCNICO"), normalizar("OUTRO CURSO"))])
    resultado = casar_fatores(df_cursos, df_fatores)
    assert resultado.loc[0, "fec"] == 1.0
    assert resultado.loc[0, "fech"] == 1.0
    assert resultado.loc[0, "fator_nao_encontrado"] == 1


def test_diferenca_fatores_identifica_incluidas_removidas_alteradas():
    atuais = _df_fatores(
        [
            ("TÉCNICO", "A", 1.0, 1.0, "TECNICO", "A"),
            ("TÉCNICO", "B", 1.0, 1.0, "TECNICO", "B"),
        ]
    ).itertuples(index=False)
    novas = _df_fatores(
        [
            ("TÉCNICO", "A", 1.5, 1.0, "TECNICO", "A"),
            ("TÉCNICO", "C", 1.0, 1.0, "TECNICO", "C"),
        ]
    ).itertuples(index=False)
    resultado = diferenca_fatores(list(atuais), list(novas))
    assert resultado["incluidas"] == [{"chave": ("TECNICO", "C"), "fec": 1.0, "fech": 1.0}]
    assert resultado["removidas"] == [{"chave": ("TECNICO", "B"), "fec": 1.0, "fech": 1.0}]
    assert resultado["alteradas"] == [{"chave": ("TECNICO", "A"), "antes": (1.0, 1.0), "depois": (1.5, 1.0)}]
