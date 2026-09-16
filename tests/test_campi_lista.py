"""Testes da lista de campi editável (`app/data/campi.py`): leitura do Sistec
preservando edições, perfis incluídos à mão, campus desativado e código da
unidade preenchido pela planilha de ciclos."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data import campi  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402

SANTA_ROSA = "ASSESSOR DA UNIDADE DE ENSINO - INSTITUTO FEDERAL FARROUPILHA - CAMPUS SANTA ROSA"
SAO_BORJA = "ASSESSOR DA UNIDADE DE ENSINO - INSTITUTO FEDERAL FARROUPILHA - CAMPUS SÃO BORJA"


@pytest.fixture
def db_path(tmp_path):
    caminho = str(tmp_path / "campi.db")
    init_db(caminho)
    return caminho


def test_linha_antiga_com_id_de_posicao_e_trocada_pelo_id_real_mantendo_edicoes(db_path):
    """A extensão salvava "0", "1"... como id; a nova leitura casa pelo nome
    do campus e herda código, cidade, nome e situação."""
    campi.salvar_captura([{"id_perfil": "0", "nome_perfil": SANTA_ROSA, "ordem": 0}], db_path)
    campi.salvar_campus_manual("0", "13478", "Santa Rosa", "Campus Santa Rosa", db_path)
    campi.definir_ativo("0", False, db_path)

    campi.salvar_captura([{"id_perfil": "8278860", "nome_perfil": SANTA_ROSA, "ordem": 0}], db_path)

    lista = campi.listar_campi(db_path)
    assert len(lista) == 1
    assert (lista[0]["id_perfil"], lista[0]["co_unidade"], lista[0]["nome_unidade"], lista[0]["ativo"]) == (
        "8278860",
        "13478",
        "Campus Santa Rosa",
        0,
    )


def test_leitura_remove_perfis_que_sumiram_mas_mantem_os_incluidos_a_mao(db_path):
    campi.salvar_captura(
        [
            {"id_perfil": "1", "nome_perfil": SANTA_ROSA, "ordem": 0},
            {"id_perfil": "2", "nome_perfil": SAO_BORJA, "ordem": 1},
        ],
        db_path,
    )
    campi.incluir_campus("9", "Perfil manual - CAMPUS AVANÇADO", "999", "Cidade", "Campus Avançado", db_path)

    campi.salvar_captura([{"id_perfil": "1", "nome_perfil": SANTA_ROSA, "ordem": 0}], db_path)

    lista = campi.listar_campi(db_path)
    assert [(c["id_perfil"], c["origem"]) for c in lista] == [("1", "sistec"), ("9", "manual")]


def test_codigo_ja_usado_por_outra_linha_fica_vazio_em_vez_de_quebrar(db_path):
    campi.incluir_campus("9", "Perfil manual", "101", None, None, db_path)

    campi.salvar_captura([{"id_perfil": "1", "nome_perfil": SANTA_ROSA, "ordem": 0, "co_unidade": "101"}], db_path)

    por_id = {c["id_perfil"]: c for c in campi.listar_campi(db_path)}
    assert por_id["1"]["co_unidade"] is None
    assert por_id["9"]["co_unidade"] == "101"


def test_incluir_campus_com_id_repetido_e_recusado(db_path):
    campi.incluir_campus("9", "Perfil manual", None, None, None, db_path)
    with pytest.raises(campi.CampusInvalido):
        campi.incluir_campus("9", "Outro", None, None, None, db_path)


def test_preencher_unidade_so_quando_vazio_e_sem_conflito(db_path):
    campi.salvar_captura(
        [
            {"id_perfil": "1", "nome_perfil": SANTA_ROSA, "ordem": 0},
            {"id_perfil": "2", "nome_perfil": SAO_BORJA, "ordem": 1, "co_unidade": "200"},
        ],
        db_path,
    )

    assert campi.preencher_unidade("1", "100", db_path) is True
    assert campi.preencher_unidade("1", "300", db_path) is False  # já tem código
    assert campi.preencher_unidade("1", "100", db_path) is True  # mesmo código, nada muda
    assert campi.preencher_unidade("2", "100", db_path) is False  # "2" já tem "200"

    campi.salvar_captura(
        [
            {"id_perfil": "1", "nome_perfil": SANTA_ROSA, "ordem": 0},
            {"id_perfil": "3", "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS NOVO", "ordem": 1},
        ],
        db_path,
    )
    assert campi.preencher_unidade("3", "100", db_path) is False  # código em uso pelo "1"
    assert campi.listar_campi(db_path)[1]["co_unidade"] is None


def test_preencher_unidade_completa_cidade_e_nome_e_projeta_interna_campus(db_path):
    campi.salvar_captura([{"id_perfil": "2", "nome_perfil": SAO_BORJA, "ordem": 0}], db_path)

    assert campi.preencher_unidade("2", "13479", db_path) is True

    linha = campi.listar_campi(db_path)[0]
    assert (linha["co_unidade"], linha["cidade"], linha["nome_unidade"]) == ("13479", "São Borja", "Campus São Borja")
    conn = get_connection(db_path)
    try:
        assert conn.execute("SELECT co_unidade FROM interna_campus").fetchall() == [("13479",)]
    finally:
        conn.close()


def test_listar_somente_ativos_e_campus_sem_unidade_ignora_desativados(db_path):
    campi.salvar_captura(
        [
            {"id_perfil": "1", "nome_perfil": SANTA_ROSA, "ordem": 0, "co_unidade": "100"},
            {"id_perfil": "2", "nome_perfil": SAO_BORJA, "ordem": 1},
        ],
        db_path,
    )
    assert campi.existe_campus_sem_unidade(db_path) is True

    campi.definir_ativo("2", False, db_path)

    assert [c["id_perfil"] for c in campi.listar_campi(db_path, somente_ativos=True)] == ["1"]
    assert campi.existe_campus_sem_unidade(db_path) is False


def test_init_db_adiciona_colunas_em_banco_antigo(tmp_path):
    caminho = str(tmp_path / "antigo.db")
    conn = get_connection(caminho)
    try:
        conn.execute(
            "CREATE TABLE campi_sistec (id_perfil TEXT PRIMARY KEY, nome_perfil TEXT NOT NULL, ordem INTEGER NOT NULL, "
            "co_unidade TEXT UNIQUE, cidade TEXT, nome_unidade TEXT, capturado_em TIMESTAMP NOT NULL)"
        )
        conn.execute("INSERT INTO campi_sistec VALUES ('0', 'x', 0, NULL, NULL, NULL, '2026-09-15')")
        conn.commit()
    finally:
        conn.close()

    init_db(caminho)

    linha = campi.listar_campi(caminho)[0]
    assert (linha["ativo"], linha["origem"]) == (1, "sistec")
