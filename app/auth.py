"""BC-05 (Administração): autenticação e controle de acesso da rota de upload.

Implementado na Tarefa 08 do plano de reconstrução (seção "BC-05", AD-04 e
BR-MIGRAR-027).

Único ponto do sistema com requisito de segurança de acesso (§AGG-Administracao):
a rota administrativa de upload exige login; as 5 páginas de
consumo público nunca exigem autenticação (`BR-MIGRAR-027`, decisão confirmada —
"é público, podem ver todos os dados do instituto inteiro"). Não é um serviço de
identidade separado (`AD-03`, monolito único) — apenas um guarda de rota simples
sobre a sessão Flask já embutida no Dash (`app.server`).

Credenciais vêm de variáveis de ambiente (`ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`
— hash gerado com `werkzeug.security.generate_password_hash`), nunca hardcoded.
`ADMIN_EMAIL` substitui o antigo `ADMIN_USERNAME` (RN-06, `001-govbr-design-system`).
"""

import os
import re
import secrets
from functools import wraps

import flask
from werkzeug.security import check_password_hash

SESSION_KEY = "admin_autenticado"

# RN-07: parte local, `@`, domínio com ao menos um ponto — validação de
# formato simples, não RFC 5322 completa (não é o ponto de verdade sobre
# e-mails existentes, apenas evita entradas obviamente inválidas).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def email_valido(email):
    return bool(email) and bool(_EMAIL_RE.match(email.strip()))


def credenciais_configuradas():
    """True se `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH` estão definidas no
    ambiente do processo atual. Usado só para distinguir, na mensagem de
    erro do login, "servidor mal configurado" de "usuário/senha errados" —
    não vaza se um *usuário específico* existe, apenas se a configuração de
    admin existe."""
    return bool(os.environ.get("ADMIN_EMAIL")) and bool(os.environ.get("ADMIN_PASSWORD_HASH"))


def verificar_credenciais(usuario, senha):
    """Compara contra `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH` do ambiente (RN-06,
    RN-07). Se as variáveis de ambiente não estiverem configuradas, ou se o
    e-mail informado não tem formato válido, nenhuma credencial é aceita
    (falha segura) — não há usuário/senha padrão."""
    usuario_esperado = os.environ.get("ADMIN_EMAIL")
    hash_esperado = os.environ.get("ADMIN_PASSWORD_HASH")
    if not usuario_esperado or not hash_esperado:
        return False
    if not email_valido(usuario):
        return False
    return usuario == usuario_esperado and check_password_hash(hash_esperado, senha)


def autenticar_sessao(usuario, senha):
    """Autentica e, se válido, marca a sessão Flask como autenticada.
    Retorna True/False — nunca lança exceção para uma tentativa inválida.

    Grava um `sessao_id` opaco a cada login (PVP-07, `previa-paginas-publicas`):
    vincula a execução de envio à sessão que a iniciou."""
    if verificar_credenciais(usuario, senha):
        flask.session[SESSION_KEY] = True
        flask.session["admin_usuario"] = usuario
        flask.session["sessao_id"] = secrets.token_urlsafe(16)
        return True
    return False


def esta_autenticado():
    return bool(flask.session.get(SESSION_KEY))


def sessao_id_atual():
    """Identificador opaco da sessão administrativa atual, para vincular a
    execução de envio à sessão dona (PVP-07). Cria um quando ausente; nunca
    devolve vazio."""
    sessao_id = flask.session.get("sessao_id")
    if not sessao_id:
        sessao_id = secrets.token_urlsafe(16)
        flask.session["sessao_id"] = sessao_id
    return sessao_id


def encerrar_sessao():
    flask.session.pop(SESSION_KEY, None)
    flask.session.pop("admin_usuario", None)
    flask.session.pop("sessao_id", None)


def requer_autenticacao(view_func):
    """Decorator para rotas Flask administrativas (ex.: `/admin/upload`).
    Redireciona para `/admin/login` quando a sessão não está autenticada —
    nunca aplicado às 5 páginas públicas do painel (`BR-MIGRAR-027`)."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not esta_autenticado():
            return flask.redirect("/admin/login")
        return view_func(*args, **kwargs)

    return wrapper
