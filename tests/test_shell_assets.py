"""Entrega do gov.br DS por `app/static/` (DS-24, DS-28): o Dash não carrega o DS
como asset, e o servidor Flask o serve em `/ds/`."""

from pathlib import Path

import pytest

RAIZ_APP = Path(__file__).resolve().parents[1] / "app"


@pytest.fixture(scope="module")
def cliente():
    from app import app as app_module

    return app_module.server.test_client()


def test_ds_sai_de_assets_e_vai_para_static():
    assert not (RAIZ_APP / "assets" / "govbr-ds").exists()
    assert (RAIZ_APP / "static" / "govbr-ds" / "dist" / "core.min.css").is_file()
    assert (RAIZ_APP / "static" / "govbr-ds" / "dist" / "core.min.js").is_file()


@pytest.mark.parametrize("arquivo", ["core.min.css", "core.min.js"])
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
