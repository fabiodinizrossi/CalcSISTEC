"""`confirmar.js` (DS-58, DS-59, DS-60): confirmação em br-modal no lugar de `confirm()`."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from flask import render_template

from app import app as app_module

RAIZ = Path(__file__).resolve().parents[1]
CONFIRMAR_JS = RAIZ / "app" / "static" / "js" / "confirmar.js"

precisa_de_node = pytest.mark.skipif(shutil.which("node") is None, reason="node não encontrado")


def avaliar_em_node(expressao):
    codigo = f"const m = require({json.dumps(str(CONFIRMAR_JS))}); process.stdout.write(JSON.stringify({expressao}));"
    resultado = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout)


@precisa_de_node
def test_tab_no_ultimo_elemento_volta_ao_primeiro():
    assert avaliar_em_node("m.proximoFoco(1, 2, false)") == 0
    assert avaliar_em_node("m.proximoFoco(4, 5, false)") == 0


@precisa_de_node
def test_shift_tab_no_primeiro_elemento_vai_ao_ultimo():
    assert avaliar_em_node("m.proximoFoco(0, 2, true)") == 1
    assert avaliar_em_node("m.proximoFoco(0, 5, true)") == 4


@precisa_de_node
def test_tab_e_shift_tab_no_meio_andam_um_elemento():
    assert avaliar_em_node("m.proximoFoco(0, 3, false)") == 1
    assert avaliar_em_node("m.proximoFoco(2, 3, true)") == 1


@precisa_de_node
def test_so_esc_fecha_o_modal():
    assert avaliar_em_node('m.teclaFecha("Escape")') is True
    assert avaliar_em_node('["Enter", "Tab", " ", "a"].map(m.teclaFecha)') == [False, False, False, False]


def test_o_arquivo_nao_chama_o_confirm_nativo():
    codigo = CONFIRMAR_JS.read_text(encoding="utf-8")
    assert not re.search(r"(?<![\w$])(?:window\.)?confirm\s*\(", codigo)


def test_ids_usados_pelo_script_existem_no_parcial_do_modal():
    codigo = CONFIRMAR_JS.read_text(encoding="utf-8")
    usados = set(re.findall(r'getElementById\(\s*"([^"]+)"', codigo))
    with app_module.server.test_request_context("/"):
        html = render_template("shell/_modal_confirmacao.html")
    assert usados == {
        "modal-confirmacao",
        "modal-confirmacao-mensagem",
        "modal-confirmacao-cancelar",
        "modal-confirmacao-confirmar",
    }
    for id_usado in usados:
        assert f'id="{id_usado}"' in html


def test_scripts_carrega_confirmar_js_uma_vez_depois_de_core_min_js():
    with app_module.server.test_request_context("/"):
        html = render_template("shell/_scripts.html")
    assert html.count("/ds/js/confirmar.js") == 1
    assert html.index("core.min.js") < html.index("/ds/js/confirmar.js")


def test_nenhum_js_estatico_chama_o_confirm_nativo():
    for arquivo in (RAIZ / "app" / "static" / "js").glob("*.js"):
        codigo = arquivo.read_text(encoding="utf-8")
        assert not re.search(r"(?<![\w$])(?:window\.)?confirm\s*\(", codigo), arquivo.name


def test_atualizar_js_confirma_os_4_botoes_pelo_modal_com_o_texto_do_data_confirm():
    codigo = (RAIZ / "app" / "static" / "js" / "atualizar.js").read_text(encoding="utf-8")
    chamadas = re.findall(r"await confirmarAcao\(\s*(btn\w+)\.dataset\.confirm", codigo)
    assert sorted(chamadas) == ["btnCancelar", "btnDescartar", "btnDesfazer", "btnPublicar"]
