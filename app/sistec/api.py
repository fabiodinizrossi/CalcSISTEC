"""*Blueprint* `/api/sistec`: rotas HTTP consumidas pela extensão
(`002-baixador-planilhas-sistec`, T047-T051, T060, D-16, D-19,
`interfaces/api-extensao-calcsistec.md` §3-§4).

Autenticação por `Authorization: Bearer <token>` (D-16) — nunca a sessão
Flask do administrador (evita CSRF e limita o alcance a uma execução/
captura). Erros nunca ecoam o conteúdo recebido (RN-13).
"""

import flask

from app.sistec import execucoes

bp = flask.Blueprint("sistec_api", __name__, url_prefix="/api/sistec")

CORPO_MAXIMO_PAR_BYTES = 200 * 1024 * 1024


@bp.before_request
def _exigir_https_fora_de_localhost():
    """D-19: recusa requisição HTTP simples fora de `localhost`/`127.0.0.1`,
    independentemente de `CALCSISTEC_HTTPS` (falha segura)."""
    host = (flask.request.host or "").split(":")[0]
    if flask.request.is_secure or host in ("localhost", "127.0.0.1"):
        return None
    return flask.jsonify({"erro": "https_obrigatorio"}), 403


def _token_do_cabecalho():
    auth = flask.request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth[len("Bearer ") :]


def _execucao_autenticada(execucao_id):
    token = _token_do_cabecalho()
    if not token:
        return None
    try:
        return execucoes.obter_por_token(execucao_id, token)
    except execucoes.ExecucaoInvalida:
        return None


def _captura_autenticada(captura_id):
    token = _token_do_cabecalho()
    if not token:
        return None
    try:
        return execucoes.obter_captura_por_token(captura_id, token)
    except execucoes.ExecucaoInvalida:
        return None


@bp.route("/execucoes/<execucao_id>/proximo", methods=["POST"])
def proximo(execucao_id):
    execucao = _execucao_autenticada(execucao_id)
    if execucao is None:
        return flask.jsonify({"erro": "nao_autorizado"}), 401
    return flask.jsonify(execucoes.proximo(execucao))


@bp.route("/execucoes/<execucao_id>/pares/<int:n>", methods=["PUT"])
def receber_par(execucao_id, n):
    execucao = _execucao_autenticada(execucao_id)
    if execucao is None:
        return flask.jsonify({"erro": "nao_autorizado"}), 401

    if flask.request.content_length and flask.request.content_length > CORPO_MAXIMO_PAR_BYTES:
        return "", 413

    conteudo = flask.request.get_data()
    try:
        execucoes.receber_bytes(execucao, n, conteudo)
    except ValueError as exc:
        codigo = str(exc)
        if codigo == "par_inesperado":
            return flask.jsonify({"erro": "par_inesperado"}), 409
        if codigo == "colunas_ausentes":
            return flask.jsonify({"erro": "colunas_ausentes"}), 422
        return flask.jsonify({"erro": "leitura_csv", "linha": None}), 422

    return "", 204


@bp.route("/execucoes/<execucao_id>/pares/<int:n>/falha", methods=["POST"])
def falha_par(execucao_id, n):
    execucao = _execucao_autenticada(execucao_id)
    if execucao is None:
        return flask.jsonify({"erro": "nao_autorizado"}), 401

    corpo = flask.request.get_json(silent=True) or {}
    try:
        execucoes.reportar_falha(execucao, n, corpo.get("motivo"))
    except execucoes.ExecucaoInvalida:
        return flask.jsonify({"erro": "par_inesperado"}), 409
    except ValueError:
        return flask.jsonify({"erro": "motivo_invalido"}), 422

    return "", 204


@bp.route("/capturas/<captura_id>/perfis", methods=["POST"])
def perfis_capturados(captura_id):
    captura = _captura_autenticada(captura_id)
    if captura is None:
        return flask.jsonify({"erro": "nao_autorizado"}), 401

    corpo = flask.request.get_json(silent=True) or {}
    perfis = corpo.get("perfis") or []
    if len(perfis) > 200:
        perfis = perfis[:200]

    execucoes.receber_perfis(captura, perfis)
    if captura.estado == "sem_resultado":
        return flask.jsonify({"erro": "nenhum_perfil"}), 422
    return "", 200


@bp.route("/capturas/<captura_id>/falha", methods=["POST"])
def falha_captura(captura_id):
    captura = _captura_autenticada(captura_id)
    if captura is None:
        return flask.jsonify({"erro": "nao_autorizado"}), 401

    corpo = flask.request.get_json(silent=True) or {}
    execucoes.reportar_falha_captura(captura, corpo.get("motivo"))
    return "", 204
