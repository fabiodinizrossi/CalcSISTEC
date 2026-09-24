"""Testes de `run.py`, o ponto de entrada do painel.

WDG-01: o processo chama `execucoes.iniciar_varredura()` uma vez, antes de
`app.run(...)`, com host/porta vindos de `--host`/`--port`.

WDG-02: importar `app.app` (testes, Dash) não pode criar a thread de
varredura — por isso o import é feito num subprocesso, que isola o estado
global de `app.sistec.execucoes`.
"""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import run  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def espioes(monkeypatch):
    """Espiões no lugar do watchdog e do `app.run`, em ordem de chamada."""
    chamadas = []

    def varredura():
        chamadas.append("varredura")

    def executar(**kwargs):
        chamadas.append(("run", kwargs))

    monkeypatch.setattr(run.execucoes, "iniciar_varredura", varredura)
    monkeypatch.setattr(run.app, "run", executar)
    return chamadas


def test_varredura_roda_uma_vez_antes_do_app_run(espioes):
    run.main([])

    assert len(espioes) == 2  # exatamente uma chamada de cada
    assert espioes[0] == "varredura"
    assert espioes[1][0] == "run"


def test_host_e_porta_da_linha_de_comando_chegam_ao_app_run(espioes):
    run.main(["--host", "127.0.0.1", "--port", "9999"])

    assert espioes[1] == ("run", {"host": "127.0.0.1", "port": 9999, "debug": False})


def test_sem_argumentos_usa_host_e_porta_padrao(espioes):
    run.main([])

    assert espioes[1] == ("run", {"host": "0.0.0.0", "port": 8050, "debug": False})


def test_porta_nao_inteira_sai_com_codigo_2_sem_varredura(espioes):
    with pytest.raises(SystemExit) as excinfo:
        run.main(["--port", "abc"])

    assert excinfo.value.code == 2
    assert espioes == []


def test_processo_sobe_por_run_py_chama_main():
    """`python run.py --port abc` sai com 2 (argparse), o que só acontece se o
    bloco `__main__` chamar `main`."""
    resultado = subprocess.run(
        [sys.executable, "run.py", "--port", "abc"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert resultado.returncode == 2
    assert "iniciar_varredura" not in resultado.stderr
    assert "iniciar_varredura" not in resultado.stdout


def test_importar_app_app_nao_cria_a_thread_de_varredura():
    codigo = (
        "import app.app; from app.sistec import execucoes; "
        "print(execucoes._VARREDURA_THREAD)"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "None"
