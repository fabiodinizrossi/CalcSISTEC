"""Rotas de publicação, desfazer e histórico de atualizações."""

import flask

from app.auth import requer_autenticacao
from app.data import versoes
from app.data.historico import encerrar as historico_encerrar
from app.data.historico import iniciar as historico_iniciar
from app.data.historico import listar as historico_listar
from app.data.schema import DEFAULT_DB_PATH
from app.rotas import comum

publicacao_bp = flask.Blueprint("publicacao_bp", __name__)


def historico_iniciar_e_encerrar(tipo, admin_email, desfecho):
    """Ações que não têm execução/captura em memória (publicar, desfazer):
    abre e fecha a linha de histórico na mesma requisição."""
    historico_id = historico_iniciar(tipo, admin_email)
    historico_encerrar(historico_id, desfecho)
    return historico_id


@publicacao_bp.route("/admin/atualizar/publicar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_publicar():
    """Publica a versão interna e registra a ação no histórico."""
    versoes.publicar(DEFAULT_DB_PATH, admin_email=comum.admin_email())
    historico_iniciar_e_encerrar("publicacao", comum.admin_email(), "publicada")
    return "", 204


@publicacao_bp.route("/admin/atualizar/desfazer", methods=["POST"])
@requer_autenticacao
def admin_atualizar_desfazer():
    """Restaura a publicação anterior e registra a ação no histórico."""
    try:
        versoes.desfazer(DEFAULT_DB_PATH)
    except ValueError as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    historico_iniciar_e_encerrar("desfazer_publicacao", comum.admin_email(), "publicacao_desfeita")
    return "", 204


@publicacao_bp.route("/admin/historico", methods=["GET"])
@requer_autenticacao
def admin_historico():
    """Mostra os eventos do histórico de atualizações."""
    return flask.render_template(
        "historico.html", usuario=comum.admin_email(), eventos=historico_listar(), **comum.contexto_base()
    )
