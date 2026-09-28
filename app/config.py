"""Configuração de segurança da sessão Flask.

`SESSION_COOKIE_SAMESITE="Lax"` sempre; `SESSION_COOKIE_SECURE=True` quando
`CALCSISTEC_HTTPS=1` (implantação com HTTPS configurado, ver `DEPLOY.md`).
Publicar e desfazer mudam o painel público; bytes com dados pessoais só podem
trafegar cifrados.
"""

import os


def https_ativo():
    return os.environ.get("CALCSISTEC_HTTPS") == "1"


def aplicar_configuracao_sessao(server):
    server.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    server.config["SESSION_COOKIE_SECURE"] = https_ativo()
