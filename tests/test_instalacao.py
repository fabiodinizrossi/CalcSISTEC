"""Testes da instalação para qualquer instituição (`app/data/instalacao.py`,
`app/data/config_store.py`, `app/sistec/perfis.perfis_de_texto`).

Nada de identidade fica fixo no código: os padrões de fábrica são vazios, o
assistente preenche, e o reset devolve tudo ao estado de instalação nova."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data import campi, config_store, instalacao  # noqa: E402
from app.data.schema import get_connection, init_db  # noqa: E402
from app.sistec.perfis import perfis_de_texto  # noqa: E402


@pytest.fixture
def db_path(tmp_path):
    caminho = str(tmp_path / "instalacao.db")
    init_db(caminho)
    return caminho


def test_padroes_de_fabrica_nao_citam_nenhuma_instituicao():
    assert config_store.DEFAULT_INSTITUICAO_NOME == ""
    assert config_store.DEFAULT_CONTATO_EMAIL == ""
    assert "iffar" not in config_store.DEFAULT_LOGO_PATH.lower()


def test_logotipo_padrao_existe_no_disco():
    """`GET /branding/logo` cai nesse arquivo quando não há logotipo enviado."""
    caminho = os.path.join(os.path.dirname(__file__), "..", config_store.DEFAULT_LOGO_PATH)
    assert os.path.isfile(caminho)


def test_dados_da_instituicao_ficam_salvos(db_path):
    config_store.set_instituicao(nome="Instituto Federal de Exemplo", sigla="IFE", site="www.ife.edu.br", db_path=db_path)
    config_store.set_contato_email("pi@ife.edu.br", db_path)

    assert config_store.dados_instituicao(db_path) == {
        "nome": "Instituto Federal de Exemplo",
        "sigla": "IFE",
        "site": "www.ife.edu.br",
        "contato_email": "pi@ife.edu.br",
    }


def test_instalacao_comeca_pendente_e_e_concluida(db_path):
    assert instalacao.concluida(db_path) is False
    assert "nome da instituição" in instalacao.pendencias(db_path)
    assert "lista de campi" in instalacao.pendencias(db_path)

    config_store.set_instituicao(nome="IF Exemplo", db_path=db_path)
    campi.salvar_captura([{"id_perfil": "1", "nome_perfil": "IF - CAMPUS A", "ordem": 0}], db_path)
    instalacao.concluir(db_path)

    assert instalacao.concluida(db_path) is True
    assert instalacao.pendencias(db_path) == []


def test_resetar_volta_ao_estado_de_instalacao_nova(db_path):
    """Troca da pessoa do setor ou mudança de instituição."""
    config_store.set_instituicao(nome="IF Exemplo", sigla="IFE", site="ife.edu.br", db_path=db_path)
    config_store.set_contato_email("pi@ife.edu.br", db_path)
    config_store.set_logo("app/data/uploads/branding/logo-atual.png", db_path)
    campi.salvar_captura([{"id_perfil": "1", "nome_perfil": "IF - CAMPUS A", "co_unidade": "10", "ordem": 0}], db_path)
    instalacao.concluir(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO historico (tipo, admin_email, inicio) VALUES ('baixa', 'x@y', '2026-01-01')")
        conn.commit()
    finally:
        conn.close()

    instalacao.resetar(db_path)

    assert instalacao.concluida(db_path) is False
    assert config_store.dados_instituicao(db_path) == {"nome": "", "sigla": "", "site": "", "contato_email": ""}
    assert config_store.get_logo_path(db_path) == config_store.DEFAULT_LOGO_PATH
    assert campi.listar_campi(db_path) == []
    conn = get_connection(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM historico").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM interna_campus").fetchone()[0] == 0
        # Os fatores são regra nacional da PNP, não da instituição: ficam.
        assert conn.execute("SELECT COUNT(*) FROM interna_fatores").fetchone()[0] > 0
        assert conn.execute("SELECT valor FROM config WHERE chave='ano_base'").fetchone() is not None
    finally:
        conn.close()


def test_resetar_sem_apagar_dados_mantem_as_tabelas_do_painel(db_path):
    campi.salvar_captura([{"id_perfil": "1", "nome_perfil": "IF - CAMPUS A", "ordem": 0}], db_path)
    conn = get_connection(db_path)
    try:
        conn.execute("INSERT INTO historico (tipo, admin_email, inicio) VALUES ('baixa', 'x@y', '2026-01-01')")
        conn.commit()
    finally:
        conn.close()

    instalacao.resetar(db_path, apagar_dados=False)

    assert campi.listar_campi(db_path) == []
    conn = get_connection(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM historico").fetchone()[0] == 1
    finally:
        conn.close()


def test_perfis_de_texto_aceita_separadores_e_recusa_linha_sem_id():
    perfis, invalidas = perfis_de_texto(
        "8278857 ; ASSESSOR DA UNIDADE DE ENSINO - 101 - IF EXEMPLO - CAMPUS ALEGRETE\n"
        "8278858,ASSESSOR DA UNIDADE DE ENSINO - IF EXEMPLO - CÂMPUS JAGUARI\n"
        "\n"
        "CAMPUS SEM IDENTIFICADOR\n"
    )

    assert [p["id_perfil"] for p in perfis] == ["8278857", "8278858"]
    assert perfis[0]["co_unidade"] == "101"
    assert perfis[1]["cidade"] == "Jaguari"
    assert invalidas == ["CAMPUS SEM IDENTIFICADOR"]


def test_tela_administrativa_leva_ao_assistente_enquanto_a_instalacao_nao_termina(monkeypatch):
    """Guarda de `_exigir_instalacao`: primeira execução cai no assistente."""
    from app import app as app_module

    cliente = app_module.server.test_client()
    with cliente.session_transaction() as sessao:
        sessao["admin_usuario"] = "pi@ife.edu.br"
        sessao["admin_autenticado"] = True

    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: False)
    resposta = cliente.get("/admin/atualizar", follow_redirects=False)
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/instalacao")

    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: True)
    assert cliente.get("/admin/atualizar", follow_redirects=False).status_code == 200


def test_assistente_nao_exige_instalacao_concluida(monkeypatch):
    from app import app as app_module

    cliente = app_module.server.test_client()
    with cliente.session_transaction() as sessao:
        sessao["admin_usuario"] = "pi@ife.edu.br"
        sessao["admin_autenticado"] = True
    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: False)

    assert cliente.get("/admin/instalacao", follow_redirects=False).status_code == 200
