"""Parciais Jinja do shell (`app/templates/shell/`)."""

import html as html_lib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from flask import render_template, render_template_string

from app import app as app_module
from app import shell as shell_modulo
from app.shell import PAGINAS_ADMIN, contexto_shell


@pytest.fixture(scope="module")
def servidor():
    return app_module.server


def renderizar(servidor, modelo, **contexto):
    with servidor.test_request_context("/"):
        return render_template(modelo, **contexto)


def test_head_tem_viewport_e_um_unico_core_min_css(servidor):
    html = renderizar(servidor, "shell/_head.html", titulo="Matrículas")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert len(re.findall(r'<link[^>]+href="/ds/govbr-ds/dist/core\.min\.css"', html)) == 1
    assert "<title>Matrículas</title>" in html


def test_head_nao_referencia_url_externa(servidor):
    html = renderizar(servidor, "shell/_head.html", titulo="Início")
    assert "http://" not in html
    assert "https://" not in html


def cabecalho(servidor, nome="Instituto Teste", com_menu=True):
    return renderizar(
        servidor,
        "shell/_header.html",
        shell={"com_menu": com_menu},
        instituicao={"nome": nome},
    )


def test_primeiro_link_do_cabecalho_salta_para_o_conteudo_principal(servidor):
    html = cabecalho(servidor)
    primeiro = re.search(r"<a\b([^>]*)>(.*?)</a>", html, re.S)
    assert 'href="#main-content"' in primeiro.group(1)
    assert primeiro.group(2).strip() == "Ir para o conteúdo principal"


def test_logotipo_tem_alt_nao_vazio_com_e_sem_nome_de_instituicao(servidor):
    com_nome = re.search(r'<img[^>]*alt="([^"]*)"', cabecalho(servidor, nome="Instituto Teste")).group(1)
    sem_nome = re.search(r'<img[^>]*alt="([^"]*)"', cabecalho(servidor, nome="")).group(1)
    assert "Instituto Teste" in com_nome
    assert sem_nome.strip() != ""


def test_logotipo_fica_em_involucro_de_superficie_clara(servidor):
    assert re.search(r'class="logo-superficie"[^>]*>\s*<img', cabecalho(servidor))


def test_cabecalho_mostra_titulo_do_painel_e_nome_da_instituicao(servidor):
    html = cabecalho(servidor)
    assert "Painel de Acompanhamento Sistec" in html
    assert "Instituto Teste" in html


def test_botao_de_tema_tem_rotulo_textual_e_aria_pressed_falso(servidor):
    botao = re.search(r'<button\b[^>]*id="botao-tema"[^>]*>(.*?)</button>', cabecalho(servidor), re.S)
    assert 'aria-pressed="false"' in botao.group(0)
    assert "Usar tema escuro" in botao.group(1)


def test_botao_hamburguer_declara_estado_e_alvo_e_some_sem_menu(servidor):
    botao = re.search(r'<button\b[^>]*id="botao-menu"[^>]*>', cabecalho(servidor, com_menu=True))
    assert 'aria-expanded="false"' in botao.group(0)
    assert 'aria-controls="main-navigation"' in botao.group(0)
    assert 'id="botao-menu"' not in cabecalho(servidor, com_menu=False)


def test_logotipo_sem_arquivo_enviado_cai_em_padrao_generico(servidor, monkeypatch):
    monkeypatch.setattr(app_module, "get_logo_path", lambda: "app/data/uploads/branding/nao-existe.png")
    resposta = servidor.test_client().get("/branding/logo")
    padrao = Path(app_module.DEFAULT_LOGO_PATH).read_bytes()
    assert resposta.status_code == 200
    assert resposta.mimetype == "image/svg+xml"
    assert resposta.data == padrao


def itens_do_menu(servidor, caminho):
    html = renderizar(servidor, "shell/_menu.html", shell=contexto_shell(caminho))
    return html, re.findall(r"<a\b([^>]*)>\s*<span class=\"content\">(.*?)</span>", html, re.S)


@pytest.fixture
def instituicao_configurada(monkeypatch):
    monkeypatch.setattr(shell_modulo, "dados_instituicao", lambda: {"nome": "Instituto Teste"})
    monkeypatch.setattr(shell_modulo, "get_contato_email", lambda: "")


def test_menu_publico_renderiza_5_links_na_ordem_da_spec(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/matriculas")
    assert [rotulo.strip() for _, rotulo in itens] == [
        "Início",
        "Matrículas",
        "Eficiência Acadêmica",
        "Taxa de Evasão Anual",
        "Percentuais Legais",
    ]


def test_so_o_link_da_pagina_atual_tem_aria_current_e_classe_ativa(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/matriculas")
    com_aria = [rotulo.strip() for atributos, rotulo in itens if 'aria-current="page"' in atributos]
    com_classe = [rotulo.strip() for atributos, rotulo in itens if re.search(r'class="[^"]*\bactive\b', atributos)]
    assert com_aria == ["Matrículas"]
    assert com_classe == ["Matrículas"]


def test_menu_administrativo_renderiza_os_itens_de_paginas_admin(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/admin/historico")
    assert [rotulo.strip() for _, rotulo in itens] == [rotulo for rotulo, _ in PAGINAS_ADMIN]


def test_todos_os_itens_do_menu_sao_links_com_href(servidor, instituicao_configurada):
    _, itens = itens_do_menu(servidor, "/")
    assert len(itens) == 5
    assert all(re.search(r'href="/[^"]*"', atributos) for atributos, _ in itens)


@pytest.mark.parametrize("caminho", ["/admin/login", "/recuperar-acesso", "/admin/instalacao"])
def test_sem_menu_o_parcial_nao_renderiza_nada(servidor, instituicao_configurada, caminho):
    html, _ = itens_do_menu(servidor, caminho)
    assert html.strip() == ""


def migalhas(servidor, caminho):
    html = renderizar(servidor, "shell/_breadcrumb.html", shell=contexto_shell(caminho))
    return html, re.findall(r'<li class="crumb"[^>]*>(.*?)</li>', html, re.S)


def texto(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


@pytest.mark.parametrize("caminho", ["/", "/admin/login", "/recuperar-acesso", "/admin/instalacao"])
def test_sem_migalhas_o_breadcrumb_nao_renderiza_nada(servidor, instituicao_configurada, caminho):
    html, _ = migalhas(servidor, caminho)
    assert html.strip() == ""


def test_breadcrumb_inicio_matriculas_tem_link_e_pagina_atual(servidor, instituicao_configurada):
    _, itens = migalhas(servidor, "/matriculas")
    assert len(itens) == 2
    assert re.search(r'<a\b[^>]*href="/"[^>]*>\s*Início\s*</a>', itens[0])
    assert "<a" not in itens[1]
    assert re.search(r'<span\b[^>]*aria-current="page"[^>]*>\s*Matrículas\s*</span>', itens[1])


def test_breadcrumb_de_editar_campus_renderiza_3_itens_na_ordem(servidor, instituicao_configurada):
    _, itens = migalhas(servidor, "/admin/campi/8278857/editar")
    assert [texto(item) for item in itens] == ["Configurações", "Campi", "Editar"]


def rodape(servidor, nome="Instituto Teste", site="https://it.edu.br", email="pi@it.edu.br"):
    return renderizar(
        servidor,
        "shell/_footer.html",
        instituicao={"nome": nome, "site": site},
        contato_email=email,
    )


def test_rodape_completo_mostra_nome_site_email_e_area_administrativa(servidor):
    html = rodape(servidor)
    assert "Instituto Teste" in html
    assert re.search(r'<a\b[^>]*href="https://it\.edu\.br"[^>]*rel="noopener"[^>]*>', html)
    assert re.search(r'<a\b[^>]*href="mailto:pi@it\.edu\.br"[^>]*>\s*pi@it\.edu\.br\s*</a>', html)
    assert re.search(r'<a\b[^>]*href="/admin/login"[^>]*>\s*Área administrativa\s*</a>', html)


def test_site_sem_protocolo_recebe_https(servidor):
    assert 'href="https://it.edu.br"' in rodape(servidor, site="it.edu.br")


def test_rodape_sem_email_e_sem_site_nao_deixa_rotulo_link_nem_espaco_vazio(servidor):
    html = rodape(servidor, site="", email="")
    assert "mailto:" not in html
    assert len(re.findall(r"<a\b", html)) == 1
    assert "Instituto Teste" in html
    assert "Área administrativa" in html
    assert not re.search(r"<(span|li|a|div|p)\b[^>]*>\s*</\1>", html)


def test_rodape_sem_nome_nao_deixa_elemento_vazio(servidor):
    html = rodape(servidor, nome="")
    assert not re.search(r"<(span|li|a|div|p)\b[^>]*>\s*</\1>", html)
    assert "Área administrativa" in html


def scripts(servidor):
    return renderizar(servidor, "shell/_scripts.html")


def test_scripts_carrega_o_script_do_ds_uma_vez(servidor):
    html = scripts(servidor)
    assert len(re.findall(r'<script\b[^>]*src="/ds/govbr-ds/dist/core-init.min.js"', html)) == 1


def test_scripts_nao_carrega_componentes_avulsos_nem_versao_nao_minificada(servidor):
    html = scripts(servidor)
    for proibido in ("dist/components/", "core-base", "core-init.js"):
        assert proibido not in html
    assert not re.search(r'src="[^"]*core\.js"', html)


@pytest.mark.skipif(shutil.which("node") is None, reason="node não encontrado")
def test_falha_ao_carregar_core_min_js_marca_ds_sem_js_no_html(servidor):
    onerror = re.search(r'onerror="([^"]*)"', scripts(servidor)).group(1)
    executor = (
        "const vm = require('vm');"
        "const classes = [];"
        "const sandbox = { document: { documentElement: { classList: { add: (c) => classes.push(c) } } } };"
        "vm.runInNewContext(process.argv[1], sandbox);"
        "process.stdout.write(JSON.stringify(classes));"
    )
    resultado = subprocess.run(["node", "-e", executor, html_desescapado(onerror)], capture_output=True, text=True, timeout=30)
    assert resultado.returncode == 0, resultado.stderr
    assert json.loads(resultado.stdout) == ["ds-sem-js"]


def html_desescapado(valor):
    return html_lib.unescape(valor)


def modal(servidor):
    return renderizar(servidor, "shell/_modal_confirmacao.html")


def test_modal_e_dialogo_modal_rotulado_por_um_id_existente(servidor):
    html = modal(servidor)
    dialogo = re.search(r'<div\b[^>]*class="br-modal[^"]*"[^>]*>', html).group(0)
    assert 'role="dialog"' in dialogo
    assert 'aria-modal="true"' in dialogo
    rotulo = re.search(r'aria-labelledby="([^"]+)"', dialogo).group(1)
    assert f'id="{rotulo}"' in html


def test_modal_tem_icone_de_alerta_escondido_de_leitores_de_tela(servidor):
    assert re.search(r'<i\b[^>]*class="[^"]*fa-exclamation-triangle[^"]*"[^>]*aria-hidden="true"', modal(servidor))


def test_modal_tem_cancelar_secundario_e_confirmar_primario_com_ids_fixos(servidor):
    html = modal(servidor)
    cancelar = re.search(r'<button\b[^>]*id="modal-confirmacao-cancelar"[^>]*>(.*?)</button>', html, re.S)
    confirmar = re.search(r'<button\b[^>]*id="modal-confirmacao-confirmar"[^>]*>(.*?)</button>', html, re.S)
    assert re.search(r'class="br-button secondary\b', cancelar.group(0))
    assert cancelar.group(1).strip() == "Cancelar"
    assert re.search(r'class="br-button primary\b', confirmar.group(0))
    assert 'id="modal-confirmacao-mensagem"' in html


def test_modal_renderiza_fechado(servidor):
    scrim = re.search(r'<div\b[^>]*class="br-scrim[^"]*"[^>]*>', modal(servidor)).group(0)
    assert "foco" in scrim
    assert not re.search(r'class="[^"]*\bactive\b', scrim)


def macro(servidor, chamada):
    with servidor.test_request_context("/"):
        return render_template_string('{% from "shell/_macros.html" import campo, mensagem, botoes_formulario, tag_situacao, botao_icone %}' + chamada)


def test_campo_com_erro_fica_em_danger_com_texto_abaixo_ligado_por_aria_describedby(servidor):
    html = macro(servidor, '{{ campo("co_unidade", "Código da unidade", "", erro="Preencha o campo obrigatório") }}')
    assert re.search(r'class="br-input danger"', html)
    assert html.index("<input") < html.index("Preencha o campo obrigatório")
    descrito_por = re.search(r'aria-describedby="([^"]+)"', html).group(1)
    assert re.search(rf'id="{re.escape(descrito_por)}"[^>]*>[^<]*(<[^>]+>\s*)*Preencha o campo obrigatório', html, re.S)


def test_campo_sem_erro_nao_tem_aria_describedby(servidor):
    html = macro(servidor, '{{ campo("cidade", "Cidade", "Jaguari") }}')
    assert "aria-describedby" not in html
    assert 'value="Jaguari"' in html


def test_campo_tem_rotulo_visivel_acima_e_marca_obrigatorio(servidor):
    html = macro(servidor, '{{ campo("cidade", "Cidade", "", obrigatorio=True) }}')
    assert re.search(r'<label for="cidade">\s*Cidade', html)
    assert html.index("<label") < html.index("<input")
    assert re.search(r"<input\b[^>]*\brequired\b", html)


@pytest.mark.parametrize("tipo,papel", [("success", "alert"), ("danger", "alert"), ("info", "status"), ("warning", "status")])
def test_mensagem_usa_classe_do_tipo_e_o_papel_da_spec(servidor, tipo, papel):
    html = macro(servidor, '{{ mensagem("' + tipo + '", "Campus atualizado.") }}')
    assert re.search(rf'class="br-message {tipo}"[^>]*role="{papel}"|role="{papel}"[^>]*class="br-message {tipo}"', html)
    assert "Campus atualizado." in html


def test_botoes_do_formulario_tem_cancelar_secundario_antes_de_salvar_primario(servidor):
    html = macro(servidor, '{{ botoes_formulario("/admin/campi", "Salvar") }}')
    cancelar = re.search(r'<a\b[^>]*class="br-button secondary[^"]*"[^>]*href="/admin/campi"[^>]*>\s*Cancelar\s*</a>', html)
    salvar = re.search(r'<button\b[^>]*class="br-button primary[^"]*"[^>]*type="submit"[^>]*>\s*Salvar\s*</button>', html)
    assert cancelar and salvar
    assert cancelar.start() < salvar.start()


def test_tag_de_situacao_mostra_o_texto_em_br_tag(servidor):
    ativo = macro(servidor, "{{ tag_situacao(True) }}")
    desativado = macro(servidor, "{{ tag_situacao(False) }}")
    assert re.search(r'<span class="br-tag">\s*Ativo\s*</span>', ativo)
    assert re.search(r'<span class="br-tag">\s*Desativado\s*</span>', desativado)


def test_botao_de_icone_tem_nome_acessivel_icone_escondido_e_area_minima_do_ds(servidor):
    html = macro(servidor, '{{ botao_icone("edit", "Editar campus Perfil A") }}')
    botao = re.search(r"<button\b[^>]*>", html).group(0)
    assert 'aria-label="Editar campus Perfil A"' in botao
    assert re.search(r'class="br-button circle"', botao)
    assert re.search(r'<i\b[^>]*aria-hidden="true"', html)


def test_botao_de_icone_com_href_vira_link_com_o_mesmo_nome_acessivel(servidor):
    html = macro(servidor, '{{ botao_icone("edit", "Editar campus Perfil A", href="/admin/campi/1/editar") }}')
    assert re.search(r'<a\b[^>]*href="/admin/campi/1/editar"[^>]*aria-label="Editar campus Perfil A"', html)
    assert "<button" not in html


def test_botao_de_icone_escapa_o_texto_de_confirmacao(servidor):
    html = macro(servidor, '{{ botao_icone("trash", "Excluir", tipo="submit", confirmar="Excluir \\"A&B\\"?", rotulo_confirmar="Excluir") }}')
    assert 'data-confirm="Excluir &#34;A&amp;B&#34;?"' in html
    assert 'data-confirm-rotulo="Excluir"' in html


def test_botoes_do_formulario_empilham_abaixo_de_576px_e_alinham_a_direita_depois(servidor):
    html = macro(servidor, '{{ botoes_formulario("/admin/campi", "Salvar") }}')
    conteiner = re.search(r'<div class="([^"]*)">\s*<a\b', html).group(1).split()
    assert {"d-flex", "flex-column", "flex-sm-row", "justify-content-sm-end"} <= set(conteiner)


def test_head_define_o_tema_antes_de_qualquer_folha_de_estilo_para_nao_piscar(servidor):
    html = renderizar(servidor, "shell/_head.html", titulo="Início")
    assert html.index("<script>") < html.index('rel="stylesheet"')
