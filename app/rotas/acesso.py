"""Rotas de acesso administrativo e recuperação de acesso."""

import flask

from app.auth import autenticar_sessao, credenciais_configuradas, email_valido, encerrar_sessao, esta_autenticado
from app.rotas import comum

acesso_bp = flask.Blueprint("acesso_bp", __name__)

_MSG_EMAIL_INVALIDO = "Informe um e-mail válido, por exemplo nome@suainstituicao.edu.br."
_MSG_SENHA_CURTA = "A senha deve ter pelo menos 8 caracteres."
_MSG_CONFIG_AUSENTE = (
    "Servidor sem credenciais administrativas configuradas "
    "(variáveis de ambiente ADMIN_EMAIL/ADMIN_PASSWORD_HASH ausentes neste processo). "
    "Nenhum usuário/senha vai funcionar até isso ser corrigido — não é um problema de senha errada."
)


@acesso_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """BC-05/AD-04: única porta de entrada autenticada do sistema — as 5
    páginas públicas (Dash `use_pages`) nunca passam por esta rota.

    `001-govbr-design-system` (T033): RF-10 a RF-14 — campos E-mail/Senha
    (em vez de Usuário/Senha), validação de formato por campo (RF-11),
    mensagem global genérica em caso de credencial incorreta, sem indicar
    qual campo errou (RF-12), foco no primeiro campo inválido."""
    if not credenciais_configuradas():
        return flask.render_template(
            "login.html", erro_global=_MSG_CONFIG_AUSENTE, email="", **comum.contexto_base()
        )

    if flask.request.method == "POST":
        email = flask.request.form.get("email", "").strip()
        senha = flask.request.form.get("senha", "")

        erro_email = None if email_valido(email) else _MSG_EMAIL_INVALIDO
        erro_senha = None if len(senha) >= 8 else _MSG_SENHA_CURTA
        if erro_email or erro_senha:
            return flask.render_template(
                "login.html",
                erro_email=erro_email,
                erro_senha=erro_senha,
                email=email,
                **comum.contexto_base(),
            )

        if autenticar_sessao(email, senha):
            return flask.redirect("/admin/atualizar")
        return flask.render_template(
            "login.html",
            erro_global="E-mail ou senha incorretos.",
            email=email,
            **comum.contexto_base(),
        )

    return flask.render_template("login.html", email="", **comum.contexto_base())


@acesso_bp.route("/admin/logout")
def admin_logout():
    encerrar_sessao()
    return flask.redirect("/admin/login")


@acesso_bp.route("/recuperar-acesso")
def recuperar_acesso():
    """RF-15/RN-10: pública, sem exigir sessão — orienta a pedir a
    redefinição à Pesquisa Institucional, sem nenhum campo de formulário."""
    return flask.render_template("recuperar_acesso.html", **comum.contexto_base())


@acesso_bp.before_app_request
def _exigir_sessao_previa():
    """PVP-07 (`previa-paginas-publicas`, T15): barra no servidor qualquer
    requisição a `/admin/previa/...` sem sessão autenticada, redirecionando
    para `/admin/login` antes de o Dash montar o layout. Camada a mais — não
    substitui a validação de posse de `obter_previa`/`abrir_leitura_previa`
    (T4/T7), que continuam valendo nos callbacks."""
    if flask.request.path.startswith("/admin/previa/") and not esta_autenticado():
        return flask.redirect("/admin/login")
    return None
