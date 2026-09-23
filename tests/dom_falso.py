"""Roda um script de `app/static/js/` em `node` sobre um DOM mínimo simulado, para testar a
fiação dos manipuladores de evento (clique, teclado, observador), que as funções puras não cobrem."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

JS = Path(__file__).resolve().parents[1] / "app" / "static" / "js"

precisa_de_node = pytest.mark.skipif(shutil.which("node") is None, reason="node não encontrado")

HARNESS = r"""
const vm = require("vm");
const entrada = JSON.parse(require("fs").readFileSync(0, "utf8"));

function criarElemento(id) {
  const ouvintes = {};
  const classes = new Set();
  const e = {
    id: id || "", pai: null, atributos: {}, dataset: {}, textContent: "", filhosPorSeletor: {}, seletores: [], observadores: [],
    addEventListener(tipo, f) { (ouvintes[tipo] = ouvintes[tipo] || []).push(f); },
    removeEventListener(tipo, f) { ouvintes[tipo] = (ouvintes[tipo] || []).filter((x) => x !== f); },
    disparar(tipo, extra) {
      const ev = Object.assign({ target: e, evitado: false, preventDefault() { this.evitado = true; } }, extra || {});
      (ouvintes[tipo] || []).slice().forEach((f) => f(ev));
      return ev;
    },
    setAttribute(k, v) { e.atributos[k] = String(v); },
    getAttribute(k) { return k in e.atributos ? e.atributos[k] : null; },
    focus() { doc.activeElement = e; },
    contains(o) { for (let x = o; x; x = x.pai) { if (x === e) return true; } return false; },
    querySelector(sel) { return e.filhosPorSeletor[sel] || null; },
    matches(sel) { return e.seletores.indexOf(sel) !== -1; },
  };
  const avisar = () => e.observadores.forEach((f) => f());
  e.classList = {
    add(c) { classes.add(c); avisar(); },
    remove(c) { classes.delete(c); avisar(); },
    contains(c) { return classes.has(c); },
    toggle(c) { const tem = classes.has(c); if (tem) { classes.delete(c); } else { classes.add(c); } avisar(); return !tem; },
  };
  return e;
}

const doc = criarElemento("documento");
doc.body = criarElemento("body");
doc.documentElement = criarElemento("html");
doc.activeElement = doc.body;
doc.porId = {};
doc.porSeletor = {};
doc.getElementById = (id) => doc.porId[id] || null;
doc.querySelector = (sel) => doc.porSeletor[sel] || null;

const janela = { innerWidth: entrada.largura || 1280, localStorage: null };
const ouvintesJanela = {};
janela.addEventListener = (t, f) => { (ouvintesJanela[t] = ouvintesJanela[t] || []).push(f); };
janela.disparar = (t) => (ouvintesJanela[t] || []).forEach((f) => f({}));

const fila = [];
const submetidos = [];
class FormularioFalso {}
FormularioFalso.prototype.submit = function () { submetidos.push(this); };

const consultas = [];
const ambiente = {
  document: doc,
  window: janela,
  setTimeout: (f) => { fila.push(f); return fila.length; },
  matchMedia: (consulta) => {
    const ouvintes = [];
    const m = { media: consulta, matches: false, addEventListener(t, f) { ouvintes.push(f); }, mudar(valor) { m.matches = valor; ouvintes.forEach((f) => f({ matches: valor })); } };
    consultas.push(m);
    return m;
  },
  MutationObserver: class { constructor(f) { this.f = f; } observe(alvo) { alvo.observadores.push(this.f); } },
  HTMLFormElement: FormularioFalso,
};
janela.matchMedia = ambiente.matchMedia;

const contexto = vm.createContext(ambiente);
const ferramentas = {
  criarElemento, doc, janela, consultas, submetidos,
  registrar(el, id, seletor) { if (id) { el.id = id; doc.porId[id] = el; } if (seletor) { doc.porSeletor[seletor] = el; } return el; },
  executarFila() { while (fila.length) { fila.shift()(); } },
};
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
(async () => {
  await new AsyncFunction(...Object.keys(ferramentas), "contexto", entrada.preparar)(...Object.values(ferramentas), contexto);
  vm.runInContext(entrada.script, contexto);
  const resultado = await new AsyncFunction(...Object.keys(ferramentas), "contexto", entrada.verificar)(...Object.values(ferramentas), contexto);
  process.stdout.write(JSON.stringify(resultado === undefined ? null : resultado));
})().catch((erro) => { process.stderr.write(String(erro && erro.stack || erro)); process.exit(1); });
"""


def rodar(script, preparar, verificar, largura=1280):
    """Executa `app/static/js/<script>` depois de `preparar` (monta o DOM) e devolve o que `verificar` retornar."""
    entrada = json.dumps(
        {
            "script": (JS / script).read_text(encoding="utf-8"),
            "preparar": preparar,
            "verificar": verificar,
            "largura": largura,
        }
    )
    # `node` escreve UTF-8; sem isto o Windows decodifica em cp1252 e as
    # mensagens em português voltam com mojibake.
    resultado = subprocess.run(
        ["node", "-e", HARNESS], input=entrada, capture_output=True, text=True, encoding="utf-8", timeout=60
    )
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout)
