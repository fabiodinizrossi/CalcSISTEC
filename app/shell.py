"""Shell da interface: entrega do gov.br DS e (nas tasks seguintes) cabeçalho,
menu, breadcrumb e rodapé compartilhados por páginas Flask e Dash."""

import os

from flask import Blueprint, request

from app.data.config_store import dados_instituicao, get_contato_email

PASTA_STATIC = os.path.join(os.path.dirname(__file__), "static")

# O DS fica fora de `app/assets/`: o Dash carrega tudo de lá, e o shell decide
# o que carregar (AD-002).
ds_static = Blueprint("ds_static", __name__, static_folder=PASTA_STATIC, static_url_path="/ds")

PAGINAS_PUBLICAS = [
    ("Início", "/"),
    ("Matrículas", "/matriculas"),
    ("Eficiência Acadêmica", "/eficiencia"),
    ("Taxa de Evasão Anual", "/evasao"),
    ("Percentuais Legais", "/percentuais-legais"),
]

PAGINAS_ADMIN = [
    ("Atualizar dados", "/admin/atualizar"),
    ("Histórico de atualizações", "/admin/historico"),
    ("Configurações", "/admin/config"),
]

_SEM_MENU = ("/admin/login", "/recuperar-acesso", "/admin/instalacao")


def _trilha(caminho):
    """Migalhas da página como pares (rótulo, href); a última é a página atual."""
    if caminho == "/admin/campi":
        return [("Configurações", "/admin/config"), ("Campi", caminho)]
    campi = [("Configurações", "/admin/config"), ("Campi", "/admin/campi")]
    if caminho == "/admin/campi/novo":
        return campi + [("Incluir", caminho)]
    partes = caminho.split("/")
    if len(partes) == 5 and partes[:3] == ["", "admin", "campi"] and partes[4] == "editar":
        return campi + [("Editar", caminho)]
    for rotulo, href in PAGINAS_PUBLICAS[1:] + PAGINAS_ADMIN:
        if caminho == href:
            return [("Início", "/"), (rotulo, href)]
    return []


def _texto(valor):
    return (valor or "").strip()


def contexto_shell(caminho):
    """Menu, breadcrumb e identidade que o shell mostra na página `caminho`."""
    caminho = caminho.rstrip("/") or "/"
    itens = PAGINAS_ADMIN if caminho.startswith("/admin/") else PAGINAS_PUBLICAS
    trilha = _trilha(caminho)
    return {
        "com_menu": caminho not in _SEM_MENU,
        "menu": [{"rotulo": rotulo, "href": href, "ativo": href == caminho} for rotulo, href in itens],
        "breadcrumb": [
            {"rotulo": rotulo, "href": href if i < len(trilha) - 1 else None}
            for i, (rotulo, href) in enumerate(trilha)
        ],
        "instituicao": {chave: _texto(valor) for chave, valor in dados_instituicao().items()},
        "contato_email": _texto(get_contato_email()),
    }


def init_shell(server, dash_app):
    server.register_blueprint(ds_static)

    @server.context_processor
    def contexto_do_shell():
        contexto = contexto_shell(request.path)
        return {
            "shell": contexto,
            "instituicao": contexto["instituicao"],
            "contato_email": contexto["contato_email"],
        }
