"""Paridade de IDs entre callbacks e layout, público e de prévia (CPR-02,
spec P1.2 AC3).

A causa raiz do defeito do painel público era estrutural: o callback de uma
página declarava `State` de um componente que só existia no layout de prévia.
Nada impedia a mesma classe de bug voltar num componente novo. Este teste
reúne todo `id` citado como `Input`/`State` dos callbacks de cada uma das
quatro páginas e exige que ele esteja presente **nos dois** layouts — o
público (`layout()`) e o de prévia (`layout(preview_id=...)`).

O `dash.callback_map` só é populado na primeira requisição ao servidor
(`Dash.enable_pages` registra o roteador de páginas num `before_request`), por
isso a fixture autouse faz um `GET /` antes de cada teste.
"""

import importlib
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arvore_dash import componentes  # noqa: E402
from app import app as _app  # noqa: E402, F401  (instancia e registra as páginas)

# página -> prefixo dos ids daquela página (cada página nomeia tudo com o
# próprio prefixo; o roteador de páginas do Dash usa `_pages_*`).
PAGINAS = {
    "matriculas": "matriculas-",
    "eficiencia": "eficiencia-",
    "evasao": "evasao-",
    "percentuais_legais": "percentuais-",
}


@pytest.fixture(autouse=True)
def roteador_registrado():
    """Primeira requisição: o Dash registra o roteador e os callbacks das
    páginas passam a aparecer em `callback_map`."""
    _app.server.test_client().get("/")


def _df(pagina):
    colunas = {
        "matriculas": ("cidade", "tipo_curso_pnp", "tipo_programa_curso"),
        "eficiencia": ("cidade", "modalidade_ensino"),
        "evasao": ("cidade", "tipo_curso_pnp"),
        "percentuais_legais": ("cidade", "tipo_programa_curso"),
    }[pagina]
    return pd.DataFrame({coluna: ["Valor"] for coluna in colunas})


def _ids_do_layout(modulo, monkeypatch, pagina, preview_id=None):
    """IDs presentes na árvore do layout, sem tocar banco: `_carregar` devolve
    um DataFrame mínimo e as funções de estado viram dublês."""
    monkeypatch.setattr(modulo, "_carregar", lambda _preview_id: (_df(pagina), 2026))
    monkeypatch.setattr(modulo, "dataset_disponivel", lambda: True)
    monkeypatch.setattr(modulo, "data_ultima_publicacao", lambda: None)

    layout = modulo.layout() if preview_id is None else modulo.layout(preview_id=preview_id)
    return {getattr(componente, "id", None) for componente in componentes(layout)}


def _ids_de_callback(prefixo):
    """IDs citados como `Input` ou `State` dos callbacks daquela página."""
    ids = set()
    for registro in _app.app.callback_map.values():
        entradas = list(registro.get("inputs") or []) + list(registro.get("state") or [])
        for entrada in entradas:
            id_ = entrada.get("id") if isinstance(entrada, dict) else getattr(entrada, "component_id", None)
            if isinstance(id_, str) and id_.startswith(prefixo):
                ids.add(id_)
    return ids


@pytest.mark.parametrize("pagina", sorted(PAGINAS))
def test_todo_input_e_state_do_callback_existe_nos_dois_layouts(pagina, monkeypatch):
    modulo = importlib.import_module(f"pages.{pagina}")
    prefixo = PAGINAS[pagina]

    ids_callback = _ids_de_callback(prefixo)
    assert ids_callback, f"nenhum callback encontrado para a página {pagina} (prefixo {prefixo})"

    ids_publico = _ids_do_layout(modulo, monkeypatch, pagina)
    ids_previa = _ids_do_layout(modulo, monkeypatch, pagina, preview_id="previa-de-teste")

    faltando_publico = sorted(ids_callback - ids_publico)
    faltando_previa = sorted(ids_callback - ids_previa)
    assert not faltando_publico, (
        f"{pagina}: Input/State de callback sem componente no layout público: {faltando_publico}"
    )
    assert not faltando_previa, (
        f"{pagina}: Input/State de callback sem componente no layout de prévia: {faltando_previa}"
    )
