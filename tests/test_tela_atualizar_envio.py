"""Os dois cards (Sistec e envio) na tela Atualizar dados (T10/UPL-01, CAD-01).

Integração com o `test_client`: o HTML é lido como a pessoa o recebe. A tela
não é um formulário que envia arquivos sozinho — quem monta o multipart é
`atualizar.js` (T11) — então o que se cobra aqui é a marcação e os ids que o
script procura.
"""

import re

import pytest

from app import app as app_module


@pytest.fixture
def cliente_autenticado(monkeypatch):
    cliente = app_module.server.test_client()
    with cliente.session_transaction() as sessao:
        sessao["admin_usuario"] = "pi@ife.edu.br"
        sessao["admin_autenticado"] = True
    monkeypatch.setattr(app_module.instalacao, "concluida", lambda: True)
    return cliente


@pytest.fixture
def html(cliente_autenticado):
    resposta = cliente_autenticado.get("/admin/atualizar")
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


def test_tela_oferece_os_dois_caminhos_sempre_visiveis_em_cards(html):
    """CAD-01/CAD-04: sem rádio de origem — os dois cards convivem lado a lado,
    e nenhum usa a classe `br-card` do pacote (`position:absolute`, feita para
    menu flutuante/cookiebar, não para conteúdo de página)."""
    assert "origem-sistec" not in html
    assert "origem-envio" not in html
    assert "atualizar-origem" not in html
    assert re.search(r'<div id="bloco-sistec" class="card-atualizar[^"]*">\s*<h2>Atualizar do Sistec</h2>', html)
    assert re.search(r'<div id="bloco-envio" class="card-atualizar">\s*<h2>Enviar pastas</h2>', html)
    assert "br-card" not in html


def test_bloco_de_envio_tem_uma_pasta_para_ciclos_e_uma_para_matriculas(html):
    for campo_id in ("envio-ciclos", "envio-matriculas"):
        tag = re.search(rf'<input\b[^>]*id="{campo_id}"[^>]*>', html).group(0)
        assert "webkitdirectory" in tag
        assert "multiple" in tag
        assert 'accept=".csv"' in tag
        assert " hidden>" in tag
    # Os dois campos têm nome de formulário igual ao que a rota lê.
    assert re.search(r'<input\b[^>]*id="envio-ciclos"[^>]*name="ciclos"', html)
    assert re.search(r'<input\b[^>]*id="envio-matriculas"[^>]*name="matriculas"', html)


@pytest.mark.parametrize(
    ("campo_id", "rotulo"),
    [("ciclos", "Escolher pasta de ciclos"), ("matriculas", "Escolher pasta de matrículas")],
)
def test_cada_pasta_tem_um_botao_visivel_que_aponta_para_o_status(html, campo_id, rotulo):
    """CEP-01: quem recebe o clique é um `button` nativo, não um `input` escondido
    pelo componente do DS."""
    botao = re.search(rf'<button\b[^>]*id="btn-escolher-{campo_id}"[^>]*>{rotulo}</button>', html)
    assert botao, f"botão de escolher a pasta de {campo_id} ausente"
    tag = botao.group(0)
    assert 'class="br-button secondary"' in tag
    assert 'type="button"' in tag
    assert f'aria-describedby="envio-{campo_id}-status"' in tag
    assert " hidden" not in tag


@pytest.mark.parametrize(("campo_id", "palavra"), [("ciclos", "ciclos"), ("matriculas", "matrículas")])
def test_cada_pasta_tem_um_status_anunciado_comecando_pela_obrigatoriedade(html, campo_id, palavra):
    """CEP-02: o status de cada pasta é um parágrafo anunciado, com o texto de
    obrigatoriedade enquanto nada foi escolhido."""
    status = re.search(
        rf'<p class="campo-pasta-status" id="envio-{campo_id}-status" role="status" aria-live="polite">([^<]+)</p>',
        html,
    )
    assert status, f"status da pasta de {campo_id} ausente"
    assert status.group(1) == f"Nenhuma pasta de {palavra} escolhida — obrigatória."


def test_o_input_escondido_de_cada_pasta_fica_atras_do_botao(html):
    """CEP-01: o `input` de arquivo é o mesmo de antes, só escondido; o controle
    que a pessoa vê e clica é o botão."""
    for campo_id in ("ciclos", "matriculas"):
        input_tag = re.search(rf'<input\b[^>]*id="envio-{campo_id}"[^>]*>', html).group(0)
        assert " hidden>" in input_tag
        botao_tag = re.search(rf'<button\b[^>]*id="btn-escolher-{campo_id}"[^>]*>', html).group(0)
        assert "hidden" not in botao_tag


def test_o_bloco_de_envio_nao_usa_mais_a_classe_br_upload(html):
    """CEP-01: o componente `.br-upload` do pacote (que esconde o `input`) sai
    do caminho; a marcação passa a ser própria."""
    inicio = html.index('id="bloco-envio"')
    bloco = html[inicio : html.index('id="atualizar-progresso"', inicio)]
    assert "br-upload" not in bloco
    assert "upload-input" not in bloco


def test_resultados_do_envio_ocupam_a_largura_inteira_abaixo_dos_dois_cards(html):
    """AFE-02 (supera CAD-03): o resultado por arquivo e os avisos do envio saem
    da coluna do card e passam a ocupar a largura inteira da página, na mesma
    faixa de Progresso e Prévia — fora do container flex dos dois cards."""
    inicio_cards = html.index('<div class="d-flex flex-column flex-lg-row">')
    inicio_resultado = html.index('id="envio-arquivos-area"')
    inicio_progresso = html.index('id="atualizar-progresso"')
    cards = html[inicio_cards:inicio_resultado]
    largura_inteira = html[inicio_resultado:inicio_progresso]

    # Os dois cards seguem com o que é deles: texto, seletores de pasta, botão e status.
    assert 'id="bloco-sistec"' in cards and 'id="bloco-envio"' in cards
    assert 'id="envio-ciclos"' in cards and 'id="envio-matriculas"' in cards
    assert 'id="btn-enviar-pastas"' in cards and 'id="status-envio"' in cards

    # O resultado e os avisos ficam fora dos cards, na faixa de largura inteira.
    assert 'id="envio-arquivos-area"' not in cards
    assert 'id="envio-avisos"' not in cards
    assert 'id="envio-arquivos-area"' in largura_inteira
    assert 'id="envio-avisos"' in largura_inteira
    # Progresso/Prévia continuam fora dos dois cards, depois do resultado.
    assert 'id="atualizar-previa"' not in cards


def test_area_de_resultados_tem_o_resultado_por_arquivo(html):
    area = re.search(r'<div id="envio-arquivos-area".*?</div>\s*</div>', html, re.S).group(0)
    assert re.search(r'<div class="br-table"><div class="responsive"><table>', area.replace("\n", "").replace("  ", ""))
    assert re.search(r'<tbody id="envio-arquivos"></tbody>', area)
    # AFE-03: a linha do cadastro automático é um texto simples ao lado da dos
    # ignorados — não um `br-message warning`.
    assert re.search(r'<p id="envio-ignorados" hidden></p>\s*<p id="envio-cadastrados" hidden></p>', html)
    # A lista de avisos do envio continua existindo, escondida.
    assert re.search(r'<ul id="envio-avisos" class="br-message warning" role="alert" hidden></ul>', html)


def test_card_de_envio_nao_pede_confirmacao_de_preservacao(html):
    """AFE-01: nenhuma caixa amarela de confirmação na tela; o parágrafo do card
    segue dizendo que os campi ausentes são preservados, mas não promete nenhuma
    confirmação antes de salvar."""
    for id_removido in ("envio-preservacao", "envio-preservacao-texto", "envio-confirmar-preservacao"):
        assert id_removido not in html

    paragrafo = re.search(
        r'Campus que você não enviar tem os dados atuais <strong>preservados</strong>[^<]*</p>', html
    )
    assert paragrafo, "o card continua avisando que os campi ausentes ficam preservados"
    assert "nada dele é apagado" in paragrafo.group(0)
    assert "confirmação" not in paragrafo.group(0)


def test_os_dois_cards_empilham_abaixo_de_992px_com_classes_do_ds(html):
    """CAD-02: os dois cards ficam num único container flex — lado a lado a
    partir de 992px, empilhados abaixo disso."""
    inicio = html.index('class="d-flex flex-column flex-lg-row"')
    trecho = html[inicio : html.index('id="btn-enviar-pastas"', inicio)]
    assert 'id="bloco-sistec"' in trecho
    assert 'id="bloco-envio"' in trecho
    assert "@media" not in html
    # O empilhamento abaixo de 576px da baixa continua como estava.
    acoes = re.search(r'<div[^>]*id="atualizar-acoes"[^>]*>', html).group(0)
    assert "flex-column" in acoes and "flex-sm-row" in acoes


def test_bloco_de_envio_nao_mexe_nos_ids_e_data_confirm_da_baixa(html):
    for botao, pergunta in (
        ("btn-atualizar-sistec", None),
        ("btn-login-feito", None),
        ("btn-cancelar", "Cancelar a atualização em andamento?"),
        ("btn-salvar", None),
        ("btn-descartar", "Descartar esta prévia?"),
        ("btn-publicar", "Publicar a versão interna no painel público?"),
        ("btn-desfazer", "Desfazer a última publicação?"),
    ):
        tag = re.search(rf'<button\b[^>]*id="{botao}"[^>]*>', html).group(0)
        if pergunta is not None:
            assert f'data-confirm="{pergunta}"' in tag
    # Os dois cards ficam sempre visíveis (CAD-01): nenhum começa escondido.
    assert re.search(r'<div id="bloco-sistec" class="card-atualizar[^"]*">', html)
    assert re.search(r'<div id="bloco-envio" class="card-atualizar">', html)


# ===================== previa-paginas-publicas, T18 =====================


def test_previa_mostra_a_faixa_nao_publicada(html):
    """PVP-02: a faixa identifica os dados como prévia não publicada."""
    assert re.search(r'<div id="previa-nao-publicada" class="br-message warning" role="status">', html)
    assert "Prévia não publicada" in html
    assert "nada foi salvo" in html


def test_previa_tem_quatro_links_de_pagina_com_data_pagina(html):
    """PVP-01: quatro links, cada um com `data-pagina` para o script preencher
    o `href` com o `execucao_id` do polling."""
    paginas = re.findall(r'data-pagina="([^"]+)"', html)
    assert paginas == ["matriculas", "eficiencia", "evasao", "percentuais-legais"]
    for pagina in paginas:
        assert re.search(rf'<a\b[^>]*class="br-button secondary"[^>]*data-pagina="{pagina}"', html)


def test_salvar_e_descartar_continuam_na_area_da_previa(html):
    inicio = html.index('id="atualizar-previa"')
    fim = html.index('id="status-salvar"', inicio)
    area = html[inicio:fim]
    assert 'id="btn-salvar"' in area
    assert "Salvar na versão interna" in area
    assert 'id="btn-descartar"' in area
    assert 'data-confirm="Descartar esta prévia?"' in area


def test_previa_nao_usa_cor_hexadecimal_literal(html):
    """AD-003: nenhuma cor hexadecimal literal na área da prévia."""
    inicio = html.index('id="atualizar-previa"')
    fim = html.index('id="status-salvar"', inicio)
    area = html[inicio:fim]
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", area)
