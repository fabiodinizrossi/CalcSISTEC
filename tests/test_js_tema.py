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
