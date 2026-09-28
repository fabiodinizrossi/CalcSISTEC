"""`menu.js` (DS-37, DS-38): estado do botão do menu e foco de volta ao fechar."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from flask import render_template

from app import app as app_module

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node não encontrado")

MENU_JS = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "menu.js"


def avaliar(expressao):
    codigo = f"const m = require({json.dumps(str(MENU_JS))}); process.stdout.write(JSON.stringify({expressao}));"
    resultado = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout)


def test_aria_expanded_acompanha_o_menu_aberto_ou_fechado():
    assert avaliar("[m.valorAriaExpanded(true), m.valorAriaExpanded(false)]") == ["true", "false"]


def test_devolve_o_foco_so_quando_o_menu_acabou_de_fechar_e_o_foco_se_perdeu():
    assert avaliar("m.deveDevolverFoco(true, false, true)") is True
    assert avaliar("m.deveDevolverFoco(true, false, false)") is False
    assert avaliar("m.deveDevolverFoco(false, false, true)") is False
    assert avaliar("m.deveDevolverFoco(true, true, true)") is False
    assert avaliar("m.deveDevolverFoco(false, true, true)") is False


def test_scripts_carrega_menu_js_uma_vez_depois_de_core_init():
    with app_module.server.test_request_context("/"):
        html = render_template("shell/_scripts.html")
    assert html.count("/ds/js/menu.js") == 1
    assert html.index("core-init.min.js") < html.index("/ds/js/menu.js")
