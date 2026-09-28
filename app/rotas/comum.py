"""Funções auxiliares usadas por mais de um grupo de rotas administrativas."""

import os

import flask

from app.data.config_store import dados_instituicao, get_contato_email
from app.sistec import execucoes


def contexto_base():
    return {"contato_email": get_contato_email(), "instituicao": dados_instituicao()}


def admin_email():
    return flask.session.get("admin_usuario", "")


def execucao_da_sessao():
    """Obtém a execução do administrador da sessão para as rotas de atualização."""
    execucao = execucoes.obter_do_admin(admin_email())
    return execucao


def ano_base_config():
    return int(os.environ.get("ANO_BASE", 2026))
