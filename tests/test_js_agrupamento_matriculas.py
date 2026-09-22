import json
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node não encontrado")
SCRIPT = Path(__file__).parents[1] / "app" / "static" / "js" / "agrupamento-matriculas.js"


def avaliar(expressao):
    codigo = f"const m = require({json.dumps(str(SCRIPT))}); console.log(JSON.stringify({expressao}));"
    resultado = subprocess.run(["node", "-e", codigo], capture_output=True, text=True, timeout=30, check=True)
    return json.loads(resultado.stdout)


def test_encontra_todos_os_descendentes_em_ordem_de_nivel():
    expressao = """(() => {
      const linhas = [
        {dataset: {groupId: 'filho', parentId: 'raiz'}},
        {dataset: {groupId: 'neto', parentId: 'filho'}},
        {dataset: {groupId: 'outro', parentId: ''}},
      ];
      const tabela = {querySelectorAll(seletor) {
        const pai = seletor.match(/data-parent-id=\\"([^\\"]*)/)[1];
        return linhas.filter(linha => linha.dataset.parentId === pai);
      }};
      return m.descendentes(tabela, 'raiz').map(linha => linha.dataset.groupId);
    })()"""
    assert avaliar(expressao) == ["filho", "neto"]
