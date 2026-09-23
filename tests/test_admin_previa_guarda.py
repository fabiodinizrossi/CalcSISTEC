"""Testes do guarda de sessão das rotas de prévia (`previa-paginas-publicas`,
T15): `before_request` redireciona `/admin/previa/...` sem sessão para
`/admin/login`; com sessão, não interfere (PVP-07).
"""

import flask
import pytest

from app import app as app_module


def test_previa_sem_sessao_redireciona_para_login():
    with app_module.server.test_request_context("/admin/previa/abc/matriculas"):
        resposta = app_module._exigir_sessao_previa()
        assert resposta is not None
        assert resposta.status_code in (301, 302)
        assert "/admin/login" in resposta.headers.get("Location", "")


def test_previa_com_sessao_nao_interfere():
    with app_module.server.test_request_context("/admin/previa/abc/matriculas"):
        flask.session["admin_autenticado"] = True
        assert app_module._exigir_sessao_previa() is None


def test_rota_publica_nao_interfere():
    with app_module.server.test_request_context("/"):
        assert app_module._exigir_sessao_previa() is None
