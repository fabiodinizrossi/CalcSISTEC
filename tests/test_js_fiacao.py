"""Fiação de DOM de `tema.js`, `menu.js` e `confirmar.js` (DS-38, DS-47, DS-48, DS-49, DS-58, DS-59,
DS-60, DS-75 e o caso de borda de mudança da preferência do sistema): cliques, teclas e observadores."""

import pytest

from dom_falso import precisa_de_node, rodar

pytestmark = precisa_de_node

# ---------------------------------------------------------------- tema.js

PREPARAR_TEMA = """
const armazenado = {};
janela.localStorage = { getItem: (k) => (k in armazenado ? armazenado[k] : null), setItem: (k, v) => { armazenado[k] = v; } };
doc.documentElement.setAttribute("data-tema", "claro");
const rotulo = criarElemento("rotulo");
const botao = criarElemento("botao-tema");
botao.filhosPorSeletor["span"] = rotulo;
rotulo.textContent = "Tema escuro";
registrar(botao, "botao-tema");
globalThis.__estado = { armazenado, rotulo, botao };
"""


def test_clique_no_botao_de_tema_troca_o_tema_o_aria_pressed_o_rotulo_e_grava_a_escolha():
    verificar = """
    const { armazenado, rotulo, botao } = globalThis.__estado;
    const ler = () => ({ tema: doc.documentElement.getAttribute("data-tema"), pressed: botao.getAttribute("aria-pressed"), rotulo: rotulo.textContent, salvo: armazenado["calcsistec-tema"] || null });
    const inicial = ler();
    botao.disparar("click");
    const aposEscuro = ler();
    botao.disparar("click");
    return { inicial, aposEscuro, aposClaro: ler() };
    """
    preparar = PREPARAR_TEMA.replace("globalThis.__estado", "contexto.__estado")
    verificar = verificar.replace("globalThis.__estado", "contexto.__estado")
    resultado = rodar("tema.js", preparar, verificar)
    assert resultado["inicial"] == {"tema": "claro", "pressed": "false", "rotulo": "Tema escuro", "salvo": None}
    assert resultado["aposEscuro"] == {"tema": "escuro", "pressed": "true", "rotulo": "Tema claro", "salvo": "escuro"}
    assert resultado["aposClaro"] == {"tema": "claro", "pressed": "false", "rotulo": "Tema escuro", "salvo": "claro"}


@pytest.mark.parametrize(
    "salvo,esperado",
    [(None, "escuro"), ("claro", "claro")],
)
def test_mudanca_da_preferencia_do_sistema_so_vale_sem_escolha_salva(salvo, esperado):
    preparar = PREPARAR_TEMA.replace("globalThis.__estado", "contexto.__estado") + (
        f'if ({salvo!r} !== null) {{ armazenado["calcsistec-tema"] = {salvo!r}; }}' if salvo else ""
    )
    verificar = """
    consultas[0].mudar(true);
    return doc.documentElement.getAttribute("data-tema");
    """
    assert rodar("tema.js", preparar, verificar) == esperado


# ---------------------------------------------------------------- menu.js

PREPARAR_MENU = """
const menu = criarElemento("menu");
const botao = criarElemento("botao-menu");
const item = criarElemento("item");
item.pai = menu;
registrar(menu, null, ".br-menu");
registrar(botao, "botao-menu");
contexto.__estado = { menu, botao, item };
"""


def test_o_menu_nao_tem_recolhimento_persistente_em_nenhuma_largura():
    verificar = """
    const { menu, botao } = contexto.__estado;
    const ler = () => ({ expanded: botao.getAttribute("aria-expanded"), recolhido: menu.classList.contains("menu-recolhido") });
    const inicial = ler();
    botao.disparar("click");
    botao.disparar("keydown", { code: "Enter" });
    botao.disparar("keydown", { code: "Space" });
    return { inicial, aposTeclas: ler() };
    """
    assert rodar("menu.js", PREPARAR_MENU, verificar, largura=1280) == {
        "inicial": {"expanded": "false", "recolhido": False},
        "aposTeclas": {"expanded": "false", "recolhido": False},
    }


def test_abaixo_de_992px_o_menu_comeca_fechado_e_o_botao_nao_recolhe_nada():
    verificar = """
    const { menu, botao } = contexto.__estado;
    const inicial = botao.getAttribute("aria-expanded");
    botao.disparar("click");
    return { inicial, recolhido: menu.classList.contains("menu-recolhido") };
    """
    assert rodar("menu.js", PREPARAR_MENU, verificar, largura=576) == {"inicial": "false", "recolhido": False}


def test_abaixo_de_992px_aria_expanded_acompanha_o_menu_e_o_foco_volta_ao_botao_ao_fechar():
    verificar = """
    const { menu, botao, item } = contexto.__estado;
    menu.classList.add("active");
    const aberto = botao.getAttribute("aria-expanded");
    item.focus();
    menu.classList.remove("active");
    const aposFechar = botao.getAttribute("aria-expanded");
    executarFila();
    return { aberto, aposFechar, foco: doc.activeElement === botao };
    """
    assert rodar("menu.js", PREPARAR_MENU, verificar, largura=576) == {"aberto": "true", "aposFechar": "false", "foco": True}


def test_o_foco_nao_e_tomado_se_o_usuario_ja_foi_para_outro_controle():
    verificar = """
    const { menu, botao } = contexto.__estado;
    const outro = criarElemento("outro");
    menu.classList.add("active");
    menu.classList.remove("active");
    outro.focus();
    executarFila();
    return doc.activeElement === outro;
    """
    assert rodar("menu.js", PREPARAR_MENU, verificar, largura=576) is True


# ---------------------------------------------------------------- confirmar.js

PREPARAR_MODAL = """
const scrim = criarElemento("scrim");
const mensagem = criarElemento("mensagem");
const cancelar = criarElemento("cancelar");
const confirmar = criarElemento("confirmar");
registrar(scrim, "modal-confirmacao");
registrar(mensagem, "modal-confirmacao-mensagem");
registrar(cancelar, "modal-confirmacao-cancelar");
registrar(confirmar, "modal-confirmacao-confirmar");
const origem = criarElemento("origem");
origem.focus();
contexto.__estado = { scrim, mensagem, cancelar, confirmar, origem };
"""


def test_confirmar_acao_abre_o_modal_com_a_pergunta_o_rotulo_e_o_foco_em_cancelar():
    verificar = """
    const { scrim, mensagem, cancelar, confirmar } = contexto.__estado;
    contexto.window.confirmarAcao("Excluir o campus X?", { rotuloConfirmar: "Excluir" });
    return { ativo: scrim.classList.contains("active"), texto: mensagem.textContent, rotulo: confirmar.textContent, foco: doc.activeElement === cancelar };
    """
    assert rodar("confirmar.js", PREPARAR_MODAL, verificar) == {
        "ativo": True,
        "texto": "Excluir o campus X?",
        "rotulo": "Excluir",
        "foco": True,
    }


@pytest.mark.parametrize(
    "acao,resposta_esperada",
    [
        ('doc.disparar("keydown", { key: "Escape" });', False),
        ("cancelar.disparar('click');", False),
        ("confirmar.disparar('click');", True),
    ],
)
def test_esc_e_cancelar_recusam_e_confirmar_aceita_e_todos_devolvem_o_foco_a_origem(acao, resposta_esperada):
    verificar = f"""
    const {{ scrim, cancelar, confirmar, origem }} = contexto.__estado;
    const promessa = contexto.window.confirmarAcao("Pergunta?");
    {acao}
    const resposta = await promessa;
    return {{ resposta, fechado: !scrim.classList.contains("active"), foco: doc.activeElement === origem }};
    """
    assert rodar("confirmar.js", PREPARAR_MODAL, verificar) == {"resposta": resposta_esperada, "fechado": True, "foco": True}


def test_tab_prende_o_foco_entre_cancelar_e_confirmar():
    verificar = """
    const { cancelar, confirmar } = contexto.__estado;
    contexto.window.confirmarAcao("Pergunta?");
    const foco = [];
    doc.disparar("keydown", { key: "Tab", shiftKey: false }); foco.push(doc.activeElement === confirmar);
    doc.disparar("keydown", { key: "Tab", shiftKey: false }); foco.push(doc.activeElement === cancelar);
    doc.disparar("keydown", { key: "Tab", shiftKey: true }); foco.push(doc.activeElement === confirmar);
    return foco;
    """
    assert rodar("confirmar.js", PREPARAR_MODAL, verificar) == [True, True, True]


PREPARAR_FORMULARIO = (
    PREPARAR_MODAL
    + """
const formulario = criarElemento("formulario");
formulario.seletores = ["form.confirm-form"];
const excluir = criarElemento("excluir");
excluir.dataset.confirm = "Tem certeza?";
excluir.dataset.confirmRotulo = "Excluir";
formulario.filhosPorSeletor["button[data-confirm]"] = excluir;
Object.setPrototypeOf(formulario, contexto.HTMLFormElement.prototype);
contexto.__estado.formulario = formulario;
"""
)


@pytest.mark.parametrize("botao,enviado", [("confirmar", True), ("cancelar", False)])
def test_formulario_confirm_form_so_e_enviado_depois_de_confirmar_no_modal(botao, enviado):
    verificar = f"""
    const {{ scrim, mensagem, confirmar, cancelar, formulario }} = contexto.__estado;
    const evento = doc.disparar("submit", {{ target: formulario }});
    const pergunta = mensagem.textContent;
    const rotulo = confirmar.textContent;
    const abriu = scrim.classList.contains("active");
    {botao}.disparar("click");
    await Promise.resolve(); await Promise.resolve();
    return {{ evitado: evento.evitado, abriu, pergunta, rotulo, enviados: submetidos.length, marcado: formulario.dataset.confirmado || null }};
    """
    r = rodar("confirmar.js", PREPARAR_FORMULARIO, verificar)
    assert r["evitado"] is True
    assert r["abriu"] is True
    assert r["pergunta"] == "Tem certeza?"
    assert r["rotulo"] == "Excluir"
    assert r["enviados"] == (1 if enviado else 0)
    assert r["marcado"] == ("1" if enviado else None)
