"""Páginas administrativas (Flask/Jinja) no padrão do gov.br DS."""

import re

import pytest

from app import app as app_module


@pytest.fixture
def cliente():
    return app_module.server.test_client()


@pytest.fixture
def cliente_autenticado(cliente, monkeypatch):
    with cliente.session_transaction() as sessao:
        sessao["admin_usuario"] = "pi@ife.edu.br"
        sessao["admin_autenticado"] = True
    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: True)
    return cliente


def test_base_compoe_o_shell_do_ds(cliente):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert '<html lang="pt-BR"' in html
    assert len(re.findall(r'<link[^>]+href="/ds/govbr-ds/dist/core\.min\.css"', html)) == 1
    assert len(re.findall(r'<script[^>]+src="/ds/govbr-ds/dist/core-init.min.js"', html)) == 1
    assert 'class="br-header"' in html
    assert 'class="br-footer"' in html
    assert "container-fluid" in html
    for antigo in ("app-header", "app-footer", "admin-nav"):
        assert antigo not in html


def test_base_nao_carrega_folha_do_bootstrap(cliente):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert "bootstrap" not in html.lower()


def test_pagina_administrativa_autenticada_mostra_menu_e_breadcrumb(cliente_autenticado):
    html = cliente_autenticado.get("/admin/historico").get_data(as_text=True)
    assert 'class="br-menu"' in html
    assert 'class="br-breadcrumb"' in html
    assert "admin-nav" not in html


def test_login_nao_mostra_menu_nem_breadcrumb(cliente):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert 'class="br-menu"' not in html
    assert 'class="br-breadcrumb"' not in html


@pytest.fixture
def login_configurado(monkeypatch):
    monkeypatch.setattr(app_module, "credenciais_configuradas", lambda: True)


def test_login_tem_titulo_campos_com_rotulo_e_apoio_e_link_depois_da_senha(cliente, login_configurado):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert re.search(r"<h1[^>]*>\s*Acesso ao sistema\s*</h1>", html)
    assert len(re.findall(r'<label for="(email|senha)">', html)) == 2
    assert "Mínimo de 8 caracteres." in html
    assert 'id="email-ajuda"' in html
    assert html.index('id="senha"') < html.index("Esqueci minha senha")


def test_botao_entrar_ocupa_a_largura_do_formulario(cliente, login_configurado):
    html = cliente.get("/admin/login").get_data(as_text=True)
    assert re.search(r'<button\b[^>]*class="br-button primary block"[^>]*>\s*Entrar\s*</button>', html)


def test_login_com_campo_invalido_devolve_o_campo_em_danger_ligado_ao_erro(cliente, login_configurado):
    resposta = cliente.post("/admin/login", data={"email": "nao-e-email", "senha": "curta"})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"', html)
    descrito = re.search(r'<input\b[^>]*id="email"[^>]*aria-describedby="([^"]+)"', html).group(1)
    assert f'id="{descrito.split()[-1]}"' in html


def test_login_recusado_mostra_mensagem_danger_com_role_alert(cliente, login_configurado, monkeypatch):
    monkeypatch.setattr(app_module, "autenticar_sessao", lambda email, senha: False)
    html = cliente.post("/admin/login", data={"email": "pi@ife.edu.br", "senha": "12345678"}).get_data(as_text=True)
    assert re.search(r'class="br-message danger"[^>]*role="alert"', html)
    assert "E-mail ou senha incorretos." in html


def test_recuperar_acesso_tem_titulo_shell_sem_menu_e_sem_breadcrumb(cliente):
    resposta = cliente.get("/recuperar-acesso")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r"<h1[^>]*>\s*Recuperação de acesso\s*</h1>", html)
    assert 'class="br-header"' in html
    assert 'class="br-footer"' in html
    assert 'class="br-menu"' not in html
    assert 'class="br-breadcrumb"' not in html


def test_recuperar_acesso_volta_ao_login_por_um_br_button(cliente):
    html = cliente.get("/recuperar-acesso").get_data(as_text=True)
    assert re.search(r'<a\b[^>]*class="br-button[^"]*"[^>]*href="/admin/login"[^>]*>\s*Voltar ao login\s*</a>', html)


def test_instalacao_tem_rotulo_e_br_input_para_todo_campo_de_texto(cliente_autenticado):
    resposta = cliente_autenticado.get("/admin/instalacao")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    ids = re.findall(r'<input\b[^>]*type="(?:text|email)"[^>]*id="([^"]+)"', html)
    assert sorted(ids) == ["contato_email", "nome", "sigla", "site"]
    for campo_id in ids:
        assert f'<label for="{campo_id}">' in html
    assert len(re.findall(r'class="br-input\b', html)) == len(ids)


def test_instalacao_nao_mostra_menu_nem_breadcrumb_e_nao_usa_confirm_nativo(cliente_autenticado):
    html = cliente_autenticado.get("/admin/instalacao").get_data(as_text=True)
    assert 'class="br-menu"' not in html
    assert 'class="br-breadcrumb"' not in html
    assert "confirm(" not in html


def test_instalacao_com_nome_vazio_marca_o_campo_em_danger_ligado_a_mensagem(cliente_autenticado):
    resposta = cliente_autenticado.post("/admin/instalacao", data={"acao": "salvar_instituicao", "nome": "  "})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"[^>]*>\s*<label for="nome">', html)
    assert re.search(r'<input\b[^>]*id="nome"[^>]*aria-describedby="nome-erro[^"]*"', html)
    assert re.search(r'id="nome-erro"[^>]*>\s*<i[^>]*></i>Informe o nome da instituição\.', html)


EVENTOS = [
    {
        "inicio": "2026-09-01 10:00",
        "tipo": "sistec",
        "admin_email": "pi@ife.edu.br",
        "desfecho": "publicada",
        "sucessos": 12,
        "falhas": 0,
        "pausas": 1,
        "linhas_consolidadas": 5300,
    },
    {
        "inicio": "2026-09-02 09:30",
        "tipo": "sistec",
        "admin_email": "pi@ife.edu.br",
        "desfecho": None,
        "sucessos": None,
        "falhas": None,
        "pausas": None,
        "linhas_consolidadas": None,
    },
]


def test_historico_com_registros_usa_br_table_em_conteiner_rolavel(cliente_autenticado, monkeypatch):
    monkeypatch.setattr(app_module, "historico_listar", lambda: EVENTOS)
    html = cliente_autenticado.get("/admin/historico").get_data(as_text=True)
    assert re.search(r'<div class="br-table">\s*<div class="responsive">\s*<table', html)
    assert "table-scroll-wrapper" not in html
    assert len(re.findall(r"<tbody>.*?</tbody>", html, re.S)) == 1
    linhas = re.findall(r"<tr>\s*<td>", html)
    assert len(linhas) == len(EVENTOS)
    assert "em andamento" in html


def test_historico_sem_registros_mostra_br_message_info_no_lugar_da_tabela(cliente_autenticado, monkeypatch):
    monkeypatch.setattr(app_module, "historico_listar", lambda: [])
    html = cliente_autenticado.get("/admin/historico").get_data(as_text=True)
    assert re.search(r'class="br-message info"[^>]*>.*Nenhuma atualização registrada ainda\.', html, re.S)
    assert "<table" not in html


def test_historico_tem_breadcrumb_inicio_e_pagina_atual(cliente_autenticado, monkeypatch):
    monkeypatch.setattr(app_module, "historico_listar", lambda: [])
    html = cliente_autenticado.get("/admin/historico").get_data(as_text=True)
    crumbs = re.search(r'<nav class="br-breadcrumb".*?</nav>', html, re.S).group(0)
    assert re.search(r'<a\b[^>]*href="/"[^>]*>\s*Início\s*</a>', crumbs)
    assert re.search(r'<span aria-current="page">Histórico de atualizações</span>', crumbs)


def test_atualizar_mostra_breadcrumb_e_menu_administrativo(cliente_autenticado):
    resposta = cliente_autenticado.get("/admin/atualizar")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    menu = re.search(r'<div class="br-menu".*?</nav>', html, re.S).group(0)
    assert re.search(r'<a\b[^>]*aria-current="page"[^>]*>\s*<span class="content">Atualizar dados</span>', menu)
    assert 'class="br-breadcrumb"' in html


@pytest.mark.parametrize(
    "botao,pergunta",
    [
        ("btn-cancelar", "Cancelar a atualização em andamento?"),
        ("btn-descartar", "Descartar esta prévia?"),
        ("btn-publicar", "Publicar a versão interna no painel público?"),
        ("btn-desfazer", "Desfazer a última publicação?"),
    ],
)
def test_atualizar_mantem_os_ids_e_os_data_confirm_dos_botoes(cliente_autenticado, botao, pergunta):
    html = cliente_autenticado.get("/admin/atualizar").get_data(as_text=True)
    tag = re.search(rf'<button\b[^>]*id="{botao}"[^>]*>', html).group(0)
    assert f'data-confirm="{pergunta}"' in tag


def test_atualizar_empilha_os_botoes_abaixo_de_576px_com_classes_do_ds(cliente_autenticado):
    html = cliente_autenticado.get("/admin/atualizar").get_data(as_text=True)
    acoes = re.search(r'<div[^>]*id="atualizar-acoes"[^>]*>', html).group(0)
    assert "flex-column" in acoes
    assert "flex-sm-row" in acoes
    assert "@media" not in html


CONFIG_CAMPI = [
    {"id_perfil": "8278857", "nome_perfil": "A", "ativo": 1},
    {"id_perfil": "1", "nome_perfil": "B", "ativo": 1},
    {"id_perfil": "8278859", "nome_perfil": "C", "ativo": 0},
]


def test_configuracoes_resume_os_campi_e_leva_a_gerenciar_campi(cliente_autenticado, monkeypatch):
    monkeypatch.setattr(app_module, "listar_campi", lambda *a, **k: CONFIG_CAMPI)
    resposta = cliente_autenticado.get("/admin/config")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'<a\b[^>]*href="/admin/campi"[^>]*>\s*Gerenciar campi\s*</a>', html)
    assert "3 campi cadastrados, 2 ativos." in html
    assert re.search(r'class="br-message warning".*1 campus com identificador inválido: a atualização não roda assim', html, re.S)
    assert 'name="novo_id_perfil"' not in html
    assert "<table" not in html
    for celula in re.findall(r"<td>(.*?)</td>", html, re.S):
        assert "<input" not in celula


def test_configuracoes_sem_suspeitos_nao_mostra_o_aviso(cliente_autenticado, monkeypatch):
    monkeypatch.setattr(app_module, "listar_campi", lambda *a, **k: CONFIG_CAMPI[:1])
    html = cliente_autenticado.get("/admin/config").get_data(as_text=True)
    assert "1 campi cadastrados, 1 ativos." in html
    assert "identificador inválido" not in html


def test_configuracoes_nao_usa_confirm_nativo_e_mantem_os_6_data_confirm(cliente_autenticado):
    com_data_confirm = [
        "Restaurar o e-mail de contato para o padrão de fábrica?",
        "Restaurar o logotipo para o padrão de fábrica?",
        "Confirmar a troca da tabela de fatores?",
        "Restaurar a tabela de fatores para o padrão de fábrica?",
        "Apagar configuração, campi e dados baixados, voltando ao assistente de instalação? Isso não pode ser desfeito.",
        "Aplicar os campi e fatores da versão interna diretamente ao painel público?",
    ]
    modelo = app_module.server.root_path + "/templates/configuracoes.html"
    with open(modelo, encoding="utf-8") as arquivo:
        fonte = arquivo.read()
    assert "confirm(" not in fonte
    assert sorted(re.findall(r'data-confirm="([^"]+)"', fonte)) == sorted(com_data_confirm)
    html = cliente_autenticado.get("/admin/config").get_data(as_text=True)
    assert "confirm(" not in html
    # "Confirmar troca" só aparece depois de enviar um arquivo de fatores.
    assert sorted(re.findall(r'data-confirm="([^"]+)"', html)) == sorted(t for t in com_data_confirm if not t.startswith("Confirmar a troca"))


def test_configuracoes_todo_campo_de_texto_tem_rotulo_visivel(cliente_autenticado):
    html = cliente_autenticado.get("/admin/config").get_data(as_text=True)
    ids = re.findall(r'<input\b[^>]*type="(?:text|email)"[^>]*id="([^"]+)"', html)
    assert sorted(ids) == ["contato_email", "nome", "qtd_perfis", "sigla", "site"]
    for campo_id in ids:
        assert f'<label for="{campo_id}">' in html


def test_email_invalido_mostra_o_campo_em_danger_e_a_mensagem_em_br_message(cliente_autenticado):
    html = cliente_autenticado.post("/admin/config", data={"acao": "salvar_email", "contato_email": "nao-e-email"}).get_data(as_text=True)
    assert re.search(r'class="br-input danger"[^>]*>\s*<label for="contato_email">', html)
    assert re.search(r'class="br-message danger"[^>]*role="alert".*Não foi possível salvar: e-mail inválido\.', html, re.S)


def test_mensagem_do_logotipo_aparece_em_br_message(cliente_autenticado, monkeypatch):
    monkeypatch.setattr(app_module, "reset_logo", lambda: None)
    html = cliente_autenticado.post("/admin/config", data={"acao": "restaurar_logo"}).get_data(as_text=True)
    assert re.search(r'class="br-message success"[^>]*role="alert".*Logotipo restaurado ao padrão de fábrica\.', html, re.S)


def test_mensagem_dos_fatores_aparece_em_br_message(cliente_autenticado):
    html = cliente_autenticado.post("/admin/config", data={"acao": "enviar_fatores"}).get_data(as_text=True)
    assert re.search(r'class="br-message danger"[^>]*role="alert".*Selecione um arquivo de fatores \(\.xlsx\)\.', html, re.S)


@pytest.fixture
def banco_temporario(tmp_path, monkeypatch):
    from app.data.schema import init_db

    caminho = str(tmp_path / "config.db")
    init_db(caminho)
    monkeypatch.setattr(app_module, "DEFAULT_DB_PATH", caminho)
    return caminho


def _campi_do_banco(caminho):
    from app.data import campi as dados_campi

    return dados_campi.listar_campi(caminho)


@pytest.mark.parametrize(
    "acao",
    ["salvar_campus", "incluir_campus", "excluir_campus", "ativar_campus", "desativar_campus"],
)
def test_acoes_de_campus_sairam_de_admin_config(cliente_autenticado, banco_temporario, acao):
    from app.data import campi as dados_campi

    dados_campi.incluir_campus("8278857", "Perfil A", "101", "A", "Campus A", banco_temporario)
    antes = _campi_do_banco(banco_temporario)
    cliente_autenticado.post(
        "/admin/config",
        data={
            "acao": acao,
            "id_perfil": "8278857",
            "novo_id_perfil": "8279999",
            "nome_perfil": "Outro",
            "co_unidade": "999",
            "cidade": "Outra",
            "nome_unidade": "Outro campus",
        },
    )
    assert _campi_do_banco(banco_temporario) == antes


def test_salvar_qtd_perfis_continua_gravando_o_valor(cliente_autenticado, banco_temporario, monkeypatch):
    gravado = []
    monkeypatch.setattr(app_module, "set_qtd_perfis", gravado.append)
    monkeypatch.setattr(app_module, "get_qtd_perfis", lambda: gravado[-1] if gravado else "")
    html = cliente_autenticado.post("/admin/config", data={"acao": "salvar_qtd_perfis", "qtd_perfis": "18"}).get_data(as_text=True)
    assert gravado == ["18"]
    assert "Quantidade de perfis salva." in html


def test_importar_perfis_continua_importando_uma_linha_valida(cliente_autenticado, banco_temporario):
    cliente_autenticado.post(
        "/admin/config", data={"acao": "importar_perfis", "lista_perfis": "8278860 ; ASSESSOR - IF EXEMPLO - CAMPUS X"}
    )
    campi_gravados = _campi_do_banco(banco_temporario)
    assert [c["id_perfil"] for c in campi_gravados] == ["8278860"]
