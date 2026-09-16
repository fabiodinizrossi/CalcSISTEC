"""Testes de `app/data/versoes.py` (`002-baixador-planilhas-sistec`, T022):
salvar interna, publicar, desfazer, aplicar no público — cada um em transação
isolada (D-05, D-06, `data-delta.md` §3.3)."""

import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data import versoes  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402


@pytest.fixture
def db_path():
    path = os.path.join(tempfile.mkdtemp(), "versoes.db")
    init_db(path)
    return path


def _conjunto_um_curso(codigo="P1", co_unidade="U1"):
    return {
        "cursos": pd.DataFrame(
            [
                {
                    "codigo_portfolio": codigo,
                    "nome_curso_ajustado": "TÉCNICO EM X",
                    "tipo_curso_pnp": "TÉCNICO",
                    "subtipo_curso": "Técnico",
                    "modalidade_ensino": "PRESENCIAL",
                    "eixo_tecnologico_ajustado": "EIXO1",
                    "fec": 1.0,
                    "fech": 1.0,
                    "carga_horaria_total": 1200,
                    "co_unidade": co_unidade,
                    "tipo_oferta_curso": "ANUAL",
                    "categoria_origem_curso": "TECNICO",
                    "fator_nao_encontrado": 0,
                }
            ]
        ),
        "ciclos": pd.DataFrame(
            [
                {
                    "codigo_ciclo_matricula": f"C-{codigo}",
                    "codigo_portfolio": codigo,
                    "co_unidade": co_unidade,
                    "dt_data_inicio": "2026-01-01",
                    "dt_data_fim_previsto": "2027-01-01",
                    "tipo_programa_curso": "REGULAR",
                    "status_ciclo": "ATIVO",
                }
            ]
        ),
        "matriculas": pd.DataFrame(
            [
                {
                    "co_matricula": f"M-{codigo}",
                    "codigo_ciclo_matricula": f"C-{codigo}",
                    "status_corrigido": "EM_CURSO",
                    "mes_ocorrencia_corrigido": "2026-01-01",
                    "ano_base": 2026,
                }
            ]
        ),
        "matriculas_eficiencia": pd.DataFrame(
            [
                {
                    "co_matricula": f"M-{codigo}",
                    "codigo_ciclo_matricula": f"C-{codigo}",
                    "status_corrigido2": "EM_CURSO",
                }
            ]
        ),
    }


def test_salvar_interna_grava_e_incrementa_rev_interna(db_path):
    versoes.salvar_interna(_conjunto_um_curso(), db_path)

    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
        rev_interna, gravada_em = conn.execute(
            "SELECT rev_interna, interna_gravada_em FROM estado_versoes WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()

    assert total == 1
    assert rev_interna == 1
    assert gravada_em is not None


def test_salvar_interna_substitui_conteudo_anterior(db_path):
    versoes.salvar_interna(_conjunto_um_curso("P1"), db_path)
    versoes.salvar_interna(_conjunto_um_curso("P2"), db_path)

    conn = get_connection(db_path)
    try:
        codigos = [r[0] for r in conn.execute("SELECT codigo_portfolio FROM interna_cursos")]
    finally:
        conn.close()

    assert codigos == ["P2"]


def test_publicar_move_interna_para_publicada_e_atualiza_estado(db_path):
    versoes.salvar_interna(_conjunto_um_curso(), db_path)
    versoes.publicar(db_path, admin_email="pi@iffarroupilha.edu.br")

    conn = get_connection(db_path)
    try:
        total_publicada = conn.execute("SELECT COUNT(*) FROM cursos").fetchone()[0]
        rev_publicada, rev_anterior, publicada_por = conn.execute(
            "SELECT rev_publicada, rev_anterior, publicada_por FROM estado_versoes WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()

    assert total_publicada == 1
    assert rev_publicada == 1
    assert rev_anterior is None  # primeira publicação: nada a desfazer
    assert publicada_por == "pi@iffarroupilha.edu.br"


def test_publicar_pela_segunda_vez_guarda_a_publicada_anterior(db_path):
    versoes.salvar_interna(_conjunto_um_curso("P1"), db_path)
    versoes.publicar(db_path)

    versoes.salvar_interna(_conjunto_um_curso("P2"), db_path)
    versoes.publicar(db_path)

    conn = get_connection(db_path)
    try:
        publicada = [r[0] for r in conn.execute("SELECT codigo_portfolio FROM cursos")]
        anterior = [r[0] for r in conn.execute("SELECT codigo_portfolio FROM anterior_cursos")]
        rev_publicada, rev_anterior = conn.execute(
            "SELECT rev_publicada, rev_anterior FROM estado_versoes WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()

    assert publicada == ["P2"]
    assert anterior == ["P1"]
    assert rev_publicada == 2
    assert rev_anterior == 1


def test_desfazer_restaura_a_publicada_anterior(db_path):
    versoes.salvar_interna(_conjunto_um_curso("P1"), db_path)
    versoes.publicar(db_path)
    versoes.salvar_interna(_conjunto_um_curso("P2"), db_path)
    versoes.publicar(db_path)

    versoes.desfazer(db_path)

    conn = get_connection(db_path)
    try:
        publicada = [r[0] for r in conn.execute("SELECT codigo_portfolio FROM cursos")]
        anterior_vazia = conn.execute("SELECT COUNT(*) FROM anterior_cursos").fetchone()[0]
        interna = [r[0] for r in conn.execute("SELECT codigo_portfolio FROM interna_cursos")]
        rev_publicada, rev_anterior = conn.execute(
            "SELECT rev_publicada, rev_anterior FROM estado_versoes WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()

    assert publicada == ["P1"]
    assert anterior_vazia == 0
    assert interna == ["P2"]  # interna intocada pelo desfazer
    assert rev_publicada == 1
    assert rev_anterior is None


def test_desfazer_sem_nada_para_desfazer_levanta_erro(db_path):
    with pytest.raises(ValueError):
        versoes.desfazer(db_path)


def test_aplicar_publico_projeta_campus_e_fatores(db_path):
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO interna_campus (co_unidade, cidade, nome_unidade) VALUES ('U1', 'Santa Maria', 'Campus SM')"
        )
        conn.execute(
            "DELETE FROM interna_fatores WHERE chave_tipo = 'TÉCNICO' AND chave_nome = 'TESTE'"
        )
        conn.execute(
            "INSERT OR REPLACE INTO interna_fatores (tipo_curso, nome_curso, fec, fech, chave_tipo, chave_nome) "
            "VALUES ('TÉCNICO', 'TESTE', 2.0, 1.0, 'TÉCNICO', 'TESTE')"
        )
        conn.commit()
    finally:
        conn.close()

    versoes.aplicar_publico(db_path, admin_email="pi@iffarroupilha.edu.br")

    conn = get_connection(db_path)
    try:
        campus = conn.execute("SELECT co_unidade, cidade FROM campus").fetchall()
        fator = conn.execute(
            "SELECT fec FROM fatores WHERE chave_tipo='TÉCNICO' AND chave_nome='TESTE'"
        ).fetchone()
        rev_interna, rev_publicada = conn.execute(
            "SELECT rev_interna, rev_publicada FROM estado_versoes WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()

    assert campus == [("U1", "Santa Maria")]
    assert fator[0] == 2.0
    assert rev_interna == 1
    assert rev_publicada == 1


def test_aplicar_publico_nao_mexe_em_anterior(db_path):
    versoes.salvar_interna(_conjunto_um_curso(), db_path)
    versoes.publicar(db_path)

    versoes.aplicar_publico(db_path)

    conn = get_connection(db_path)
    try:
        rev_anterior = conn.execute("SELECT rev_anterior FROM estado_versoes WHERE id = 1").fetchone()[0]
    finally:
        conn.close()

    assert rev_anterior is None
