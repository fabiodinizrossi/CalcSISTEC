"""Testes de `app/data/campi.py` (`002-baixador-planilhas-sistec`, T034,
RN-03, RN-05)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data import campi  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402


def _campi_sistec(db_path):
    conn = get_connection(db_path)
    try:
        colunas = ["id_perfil", "nome_perfil", "co_unidade", "cidade", "nome_unidade"]
        rows = conn.execute(f"SELECT {', '.join(colunas)} FROM campi_sistec ORDER BY ordem").fetchall()
        return [dict(zip(colunas, row)) for row in rows]
    finally:
        conn.close()


def test_salvar_captura_grava_cidade_e_nome_unidade_lidos_automaticamente(tmp_path):
    """RF pedido pela PI: a captura já chega com `cidade`/`nome_unidade`
    pré-preenchidos a partir do texto do perfil (`sistec-content.js`,
    `extrairPerfilDoTexto`) — `salvar_captura` só precisa persistir."""
    db_path = str(tmp_path / "captura.db")
    init_db(db_path)

    campi.salvar_captura(
        [
            {
                "id_perfil": "1",
                "nome_perfil": "Assessor - Campus Santa Rosa",
                "co_unidade": "U1",
                "cidade": "Santa Rosa",
                "nome_unidade": "Campus Santa Rosa",
            }
        ],
        db_path,
    )

    linhas = _campi_sistec(db_path)
    assert linhas == [
        {
            "id_perfil": "1",
            "nome_perfil": "Assessor - Campus Santa Rosa",
            "co_unidade": "U1",
            "cidade": "Santa Rosa",
            "nome_unidade": "Campus Santa Rosa",
        }
    ]


def test_excluir_campus_remove_a_linha(tmp_path):
    db_path = str(tmp_path / "captura.db")
    init_db(db_path)

    campi.salvar_captura(
        [
            {"id_perfil": "1", "nome_perfil": "Assessor - Campus A", "co_unidade": "U1"},
            {"id_perfil": "2", "nome_perfil": "Gestor - Campus B", "co_unidade": "U2"},
        ],
        db_path,
    )

    campi.excluir_campus("2", db_path)

    linhas = _campi_sistec(db_path)
    assert [linha["id_perfil"] for linha in linhas] == ["1"]


def test_excluir_campus_regrava_interna_campus(tmp_path):
    db_path = str(tmp_path / "captura.db")
    init_db(db_path)

    campi.salvar_captura(
        [
            {
                "id_perfil": "1",
                "nome_perfil": "Assessor - Campus A",
                "co_unidade": "U1",
                "cidade": "Cidade A",
                "nome_unidade": "Campus A",
            }
        ],
        db_path,
    )
    campi.excluir_campus("1", db_path)

    conn = get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM interna_campus").fetchone()[0]
    finally:
        conn.close()
    assert total == 0


def test_excluir_campus_id_inexistente_nao_falha(tmp_path):
    db_path = str(tmp_path / "captura.db")
    init_db(db_path)

    campi.excluir_campus("nao-existe", db_path)  # não deve levantar exceção

    assert _campi_sistec(db_path) == []


def _dois_campi(tmp_path):
    db_path = str(tmp_path / "conflito.db")
    init_db(db_path)
    campi.incluir_campus("11111", "Perfil A", co_unidade="1", cidade="A", nome_unidade="Campus A", db_path=db_path)
    campi.incluir_campus("22222", "Perfil B", co_unidade="2", cidade="B", nome_unidade="Campus B", db_path=db_path)
    return db_path


def test_edicao_com_identificador_de_outro_campus_informa_o_campo_id_perfil(tmp_path):
    db_path = _dois_campi(tmp_path)
    with pytest.raises(campi.CampusInvalido) as erro:
        campi.salvar_campus_manual("22222", "2", "B", "Campus B", db_path, novo_id_perfil="11111")
    assert erro.value.campo == "id_perfil"
    assert str(erro.value) == "esse identificador de perfil já está em outro campus"


def test_edicao_com_codigo_de_outro_campus_informa_o_campo_co_unidade(tmp_path):
    db_path = _dois_campi(tmp_path)
    with pytest.raises(campi.CampusInvalido) as erro:
        campi.salvar_campus_manual("22222", "1", "B", "Campus B", db_path)
    assert erro.value.campo == "co_unidade"
    assert str(erro.value) == "esse código da unidade já está em outro campus"


def test_edicao_que_troca_o_identificador_e_repete_o_codigo_acusa_o_codigo(tmp_path):
    db_path = _dois_campi(tmp_path)
    with pytest.raises(campi.CampusInvalido) as erro:
        campi.salvar_campus_manual("22222", "1", "B", "Campus B", db_path, novo_id_perfil="33333")
    assert erro.value.campo == "co_unidade"


def test_inclusao_com_identificador_repetido_informa_o_campo_id_perfil(tmp_path):
    db_path = _dois_campi(tmp_path)
    with pytest.raises(campi.CampusInvalido) as erro:
        campi.incluir_campus("11111", "Outro perfil", co_unidade="9", db_path=db_path)
    assert erro.value.campo == "id_perfil"
    assert str(erro.value) == "esse identificador de perfil já está em outro campus"


def test_inclusao_com_codigo_repetido_informa_o_campo_co_unidade(tmp_path):
    db_path = _dois_campi(tmp_path)
    with pytest.raises(campi.CampusInvalido) as erro:
        campi.incluir_campus("33333", "Outro perfil", co_unidade="1", db_path=db_path)
    assert erro.value.campo == "co_unidade"
    assert str(erro.value) == "esse código da unidade já está em outro campus"


def test_campus_invalido_criado_so_com_a_mensagem_tem_campo_none():
    erro = campi.CampusInvalido("mensagem antiga")
    assert erro.campo is None
    assert str(erro) == "mensagem antiga"
