"""Testes de `scripts/testar.ps1`, o ambiente de teste.

WDG-03: o app sobe por `run.py`, não por um `app.run` avulso — é o que faz o
watchdog de execuções rodar também no ambiente de teste.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(RAIZ, "scripts", "testar.ps1")


def ler_script():
    with open(SCRIPT, encoding="utf-8") as arquivo:
        return arquivo.read()


def test_script_sobe_o_app_por_run_py_na_porta_pedida():
    assert "run.py --host 127.0.0.1 --port $Porta" in ler_script()


def test_script_nao_chama_app_run_direto():
    assert "app.run(" not in ler_script()
