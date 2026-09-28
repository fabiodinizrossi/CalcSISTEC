"""Confere se docstrings e comentários descrevem o código sem IDs de spec."""

import ast
import io
import pathlib
import re
import subprocess
import tokenize

import pytest


RAIZ = pathlib.Path(__file__).resolve().parent.parent

PADROES = [
    re.compile(r"\b(BR-MIGRAR|BR-HUMANA|RISK|UPL|CPR|PVP|MAT|DS|AD|RF|RN|DEV|AMB|WDG|LIM|DEP|DOC|EST|PT|AGG|BC|REF|PAR|PBI|SEG|EXP|IMP)-\d+"),
    re.compile(r"\b[DP]-\d+\b"),
    re.compile(r"\bT-?\d{1,3}\b"),
    re.compile(r"\bTarefa \d+"),
    re.compile(r"roadmap\.md|data-delta\.md|f0-resultado\.md|data_migration_plan\.md|target_[a-z_]+\.md|paradigm_decision\.md|parity_tests|parity_specs|onboarding\.md|regression-watch|cutover_plan|_reversa_|reconstruction-plan|\d{3}-[a-z]+-[a-z-]+"),
]

# Cada tarefa de limpeza acrescenta aqui os arquivos que revisou.
ALVOS_LIMPOS = [
    "app/domain", "app/data", "app/sistec", "app/pages", "app/components",
    "app/rotas", "app/app.py", "app/shell.py", "app/auth.py",
    "app/config.py", "app/admin_campi.py", "app/__init__.py", "run.py",
    "scripts",
]


def _arquivos(alvo):
    caminho = RAIZ / alvo
    if caminho.is_file():
        return [caminho]
    return sorted(caminho.rglob("*.py"))


def _trechos(caminho):
    fonte = caminho.read_text(encoding="utf-8")
    for tok in tokenize.generate_tokens(io.StringIO(fonte).readline):
        if tok.type == tokenize.COMMENT:
            yield tok.start[0], tok.string
    arvore = ast.parse(fonte)
    for no in ast.walk(arvore):
        if isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(no, clean=False)
            if doc is not None:
                yield no.body[0].lineno, doc


@pytest.mark.parametrize("alvo", ALVOS_LIMPOS)
def test_docstrings_e_comentarios_sem_ids_de_spec(alvo):
    achados = []
    for caminho in _arquivos(alvo):
        for linha, texto in _trechos(caminho):
            for padrao in PADROES:
                encontrado = padrao.search(texto)
                if encontrado:
                    achados.append(f"{caminho.relative_to(RAIZ)}:{linha}: {encontrado.group(0)!r}")
    assert not achados, "Docstring ou comentário com ID de spec:\n" + "\n".join(achados)


@pytest.mark.parametrize("alvo", ALVOS_LIMPOS)
def test_nenhuma_docstring_ficou_vazia(alvo):
    vazias = []
    for caminho in _arquivos(alvo):
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if isinstance(no, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(no)
                if doc is not None and not doc.strip():
                    vazias.append(f"{caminho.relative_to(RAIZ)}:{getattr(no, 'lineno', 1)}")
    assert not vazias, "Docstring vazia:\n" + "\n".join(vazias)


def test_todos_os_modulos_app_estao_cobertos():
    rastreados = subprocess.run(
        ["git", "ls-files", "--", "app"],
        cwd=RAIZ,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    modulos = {nome for nome in rastreados if nome.endswith(".py")}
    cobertos = {caminho.relative_to(RAIZ).as_posix() for alvo in ALVOS_LIMPOS for caminho in _arquivos(alvo)}
    assert not modulos - cobertos, f"Módulos sem teste de higiene: {sorted(modulos - cobertos)}"


def test_relatorio_de_prontidao_sem_numeracao_de_tarefas(capsys):
    from scripts.verificar_prontidao_cutover import imprimir_relatorio

    imprimir_relatorio([])
    saida = capsys.readouterr().out

    assert "Tarefa" not in saida
    assert "[ ] Paridade com o Power BI conferida (.specs/features/mvp-2-paridade/relatorio-paridade.md)" in saida
