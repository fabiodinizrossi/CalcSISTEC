"""Testes da fonte candidata em memória (`previa-paginas-publicas`, T2):
`abrir_fonte_previa` e `FontePrevia` em `app/data/previa.py`.

Cobrem PVP-03/PVP-04: as quatro tabelas do candidato, o `campus` publicado, a
`config` (ano-base) e `estado_versoes` sem publicação entram na fonte; a
leitura é somente leitura; `fechar` é idempotente e nada vaza para disco ou
para o banco público.
"""

import os
import sqlite3
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data.previa import abrir_fonte_previa  # noqa: E402


def _candidato(ano_base=2026):
    cursos = pd.DataFrame(
        [
            {
                "codigo_portfolio": "P1",
                "nome_curso_ajustado": "TÉCNICO EM X",
                "tipo_curso_pnp": "TÉCNICO",
                "subtipo_curso": "Técnico",
                "modalidade_ensino": "PRESENCIAL",
                "eixo_tecnologico_ajustado": "EIXO1",
                "fec": 1.0,
                "fech": 1.0,
                "carga_horaria_total": 1200,
                "co_unidade": "U1",
                "tipo_oferta_curso": "ANUAL",
                "categoria_origem_curso": "TECNICO",
                "fator_nao_encontrado": 0,
            }
        ]
    )
    ciclos = pd.DataFrame(
        [
            {
                "codigo_ciclo_matricula": "C1",
                "codigo_portfolio": "P1",
                "co_unidade": "U1",
                "dt_data_inicio": "2026-01-01",
                "dt_data_fim_previsto": "2027-01-01",
                "tipo_programa_curso": "REGULAR",
                "status_ciclo": "ATIVO",
            }
        ]
    )
    matriculas = pd.DataFrame(
        [
            {
                "co_matricula": "M1",
                "codigo_ciclo_matricula": "C1",
                "status_corrigido": "EM_CURSO",
                "mes_ocorrencia_corrigido": "2026-01-01",
                "ano_base": ano_base,
            }
        ]
    )
    matriculas_eficiencia = pd.DataFrame(
        [
            {
                "co_matricula": "M1",
                "codigo_ciclo_matricula": "C1",
                "status_corrigido2": "EM_CURSO",
            }
        ]
    )
    return {
        "tabelas": {
            "cursos": cursos,
            "ciclos": ciclos,
            "matriculas": matriculas,
            "matriculas_eficiencia": matriculas_eficiencia,
        },
        "ano_base": ano_base,
    }


def _campus_publico():
    return pd.DataFrame([{"co_unidade": "U1", "cidade": "Santa Maria", "nome_unidade": "Campus SM"}])


def test_abrir_fonte_previa_guarda_quatro_tabelas_com_contagens():
    fonte = abrir_fonte_previa(_candidato(), _campus_publico())
    try:
        conn = fonte.abrir_leitura()
        try:
            for tabela in ("cursos", "ciclos", "matriculas", "matriculas_eficiencia"):
                assert conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0] == 1, tabela
        finally:
            conn.close()
    finally:
        fonte.fechar()


def test_abrir_fonte_previa_copia_campus_publicado():
    fonte = abrir_fonte_previa(_candidato(), _campus_publico())
    try:
        conn = fonte.abrir_leitura()
        try:
            linhas = conn.execute("SELECT co_unidade, cidade, nome_unidade FROM campus").fetchall()
        finally:
            conn.close()
        assert linhas == [("U1", "Santa Maria", "Campus SM")]
    finally:
        fonte.fechar()


def test_abrir_fonte_previa_config_com_ano_base_do_candidato():
    fonte = abrir_fonte_previa(_candidato(ano_base=2027), _campus_publico())
    try:
        conn = fonte.abrir_leitura()
        try:
            valor = conn.execute("SELECT valor FROM config WHERE chave='ano_base'").fetchone()[0]
        finally:
            conn.close()
        assert valor == "2027"
    finally:
        fonte.fechar()


def test_abrir_fonte_previa_estado_versoes_sem_publicacao():
    fonte = abrir_fonte_previa(_candidato(), _campus_publico())
    try:
        conn = fonte.abrir_leitura()
        try:
            publicada_em = conn.execute("SELECT publicada_em FROM estado_versoes WHERE id = 1").fetchone()[0]
        finally:
            conn.close()
        assert publicada_em is None
    finally:
        fonte.fechar()


def test_abrir_leitura_recusa_escrita():
    fonte = abrir_fonte_previa(_candidato(), _campus_publico())
    try:
        conn = fonte.abrir_leitura()
        try:
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("INSERT INTO cursos (codigo_portfolio) VALUES ('X')")
        finally:
            conn.close()
    finally:
        fonte.fechar()


def test_fechar_e_idempotente():
    fonte = abrir_fonte_previa(_candidato(), _campus_publico())
    fonte.fechar()
    fonte.fechar()  # não lança


def test_fonte_nao_cria_arquivo_em_disco():
    fonte = abrir_fonte_previa(_candidato(), _campus_publico())
    try:
        assert fonte.nome.startswith("file:previa-")
        assert "mode=memory" in fonte.nome
    finally:
        fonte.fechar()


def test_fonte_sem_colunas_pessoais():
    """PVP-03/`RISK-008`: nenhuma coluna pessoal (nome, CPF, e-mail, data de
    nascimento) entra nas tabelas da fonte."""
    fonte = abrir_fonte_previa(_candidato(), _campus_publico())
    try:
        conn = fonte.abrir_leitura()
        try:
            colunas = {
                row[1]
                for row in conn.execute("PRAGMA table_info(matriculas)")
            }
        finally:
            conn.close()
        pii = {"nome", "cpf", "email", "data_nascimento", "nascimento"}
        assert not (colunas & pii)
    finally:
        fonte.fechar()
