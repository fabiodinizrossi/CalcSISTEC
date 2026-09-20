"""Parciais Jinja do shell (`app/templates/shell/`)."""

import re

import pytest
from flask import render_template

from app import app as app_module


@pytest.fixture(scope="module")
def servidor():
    return app_module.server


def renderizar(servidor, modelo, **contexto):
    with servidor.test_request_context("/"):
        return render_template(modelo, **contexto)


def test_head_tem_viewport_e_um_unico_core_min_css(servidor):
    html = renderizar(servidor, "shell/_head.html", titulo="Matrículas")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert len(re.findall(r'<link[^>]+href="/ds/govbr-ds/dist/core\.min\.css"', html)) == 1
    assert "<title>Matrículas</title>" in html


def test_head_nao_referencia_url_externa(servidor):
    html = renderizar(servidor, "shell/_head.html", titulo="Início")
    assert "http://" not in html
    assert "https://" not in html
