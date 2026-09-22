import json
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node não encontrado")
SCRIPT = Path(__file__).parents[1] / "app" / "static" / "js" / "ordenacao-tabelas.js"


def avaliar(expressao):
    codigo = f"const m = require({json.dumps(str(SCRIPT))}); console.log(JSON.stringify({expressao}));"
    resultado = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, timeout=30, check=True)
    return json.loads(resultado.stdout)


def test_compara_numeros_formatados_percentuais_e_datas():
    assert avaliar("[m.comparar('1.200', '950') > 0, m.comparar('12,5%', '9,8%') > 0, m.comparar('02/01/2026', '31/12/2025') > 0]") == [True, True, True]


def test_compara_texto_sem_diferenciar_maiusculas_e_com_ordenacao_natural():
    assert avaliar("[m.comparar('Campus 2', 'Campus 10'), m.comparar('Água', 'agua')]") == [-1, 0]


def test_valores_vazios_ficam_depois_dos_preenchidos():
    assert avaliar("[m.comparar('—', '10'), m.comparar('', 'Campus')]") == [1, 1]


def test_ordena_linhas_nas_duas_direcoes_e_mantem_vazio_no_fim():
    expressao = """(() => {
      const linhas = ['10', '2', '\\u2014'].map(texto => ({cells: [{textContent: texto, dataset: {}}]}));
      const tbody = {rows: linhas, insertBefore(linha, referencia) {
        this.rows.splice(this.rows.indexOf(linha), 1);
        const destino = referencia ? this.rows.indexOf(referencia) : this.rows.length;
        this.rows.splice(destino, 0, linha);
      }};
      const tabela = {tBodies: [tbody]};
      m.ordenarLinhas(tabela, 0, 'descending');
      const descendente = tbody.rows.map(l => l.cells[0].textContent);
      m.ordenarLinhas(tabela, 0, 'ascending');
      return [
        descendente.map(texto => texto.codePointAt(0)),
        tbody.rows.map(l => l.cells[0].textContent.codePointAt(0)),
      ];
    })()"""
    assert avaliar(expressao) == [[49, 50, 8212], [50, 49, 8212]]


def test_ordena_grupos_pelo_valor_da_linha_externa_sem_separar_subitens():
    expressao = """(() => {
      function linha(id, pai, valor) {
        return {dataset: {groupId: id, parentId: pai}, cells: [{textContent: valor, dataset: {}}]};
      }
      const linhas = [
        linha('pai-a', '', '2'),
        linha('filho-a', 'pai-a', '999'),
        linha('neto-a', 'filho-a', '1000'),
        linha('pai-b', '', '10'),
        linha('filho-b', 'pai-b', '1'),
      ];
      const tbody = {rows: linhas, insertBefore(linha, referencia) {
        this.rows.splice(this.rows.indexOf(linha), 1);
        const destino = referencia ? this.rows.indexOf(referencia) : this.rows.length;
        this.rows.splice(destino, 0, linha);
      }};
      m.ordenarLinhas({tBodies: [tbody]}, 0, 'descending');
      const descendente = tbody.rows.map(l => l.dataset.groupId);
      m.ordenarLinhas({tBodies: [tbody]}, 0, 'ascending');
      return [descendente, tbody.rows.map(l => l.dataset.groupId)];
    })()"""
    assert avaliar(expressao) == [
        ["pai-b", "filho-b", "pai-a", "filho-a", "neto-a"],
        ["pai-a", "filho-a", "neto-a", "pai-b", "filho-b"],
    ]


def test_nao_move_linhas_que_ja_estao_ordenadas_e_nao_realimenta_observador():
    expressao = """(() => {
      const linhas = ['2', '10', '\\u2014'].map(texto => ({cells: [{textContent: texto, dataset: {}}]}));
      let movimentos = 0;
      const tbody = {rows: linhas, insertBefore(linha, referencia) {
        movimentos += 1;
        this.rows.splice(this.rows.indexOf(linha), 1);
        const destino = referencia ? this.rows.indexOf(referencia) : this.rows.length;
        this.rows.splice(destino, 0, linha);
      }};
      const tabela = {tBodies: [tbody]};
      m.ordenarLinhas(tabela, 0, 'ascending');
      const primeira = movimentos;
      m.ordenarLinhas(tabela, 0, 'ascending');
      return [primeira, movimentos, tbody.rows.map(l => l.cells[0].textContent.codePointAt(0))];
    })()"""
    assert avaliar(expressao) == [0, 0, [50, 49, 8212]]


def test_clique_logico_no_cabecalho_alterna_direcao_e_reordena_o_corpo():
    expressao = """(() => {
      const linhas = ['2', '10', '1'].map(texto => ({cells: [{textContent: texto, dataset: {}}]}));
      const tbody = {rows: linhas, insertBefore(linha, referencia) {
        this.rows.splice(this.rows.indexOf(linha), 1);
        const destino = referencia ? this.rows.indexOf(referencia) : this.rows.length;
        this.rows.splice(destino, 0, linha);
      }};
      const atributos = {};
      const tabela = {
        dataset: {}, tBodies: [tbody], getAttribute() { return null; },
        tHead: {querySelectorAll() { return [th]; }},
      };
      const thead = {rows: [{cells: []}]};
      const th = {
        colSpan: 1, rowSpan: 1, atributos,
        closest(seletor) { return seletor === 'table' ? tabela : seletor === 'thead' ? thead : null; },
        hasAttribute(nome) { return nome in atributos; },
        setAttribute(nome, valor) { atributos[nome] = String(valor); },
      };
      thead.rows[0].cells = [th];
      m.ordenar(th);
      const primeira = tbody.rows.map(l => l.cells[0].textContent);
      m.ordenar(th);
      return [primeira, tbody.rows.map(l => l.cells[0].textContent), atributos['aria-sort']];
    })()"""
    assert avaliar(expressao) == [["10", "2", "1"], ["1", "2", "10"], "ascending"]


def test_tabela_hierarquica_ordenavel_prepara_cabecalho_e_preserva_coluna_excluida():
    expressao = """(() => {
      function cabecalho(excluido) {
        const atributos = excluido ? {'data-no-sort': 'true'} : {};
        return {
          colSpan: 1, classList: {adicionadas: [], add(valor) { this.adicionadas.push(valor); }},
          closest(seletor) { return seletor === 'table' ? tabela : seletor === 'thead' ? {} : null; },
          hasAttribute(nome) { return nome in atributos; }, setAttribute(nome, valor) { atributos[nome] = String(valor); }, atributos,
        };
      }
      const tabela = {dataset: {}, tBodies: [{}], getAttribute(nome) { return nome === 'data-sortable' ? 'true' : null; }};
      const ordenavel = cabecalho(false), excluido = cabecalho(true);
      tabela.tHead = {querySelectorAll() { return [ordenavel, excluido]; }};
      m.preparar(tabela);
      return [ordenavel.classList.adicionadas, ordenavel.atributos['tabindex'], ordenavel.atributos['aria-sort'], ordenavel.atributos.title, excluido.classList.adicionadas];
    })()"""
    assert avaliar(expressao) == [["cabecalho-ordenavel"], "0", "none", "Ordenar por esta coluna", []]


def test_tabela_inserida_pelo_dash_e_preparada_pelo_observador():
    expressao = """(() => {
      let observar;
      global.MutationObserver = class { constructor(callback) { observar = callback; } observe() {} };
      const atributos = {};
      const tabela = {nodeType: 1, dataset: {}, tBodies: [{}], getAttribute() { return 'true'; }};
      const th = {
        colSpan: 1, classList: {add() {}}, closest(seletor) { return seletor === 'table' ? tabela : seletor === 'thead' ? {} : null; },
        hasAttribute(nome) { return nome in atributos; }, setAttribute(nome, valor) { atributos[nome] = String(valor); },
      };
      tabela.tHead = {querySelectorAll() { return [th]; }};
      tabela.matches = seletor => seletor === 'table';
      tabela.closest = () => null;
      const documento = {readyState: 'complete', body: {}, querySelectorAll() { return []; }, addEventListener() {}};
      m.iniciar(documento);
      observar([{addedNodes: [tabela]}]);
      return [atributos.tabindex, atributos['aria-sort'], atributos.title];
    })()"""
    assert avaliar(expressao) == ["0", "none", "Ordenar por esta coluna"]


def test_listeners_delegados_ordenam_por_clique_enter_e_espaco():
    expressao = """(() => {
      const eventos = {};
      const atributos = {};
      const linhas = ['2', '1'].map(texto => ({cells: [{textContent: texto, dataset: {}}], dataset: {}}));
      const tbody = {rows: linhas, insertBefore(linha, referencia) { this.rows.splice(this.rows.indexOf(linha), 1); this.rows.splice(referencia ? this.rows.indexOf(referencia) : this.rows.length, 0, linha); }};
      const tabela = {dataset: {}, tBodies: [tbody], getAttribute() { return 'true'; }};
      const thead = {rows: [{cells: []}]};
      const th = {
        colSpan: 1, rowSpan: 1, classList: {add() {}}, closest(seletor) { return seletor === 'table' ? tabela : seletor === 'thead' ? thead : null; },
        hasAttribute(nome) { return nome in atributos; }, setAttribute(nome, valor) { atributos[nome] = String(valor); },
      };
      thead.rows[0].cells = [th]; tabela.tHead = {querySelectorAll() { return [th]; }};
      const documento = {readyState: 'complete', body: {}, querySelectorAll() { return [tabela]; }, addEventListener(nome, funcao) { eventos[nome] = funcao; }};
      m.iniciar(documento);
      const alvo = {closest() { return th; }};
      eventos.click({target: alvo});
      let prevenidos = 0;
      eventos.keydown({target: alvo, key: 'Enter', preventDefault() { prevenidos += 1; }});
      eventos.keydown({target: alvo, key: ' ', preventDefault() { prevenidos += 1; }});
      return [prevenidos, atributos['aria-sort'], tbody.rows.map(linha => linha.cells[0].textContent)];
    })()"""
    assert avaliar(expressao) == [2, "descending", ["2", "1"]]
