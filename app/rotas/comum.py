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
    """Confere que a execução pertence ao administrador da sessão (D-14
    remove o upload; toda ação de `/admin/atualizar/*` passa por aqui)."""
    execucao = execucoes.obter_do_admin(admin_email())
    return execucao


def ano_base_config():
    return int(os.environ.get("ANO_BASE", 2026))
