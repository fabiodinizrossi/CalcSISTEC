"""`atualizar.js`, segunda origem (T11/UPL-01, UPL-08): escolha de origem,
envio multipart das duas pastas, resultado por arquivo e a confirmação de
preservação que antecede o Salvar.

Os casos rodam o script de verdade em `node` sobre o DOM simulado de
`dom_falso.py`; `fetch`, `FormData` e `setInterval` são dublês registrados em
`preparar`, que o script enxerga como globais.
"""

import json

import pytest

from dom_falso import precisa_de_node, rodar

pytestmark = precisa_de_node

IDS = [
    "status-navegador",
    "barra-area",
    "barra-progresso",
    "barra-rotulo",
    "passos-navegador",
    "avisos-navegador",
    "atualizar-progresso",
    "progresso-resumo",
    "progresso-pares",
    "atualizar-previa",
    "previa-resumo",
    "previa-cabecalho",
    "previa-linhas",
    "status-salvar",
    "status-publicacao",
    "btn-atualizar-sistec",
    "btn-login-feito",
    "btn-cancelar",
    "btn-salvar",
    "btn-descartar",
    "btn-publicar",
    "btn-desfazer",
    "origem-sistec",
    "origem-envio",
    "bloco-sistec",
    "bloco-envio",
    "envio-ciclos",
    "envio-matriculas",
    "btn-enviar-pastas",
    "status-envio",
    "envio-arquivos-area",
    "envio-ignorados",
    "envio-preservacao",
    "envio-preservacao-texto",
    "envio-confirmar-preservacao",
]

# Estado que o polling devolve por padrão: nenhuma execução aberta.
SEM_EXECUCAO = {"estado": None, "navegador": None}


def _estado_previa(
    origem="envio", campi_preservados=(), campi_nao_cadastrados=(), arquivos_ignorados=(), matriculas_orfas=0
):
    return {
        "estado": "previa",
        "execucao_id": "abc",
        "origem": origem,
        "navegador": None,
        "erro_consolidacao": None,
        "progresso": {"total": 2, "concluidos": 2},
        "pares": [],
        "previa": {"ciclos": 1, "matriculas": 1, "campi_falhos": list(campi_preservados), "amostra": []},
        "campi_preservados": list(campi_preservados),
        "campi_nao_cadastrados": list(campi_nao_cadastrados),
        "arquivos_ignorados": list(arquivos_ignorados),
        "matriculas_orfas": matriculas_orfas,
    }


def _preparar(estado=None, respostas=(), pendente=False, arquivos_ciclos=(), arquivos_matriculas=()):
    """Monta o DOM da tela e os dublês de rede para um caso."""
    return f"""
const ids = {json.dumps(IDS)};
ids.forEach((id) => {{ registrar(criarElemento(id), id); }});
const comFilhos = (id) => {{
  const e = registrar(criarElemento(id), id);
  e.filhos = [];
  e.appendChild = (f) => {{ e.filhos.push(f); return f; }};
  return e;
}};
comFilhos("envio-arquivos");
comFilhos("envio-avisos");
// O elemento simulado não limpa os filhos sozinho: `innerHTML = ""` precisa
// esvaziar a lista, senão as linhas se acumulam a cada redesenho.
["envio-arquivos", "envio-avisos"].forEach((id) => {{
  const e = doc.porId[id];
  Object.defineProperty(e, "innerHTML", {{ set() {{ e.filhos.length = 0; }}, get() {{ return ""; }} }});
}});
doc.porId["barra-progresso"].removeAttribute = () => {{}};
doc.createElement = (tag) => {{
  const e = criarElemento(tag);
  e.filhos = [];
  e.appendChild = (f) => {{ e.filhos.push(f); return f; }};
  return e;
}};
doc.porId["bloco-envio"].hidden = true;
doc.porId["origem-sistec"].checked = true;
doc.porId["envio-confirmar-preservacao"].checked = false;
doc.porId["envio-ciclos"].files = {json.dumps([{"name": nome} for nome in arquivos_ciclos])};
doc.porId["envio-matriculas"].files = {json.dumps([{"name": nome} for nome in arquivos_matriculas])};
contexto.setInterval = () => 0;
contexto.FormData = class {{
  constructor() {{ this.anexos = []; }}
  append(chave, valor) {{ this.anexos.push([chave, valor.name || String(valor)]); }}
}};
contexto.__t = {{ estado: {json.dumps(estado if estado is not None else SEM_EXECUCAO)}, respostas: {json.dumps(list(respostas))}, pendente: {json.dumps(pendente)}, resolver: null }};
contexto.fetch = (url, opcoes) => {{
  contexto.__t.chamadas = contexto.__t.chamadas || [];
  contexto.__t.chamadas.push({{ url, opcoes }});
  if (url.indexOf("/admin/atualizar/execucao") !== -1) {{
    return Promise.resolve({{ status: 200, ok: true, json: async () => contexto.__t.estado }});
  }}
  if (contexto.__t.pendente) {{
    return new Promise((resolver) => {{ contexto.__t.resolver = resolver; }});
  }}
  const proxima = contexto.__t.respostas.shift() || {{ status: 200, corpo: {{ ciclos: 1, matriculas: 1 }} }};
  return Promise.resolve({{
    status: proxima.status,
    ok: proxima.status >= 200 && proxima.status < 300,
    json: async () => proxima.corpo,
  }});
}};
contexto.__t.chamadas = [];
"""


# `setTimeout` é dublê sem relógio, então o avanço das promessas do `fetch` é
# feito à mão, em passos de microtarefa.
ESPERAR = "for (let i = 0; i < 12; i += 1) await Promise.resolve();"

CHAMADAS_PARA = """
const para = (trecho) => contexto.__t.chamadas.filter((c) => c.url.indexOf(trecho) !== -1);
"""


def test_escolher_uma_origem_ativa_so_os_controles_dela():
    verificar = (
        ESPERAR
        + """
const sistec = doc.porId["bloco-sistec"];
const envio = doc.porId["bloco-envio"];
const ler = () => ({ sistec: Boolean(sistec.hidden), envio: Boolean(envio.hidden) });
const inicial = ler();
doc.porId["origem-envio"].disparar("change");
const aposEnvio = ler();
doc.porId["origem-sistec"].disparar("change");
return { inicial, aposEnvio, aposSistec: ler() };
"""
    )
    assert rodar("atualizar.js", _preparar(), verificar) == {
        "inicial": {"sistec": False, "envio": True},
        "aposEnvio": {"sistec": True, "envio": False},
        "aposSistec": {"sistec": False, "envio": True},
    }


def test_enviar_sem_uma_das_pastas_avisa_e_nao_chama_o_servidor():
    verificar = (
        ESPERAR
        + CHAMADAS_PARA
        + """
doc.porId["envio-ciclos"].files = [{ name: "ciclos-U1.csv" }];
doc.porId["origem-envio"].disparar("change");
doc.porId["btn-enviar-pastas"].disparar("click");
"""
        + ESPERAR
        + """
return { texto: doc.porId["status-envio"].textContent, chamadas: para("/admin/atualizar/envio").length };
"""
    )
    resultado = rodar("atualizar.js", _preparar(), verificar)
    assert resultado["chamadas"] == 0
    assert "duas pastas são obrigatórias" in resultado["texto"]


def test_durante_o_envio_informa_quantos_arquivos_e_bloqueia_o_botao():
    verificar = (
        ESPERAR
        + CHAMADAS_PARA
        + """
doc.porId["origem-envio"].disparar("change");
doc.porId["btn-enviar-pastas"].disparar("click");
"""
        + ESPERAR
        + """
const botao = doc.porId["btn-enviar-pastas"];
const durante = { texto: doc.porId["status-envio"].textContent, bloqueado: botao.disabled === true };
contexto.__t.resolver({
  status: 200,
  ok: true,
  json: async () => ({
    estado: "previa", execucao_id: "abc", arquivos: [], campi_preservados: [],
    campi_nao_cadastrados: [], ignorados: [], matriculas_orfas: 0, erro_consolidacao: null, navegador: null,
  }),
});
"""
        + ESPERAR
        + """
const enviada = para("/admin/atualizar/envio")[0];
return { durante, depoisBloqueado: botao.disabled === true, anexos: enviada.opcoes.body.anexos };
"""
    )
    resultado = rodar(
        "atualizar.js",
        _preparar(pendente=True, arquivos_ciclos=("ciclos-U1.csv", "ciclos-U2.csv"), arquivos_matriculas=("matriculas-U1.csv",)),
        verificar,
    )
    assert resultado["durante"]["bloqueado"] is True
    assert "3 arquivo(s)" in resultado["durante"]["texto"]
    assert "2 de ciclos e 1 de matrículas" in resultado["durante"]["texto"]
    assert resultado["depoisBloqueado"] is False
    assert resultado["anexos"] == [
        ["ciclos", "ciclos-U1.csv"],
        ["ciclos", "ciclos-U2.csv"],
        ["matriculas", "matriculas-U1.csv"],
    ]


def test_400_mostra_o_arquivo_e_o_motivo_em_portugues():
    respostas = [{"status": 400, "corpo": {"erro": "envio_invalido", "arquivo": "quebrado.csv", "motivo": "colunas_ausentes"}}]
    verificar = (
        ESPERAR
        + """
doc.porId["origem-envio"].disparar("change");
doc.porId["btn-enviar-pastas"].disparar("click");
"""
        + ESPERAR
        + 'return doc.porId["status-envio"].textContent;'
    )
    texto = rodar(
        "atualizar.js",
        _preparar(respostas=respostas, arquivos_ciclos=("quebrado.csv",), arquivos_matriculas=("matriculas-U1.csv",)),
        verificar,
    )
    assert "quebrado.csv" in texto
    assert "colunas esperadas" in texto
    assert "pastas não estão invertidas" in texto
    assert "colunas_ausentes" not in texto
    assert "Nada foi gravado" in texto


@pytest.mark.parametrize(
    "corpo,esperado",
    [
        ({"erro": "previa_pendente"}, "Há uma prévia pendente"),
        ({"erro": "execucao_em_andamento"}, "Já existe uma atualização em andamento"),
    ],
)
def test_409_tem_mensagem_propria(corpo, esperado):
    verificar = (
        ESPERAR
        + """
doc.porId["origem-envio"].disparar("change");
doc.porId["btn-enviar-pastas"].disparar("click");
"""
        + ESPERAR
        + 'return doc.porId["status-envio"].textContent;'
    )
    texto = rodar(
        "atualizar.js",
        _preparar(respostas=[{"status": 409, "corpo": corpo}], arquivos_ciclos=("a.csv",), arquivos_matriculas=("b.csv",)),
        verificar,
    )
    assert esperado in texto


def test_413_tem_mensagem_propria():
    verificar = (
        ESPERAR
        + """
doc.porId["origem-envio"].disparar("change");
doc.porId["btn-enviar-pastas"].disparar("click");
"""
        + ESPERAR
        + 'return doc.porId["status-envio"].textContent;'
    )
    texto = rodar(
        "atualizar.js",
        _preparar(respostas=[{"status": 413, "corpo": {}}], arquivos_ciclos=("a.csv",), arquivos_matriculas=("b.csv",)),
        verificar,
    )
    assert "500 MB" in texto


def test_resultado_por_arquivo_mostra_nome_tipo_e_linhas():
    resposta = {
        "status": 200,
        "corpo": {
            "estado": "previa",
            "execucao_id": "abc",
            "arquivos": [
                {"n": 1, "tipo": "ciclo", "nome": "ciclos-U1.csv", "status": "baixado", "linhas": 3},
                {"n": 2, "tipo": "matricula", "nome": "matriculas-U1.csv", "status": "baixado", "linhas": 4},
            ],
            "campi_preservados": [],
            "campi_nao_cadastrados": ["U9"],
            "ignorados": ["LEIA-ME.txt"],
            "matriculas_orfas": 0,
            "erro_consolidacao": None,
            "navegador": None,
        },
    }
    verificar = (
        ESPERAR
        + """
doc.porId["origem-envio"].disparar("change");
doc.porId["btn-enviar-pastas"].disparar("click");
"""
        + ESPERAR
        + """
const linhas = doc.porId["envio-arquivos"].filhos.map((tr) => tr.filhos.map((td) => td.textContent));
return {
  linhas,
  area: doc.porId["envio-arquivos-area"].hidden,
  ignorados: doc.porId["envio-ignorados"].textContent,
  avisos: doc.porId["envio-avisos"].filhos.map((li) => li.textContent),
  texto: doc.porId["status-envio"].textContent,
};
"""
    )
    resultado = rodar(
        "atualizar.js",
        _preparar(
            estado=_estado_previa(campi_nao_cadastrados=["U9"], arquivos_ignorados=["LEIA-ME.txt"]),
            respostas=[resposta],
            arquivos_ciclos=("ciclos-U1.csv",),
            arquivos_matriculas=("matriculas-U1.csv",),
        ),
        verificar,
    )
    assert resultado["area"] is False
    assert resultado["linhas"] == [
        ["1", "ciclos-U1.csv", "Ciclos", "Lido", "3"],
        ["2", "matriculas-U1.csv", "Matrículas", "Lido", "4"],
    ]
    assert resultado["ignorados"] == "Ignorados (não são .csv): LEIA-ME.txt."
    assert resultado["avisos"] == ["Unidades fora do cadastro de campi, não atualizadas: U9."]
    assert "2 arquivo(s) lido(s)" in resultado["texto"]


def test_com_campi_preservados_o_salvar_nao_e_chamado_sem_a_confirmacao():
    verificar = (
        ESPERAR
        + CHAMADAS_PARA
        + """
const preservacao = doc.porId["envio-preservacao"];
const antes = { visivel: preservacao.hidden === false, texto: doc.porId["envio-preservacao-texto"].textContent, bloqueado: doc.porId["btn-salvar"].disabled === true };
doc.porId["btn-salvar"].disparar("click");
"""
        + ESPERAR
        + """
return {
  antes,
  chamadas: para("/salvar").length,
  status: doc.porId["status-salvar"].textContent,
  checkbox: doc.porId["envio-confirmar-preservacao"].checked,
};
"""
    )
    resultado = rodar("atualizar.js", _preparar(estado=_estado_previa(campi_preservados=["U2", "U3"])), verificar)
    assert resultado["antes"]["visivel"] is True
    assert resultado["antes"]["texto"] == (
        "Estas unidades não vieram no envio e os dados atuais delas serão preservados: U2, U3."
    )
    assert resultado["antes"]["bloqueado"] is True
    assert resultado["chamadas"] == 0
    assert resultado["checkbox"] is False
    assert "Confirme a preservação" in resultado["status"]


def test_com_a_confirmacao_marcada_o_salvar_leva_o_campo_ao_servidor():
    verificar = (
        ESPERAR
        + CHAMADAS_PARA
        + """
const checkbox = doc.porId["envio-confirmar-preservacao"];
checkbox.checked = true;
checkbox.disparar("change");
const liberado = doc.porId["btn-salvar"].disabled === true;
doc.porId["btn-salvar"].disparar("click");
"""
        + ESPERAR
        + """
const enviada = para("/salvar")[0];
return { liberado, corpos: para("/salvar").map((c) => c.opcoes.body), cabecalhos: enviada.opcoes.headers };
"""
    )
    resultado = rodar("atualizar.js", _preparar(estado=_estado_previa(campi_preservados=["U2"])), verificar)
    assert resultado["liberado"] is False
    assert resultado["corpos"] == ['{"confirmar_preservacao":true}']
    assert resultado["cabecalhos"]["Content-Type"] == "application/json"


def test_numa_baixa_o_bloco_de_envio_fica_fora_do_caminho():
    """UPL-08: sem `campi_preservados` do envio, Salvar continua direto."""
    verificar = (
        ESPERAR
        + CHAMADAS_PARA
        + """
doc.porId["btn-salvar"].disparar("click");
"""
        + ESPERAR
        + """
const preservacao = doc.porId["envio-preservacao"];
return {
  chamadas: para("/salvar").length,
  corpos: para("/salvar").map((c) => c.opcoes.body),
  visivel: preservacao.hidden === false,
  bloqueado: doc.porId["btn-salvar"].disabled === true,
};
"""
    )
    resultado = rodar("atualizar.js", _preparar(estado=_estado_previa(origem="baixa")), verificar)
    assert resultado["chamadas"] == 1
    assert resultado["corpos"] == ['{"confirmar_preservacao":false}']
    assert resultado["visivel"] is False
    assert resultado["bloqueado"] is False
