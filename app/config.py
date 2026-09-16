"""Configuração de segurança da sessão Flask (`002-baixador-planilhas-
sistec`, T059, D-19).

`SESSION_COOKIE_SAMESITE="Lax"` sempre; `SESSION_COOKIE_SECURE=True` quando
`CALCSISTEC_HTTPS=1` (implantação com HTTPS configurado, `CUTOVER.md`). As
ações novas desta feature mudam o painel público (publicar, desfazer), e
bytes com dado pessoal só podem trafegar cifrados.
"""

import os


def https_ativo():
    return os.environ.get("CALCSISTEC_HTTPS") == "1"


def aplicar_configuracao_sessao(server):
    server.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    server.config["SESSION_COOKIE_SECURE"] = https_ativo()
