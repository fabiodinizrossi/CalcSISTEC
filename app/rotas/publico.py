"""Rotas públicas que não exigem autenticação administrativa."""

import os

import flask

from app.data.config_store import DEFAULT_LOGO_PATH, get_logo_path

# Caminho da pasta de uploads de branding: mantém o mesmo destino de
# app/data/uploads/branding, mesmo sendo importado de app/rotas/publico.py.
UPLOADS_BRANDING_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "uploads", "branding"
)

publico_bp = flask.Blueprint("publico_bp", __name__)


@publico_bp.route("/matriculas")
def matriculas_legado():
    """Rota antiga da página Matrículas: agora a landing é `/` (Matrículas),
    então redireciona para lá para não quebrar links antigos."""
    return flask.redirect("/")


@publico_bp.route("/branding/logo")
def branding_logo():
    """Serve o logotipo vigente. Sempre com fallback ao padrão de fábrica
    quando o arquivo configurado está ausente ou ilegível — nunca um erro
    visível ao visitante público."""
    caminho = get_logo_path()
    conteudo = None
    if caminho and os.path.isfile(caminho):
        try:
            with open(caminho, "rb") as f:
                conteudo = f.read()
        except OSError:
            conteudo = None

    if conteudo is None:
        caminho = DEFAULT_LOGO_PATH
        with open(caminho, "rb") as f:
            conteudo = f.read()

    mimetype = "image/svg+xml" if caminho.lower().endswith(".svg") else "image/png"
    resposta = flask.Response(conteudo, mimetype=mimetype)
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Cache-Control"] = "no-cache"
    return resposta
