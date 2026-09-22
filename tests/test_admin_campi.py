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


import html as html_lib
import re
from urllib.parse import parse_qs, urlparse

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
    colunas = [c.strip() for c in re.findall(r"<th(?:\s[^>]*)?>(.*?)</th>", html)]
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


def test_incluir_mostra_titulo_e_5_campos(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.get("/admin/campi/novo")
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r"<h1[^>]*>\s*Incluir campus\s*</h1>", html)
    assert re.findall(r'<label for="([^"]+)">', html) == ["id_perfil", "nome_perfil", "co_unidade", "cidade", "nome_unidade"]
    assert len(re.findall(r'class="br-input\b', html)) == 5


def test_incluir_valido_grava_como_manual_redireciona_e_a_lista_mostra_a_mensagem(cliente_autenticado, tres_campi, banco):
    resposta = cliente_autenticado.post(
        "/admin/campi/novo", data={"id_perfil": "8279999", "nome_perfil": "Perfil Novo", "co_unidade": "", "cidade": "", "nome_unidade": ""}
    )
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/campi")
    campus = dados_campi.obter_campus("8279999", banco)
    assert campus["origem"] == "manual"
    assert campus["nome_perfil"] == "Perfil Novo"
    assert campus["co_unidade"] is None
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message success"[^>]*role="alert"', html)
    assert "Campus incluído." in html


def test_incluir_dois_campi_sem_codigo_nao_bate_no_unique_do_codigo(cliente_autenticado, tres_campi, banco):
    for identificador in ("8270001", "8270002"):
        resposta = cliente_autenticado.post("/admin/campi/novo", data={"id_perfil": identificador, "nome_perfil": "Perfil " + identificador})
        assert resposta.status_code == 302
    assert dados_campi.obter_campus("8270002", banco) is not None


@pytest.mark.parametrize("faltando", ["id_perfil", "nome_perfil"])
def test_incluir_sem_identificador_ou_sem_nome_devolve_campo_em_danger_e_banner(cliente_autenticado, tres_campi, faltando):
    dados = {"id_perfil": "8279999", "nome_perfil": "Perfil Novo"}
    dados[faltando] = ""
    resposta = cliente_autenticado.post("/admin/campi/novo", data=dados)
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(rf'class="br-input danger"[^>]*>\s*<label for="{faltando}">', html)
    assert "Preencha o campo obrigatório" in html
    assert "Erro. Preencha abaixo os campos obrigatórios antes de enviar os dados." in html


def test_incluir_com_identificador_repetido_mostra_a_regra_no_campo(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.post("/admin/campi/novo", data={"id_perfil": "8278857", "nome_perfil": "Outro"})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert re.search(r'class="br-input danger"[^>]*>\s*<label for="id_perfil">', html)
    assert "esse identificador de perfil já está em outro campus" in html


def test_desativar_grava_e_a_lista_mostra_a_tag_e_a_mensagem(cliente_autenticado, tres_campi, banco):
    resposta = cliente_autenticado.post("/admin/campi/8278857/situacao", data={"ativo": "0"})
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/campi")
    assert dados_campi.obter_campus("8278857", banco)["ativo"] == 0
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message success"[^>]*role="alert"', html)
    assert "Campus desativado." in html
    assert re.search(r'<span class="br-tag">\s*Desativado\s*</span>', _linhas(html)[0])


def test_reativar_grava_e_a_lista_mostra_a_tag_e_a_mensagem(cliente_autenticado, tres_campi, banco):
    resposta = cliente_autenticado.post("/admin/campi/8278859/situacao", data={"ativo": "1"})
    assert resposta.status_code == 302
    assert dados_campi.obter_campus("8278859", banco)["ativo"] == 1
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert "Campus reativado." in html
    assert re.search(r'<span class="br-tag">\s*Ativo\s*</span>', _linhas(html)[2])


def test_botoes_desativar_e_reativar_da_lista_nao_pedem_confirmacao(cliente_autenticado, tres_campi):
    linhas = _linhas(cliente_autenticado.get("/admin/campi").get_data(as_text=True))
    for linha in (linhas[0], linhas[2]):
        botao = re.search(r'<button\b[^>]*aria-label="(?:Desativar|Reativar) campus[^"]*"[^>]*>', linha).group(0)
        assert "data-confirm" not in botao


def test_situacao_de_campus_inexistente_volta_a_lista_com_mensagem_de_erro(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.post("/admin/campi/99999999/situacao", data={"ativo": "0"})
    assert resposta.status_code == 302
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message danger"', html)
    assert "Campus não encontrado." in html


@pytest.mark.parametrize("valor", [None, "", "2", "sim"])
def test_situacao_com_valor_invalido_responde_400_e_nao_altera_o_campus(cliente_autenticado, tres_campi, banco, valor):
    dados = {} if valor is None else {"ativo": valor}
    assert cliente_autenticado.post("/admin/campi/8278857/situacao", data=dados).status_code == 400
    assert dados_campi.obter_campus("8278857", banco)["ativo"] == 1


def test_excluir_e_confirm_form_com_pergunta_aviso_do_sistec_e_rotulo(cliente_autenticado, tres_campi, banco):
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    linha = _linhas(html)[0]
    formulario = re.search(r'<form\b[^>]*class="confirm-form[^"]*"[^>]*action="/admin/campi/8278857/excluir"[^>]*>|<form\b[^>]*action="/admin/campi/8278857/excluir"[^>]*class="confirm-form[^"]*"[^>]*>', linha)
    assert formulario
    botao = re.search(r'<button\b[^>]*aria-label="Excluir campus Perfil Alegrete"[^>]*>', linha).group(0)
    assert "data-confirm=\"Tem certeza que deseja excluir o campus Perfil Alegrete?" in botao
    assert "volta na próxima atualização" in botao
    assert 'data-confirm-rotulo="Excluir"' in botao
    assert dados_campi.obter_campus("8278857", banco) is not None


def test_excluir_remove_o_campus_e_a_lista_mostra_a_mensagem(cliente_autenticado, tres_campi, banco):
    resposta = cliente_autenticado.post("/admin/campi/8278857/excluir")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/campi")
    assert dados_campi.obter_campus("8278857", banco) is None
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message success"[^>]*role="alert"', html)
    assert "Perfil excluído da lista." in html
    assert "Perfil Alegrete" not in "".join(_linhas(html))


def test_excluir_campus_inexistente_volta_a_lista_com_mensagem_de_erro(cliente_autenticado, tres_campi):
    resposta = cliente_autenticado.post("/admin/campi/99999999/excluir")
    assert resposta.status_code == 302
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r'class="br-message danger"', html)
    assert "Campus não encontrado." in html


@pytest.fixture
def vinte_e_dois_campi(banco):
    for i in range(1, 23):
        dados_campi.incluir_campus(
            str(8270000 + i), f"Perfil {i:02d}", str(200 + i), f"Cidade {i:02d}", f"Campus {i:02d}", banco
        )


def _resumo(html):
    return re.search(r"(\d+-\d+ de \d+ itens)", html).group(1)


def _botao(html, nome):
    return re.search(rf'<(?:a|button)\b[^>]*aria-label="{nome}"[^>]*>', html).group(0)


def test_lista_tem_a_barra_campi_com_busca_por_envio_e_botao_de_lupa(cliente_autenticado, tres_campi):
    html = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert re.search(r"<h2[^>]*>\s*Campi\s*</h2>", html)
    busca = re.search(r'<form method="get"[^>]*role="search".*?</form>', html, re.S).group(0)
    assert re.search(r'<input\b[^>]*name="q"', busca)
    assert re.search(r'<button\b[^>]*type="submit"[^>]*aria-label="Buscar campus"', busca)
    assert html.index('role="search"') < html.index("<table")


def test_busca_lista_so_as_linhas_que_contem_o_texto(cliente_autenticado, vinte_e_dois_campi):
    html = cliente_autenticado.get("/admin/campi?q=cidade 05").get_data(as_text=True)
    linhas = _linhas(html)
    assert len(linhas) == 1
    assert "Cidade 05" in linhas[0]
    assert _resumo(html) == "1-1 de 1 itens"


def test_busca_sem_resultado_mostra_br_message_info(cliente_autenticado, vinte_e_dois_campi):
    html = cliente_autenticado.get("/admin/campi?q=zzz").get_data(as_text=True)
    assert re.search(r'class="br-message info"[^>]*>.*Nenhum campus encontrado\.', html, re.S)
    assert "<table" not in html


def test_rodape_mostra_o_intervalo_de_itens_da_pagina(cliente_autenticado, vinte_e_dois_campi):
    assert _resumo(cliente_autenticado.get("/admin/campi").get_data(as_text=True)) == "1-10 de 22 itens"
    assert _resumo(cliente_autenticado.get("/admin/campi?por_pagina=25").get_data(as_text=True)) == "1-22 de 22 itens"
    assert _resumo(cliente_autenticado.get("/admin/campi?pagina=3").get_data(as_text=True)) == "21-22 de 22 itens"


def test_seletor_exibir_tem_10_25_e_50_e_marca_o_valor_atual(cliente_autenticado, vinte_e_dois_campi):
    html = cliente_autenticado.get("/admin/campi?por_pagina=25").get_data(as_text=True)
    seletor = re.search(r'<select id="por_pagina".*?</select>', html, re.S).group(0)
    assert re.findall(r'<option value="(\d+)"', seletor) == ["10", "25", "50"]
    assert re.search(r'<option value="25" selected>', seletor)
    assert re.search(r'<button\b[^>]*type="submit"[^>]*>\s*Aplicar\s*</button>', html)


def test_anterior_fica_desabilitado_na_primeira_pagina_e_proxima_na_ultima(cliente_autenticado, vinte_e_dois_campi):
    primeira = cliente_autenticado.get("/admin/campi").get_data(as_text=True)
    assert "disabled" in _botao(primeira, "Página anterior")
    assert 'href="/admin/campi?' in _botao(primeira, "Próxima página")
    ultima = cliente_autenticado.get("/admin/campi?pagina=3").get_data(as_text=True)
    assert "disabled" in _botao(ultima, "Próxima página")
    assert 'href="/admin/campi?' in _botao(ultima, "Página anterior")


def test_pagina_e_por_pagina_invalidos_viram_1_e_10_sem_erro(cliente_autenticado, vinte_e_dois_campi):
    resposta = cliente_autenticado.get("/admin/campi?pagina=abc&por_pagina=7")
    assert resposta.status_code == 200
    assert _resumo(resposta.get_data(as_text=True)) == "1-10 de 22 itens"


def test_links_de_pagina_mantem_a_busca_e_o_tamanho_da_pagina(cliente_autenticado, vinte_e_dois_campi):
    html = cliente_autenticado.get("/admin/campi?q=cidade&por_pagina=10&pagina=2").get_data(as_text=True)
    for nome, pagina_esperada in (("Página anterior", "1"), ("Próxima página", "3")):
        href = html_lib.unescape(re.search(r'href="([^"]+)"', _botao(html, nome)).group(1))
        params = parse_qs(urlparse(href).query)
        assert params == {"q": ["cidade"], "por_pagina": ["10"], "pagina": [pagina_esperada]}


def _botao_de_visao(html):
    return re.search(r'<a\b[^>]*role="button"[^>]*aria-pressed="[^"]*"[^>]*>\s*Visualizar em \w+\s*</a>', html).group(0)


def test_botao_de_visao_na_lista_diz_visualizar_em_cards_com_aria_pressed_falso(cliente_autenticado, tres_campi):
    botao = _botao_de_visao(cliente_autenticado.get("/admin/campi").get_data(as_text=True))
    assert 'aria-pressed="false"' in botao
    assert "Visualizar em Cards" in botao
    assert "visao=cards" in botao


def test_botao_de_visao_nos_cards_diz_visualizar_em_lista_com_aria_pressed_verdadeiro(cliente_autenticado, tres_campi):
    botao = _botao_de_visao(cliente_autenticado.get("/admin/campi?visao=cards").get_data(as_text=True))
    assert 'aria-pressed="true"' in botao
    assert "Visualizar em Lista" in botao
    assert "visao=cards" not in botao


def test_cards_mostram_os_dados_a_tag_e_as_acoes_de_cada_campus(cliente_autenticado, tres_campi):
    html = cliente_autenticado.get("/admin/campi?visao=cards").get_data(as_text=True)
    assert "<table" not in html
    cards = re.findall(r'<div class="br-card">.*?<div class="card-footer">.*?</div>\s*</div>\s*</div>', html, re.S)
    assert len(cards) == 3
    alegrete, suspeito, inativo = cards
    for esperado in ("Perfil Alegrete", "8278857", "101", "Alegrete", "Campus Alegrete"):
        assert esperado in alegrete
    assert re.search(r'<span class="br-tag">\s*Ativo\s*</span>', alegrete)
    for nome in ("Editar campus Perfil Alegrete", "Desativar campus Perfil Alegrete", "Excluir campus Perfil Alegrete"):
        assert f'aria-label="{nome}"' in alegrete
    assert "Identificador inválido: a atualização não roda assim" in suspeito
    assert re.search(r'<span class="br-tag">\s*Desativado\s*</span>', inativo)
    assert 'aria-label="Reativar campus Perfil Inativo"' in inativo
    assert "Tem certeza que deseja excluir o campus Perfil Alegrete?" in alegrete


def test_visao_invalida_cai_em_lista(cliente_autenticado, tres_campi):
    html = cliente_autenticado.get("/admin/campi?visao=grade").get_data(as_text=True)
    assert "<table" in html
    assert 'class="br-card"' not in html
    assert "Visualizar em Cards" in html


def test_busca_e_paginacao_continuam_valendo_nos_cards(cliente_autenticado, vinte_e_dois_campi):
    padrao = cliente_autenticado.get("/admin/campi?visao=cards").get_data(as_text=True)
    assert len(re.findall(r'<div class="br-card">', padrao)) == 10
    assert _resumo(padrao) == "1-10 de 22 itens"
    buscado = cliente_autenticado.get("/admin/campi?visao=cards&q=cidade 05").get_data(as_text=True)
    assert len(re.findall(r'<div class="br-card">', buscado)) == 1
    href = html_lib.unescape(re.search(r'href="([^"]+)"', _botao(padrao, "Próxima página")).group(1))
    assert parse_qs(urlparse(href).query)["visao"] == ["cards"]
    assert 'name="visao" value="cards"' in padrao


def test_campos_do_formulario_de_campus_ocupam_a_linha_toda_no_celular_e_metade_a_partir_de_768px(cliente_autenticado, tres_campi):
    html = cliente_autenticado.get("/admin/campi/8278857/editar").get_data(as_text=True)
    colunas = re.findall(r'<div class="([^"]*col-[^"]*)">\s*<div class="br-input', html)
    assert len(colunas) == 4
    for classes_da_coluna in colunas:
        assert {"col-12", "col-md-6"} <= set(classes_da_coluna.split())


def test_cada_linha_liga_editar_ao_href_certo_e_desativar_reativar_e_excluir_aos_actions_certos(cliente_autenticado, tres_campi):
    linhas = _linhas(cliente_autenticado.get("/admin/campi").get_data(as_text=True))
    alegrete, _, inativo = linhas
    assert re.search(r'<a\b[^>]*href="/admin/campi/8278857/editar"[^>]*aria-label="Editar campus Perfil Alegrete"', alegrete)
    desativar = re.search(r'<form\b[^>]*action="/admin/campi/8278857/situacao"[^>]*>.*?</form>', alegrete, re.S).group(0)
    assert re.search(r'<button\b[^>]*name="ativo"[^>]*value="0"', desativar)
    reativar = re.search(r'<form\b[^>]*action="/admin/campi/8278859/situacao"[^>]*>.*?</form>', inativo, re.S).group(0)
    assert re.search(r'<button\b[^>]*name="ativo"[^>]*value="1"', reativar)
    assert re.search(r'<form\b[^>]*action="/admin/campi/8278857/excluir"', alegrete)


def test_cada_card_liga_as_acoes_aos_mesmos_destinos_da_linha(cliente_autenticado, tres_campi):
    html = cliente_autenticado.get("/admin/campi?visao=cards").get_data(as_text=True)
    cards = re.findall(r'<div class="br-card">.*?<div class="card-footer">.*?</div>\s*</div>\s*</div>', html, re.S)
    alegrete, _, inativo = cards
    assert 'href="/admin/campi/8278857/editar"' in alegrete
    assert re.search(r'action="/admin/campi/8278857/situacao".*?name="ativo"[^>]*value="0"', alegrete, re.S)
    assert re.search(r'action="/admin/campi/8278859/situacao".*?name="ativo"[^>]*value="1"', inativo, re.S)
    assert 'action="/admin/campi/8278857/excluir"' in alegrete
