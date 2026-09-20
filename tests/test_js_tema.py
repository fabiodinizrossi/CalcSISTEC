"""Script inline do tema (DS-45, DS-46, DS-50, DS-51, DS-52): roda em `node` com
`document`, `localStorage` e `matchMedia` simulados."""

import json
import re
import shutil
import subprocess

import pytest
from flask import render_template

from app import app as app_module

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node não encontrado")

EXECUTOR = """
const vm = require("vm");
const cfg = JSON.parse(require("fs").readFileSync(0, "utf8"));
const atributos = {};
const sandbox = {
  document: { documentElement: { setAttribute: (nome, valor) => { atributos[nome] = valor; } } },
};
if (cfg.storage === "bloqueado") {
  sandbox.localStorage = { getItem() { throw new Error("SecurityError"); } };
} else {
  sandbox.localStorage = { getItem: (chave) => (chave === "calcsistec-tema" ? cfg.salvo : null) };
}
if (cfg.sistema !== "sem_matchmedia") {
  sandbox.matchMedia = (consulta) => ({
    matches: cfg.sistema === "escuro" && consulta.includes("prefers-color-scheme: dark"),
  });
}
vm.runInNewContext(cfg.script, sandbox);
process.stdout.write(JSON.stringify(atributos));
"""


def script_inline_do_head():
    with app_module.server.test_request_context("/"):
        html = render_template("shell/_head.html", titulo="Início")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert len(scripts) == 1
    return scripts[0]


def tema_resultante(salvo=None, sistema="claro", storage="livre"):
    entrada = json.dumps({"script": script_inline_do_head(), "salvo": salvo, "sistema": sistema, "storage": storage})
    resultado = subprocess.run(["node", "-e", EXECUTOR], input=entrada, capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout).get("data-tema")


def test_sem_escolha_e_sistema_escuro_resulta_em_escuro():
    assert tema_resultante(salvo=None, sistema="escuro") == "escuro"


def test_sem_escolha_e_sistema_claro_resulta_em_claro():
    assert tema_resultante(salvo=None, sistema="claro") == "claro"


def test_sem_escolha_e_sem_preferencia_do_sistema_resulta_em_claro():
    assert tema_resultante(salvo=None, sistema="sem_matchmedia") == "claro"


def test_escolha_claro_salva_vale_mais_que_sistema_escuro():
    assert tema_resultante(salvo="claro", sistema="escuro") == "claro"


def test_escolha_escuro_salva_vale_mais_que_sistema_claro():
    assert tema_resultante(salvo="escuro", sistema="claro") == "escuro"


def test_storage_bloqueado_segue_a_preferencia_do_sistema_sem_erro():
    assert tema_resultante(sistema="escuro", storage="bloqueado") == "escuro"
    assert tema_resultante(sistema="claro", storage="bloqueado") == "claro"


from pathlib import Path

TEMA_JS = Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "tema.js"


def avaliar_tema_js(expressao):
    codigo = f"const m = require({json.dumps(str(TEMA_JS))}); process.stdout.write(JSON.stringify({expressao}));"
    resultado = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout)


def test_alternar_tema_troca_claro_e_escuro():
    assert avaliar_tema_js('[m.alternarTema("claro"), m.alternarTema("escuro")]') == ["escuro", "claro"]


def test_rotulo_do_botao_oferece_o_tema_que_ainda_nao_esta_ativo():
    assert avaliar_tema_js('[m.rotuloDoBotao("claro"), m.rotuloDoBotao("escuro")]') == ["Usar tema escuro", "Usar tema claro"]


def test_gravar_tema_usa_a_chave_calcsistec_tema_com_claro_ou_escuro():
    expressao = (
        "(() => { const gravado = {}; const storage = { setItem: (k, v) => { gravado[k] = v; } };"
        'return [m.gravarTema("escuro", storage), gravado]; })()'
    )
    assert avaliar_tema_js(expressao) == [True, {"calcsistec-tema": "escuro"}]


def test_gravar_tema_com_storage_que_lanca_excecao_devolve_false_sem_propagar_erro():
    expressao = '(() => { const storage = { setItem() { throw new Error("SecurityError"); } }; return m.gravarTema("claro", storage); })()'
    assert avaliar_tema_js(expressao) is False


@pytest.mark.parametrize(
    "salvo,sistema,storage",
    [
        (None, "escuro", "livre"),
        (None, "claro", "livre"),
        ("claro", "escuro", "livre"),
        ("escuro", "claro", "livre"),
        (None, "escuro", "bloqueado"),
        (None, "claro", "bloqueado"),
    ],
)
def test_resolver_tema_da_o_mesmo_resultado_que_o_script_inline_do_head(salvo, sistema, storage):
    if storage == "bloqueado":
        leitura = '{ getItem() { throw new Error("SecurityError"); } }'
    else:
        leitura = "{ getItem: () => " + json.dumps(salvo) + " }"
    expressao = f"m.resolverTema(m.lerTemaSalvo({leitura}), {json.dumps(sistema == 'escuro')})"
    assert avaliar_tema_js(expressao) == tema_resultante(salvo=salvo, sistema=sistema, storage=storage)


def test_scripts_carrega_tema_js_uma_vez_depois_de_core_min_js():
    with app_module.server.test_request_context("/"):
        html = render_template("shell/_scripts.html")
    assert html.count("/ds/js/tema.js") == 1
    assert html.index("core-init.min.js") < html.index("/ds/js/tema.js")
