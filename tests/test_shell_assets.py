"""Entrega do gov.br DS por `app/static/` (DS-24, DS-28): o Dash não carrega o DS
como asset, e o servidor Flask o serve em `/ds/`."""

from pathlib import Path

import re

import pytest

RAIZ_APP = Path(__file__).resolve().parents[1] / "app"


@pytest.fixture(scope="module")
def cliente():
    from app import app as app_module

    return app_module.server.test_client()


def test_ds_sai_de_assets_e_vai_para_static():
    assert not (RAIZ_APP / "assets" / "govbr-ds").exists()
    assert (RAIZ_APP / "static" / "govbr-ds" / "dist" / "core.min.css").is_file()
    assert (RAIZ_APP / "static" / "govbr-ds" / "dist" / "core-init.min.js").is_file()


@pytest.mark.parametrize("arquivo", ["core.min.css", "core-init.min.js"])
def test_ds_e_servido_em_ds(cliente, arquivo):
    """O corpo é o arquivo do DS (o catch-all do Dash também responde 200, com o índice)."""
    resposta = cliente.get(f"/ds/govbr-ds/dist/{arquivo}")
    assert resposta.status_code == 200
    assert resposta.data == (RAIZ_APP / "static" / "govbr-ds" / "dist" / arquivo).read_bytes()
    resposta.close()


def test_login_referencia_o_ds_em_ds_e_nao_em_assets(cliente):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert "/ds/govbr-ds/dist/core.min.css" in html
    assert "/assets/govbr-ds/" not in html


def test_atualizar_js_sai_de_assets_e_e_servido_em_ds(cliente):
    """O Dash carregava `app/assets/js/atualizar.js` em todas as páginas públicas."""
    assert not (RAIZ_APP / "assets" / "js").exists()
    resposta = cliente.get("/ds/js/atualizar.js")
    assert resposta.status_code == 200
    assert resposta.data == (RAIZ_APP / "static" / "js" / "atualizar.js").read_bytes()
    resposta.close()


def test_agrupamento_de_matriculas_e_servido_e_referenciado_pelo_shell(cliente):
    caminho = RAIZ_APP / "static" / "js" / "agrupamento-matriculas.js"
    resposta = cliente.get("/ds/js/agrupamento-matriculas.js")
    assert resposta.status_code == 200
    assert resposta.data == caminho.read_bytes()
    resposta.close()
    scripts = (RAIZ_APP / "templates" / "shell" / "_scripts.html").read_text(encoding="utf-8")
    assert 'src="/ds/js/agrupamento-matriculas.js"' in scripts


def test_tela_de_atualizar_referencia_o_script_em_ds(monkeypatch):
    from app import app as app_module

    cliente = app_module.server.test_client()
    with cliente.session_transaction() as sessao:
        sessao["admin_usuario"] = "pi@ife.edu.br"
        sessao["admin_autenticado"] = True
    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: True)

    html = cliente.get("/admin/atualizar").get_data(as_text=True)
    assert 'src="/ds/js/atualizar.js"' in html
    assert "/assets/js/" not in html


def test_shell_antigo_foi_removido():
    for antigo in (
        "components/header.py",
        "components/footer.py",
        "components/navigation.py",
        "assets/nav-toggle.js",
        "templates/_admin_nav.html",
    ):
        assert not (RAIZ_APP / antigo).exists(), antigo


def test_nada_em_app_referencia_o_shell_antigo():
    referencias = ("components.header", "components.footer", "components.navigation", "_admin_nav", "nav-toggle")
    codigo = [a for a in RAIZ_APP.rglob("*.py") if "static" not in a.parts]
    modelos_e_assets = [
        a
        for pasta in ("templates", "assets")
        for a in (RAIZ_APP / pasta).rglob("*")
        if a.is_file() and a.suffix in (".html", ".js", ".css")
    ]
    for arquivo in codigo + modelos_e_assets:
        texto = arquivo.read_text(encoding="utf-8")
        for referencia in referencias:
            assert referencia not in texto, f"{arquivo.name} ainda cita {referencia}"


RECURSOS_LOCAIS = re.compile(r'<(?:link|script|img)\b[^>]*\b(?:href|src)="([^"]+)"')


def _recursos(html):
    return [url for url in RECURSOS_LOCAIS.findall(html) if not url.startswith(("#", "data:"))]


@pytest.mark.parametrize("caminho", ["/admin/login", "/"])
def test_todo_recurso_do_html_e_local_e_resolve_para_200(cliente, caminho):
    html = cliente.get(caminho).get_data(as_text=True)
    recursos = _recursos(html)
    assert recursos
    for url in recursos:
        assert not url.startswith(("http://", "https://", "//")), url
        resposta = cliente.get(url.split("?")[0])
        assert resposta.status_code == 200, url
        resposta.close()


def test_os_arquivos_de_fonte_do_css_da_rawline_resolvem_para_200(cliente):
    css = cliente.get("/ds/vendor/rawline/rawline.css").get_data(as_text=True)
    urls = re.findall(r'url\("([^"]+)"\)', css)
    assert len(urls) == 7
    for url in urls:
        assert not url.startswith(("http://", "https://", "//")), url
        resposta = cliente.get(url)
        assert resposta.status_code == 200, url
        resposta.close()


def test_os_webfonts_do_font_awesome_resolvem_para_200(cliente):
    css = cliente.get("/ds/vendor/fontawesome/css/all.min.css").get_data(as_text=True)
    urls = re.findall(r"url\(([^)]+)\)", css)
    assert urls
    for url in urls:
        assert not url.startswith(("http://", "https://", "//")), url
        caminho = url.split("?")[0].split("#")[0]
        resposta = cliente.get("/ds/vendor/fontawesome/css/" + caminho)
        assert resposta.status_code == 200, url
        resposta.close()


def test_font_awesome_e_vendorizado_localmente():
    raiz = RAIZ_APP / "static" / "vendor" / "fontawesome"
    assert (raiz / "css" / "all.min.css").is_file()
    assert (raiz / "LICENSE.txt").is_file()
    for familia in ("fa-solid-900", "fa-regular-400", "fa-brands-400"):
        for extensao in (".woff2", ".woff", ".ttf", ".eot", ".svg"):
            assert (raiz / "webfonts" / f"{familia}{extensao}").is_file(), f"{familia}{extensao}"


def test_o_script_do_shell_instancia_os_componentes_do_ds_na_carga():
    """`core.min.js` só registra os comportamentos; `core-init.min.js` também instancia
    `br-menu`, `br-header` e os demais (verificado no Chrome: com `core.min.js` o botão
    do menu não abre)."""
    dist = RAIZ_APP / "static" / "govbr-ds" / "dist"
    chamadas_no_init = (dist / "core-init.min.js").read_text(encoding="utf-8").count(".initInstanceAll()")
    chamadas_na_biblioteca = (dist / "core.min.js").read_text(encoding="utf-8").count(".initInstanceAll()")
    assert chamadas_no_init == chamadas_na_biblioteca + 1
    with open(RAIZ_APP / "templates" / "shell" / "_scripts.html", encoding="utf-8") as arquivo:
        assert "core-init.min.js" in arquivo.read()
