"""Assistente de instalação e guarda das telas administrativas."""

import flask

from app.auth import email_valido, requer_autenticacao
from app.data import campi, instalacao as dados_instalacao
from app.data.campi import listar_campi
from app.data.config_store import set_contato_email, set_instituicao
from app.data.schema import DEFAULT_DB_PATH
from app.rotas import comum
from app.rotas.acesso import _MSG_EMAIL_INVALIDO

instalacao_bp = flask.Blueprint("instalacao_bp", __name__)


@instalacao_bp.route("/admin/instalacao", methods=["GET", "POST"])
@requer_autenticacao
def admin_instalacao():
    """Assistente da primeira configuração: identidade da instituição e lista
    de campi (lida do Sistec, colada ou digitada). Nada aqui é fixo numa
    instituição — é o que permite instalar o mesmo programa em outro IF."""
    mensagem = None
    sucesso = False
    erro_nome = erro_email = None
    valores = None

    if flask.request.method == "POST":
        acao = flask.request.form.get("acao")
        if acao == "salvar_instituicao":
            nome = flask.request.form.get("nome", "").strip()
            email = flask.request.form.get("contato_email", "").strip()
            if not nome:
                erro_nome = "Informe o nome da instituição."
            elif email and not email_valido(email):
                erro_email = _MSG_EMAIL_INVALIDO
            if erro_nome or erro_email:
                valores = flask.request.form
            else:
                set_instituicao(
                    nome=nome,
                    sigla=flask.request.form.get("sigla", "").strip(),
                    site=flask.request.form.get("site", "").strip(),
                )
                if email:
                    set_contato_email(email)
                mensagem = "Dados da instituição salvos."
                sucesso = True

        elif acao == "importar_perfis":
            from app.sistec.perfis import perfis_de_texto

            perfis, invalidas = perfis_de_texto(flask.request.form.get("lista_perfis", ""))
            if not perfis:
                mensagem = (
                    "Nenhuma linha no formato esperado (identificador ; nome do perfil). "
                    "Se você não tem os identificadores, use “Atualizar do Sistec” para lê-los."
                )
            else:
                try:
                    campi.salvar_captura([{**p, "ordem": i} for i, p in enumerate(perfis)], DEFAULT_DB_PATH)
                    mensagem = f"{len(perfis)} campus(i) importados."
                    sucesso = True
                    if invalidas:
                        mensagem += f" {len(invalidas)} linha(s) ignorada(s) por não ter identificador."
                except campi.CampusInvalido as exc:
                    mensagem = f"Não foi possível importar: {exc}."

        elif acao == "concluir":
            dados_instalacao.concluir()
            return flask.redirect("/admin/atualizar")

    return flask.render_template(
        "instalacao.html",
        usuario=comum.admin_email(),
        campi=listar_campi(),
        pendencias=dados_instalacao.pendencias(),
        mensagem=mensagem,
        sucesso=sucesso,
        erro_nome=erro_nome,
        erro_email=erro_email,
        valores=valores,
        **comum.contexto_base(),
    )


_ROTAS_SEM_INSTALACAO = ("/admin/login", "/admin/logout", "/admin/instalacao")


@instalacao_bp.before_app_request
def _exigir_instalacao():
    """Primeira execução (inclusive logo depois de instalar o programa): as
    telas administrativas levam ao assistente até a instalação ser concluída.
    O painel público segue acessível."""
    caminho = flask.request.path
    if not caminho.startswith("/admin/") or caminho.startswith(_ROTAS_SEM_INSTALACAO):
        return None
    if dados_instalacao.concluida():
        return None
    if not flask.session.get("admin_autenticado"):
        return None
    return flask.redirect("/admin/instalacao")
