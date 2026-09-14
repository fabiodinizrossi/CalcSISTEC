import os

import dash
import flask
import pandas as pd
import dash_bootstrap_components as dbc
from dash import html

from app.auth import autenticar_sessao, credenciais_configuradas, email_valido, encerrar_sessao, requer_autenticacao
from app.components.footer import make_footer
from app.components.header import make_header
from app.components.navigation import make_navigation
from app.data.config_store import (
    DEFAULT_LOGO_PATH,
    get_contato_email,
    get_logo_path,
    reset_contato_email,
    reset_logo,
    set_contato_email,
    set_logo,
)
from app.data.image_validation import ImagemInvalida, validar_e_normalizar_png
from app.data.ingest import UploadInvalido, processar_upload
from app.data.svg_sanitize import SvgInvalido, sanitizar_svg

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Início - Pesquisa Institucional - SISTEC",
)

# T021 (RF-05, WCAG 3.1.1): declara pt-BR no `<html>` — o índice padrão do
# Dash usa `lang="en"`.
app.index_string = """<!DOCTYPE html>
<html lang="pt-BR">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

server = app.server
server.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
# BC-05/AD-04: sessão Flask usada apenas para o guarda de acesso da rota
# administrativa de upload — as 5 páginas públicas nunca a consultam.
server.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# Tarefa 09 (BC-04): as 5 páginas públicas leem o dataset ativo direto do
# SQLite a cada carregamento (`app/data/consulta.py`), substituindo o antigo
# padrão de upload no navegador + `dcc.Store` de sessão — o upload agora só
# acontece na rota administrativa autenticada (`/admin/upload`, Tarefa 08).
#
# `001-govbr-design-system` (T019/T021): Header + NavigationMenu +
# page_container + Footer empilhados verticalmente (a barra lateral fixa
# saiu, RF-03). `app.layout` vira uma função (em vez de um componente
# estático) para que o rodapé releia `config_store.get_contato_email()` a
# cada carregamento de página — sem isso, uma alteração de e-mail em
# `/admin/config` só apareceria depois de reiniciar o processo (RN-12).
def serve_layout():
    return html.Div(
        [
            html.A("Ir para o conteúdo principal", href="#main-content", className="skip-link"),
            make_header(),
            make_navigation(),
            html.Main(
                id="main-content",
                role="main",
                children=dash.page_container,
            ),
            make_footer(),
        ]
    )


app.layout = serve_layout


_MSG_EMAIL_INVALIDO = "Informe um e-mail válido, por exemplo nome@iffarroupilha.edu.br."
_MSG_SENHA_CURTA = "A senha deve ter pelo menos 8 caracteres."
_MSG_CONFIG_AUSENTE = (
    "Servidor sem credenciais administrativas configuradas "
    "(variáveis de ambiente ADMIN_EMAIL/ADMIN_PASSWORD_HASH ausentes neste processo). "
    "Nenhum usuário/senha vai funcionar até isso ser corrigido — não é um problema de senha errada."
)

LOGO_MAX_BYTES = 500 * 1024  # RN-13: acima disso, rejeitado (RF-21).
UPLOADS_BRANDING_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads", "branding")


def _contexto_base():
    return {"contato_email": get_contato_email()}


@server.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """BC-05/AD-04: única porta de entrada autenticada do sistema — as 5
    páginas públicas (Dash `use_pages`) nunca passam por esta rota.

    `001-govbr-design-system` (T033): RF-10 a RF-14 — campos E-mail/Senha
    (em vez de Usuário/Senha), validação de formato por campo (RF-11),
    mensagem global genérica em caso de credencial incorreta, sem indicar
    qual campo errou (RF-12), foco no primeiro campo inválido."""
    if not credenciais_configuradas():
        return flask.render_template(
            "login.html", erro_global=_MSG_CONFIG_AUSENTE, email="", **_contexto_base()
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
                **_contexto_base(),
            )

        if autenticar_sessao(email, senha):
            return flask.redirect("/admin/upload")
        return flask.render_template(
            "login.html",
            erro_global="E-mail ou senha incorretos.",
            email=email,
            **_contexto_base(),
        )

    return flask.render_template("login.html", email="", **_contexto_base())


@server.route("/admin/logout")
def admin_logout():
    encerrar_sessao()
    return flask.redirect("/admin/login")


@server.route("/recuperar-acesso")
def recuperar_acesso():
    """RF-15/RN-10: pública, sem exigir sessão — orienta a pedir a
    redefinição à Pesquisa Institucional, sem nenhum campo de formulário."""
    return flask.render_template("recuperar_acesso.html", **_contexto_base())


@server.route("/admin/upload", methods=["GET", "POST"])
@requer_autenticacao
def admin_upload():
    """BC-05: guarda de acesso sobre BC-01 (`app/data/ingest.processar_upload`)
    — nenhum upload é aceito sem autenticação válida (`AGG-Administracao`).

    GAP herdado da Tarefa 05/07 (não bloqueante): `mapa_nomes_curso`
    (BR-MIGRAR-017, ~40 mapeamentos históricos Sistec -> PNP) ainda não foi
    externalizado como tabela de configuração real — usa dict vazio como
    placeholder até que a tabela real seja fornecida/confirmada (Tarefa 11).
    """
    mensagem = None
    sucesso = False
    if flask.request.method == "POST":
        arquivo = flask.request.files.get("arquivo")
        if arquivo is None or not arquivo.filename:
            mensagem = "Selecione um arquivo."
        elif server.config["MAX_CONTENT_LENGTH"] and flask.request.content_length and (
            flask.request.content_length > server.config["MAX_CONTENT_LENGTH"]
        ):
            mensagem = "Arquivo maior que 500 MB — envie um arquivo menor."
        else:
            try:
                xls = pd.ExcelFile(arquivo)
                planilhas = {
                    nome: pd.read_excel(xls, sheet_name=nome)
                    for nome in ("matriculas", "ciclos", "cursos", "campus", "fatores")
                    if nome in xls.sheet_names
                }
                resultado = processar_upload(
                    planilhas=planilhas,
                    mapa_nomes_curso={},
                    ano_base=int(os.environ.get("ANO_BASE", 2026)),
                    uploaded_by=flask.session.get("admin_usuario", "desconhecido"),
                    filename=arquivo.filename,
                )
                mensagem = f"Upload aceito: {resultado}"
                sucesso = True
            except UploadInvalido as exc:
                mensagem = f"Upload rejeitado: {exc}"
    return flask.render_template(
        "upload.html",
        usuario=flask.session.get("admin_usuario", ""),
        mensagem=mensagem,
        sucesso=sucesso,
        **_contexto_base(),
    )


@server.route("/admin/config", methods=["GET", "POST"])
@requer_autenticacao
def admin_config():
    """RF-19 a RF-22: e-mail de contato e logotipo administráveis
    (`001-govbr-design-system`, T036). Cada ação (`acao` no form) é
    independente — salvar/restaurar e-mail não afeta o logotipo e vice-versa."""
    contexto = {
        "contato_email": get_contato_email(),
        "erro_email": None,
        "mensagem_email": None,
        "sucesso_email": False,
        "mensagem_logo": None,
        "sucesso_logo": False,
    }

    if flask.request.method == "POST":
        acao = flask.request.form.get("acao")

        if acao == "salvar_email":
            novo_email = flask.request.form.get("contato_email", "").strip()
            if email_valido(novo_email):
                set_contato_email(novo_email)
                contexto["contato_email"] = novo_email
                contexto["mensagem_email"] = "E-mail de contato salvo."
                contexto["sucesso_email"] = True
            else:
                contexto["erro_email"] = _MSG_EMAIL_INVALIDO
                contexto["contato_email"] = novo_email
                contexto["mensagem_email"] = "Não foi possível salvar: e-mail inválido."

        elif acao == "restaurar_email":
            reset_contato_email()
            contexto["contato_email"] = get_contato_email()
            contexto["mensagem_email"] = "E-mail de contato restaurado ao padrão de fábrica."
            contexto["sucesso_email"] = True

        elif acao == "enviar_logo":
            arquivo = flask.request.files.get("logo")
            if arquivo is None or not arquivo.filename:
                contexto["mensagem_logo"] = "Selecione um arquivo de logotipo (SVG ou PNG)."
            else:
                dados = arquivo.read()
                if len(dados) > LOGO_MAX_BYTES:
                    contexto["mensagem_logo"] = "Arquivo maior que 500 KB — envie um logotipo menor."
                else:
                    extensao = os.path.splitext(arquivo.filename)[1].lower()
                    os.makedirs(UPLOADS_BRANDING_DIR, exist_ok=True)
                    try:
                        if extensao == ".svg":
                            limpo = sanitizar_svg(dados)
                            destino = os.path.join(UPLOADS_BRANDING_DIR, "logo-atual.svg")
                            with open(destino, "wb") as f:
                                f.write(limpo)
                            set_logo(destino)
                            contexto["mensagem_logo"] = "Logotipo atualizado."
                            contexto["sucesso_logo"] = True
                        elif extensao == ".png":
                            normalizado = validar_e_normalizar_png(dados)
                            destino = os.path.join(UPLOADS_BRANDING_DIR, "logo-atual.png")
                            with open(destino, "wb") as f:
                                f.write(normalizado)
                            set_logo(destino)
                            contexto["mensagem_logo"] = "Logotipo atualizado."
                            contexto["sucesso_logo"] = True
                        else:
                            contexto["mensagem_logo"] = "Formato não suportado — envie um arquivo .svg ou .png."
                    except (SvgInvalido, ImagemInvalida) as exc:
                        contexto["mensagem_logo"] = f"Logotipo rejeitado: {exc}"

        elif acao == "restaurar_logo":
            reset_logo()
            contexto["mensagem_logo"] = "Logotipo restaurado ao padrão de fábrica."
            contexto["sucesso_logo"] = True

    return flask.render_template("configuracoes.html", **contexto)


@server.route("/branding/logo")
def branding_logo():
    """RF-02/RF-21: serve o logotipo vigente. Sempre com *fallback* ao
    padrão de fábrica quando o arquivo configurado está ausente ou
    ilegível — nunca um erro visível ao visitante público (T037)."""
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
