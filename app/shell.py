"""Shell da interface: entrega do gov.br DS e (nas tasks seguintes) cabeçalho,
menu, breadcrumb e rodapé compartilhados por páginas Flask e Dash."""

import os

from flask import Blueprint

PASTA_STATIC = os.path.join(os.path.dirname(__file__), "static")

# O DS fica fora de `app/assets/`: o Dash carrega tudo de lá, e o shell decide
# o que carregar (AD-002).
ds_static = Blueprint("ds_static", __name__, static_folder=PASTA_STATIC, static_url_path="/ds")


def init_shell(server, dash_app):
    server.register_blueprint(ds_static)
