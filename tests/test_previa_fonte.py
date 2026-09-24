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


def _banco_com_campus(tmp_path, interna, publicado):
    """Banco temporário com uma linha em `interna_campus` e outra (ou
    nenhuma) em `campus`."""
    from app.data.schema import get_connection, init_db

    db_path = str(tmp_path / "fonte.db")
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO interna_campus (co_unidade, cidade, nome_unidade) VALUES (?, ?, ?)", interna
        )
        if publicado is not None:
            conn.execute(
                "INSERT INTO campus (co_unidade, cidade, nome_unidade) VALUES (?, ?, ?)", publicado
            )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_abrir_fonte_previa_sem_campus_explicito_le_interna_campus(tmp_path):
    """CPR-06 AC5: o fallback da fonte da prévia lê `interna_campus` (o que o
    Publicar leva ao ar), não o `campus` já publicado."""
    db_path = _banco_com_campus(
        tmp_path,
        interna=("U1", "Santa Maria", "Campus SM"),
        publicado=("U1", "Cidade Antiga", "Campus Antigo"),
    )

    fonte = abrir_fonte_previa(_candidato(), campus_publico=None, db_path=db_path)
    try:
        conn = fonte.abrir_leitura()
        try:
            linhas = conn.execute("SELECT co_unidade, cidade, nome_unidade FROM campus").fetchall()
        finally:
            conn.close()
    finally:
        fonte.fechar()

    assert linhas == [("U1", "Santa Maria", "Campus SM")]


def test_abrir_fonte_previa_com_interna_campus_vazio_nao_falha(tmp_path):
    from app.data.schema import get_connection, init_db

    db_path = str(tmp_path / "fonte.db")
    init_db(db_path)

    fonte = abrir_fonte_previa(_candidato(), campus_publico=None, db_path=db_path)
    try:
        conn = fonte.abrir_leitura()
        try:
            assert conn.execute("SELECT COUNT(*) FROM campus").fetchone()[0] == 0
        finally:
            conn.close()
    finally:
        fonte.fechar()


def test_abrir_fonte_previa_com_campus_explicito_ignora_o_banco(tmp_path):
    """O parâmetro `campus_publico` continua valendo: quem passa um DataFrame
    não é afetado pela troca do fallback."""
    from app.data.schema import get_connection, init_db

    db_path = str(tmp_path / "fonte.db")
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO interna_campus (co_unidade, cidade, nome_unidade) VALUES ('U9', 'Outra', 'Campus Outro')")
        conn.commit()
    finally:
        conn.close()

    fonte = abrir_fonte_previa(_candidato(), _campus_publico(), db_path=db_path)
    try:
        conn = fonte.abrir_leitura()
        try:
            linhas = conn.execute("SELECT co_unidade FROM campus").fetchall()
        finally:
            conn.close()
    finally:
        fonte.fechar()

    assert linhas == [("U1",)]


def _fonte_aberta_em_thread():
    """Abre a fonte dentro de uma `threading.Thread` e devolve o objeto — o
    servidor Flask atende cada requisição numa thread, então a fonte nasce
    numa thread e é fechada em outra."""
    import threading

    resultado = {}

    def _abrir():
        resultado["fonte"] = abrir_fonte_previa(_candidato(), _campus_publico())

    thread = threading.Thread(target=_abrir)
    thread.start()
    thread.join()
    return resultado["fonte"]


def test_fechar_em_thread_diferente_da_que_abriu():
    """T21 (UAT de 2026-09-24): `Descartar`/`Salvar` fecham a fonte numa thread
    diferente da que abriu no envio — com o default `check_same_thread=True`
    isso levantava `sqlite3.ProgrammingError` e a rota devolvia 500."""
    fonte = _fonte_aberta_em_thread()

    fonte.fechar()  # não levanta

    assert fonte._ancora is None


def test_liberar_previa_de_outra_thread_fecha_a_fonte(tmp_path):
    """O caminho real (`execucoes.liberar_previa`, usado por `descartar` e pelo
    `salvar` bem-sucedido) também funciona entre threads."""
    from app.data.schema import init_db
    from app.sistec import execucoes

    db_path = str(tmp_path / "previa.db")
    init_db(db_path)
    candidato = {
        **_candidato(),
        "resumo": {"cursos": 1, "ciclos": 1, "matriculas": 1, "matriculas_eficiencia": 1},
    }

    execucoes._REGISTRO.clear()
    try:
        execucao = execucoes.criar_execucao_envio("pi@ife.edu.br", ["ciclos.csv"], ["matriculas.csv"])

        import threading

        thread = threading.Thread(target=lambda: execucoes.abrir_previa(execucao, candidato, db_path))
        thread.start()
        thread.join()

        assert execucao.previa_fonte is not None
        execucoes.liberar_previa(execucao)  # não levanta
        assert execucao.previa_fonte is None
    finally:
        execucoes._REGISTRO.clear()
