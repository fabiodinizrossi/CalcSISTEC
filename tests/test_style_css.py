"""`style.css` só com o que o gov.br DS não cobre (DS-02, DS-29, DS-30, DS-54)."""

import re
from pathlib import Path

import pytest

CSS = (Path(__file__).resolve().parents[1] / "app" / "assets" / "style.css").read_text(encoding="utf-8")
SEM_COMENTARIOS = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
PONTOS_DO_DS = {576, 992, 1280, 1600}


def test_nao_ha_cor_literal():
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b", SEM_COMENTARIOS)
    assert not re.findall(r"\b(?:rgb|rgba|hsl|hsla)\(", SEM_COMENTARIOS)


def test_nao_ha_variavel_gov_propria():
    assert "--gov-" not in CSS


def test_nao_ha_os_pontos_de_quebra_antigos():
    assert "768px" not in CSS
    assert "320px" not in CSS


def test_todo_media_de_largura_usa_so_os_pontos_do_ds():
    consultas = re.findall(r"@media([^{]*)\{", SEM_COMENTARIOS)
    for consulta in consultas:
        larguras = {int(v) for v in re.findall(r"(?:min|max)-width:\s*(\d+)px", consulta)}
        assert larguras <= PONTOS_DO_DS, consulta
        if not larguras:
            assert "prefers-color-scheme" in consulta, consulta


@pytest.mark.parametrize("seletor", [".app-header", ".nav-menu", ".admin-nav", ".kpi-card", ".nav-card", ".hero"])
def test_nao_ha_seletor_do_shell_antigo(seletor):
    assert not re.search(re.escape(seletor) + r"(?![\w-])", SEM_COMENTARIOS)


@pytest.mark.parametrize(
    "seletor",
    [
        ".evasao-baixa",
        ".evasao-media",
        ".evasao-alta",
        ".gauge-value",
        ".gauge-situacao",
        ".gauge-meta",
        ".kpi-label",
        ".kpi-value",
    ],
)
def test_faixas_e_medidores_continuam_definidos_por_variaveis_do_ds(seletor):
    regras = re.findall(re.escape(seletor) + r"(?![\w-])[^{]*\{([^}]*)\}", SEM_COMENTARIOS)
    assert regras, f"{seletor} sem regra"
    assert any("var(--" in regra for regra in regras), seletor
