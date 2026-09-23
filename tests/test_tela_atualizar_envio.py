"""Escolha de origem e bloco de envio na tela Atualizar dados (T10/UPL-01).

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


def test_tela_oferece_as_duas_origens_em_br_radio(html):
    radios = re.findall(r'<div class="br-radio[^"]*">\s*<input[^>]*id="(origem-[a-z]+)"[^>]*>\s*<label for="origem-[a-z]+">([^<]+)</label>', html)
    assert radios == [("origem-sistec", "Atualizar do Sistec"), ("origem-envio", "Enviar pastas")]
    assert re.search(r'<input[^>]*id="origem-sistec"[^>]*name="origem"[^>]*value="sistec"[^>]*checked', html)
    assert re.search(r'<input[^>]*id="origem-envio"[^>]*name="origem"[^>]*value="envio"', html)


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


def test_bloco_de_envio_tem_resultado_por_arquivo_e_confirmacao_de_preservacao(html):
    area = re.search(r'<div id="envio-arquivos-area".*?</div>\s*</div>', html, re.S).group(0)
    assert re.search(r'<div class="br-table"><div class="responsive"><table>', area.replace("\n", "").replace("  ", ""))
    assert re.search(r'<tbody id="envio-arquivos"></tbody>', area)

    preservacao = re.search(r'<div id="envio-preservacao"[^>]*>.*?</div>\s*</div>', html, re.S).group(0)
    assert re.search(r'<input id="envio-confirmar-preservacao" type="checkbox">', preservacao)
    assert re.search(r'<label for="envio-confirmar-preservacao">[^<]+</label>', preservacao)
    assert 'class="br-message warning"' in html
    # A caixa de confirmação é separada do botão de enviar e começa escondida.
    assert re.search(r'<div id="envio-preservacao"[^>]*hidden>', html)
    assert re.search(r'<div id="bloco-envio" hidden>', html)


def test_blocos_empilham_abaixo_de_992px_com_classes_do_ds(html):
    for bloco in ("atualizar-origem", "bloco-envio"):
        inicio = html.index(f'id="{bloco}"')
        trecho = html[inicio : html.index('id="btn-enviar-pastas"', inicio)]
        assert 'class="d-flex flex-column flex-lg-row"' in trecho, bloco
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
    # A baixa continua visível por padrão; o envio é que começa escondido.
    assert re.search(r'<div id="bloco-sistec">', html)
