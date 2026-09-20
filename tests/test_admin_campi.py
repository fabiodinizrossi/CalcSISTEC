"""Lista de campi do painel administrativo (DS-62 a DS-85): busca, paginação e telas."""

import pytest

from app.admin_campi import filtrar_e_paginar


def _campi(quantidade):
    return [
        {
            "id_perfil": str(8278800 + i),
            "nome_perfil": f"Perfil {i:02d}",
            "cidade": f"Cidade {i:02d}",
            "nome_unidade": f"Campus {i:02d}",
        }
        for i in range(1, quantidade + 1)
    ]


def test_terceira_pagina_de_10_com_22_campi_tem_2_itens_e_indices_21_a_22():
    pagina = filtrar_e_paginar(_campi(22), "", 3, 10)
    assert len(pagina["itens"]) == 2
    assert pagina["inicio"] == 21
    assert pagina["fim"] == 22
    assert pagina["total"] == 22
    assert pagina["pagina"] == 3
    assert pagina["por_pagina"] == 10


def test_25_por_pagina_com_22_campi_cabe_em_uma_pagina():
    pagina = filtrar_e_paginar(_campi(22), "", 1, 25)
    assert len(pagina["itens"]) == 22
    assert (pagina["inicio"], pagina["fim"], pagina["total"]) == (1, 22, 22)


def test_primeira_e_segunda_pagina_pegam_as_faixas_certas():
    campi = _campi(22)
    primeira = filtrar_e_paginar(campi, "", 1, 10)
    segunda = filtrar_e_paginar(campi, "", 2, 10)
    assert [c["nome_perfil"] for c in primeira["itens"]] == [f"Perfil {i:02d}" for i in range(1, 11)]
    assert [c["nome_perfil"] for c in segunda["itens"]] == [f"Perfil {i:02d}" for i in range(11, 21)]
    assert (segunda["inicio"], segunda["fim"]) == (11, 20)


def test_busca_acha_perfil_cidade_ou_nome_da_unidade_sem_diferenciar_caixa():
    campi = [
        {"id_perfil": "1", "nome_perfil": "Assessor Santa Rosa", "cidade": "X", "nome_unidade": "Y"},
        {"id_perfil": "2", "nome_perfil": "Assessor B", "cidade": "Santa Maria", "nome_unidade": "Y"},
        {"id_perfil": "3", "nome_perfil": "Assessor C", "cidade": "X", "nome_unidade": "Campus Santana"},
        {"id_perfil": "4", "nome_perfil": "Assessor D", "cidade": "Jaguari", "nome_unidade": "Campus Jaguari"},
    ]
    for texto in ("santa", "SANTA", "  Santa  "):
        pagina = filtrar_e_paginar(campi, texto, 1, 10)
        assert [c["id_perfil"] for c in pagina["itens"]] == ["1", "2", "3"]
        assert pagina["total"] == 3


def test_busca_sem_resultado_zera_itens_total_e_indices():
    pagina = filtrar_e_paginar(_campi(22), "zzz", 1, 10)
    assert pagina["itens"] == []
    assert (pagina["total"], pagina["inicio"], pagina["fim"]) == (0, 0, 0)


@pytest.mark.parametrize("por_pagina", [7, "x", 0, -10, None, "100"])
def test_por_pagina_invalido_vira_10(por_pagina):
    assert filtrar_e_paginar(_campi(22), "", 1, por_pagina)["por_pagina"] == 10


@pytest.mark.parametrize("por_pagina,esperado", [(10, 10), (25, 25), (50, 50), ("25", 25)])
def test_por_pagina_valido_e_mantido(por_pagina, esperado):
    assert filtrar_e_paginar(_campi(22), "", 1, por_pagina)["por_pagina"] == esperado


@pytest.mark.parametrize("pagina", [0, -1, "x", None, 99, "4"])
def test_pagina_invalida_ou_alem_do_fim_vira_1(pagina):
    resultado = filtrar_e_paginar(_campi(22), "", pagina, 10)
    assert resultado["pagina"] == 1
    assert (resultado["inicio"], resultado["fim"]) == (1, 10)


import re

from app import admin_campi
from app import app as app_module
from app.data import campi as dados_campi
from app.data.schema import init_db


@pytest.fixture
def banco(tmp_path, monkeypatch):
    caminho = str(tmp_path / "campi.db")
    init_db(caminho)
    monkeypatch.setattr(admin_campi, "DB_PATH", caminho)
    return caminho


@pytest.fixture
def cliente(banco, monkeypatch):
    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: True)
    return app_module.server.test_client()


@pytest.fixture
def cliente_autenticado(cliente):
    with cliente.session_transaction() as sessao:
        sessao["admin_usuario"] = "pi@ife.edu.br"
        sessao["admin_autenticado"] = True
    return cliente


@pytest.fixture
def tres_campi(banco):
    dados_campi.incluir_campus("8278857", "Perfil Alegrete", "101", "Alegrete", "Campus Alegrete", banco)
    dados_campi.incluir_campus("1", "Perfil Suspeito", "102", "Jaguari", "Campus Jaguari", banco)
    dados_campi.incluir_campus("8278859", "Perfil Inativo", "103", "Santa Maria", "Campus Santa Maria", banco)
    dados_campi.definir_ativo("8278859", False, banco)


def _linhas(html):
    corpo = re.search(r"<tbody>(.*?)</tbody>", html, re.S).group(1)
    return re.findall(r"<tr>(.*?)</tr>", corpo, re.S)


def test_lista_sem_sessao_redireciona_ao_login(cliente):
    resposta = cliente.get("/admin/campi")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/login")


def test_lista_autenticada_tem_as_7_colunas_e_o_titulo(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.get("/admin/campi")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r"<h1[^>]*>\s*Campi do Sistec\s*</h1>", html)
    colunas = [c.strip() for c in re.findall(r"<th>(.*?)</th>", html)]
    assert colunas == ["Perfil", "Identificador", "Código da unidade", "Cidade", "Nome da unidade", "Situação", "Ações"]
    assert re.search(r'<a\b[^>]*class="br-button primary"[^>]*href="/admin/campi/novo"[^>]*>\s*Incluir campus', html)


def test_cada_linha_tem_tag_de_situacao_e_botoes_com_nome_acessivel(cliente_autenticado, tres_campi):
    linhas = _linhas(cliente_autenticado.get("/admin/campi").get_data(as_text=True))
    assert len(linhas) == 3
    alegrete, suspeito, inativo = linhas
    assert re.search(r'<span class="br-tag">\s*Ativo\s*</span>', alegrete)
    assert 'aria-label="Editar campus Perfil Alegrete"' in alegrete
    assert 'aria-label="Desativar campus Perfil Alegrete"' in alegrete
    assert 'aria-label="Excluir campus Perfil Alegrete"' in alegrete
    assert re.search(r'<span class="br-tag">\s*Desativado\s*</span>', inativo)
    assert 'aria-label="Reativar campus Perfil Inativo"' in inativo
    assert "Desativar campus" not in inativo
    assert 'aria-label="Excluir campus Perfil Inativo"' in inativo


def test_identificador_suspeito_mostra_o_aviso_so_na_linha_dele(cliente_autenticado, tres_campi):
    linhas = _linhas(cliente_autenticado.get("/admin/campi").get_data(as_text=True))
    aviso = "Identificador inválido: a atualização não roda assim"
    assert aviso not in linhas[0]
    assert aviso in linhas[1]
    assert aviso not in linhas[2]


def test_tabela_sem_input_em_celula_e_com_rolagem_propria(cliente_autenticado, tres_campi):
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'<div class="br-table">\s*<div class="responsive">\s*<table', html)
    for celula in re.findall(r"<td>(.*?)</td>", html, re.S):
        assert "<input" not in celula


def test_sem_campus_cadastrado_mostra_br_message_info_convidando_a_importar_ou_incluir(cliente_autenticado):
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message info"', html)
    assert "Importe a lista de perfis" in html
    assert "inclua um campus" in html
    assert "<table" not in html


def test_mensagem_flash_aparece_como_br_message_da_categoria(cliente_autenticado, tres_campi):
    with cliente_autenticado.session_transaction() as sessao:
        sessao["_flashes"] = [("success", "Campus atualizado.")]
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message success"[^>]*role="alert"', html)
    assert "Campus atualizado." in html


DADOS_VALIDOS = {"id_perfil": "8278857", "co_unidade": "101", "cidade": "Alegrete", "nome_unidade": "Campus Alegrete"}


def _texto(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def test_editar_mostra_titulo_breadcrumb_e_4_campos_com_rotulo_visivel(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.get("/admin/campi/8278857/editar")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r"<h1[^>]*>\s*Editar campus \| Perfil Alegrete\s*</h1>", html)
    crumbs = re.search(r'<nav class="br-breadcrumb".*?</nav>', html, re.S).group(0)
    assert [_texto(c) for c in re.findall(r'<li class="crumb".*?</li>', crumbs, re.S)] == ["Configurações", "Campi", "Editar"]
    assert len(re.findall(r'class="br-input\b', html)) == 4
    for campo in ("id_perfil", "co_unidade", "cidade", "nome_unidade"):
        assert f'<label for="{campo}">' in html
    assert re.search(r'<a\b[^>]*class="br-button secondary[^"]*"[^>]*href="/admin/campi"[^>]*>\s*Cancelar', html)
    assert re.search(r'<button\b[^>]*class="br-button primary[^"]*"[^>]*type="submit"[^>]*>\s*Salvar', html)


def test_editar_valido_grava_redireciona_e_a_lista_mostra_a_mensagem_de_sucesso(cliente_autenticado, tres_campi, banco):
    resposta = cliente_autenticado.post("/admin/campi/8278857/editar", data={**DADOS_VALIDOS, "cidade": "Uruguaiana"})
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/campi")
    assert dados_campi.obter_campus("8278857", banco)["cidade"] == "Uruguaiana"
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message success"[^>]*role="alert"', html)
    assert "Campus atualizado." in html


def test_editar_aceita_identificador_com_menos_de_5_digitos(cliente_autenticado, tres_campi, banco):
    resposta = cliente_autenticado.post("/admin/campi/8278857/editar", data={**DADOS_VALIDOS, "id_perfil": "1234"})
    assert resposta.status_code == 302
    assert dados_campi.obter_campus("1234", banco) is not None
    assert dados_campi.obter_campus("8278857", banco) is None


def test_editar_com_codigo_vazio_devolve_a_tela_com_erro_no_campo_e_banner_e_mantem_valores(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.post(
        "/admin/campi/8278857/editar", data={**DADOS_VALIDOS, "co_unidade": "", "cidade": "Cidade digitada"}
    )
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"[^>]*>\s*<label for="co_unidade">', html)
    assert re.search(r'id="co_unidade-erro"[^>]*>\s*<i[^>]*></i>Preencha o campo obrigatório', html)
    assert re.search(
        r'class="br-message danger"[^>]*role="alert".*Erro\. Preencha abaixo os campos obrigatórios antes de enviar os dados\.',
        html,
        re.S,
    )
    assert 'value="Cidade digitada"' in html


def test_editar_com_identificador_de_outro_campus_mostra_a_regra_no_campo(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.post("/admin/campi/8278857/editar", data={**DADOS_VALIDOS, "id_perfil": "8278859"})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"[^>]*>\s*<label for="id_perfil">', html)
    assert "esse identificador de perfil já está em outro campus" in html


def test_editar_com_codigo_de_outro_campus_mostra_a_regra_no_campo(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.post("/admin/campi/8278857/editar", data={**DADOS_VALIDOS, "co_unidade": "103"})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"[^>]*>\s*<label for="co_unidade">', html)
    assert "esse código da unidade já está em outro campus" in html


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_editar_campus_inexistente_volta_a_lista_com_mensagem_de_erro(cliente_autenticado, tres_campi, metodo):
    resposta = getattr(cliente_autenticado, metodo)("/admin/campi/99999999/editar", data=DADOS_VALIDOS)
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/campi")
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message danger"', html)
    assert "Campus não encontrado." in html
