"""Testes da preparação do candidato da prévia (`previa-paginas-publicas`, T1):
`preparar_versao` e `calcular_assinatura_origem` em `app/data/ingest.py`.

Cobrem PVP-03 (leitura sem escrita) e PVP-04 (paridade de dados): as quatro
tabelas preparadas são iguais às gravadas, campi preservados entram, `RISK-002`
(vazio, NaN, data nula) não diverge e a assinatura de origem é determinística.
"""

import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.ingest import (  # noqa: E402
    calcular_assinatura_origem,
    montar_versao_interna,
    preparar_versao,
)
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec.consolidacao import consolidar  # noqa: E402


@pytest.fixture
def db_path():
    path = os.path.join(tempfile.mkdtemp(), "candidato.db")
    init_db(path)
    return path


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


def _conjunto(ciclos=None, matriculas=None):
    return consolidar(
        [pd.DataFrame(ciclos or [_linha_ciclo()])],
        [pd.DataFrame(matriculas or [_linha_matricula()])],
    )


def _rev_interna(db_path):
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT rev_interna FROM estado_versoes WHERE id = 1").fetchone()[0]
    finally:
        conn.close()


def test_preparar_versao_nao_grava_nada(db_path):
    """PVP-03: a preparação é só leitura — nenhuma tabela interna muda nem a
    revisão avança."""
    preparar_versao(_conjunto(), (), db_path=db_path, ano_base=2026)

    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
    finally:
        conn.close()
    assert total == 0
    assert _rev_interna(db_path) == 0


def test_preparar_versao_tabelas_iguais_as_gravadas(db_path):
    """PVP-04: para os mesmos CSVs, as quatro tabelas preparadas em memória
    são iguais às gravadas por `montar_versao_interna` (round-trip pelo
    SQLite, incluindo a normalização de nulos)."""
    conjunto = _conjunto()
    candidato = preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)
    montar_versao_interna(conjunto, (), db_path=db_path, ano_base=2026)

    conn = get_connection(db_path)
    try:
        gravadas = {
            "cursos": pd.read_sql_query("SELECT * FROM interna_cursos", conn),
            "ciclos": pd.read_sql_query("SELECT * FROM interna_ciclos", conn),
            "matriculas": pd.read_sql_query("SELECT * FROM interna_matriculas", conn),
            "matriculas_eficiencia": pd.read_sql_query("SELECT * FROM interna_matriculas_eficiencia", conn),
        }
    finally:
        conn.close()

    for tabela in ("cursos", "ciclos", "matriculas", "matriculas_eficiencia"):
        preparada = candidato["tabelas"][tabela].reset_index(drop=True)
        gravada = gravadas[tabela].reset_index(drop=True)
        assert list(preparada.columns) == list(gravada.columns), tabela
        assert len(preparada) == len(gravada), tabela
        pd.testing.assert_frame_equal(preparada, gravada, check_dtype=False)


def test_preparar_versao_preserva_campus_falho(db_path):
    """PVP-04 AC3: as linhas internas de um campus ausente são preservadas na
    prévia exatamente como apareceriam na versão interna após Salvar."""
    # Semente: grava U1 na interna antes.
    montar_versao_interna(_conjunto(), (), db_path=db_path, ano_base=2026)

    # Novo envio só com U2; U1 é campus ausente (preservado).
    ciclo_novo = {
        **_linha_ciclo(),
        "CODIGO_CICLO_MATRICULA": "C2",
        "CO_UNIDADE": "U2",
        "CÓDIGO DO PORTFÓLIO": "P2",
    }
    matricula_nova = {**_linha_matricula(), "CO_MATRICULA": "M2", "CODIGO_CICLO_MATRICULA": "C2"}
    conjunto_novo = consolidar([pd.DataFrame([ciclo_novo])], [pd.DataFrame([matricula_nova])])

    candidato = preparar_versao(conjunto_novo, ["U1"], db_path=db_path, ano_base=2026)

    ciclos = candidato["tabelas"]["ciclos"]
    unidades = set(ciclos["co_unidade"])
    assert unidades == {"U1", "U2"}
    assert candidato["resumo"]["campi_mantidos"] == ["U1"]


def test_preparar_versao_ano_base_none_le_config(db_path):
    """Done-when: `ano_base=None` lê `config.ano_base` do banco."""
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE config SET valor = '2027' WHERE chave = 'ano_base'")
        conn.commit()
    finally:
        conn.close()

    candidato = preparar_versao(_conjunto(), (), db_path=db_path)
    assert candidato["ano_base"] == 2027


def test_preparar_versao_ano_base_explicito_prevalece(db_path):
    """Done-when: um valor explícito de `ano_base` prevalece sobre a config."""
    candidato = preparar_versao(_conjunto(), (), db_path=db_path, ano_base=2030)
    assert candidato["ano_base"] == 2030


def test_calcular_assinatura_origem_deterministica(db_path):
    """Done-when: a assinatura de origem é estável entre chamadas e traz as
    dependências (revisões, ano-base, fatores e campus publicado)."""
    montar_versao_interna(_conjunto(), (), db_path=db_path, ano_base=2026)

    primeira = calcular_assinatura_origem(db_path)
    segunda = calcular_assinatura_origem(db_path)

    assert primeira == segunda
    assert set(primeira) == {"rev_interna", "rev_publicada", "ano_base", "fatores", "campus"}
    assert primeira["rev_interna"] == 1
    assert primeira["ano_base"] == 2026


def test_preparar_versao_risco_002_vazio_nan_data_nula(db_path):
    """RISK-002: datas nulas e mês de ocorrência nulo não divergem nem
    derrubam a preparação — a célula fica nula na interna e NaT no candidato."""
    ciclo = _linha_ciclo(DT_DATA_INICIO=None, DT_DATA_FIM_PREVISTO=None)
    matricula = _linha_matricula(MES_OCORRENCIA_CORRIGIDO=None)
    conjunto = _conjunto([ciclo], [matricula])

    candidato = preparar_versao(conjunto, (), db_path=db_path, ano_base=2026)
    montar_versao_interna(conjunto, (), db_path=db_path, ano_base=2026)

    ciclos = candidato["tabelas"]["ciclos"]
    assert pd.isna(ciclos["dt_data_inicio"].iloc[0])
    assert pd.isna(ciclos["dt_data_fim_previsto"].iloc[0])

    conn = get_connection(db_path)
    try:
        inicio, fim = conn.execute(
            "SELECT dt_data_inicio, dt_data_fim_previsto FROM interna_ciclos WHERE codigo_ciclo_matricula='C1'"
        ).fetchone()
        mes = conn.execute(
            "SELECT mes_ocorrencia_corrigido FROM interna_matriculas WHERE co_matricula='M1'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert inicio is None and fim is None
    assert mes is None


def test_montar_versao_interna_mantem_retorno_e_grava(db_path):
    """Done-when: `montar_versao_interna` mantém o resumo atual e continua
    gravando via `salvar_interna` (rev_interna incrementada)."""
    resumo = montar_versao_interna(_conjunto(), (), db_path=db_path, ano_base=2026)

    assert set(resumo) == {
        "cursos",
        "ciclos",
        "matriculas",
        "matriculas_eficiencia",
        "cursos_rejeitados_sem_portfolio",
        "cursos_fator_nao_encontrado",
        "campi_mantidos",
    }
    assert _rev_interna(db_path) == 1
