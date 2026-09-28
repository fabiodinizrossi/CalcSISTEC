"""Rotas administrativas de coleta de dados do Sistec."""

import flask

from app.auth import requer_autenticacao
from app.data.campi import existe_campus_sem_unidade, listar_campi
from app.data.historico import encerrar as historico_encerrar
from app.data.historico import iniciar as historico_iniciar
from app.rotas import comum
from app.sistec import execucoes, navegador

coleta_sistec_bp = flask.Blueprint("coleta_sistec_bp", __name__)


@coleta_sistec_bp.route("/admin/atualizar/sistec", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec():
    """Botão único "Atualizar do Sistec": abre uma janela do navegador para o
    login gov.br e, depois dele, lê os campi, baixa ciclos e matrículas e
    monta a prévia (`app/sistec/navegador.py`). Substitui a extensão no uso
    local."""
    estado_navegador = navegador.status(comum.admin_email())
    if estado_navegador and estado_navegador["ativa"]:
        return flask.jsonify({"erro": "atualizacao_em_andamento"}), 409
    execucao = comum.execucao_da_sessao()
    if execucao is not None and execucao.estado not in execucoes.ESTADOS_TERMINAIS:
        erro = "previa_pendente" if execucao.estado == "previa" else "execucao_em_andamento"
        return flask.jsonify({"erro": erro}), 409

    historico_id = historico_iniciar("baixa", comum.admin_email())
    try:
        navegador.iniciar(comum.admin_email(), historico_id=historico_id)
    except execucoes.ExecucaoInvalida:
        historico_encerrar(historico_id, "cancelada")
        return flask.jsonify({"erro": "atualizacao_em_andamento"}), 409
    return "", 202


@coleta_sistec_bp.route("/admin/atualizar/sistec/login-feito", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec_login_feito():
    """Reserva para quando a detecção automática do login não dispara."""
    if not navegador.confirmar_login(comum.admin_email()):
        return flask.jsonify({"erro": "sem_atualizacao_aguardando_login"}), 409
    return "", 204


@coleta_sistec_bp.route("/admin/atualizar/sistec/cancelar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_sistec_cancelar():
    """Com a coleta em andamento, a thread do navegador encerra a execução e o
    histórico. Sem ela (ex.: execução presa de uma tentativa anterior),
    cancela a execução aqui mesmo."""
    if navegador.cancelar(comum.admin_email()):
        return "", 204
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.estado in execucoes.ESTADOS_TERMINAIS:
        return flask.jsonify({"erro": "nada_para_cancelar"}), 409
    execucoes.cancelar(execucao)
    if execucao.historico_id:
        historico_encerrar(execucao.historico_id, "cancelada", pausas=execucao.pausas)
    return "", 204


@coleta_sistec_bp.route("/admin/atualizar/execucoes", methods=["POST"])
@requer_autenticacao
def admin_atualizar_criar_execucao():
    campi = [c for c in listar_campi() if c["co_unidade"]]
    if not campi:
        return flask.jsonify({"erro": "sem_campus_com_unidade"}), 409

    try:
        historico_id = historico_iniciar("baixa", comum.admin_email())
        execucao = execucoes.criar_execucao(comum.admin_email(), campi, historico_id=historico_id)
    except execucoes.ExecucaoInvalida:
        return flask.jsonify({"erro": "execucao_em_andamento"}), 409

    return flask.jsonify({"execucao_id": execucao.id, "token": execucao.token})


@coleta_sistec_bp.route("/admin/atualizar/execucoes/<execucao_id>/iniciar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_iniciar(execucao_id):
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    if existe_campus_sem_unidade():
        return flask.jsonify({"erro": "campus_sem_unidade"}), 409

    try:
        execucoes.iniciar_baixa(execucao)
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    return "", 204


@coleta_sistec_bp.route("/admin/atualizar/execucoes/<execucao_id>/retomar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_retomar(execucao_id):
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    try:
        execucoes.retomar(execucao)
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    return "", 204


@coleta_sistec_bp.route("/admin/atualizar/execucoes/<execucao_id>/cancelar", methods=["POST"])
@requer_autenticacao
def admin_atualizar_cancelar(execucao_id):
    execucao = comum.execucao_da_sessao()
    if execucao is None or execucao.id != execucao_id:
        return flask.jsonify({"erro": "execucao_nao_encontrada"}), 404
    try:
        execucoes.cancelar(execucao)
    except execucoes.ExecucaoInvalida as exc:
        return flask.jsonify({"erro": str(exc)}), 409
    if execucao.historico_id:
        historico_encerrar(execucao.historico_id, "cancelada", pausas=execucao.pausas)
    return "", 204
