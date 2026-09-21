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


def _bloco_media(consulta):
    inicio = SEM_COMENTARIOS.index(consulta)
    abertura = SEM_COMENTARIOS.index("{", inicio)
    profundidade, i = 1, abertura + 1
    while profundidade:
        profundidade += {"{": 1, "}": -1}.get(SEM_COMENTARIOS[i], 0)
        i += 1
    return SEM_COMENTARIOS[abertura + 1 : i - 1]


def _regra(seletor_contem, texto=SEM_COMENTARIOS):
    for seletor, corpo in re.findall(r"([^{}]+)\{([^{}]*)\}", texto):
        if seletor_contem in seletor:
            return corpo
    raise AssertionError(f"sem regra para {seletor_contem}")


def test_a_partir_de_1600px_o_conteudo_e_limitado_ao_token_de_tv_e_centralizado():
    corpo = _regra(".container-fluid", _bloco_media("@media (min-width: 1600px)"))
    assert re.search(r"max-width:\s*var\(--grid-tv-maxwidth\)", corpo)
    assert re.search(r"margin-inline:\s*auto", corpo)


def test_controles_interativos_tem_area_minima_de_24px():
    assert re.search(r"--alvo-toque-minimo:\s*24px", SEM_COMENTARIOS)
    corpo = _regra("button, input, select")
    assert "min-width: var(--alvo-toque-minimo)" in corpo
    assert "min-height: var(--alvo-toque-minimo)" in corpo


def test_foco_visivel_tem_contorno_de_ao_menos_3px_na_cor_de_foco_do_ds():
    corpo = _regra(":focus-visible")
    largura = int(re.search(r"outline:\s*(\d+)px\s+solid\s+var\(--focus-color\)", corpo).group(1))
    assert largura >= 3


def test_menu_fica_persistente_e_aberto_a_partir_de_992px():
    bloco = _bloco_media("@media (min-width: 992px)")
    assert re.search(r"\.br-menu \.menu-container, \.br-menu\.active \.menu-container\s*\{[^}]*display:\s*block", bloco)


def test_a_partir_de_992px_o_menu_vira_barra_lateral_fixa_sem_botao():
    bloco = _bloco_media("@media (min-width: 992px)")
    assert re.search(r"body\s*\{[^}]*grid-template-columns:\s*var\(--menu-largura\)", bloco)
    assert re.search(r"\.br-menu\s*\{[^}]*position:\s*static", bloco)
    assert re.search(r"\.header-menu-trigger\s*\{[^}]*display:\s*none", bloco)


def test_sem_js_o_menu_fica_sempre_visivel():
    assert re.search(r"\.ds-sem-js \.br-menu \.menu-container\s*\{\s*display:\s*block", SEM_COMENTARIOS)


def test_dropdown_do_dash_usa_variaveis_do_ds():
    corpo = _regra(".filtro-dropdown .dash-dropdown-trigger")
    assert "var(--background)" in corpo
    assert "var(--color)" in corpo
    assert "var(--border-color)" in corpo


def test_o_bloco_do_tema_escuro_existe_e_todo_valor_dentro_dele_e_var():
    corpo = re.search(r':root\[data-tema="escuro"\]\s*\{([^}]*)\}', SEM_COMENTARIOS).group(1)
    valores = re.findall(r"--[\w-]+:\s*([^;]+);", corpo)
    assert valores
    assert all(valor.strip().startswith("var(--") for valor in valores)


@pytest.mark.parametrize("componente", ["br-header", "br-menu", "br-footer", "br-message", "br-card", "br-table", "br-input", "br-button"])
def test_o_tema_escuro_tem_regra_para_o_componente(componente):
    assert re.search(r':root\[data-tema="escuro"\]\s+\.' + componente + r"\b", SEM_COMENTARIOS)


def test_o_involucro_do_logotipo_mantem_superficie_clara_nos_dois_temas():
    assert re.search(r"\.logo-superficie\s*\{[^}]*background:\s*var\(--pure-0\)", SEM_COMENTARIOS)
    assert not re.search(r'data-tema="escuro"\][^{]*\.logo-superficie', SEM_COMENTARIOS)


def test_mensagem_quebra_texto_longo_e_o_pre_rola_dentro_do_proprio_quadro():
    assert re.search(r"\.br-message \.content\s*\{[^}]*overflow-wrap:\s*anywhere", SEM_COMENTARIOS)
    assert re.search(r"(?m)^pre\s*\{[^}]*overflow-x:\s*auto", SEM_COMENTARIOS)


def test_botao_do_ds_quebra_o_rotulo_em_vez_de_estourar_a_largura():
    corpo = _regra(".br-button{") if False else re.search(r"(?m)^\.br-button\s*\{([^}]*)\}", SEM_COMENTARIOS).group(1)
    assert "max-width: 100%" in corpo
    assert "white-space: normal" in corpo
    assert "min-height: var(--button-size)" in corpo


def test_style_css_nao_redefine_as_classes_de_grade_row_e_col_do_ds():
    assert not re.search(r"(?m)^\s*\.(?:row|col(?:-[\w-]+)?)\s*[,{]", SEM_COMENTARIOS)
