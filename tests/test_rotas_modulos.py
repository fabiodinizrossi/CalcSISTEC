"""Cada rota administrativa mora no blueprint da sua área (REF-01, REF-02)."""

import pathlib

import pytest

import app.app as app_module
from app.rotas import comum
from app.rotas.publico import UPLOADS_BRANDING_DIR

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# (URL como aparece em url_map, método, prefixo esperado do endpoint)
# Preenchido pelas tarefas de migração de cada área (T2-T9).
ROTAS_ESPERADAS = [
    ("/matriculas", "GET", "publico_bp"),
    ("/branding/logo", "GET", "publico_bp"),
    ("/admin/login", "GET", "acesso_bp"),
    ("/admin/login", "POST", "acesso_bp"),
    ("/admin/logout", "GET", "acesso_bp"),
    ("/recuperar-acesso", "GET", "acesso_bp"),
    ("/admin/instalacao", "GET", "instalacao_bp"),
    ("/admin/instalacao", "POST", "instalacao_bp"),
    ("/admin/config", "GET", "configuracoes_bp"),
    ("/admin/config", "POST", "configuracoes_bp"),
    ("/admin/config/captura", "GET", "configuracoes_bp"),
    ("/admin/atualizar/publicar", "POST", "publicacao_bp"),
    ("/admin/atualizar/desfazer", "POST", "publicacao_bp"),
    ("/admin/historico", "GET", "publicacao_bp"),
    ("/admin/atualizar/envio", "POST", "envio_bp"),
    ("/admin/atualizar", "GET", "atualizar_bp"),
    ("/admin/atualizar/execucao", "GET", "atualizar_bp"),
    ("/admin/atualizar/execucoes/<execucao_id>/salvar", "POST", "atualizar_bp"),
    ("/admin/atualizar/execucoes/<execucao_id>/descartar", "POST", "atualizar_bp"),
]


def _endpoint(url, metodo):
    for regra in app_module.server.url_map.iter_rules():
        if regra.rule == url and metodo in regra.methods:
            return regra.endpoint
    return None


@pytest.mark.parametrize("url,metodo,prefixo", ROTAS_ESPERADAS)
def test_rota_mora_no_blueprint_da_area(url, metodo, prefixo):
    endpoint = _endpoint(url, metodo)
    assert endpoint is not None, f"{metodo} {url} não está registrada"
    assert endpoint.startswith(prefixo + "."), f"{metodo} {url} está em {endpoint}, esperado {prefixo}"


def test_app_py_so_monta_o_app():
    texto = (RAIZ / "app" / "app.py").read_text(encoding="utf-8")
    assert "@server.route" not in texto
    assert "before_request" not in texto
    assert len(texto.splitlines()) <= 150


def test_pacote_rotas_existe_com_modulo_comum():
    assert (RAIZ / "app" / "rotas" / "__init__.py").exists()

    for nome in ("contexto_base", "admin_email", "execucao_da_sessao", "ano_base_config"):
        assert callable(getattr(comum, nome))


def test_uploads_branding_dir_aponta_para_app_data_uploads_branding():
    assert UPLOADS_BRANDING_DIR == str(RAIZ / "app" / "data" / "uploads" / "branding")


def test_contexto_base_reune_contato_e_instituicao(monkeypatch):
    monkeypatch.setattr(comum, "get_contato_email", lambda: "contato@iffar.edu.br")
    monkeypatch.setattr(comum, "dados_instituicao", lambda: {"nome": "IFFar"})

    ctx = comum.contexto_base()

    assert ctx == {"contato_email": "contato@iffar.edu.br", "instituicao": {"nome": "IFFar"}}


def test_admin_email_le_da_sessao(monkeypatch):
    class SessaoFake:
        def __init__(self, valor):
            self._valor = valor

        def get(self, chave, padrao=""):
            return self._valor if chave == "admin_usuario" else padrao

    monkeypatch.setattr(comum.flask, "session", SessaoFake("admin@iffar.edu.br"))

    assert comum.admin_email() == "admin@iffar.edu.br"


def test_execucao_da_sessao_busca_pelo_email_do_admin(monkeypatch):
    capturado = {}

    def obter_do_admin(email):
        capturado["email"] = email
        return {"execucao": email}

    monkeypatch.setattr(comum, "admin_email", lambda: "admin@iffar.edu.br")
    monkeypatch.setattr(comum.execucoes, "obter_do_admin", obter_do_admin)

    resultado = comum.execucao_da_sessao()

    assert capturado["email"] == "admin@iffar.edu.br"
    assert resultado == {"execucao": "admin@iffar.edu.br"}


def test_ano_base_config_le_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("ANO_BASE", "2025")

    assert comum.ano_base_config() == 2025


def test_ano_base_config_usa_padrao_quando_variavel_ausente(monkeypatch):
    monkeypatch.delenv("ANO_BASE", raising=False)

    assert comum.ano_base_config() == 2026
