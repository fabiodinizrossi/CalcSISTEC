"""Testes de `app/sistec/perfis.py`: leitura do texto dos perfis do Sistec e
um perfil por campus."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.sistec.perfis import chave_campus, deduplicar_por_campus, extrair_perfil_do_texto  # noqa: E402


def test_extrai_codigo_cidade_e_nome_quando_o_texto_tem_codigo():
    perfil = extrair_perfil_do_texto("ASSESSOR DA UNIDADE DE ENSINO - 101 - IFFAR - CAMPUS SÃO VICENTE DO SUL")
    assert perfil == {
        "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - 101 - IFFAR - CAMPUS SÃO VICENTE DO SUL",
        "co_unidade": "101",
        "cidade": "São Vicente do Sul",
        "nome_unidade": "Campus São Vicente do Sul",
    }


def test_texto_sem_codigo_e_com_campus_acentuado():
    """Formato real visto na base local: sem código e com "CÂMPUS"."""
    perfil = extrair_perfil_do_texto(
        "ASSESSOR  DA UNIDADE DE ENSINO - INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA FARROUPILHA - CÂMPUS JÚLIO DE CASTILHOS"
    )
    assert perfil["co_unidade"] is None
    assert perfil["cidade"] == "Júlio de Castilhos"
    assert perfil["nome_perfil"].startswith("ASSESSOR DA UNIDADE")  # espaços normalizados


def test_texto_fora_do_padrao_vira_so_nome():
    assert extrair_perfil_do_texto("  Outro perfil  ") == {
        "nome_perfil": "Outro perfil",
        "co_unidade": None,
        "cidade": None,
        "nome_unidade": None,
    }


def test_chave_campus_ignora_papel_acento_e_codigo():
    assert chave_campus("GESTOR DA UNIDADE DE ENSINO - 43190 - IF - CÂMPUS FREDERICO WESTPHALEN") == "FREDERICO WESTPHALEN"
    assert chave_campus("ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS FREDERICO WESTPHALEN") == "FREDERICO WESTPHALEN"


def test_deduplica_um_perfil_por_campus_na_ordem_de_aparicao():
    perfis = [
        {"id_perfil": "1", "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS A", "co_unidade": None},
        {"id_perfil": "2", "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS B", "co_unidade": None},
        {"id_perfil": "3", "nome_perfil": "GESTOR DA UNIDADE DE ENSINO - 9 - IF - CAMPUS A", "co_unidade": "9"},
    ]
    resultado = deduplicar_por_campus(perfis)
    assert [p["id_perfil"] for p in resultado] == ["1", "2"]
    assert resultado[0]["co_unidade"] == "9"  # código completado a partir do outro papel


def test_deduplica_preferindo_o_perfil_ja_salvo():
    perfis = [
        {"id_perfil": "1", "nome_perfil": "ASSESSOR DA UNIDADE DE ENSINO - IF - CAMPUS A"},
        {"id_perfil": "2", "nome_perfil": "GESTOR DA UNIDADE DE ENSINO - IF - CAMPUS A"},
    ]
    resultado = deduplicar_por_campus(perfis, nomes_preferidos=["GESTOR DA UNIDADE DE ENSINO - IF - CAMPUS A"])
    assert [p["id_perfil"] for p in resultado] == ["2"]
