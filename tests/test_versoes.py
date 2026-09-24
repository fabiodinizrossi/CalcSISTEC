"""Testes de `app/data/versoes.py` (`002-baixador-planilhas-sistec`, T022):
salvar interna, publicar, desfazer, aplicar no público — cada um em transação
isolada (D-05, D-06, `data-delta.md` §3.3)."""

import os
import sqlite3
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


def _definir_campus(db_path, cidade, nome_unidade, co_unidade="U1"):
    """CPR-06: escreve a projeção `interna_campus` (RN-33)."""
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM interna_campus")
        conn.execute(
            "INSERT INTO interna_campus (co_unidade, cidade, nome_unidade) VALUES (?, ?, ?)",
            (co_unidade, cidade, nome_unidade),
        )
        conn.commit()
    finally:
        conn.close()


def _campus_publicado(db_path, prefixo=""):
    conn = get_connection(db_path)
    try:
        return conn.execute(
            f"SELECT co_unidade, cidade, nome_unidade FROM {prefixo}campus ORDER BY co_unidade"
        ).fetchall()
    finally:
        conn.close()


def test_publicar_move_interna_para_publicada_e_atualiza_estado(db_path):
    versoes.salvar_interna(_conjunto_um_curso(), db_path)
    _definir_campus(db_path, "Santa Maria", "Campus SM")
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
    # CPR-06 AC3: `interna_campus` acompanha a publicação — sem isso o painel
    # público fica sem campus numa instalação que nunca usou "Aplicar ao público".
    assert _campus_publicado(db_path) == [("U1", "Santa Maria", "Campus SM")]


def test_publicar_pela_segunda_vez_guarda_a_publicada_anterior(db_path):
    versoes.salvar_interna(_conjunto_um_curso("P1"), db_path)
    _definir_campus(db_path, "Santa Maria", "Campus SM")
    versoes.publicar(db_path)

    versoes.salvar_interna(_conjunto_um_curso("P2"), db_path)
    _definir_campus(db_path, "Jaguari", "Campus Jaguari")
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
    # CPR-06 AC4: a publicação anterior também guarda o campus dela.
    assert _campus_publicado(db_path) == [("U1", "Jaguari", "Campus Jaguari")]
    assert _campus_publicado(db_path, prefixo="anterior_") == [("U1", "Santa Maria", "Campus SM")]


def test_desfazer_restaura_a_publicada_anterior(db_path):
    versoes.salvar_interna(_conjunto_um_curso("P1"), db_path)
    _definir_campus(db_path, "Santa Maria", "Campus SM")
    versoes.publicar(db_path)
    versoes.salvar_interna(_conjunto_um_curso("P2"), db_path)
    _definir_campus(db_path, "Jaguari", "Campus Jaguari")
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
    # CPR-06 AC4: o Desfazer devolve o campus anterior junto com a versão.
    assert _campus_publicado(db_path) == [("U1", "Santa Maria", "Campus SM")]
    assert _campus_publicado(db_path, prefixo="anterior_") == []


def test_publicar_com_interna_campus_vazio_nao_falha(db_path):
    """Edge case da spec: instalação sem campus cadastrado publica normalmente
    e o painel público fica com `campus` vazio — sem erro."""
    versoes.salvar_interna(_conjunto_um_curso(), db_path)

    versoes.publicar(db_path)

    assert _campus_publicado(db_path) == []
    assert _campus_publicado(db_path, prefixo="anterior_") == []


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


# ===================== previa-paginas-publicas, T20 =====================


def _assinatura(db_path):
    from app.data.ingest import calcular_assinatura_origem

    return calcular_assinatura_origem(db_path)


def _rev_interna(db_path):
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT rev_interna FROM estado_versoes WHERE id = 1").fetchone()[0]
    finally:
        conn.close()


def test_salvar_interna_com_assinatura_igual_grava_e_incrementa(db_path):
    versoes.salvar_interna(_conjunto_um_curso(), db_path, assinatura_esperada=_assinatura(db_path))

    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
    finally:
        conn.close()
    assert total == 1
    assert _rev_interna(db_path) == 1


def test_salvar_interna_com_assinatura_divergente_levanta_conflito_sem_gravar(db_path):
    assinatura_falsa = {"rev_interna": 999, "rev_publicada": None, "ano_base": 2026, "fatores": (), "campus": ()}

    with pytest.raises(versoes.ConflitoDeConferencia):
        versoes.salvar_interna(_conjunto_um_curso(), db_path, assinatura_esperada=assinatura_falsa)

    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
    finally:
        conn.close()
    assert total == 0
    assert _rev_interna(db_path) == 0


def test_salvar_interna_conflito_quando_rev_interna_muda(db_path):
    assinatura = _assinatura(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE estado_versoes SET rev_interna = rev_interna + 1 WHERE id = 1")
        conn.commit()
    finally:
        conn.close()

    with pytest.raises(versoes.ConflitoDeConferencia):
        versoes.salvar_interna(_conjunto_um_curso(), db_path, assinatura_esperada=assinatura)

    # o conflito não grava nada: a revisão fica no valor da alteração acima
    assert _rev_interna(db_path) == 1


def test_salvar_interna_rollback_integral_em_falha_no_meio(db_path):
    conjunto = _conjunto_um_curso()
    # matrícula aponta para ciclo inexistente: viola a FK no meio da gravação
    conjunto["matriculas"] = pd.DataFrame(
        [
            {
                "co_matricula": "M2",
                "codigo_ciclo_matricula": "C-INEXISTENTE",
                "status_corrigido": "EM_CURSO",
                "mes_ocorrencia_corrigido": "2026-01-01",
                "ano_base": 2026,
            }
        ]
    )

    with pytest.raises(sqlite3.IntegrityError):
        versoes.salvar_interna(conjunto, db_path)

    conn = get_connection(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM interna_ciclos").fetchone()[0] == 0
    finally:
        conn.close()
    assert _rev_interna(db_path) == 0


def test_salvar_interna_nan_e_data_nula_vira_null(db_path):
    conjunto = _conjunto_um_curso()
    conjunto["ciclos"]["dt_data_inicio"] = None
    conjunto["ciclos"]["dt_data_fim_previsto"] = pd.NaT

    versoes.salvar_interna(conjunto, db_path)

    conn = get_connection(db_path)
    try:
        inicio, fim = conn.execute(
            "SELECT dt_data_inicio, dt_data_fim_previsto FROM interna_ciclos WHERE codigo_ciclo_matricula='C-P1'"
        ).fetchone()
    finally:
        conn.close()
    assert inicio is None and fim is None


def test_salvar_interna_sem_assinatura_mantem_comportamento(db_path):
    # baixa direta: assinatura_esperada=None (default) grava como antes
    versoes.salvar_interna(_conjunto_um_curso(), db_path)

    assert _rev_interna(db_path) == 1
    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_cursos").fetchone()[0]
    finally:
        conn.close()
    assert total == 1
