/**
 * Script de conteúdo injetado em `https://sistec.mec.gov.br/*` (e no Sistec
 * simulado, `http://127.0.0.1:8051/*`, para os testes de `onboarding.md`)
 * (`002-baixador-planilhas-sistec`, T046, D-01, D-03).
 *
 * Faz `fetch` de mesma origem (troca de perfil e exportação), sempre com a
 * sessão que o navegador já tem depois do login humano — nunca lê, envia ou
 * guarda senha (RN-01). Os bytes da exportação só existem aqui até serem
 * repassados ao service worker (`background.js`), que os encaminha ao
 * servidor CalcSISTEC; a referência é liberada logo depois (D-03).
 *
 * `interfaces/sistec-http.md` §1-§3, corrigido pela F0 (`f0-resultado.md`):
 * troca de perfil é `POST` sem query string (achado 1); a página de perfis
 * é um combobox customizado, sem `<select>` (achado 3).
 */

const REGEX_ITEM_PERFIL = /^(.*?DA UNIDADE DE ENSINO)\s*-\s*([A-Za-z0-9.]+)\s*-\s*(.*?)\s*-\s*(CAMPUS\s+.*)$/i;
const REGEX_TEXTO_ITEM_PERFIL = /DA UNIDADE DE ENSINO/i;
const REGEX_PREFIXO_CAMPUS = /^CAMPUS\s+/i;

// Preposições que o português mantém em minúsculo num nome próprio (exceto
// como primeira palavra) — ex.: "Júlio de Castilhos", "São Vicente do Sul".
const PREPOSICOES_MINUSCULAS = new Set(["de", "do", "da", "dos", "das", "e"]);

function normalizarTexto(texto) {
  return (texto || "").replace(/\s+/g, " ").trim();
}

function paraNomeProprio(textoMaiusculo) {
  return normalizarTexto(textoMaiusculo)
    .toLowerCase()
    .split(" ")
    .map((palavra, indice) => {
      if (indice > 0 && PREPOSICOES_MINUSCULAS.has(palavra)) return palavra;
      return palavra.charAt(0).toUpperCase() + palavra.slice(1);
    })
    .join(" ");
}

function extrairPerfilDoTexto(texto) {
  const limpo = normalizarTexto(texto);
  const m = limpo.match(REGEX_ITEM_PERFIL);
  if (!m) {
    return { nome_perfil: limpo, co_unidade: null, cidade: null, nome_unidade: null };
  }
  const [, papel, coUnidade, instituicao, campus] = m;
  // RF pedido pela PI: pré-preenche cidade/nome da unidade a partir do
  // próprio texto do perfil ("CAMPUS <nome>"), já que no IFFar o nome do
  // campus é sempre o nome da cidade onde fica. Continua editável em
  // Configurações para o caso de algum campus fugir dessa regra.
  const nomeCampus = paraNomeProprio(campus.replace(REGEX_PREFIXO_CAMPUS, ""));
  return {
    nome_perfil: normalizarTexto(`${papel} - ${instituicao} - ${campus}`),
    co_unidade: coUnidade,
    cidade: nomeCampus || null,
    nome_unidade: nomeCampus ? `Campus ${nomeCampus}` : null,
  };
}

function localizarItensDoCombobox() {
  // §2.1: sem `<select>`, os itens do combobox MooTools ficam em elementos
  // de lista/opção customizados. Tenta primeiro os padrões mais prováveis
  // de bibliotecas de combobox renderizadas sobre um `<select>` oculto.
  const candidatos = [
    ...document.querySelectorAll("[data-choice] .choices__item"),
    ...document.querySelectorAll(".choices__list--dropdown .choices__item"),
    ...document.querySelectorAll("select[name] option"),
    ...document.querySelectorAll("[role='option']"),
    ...document.querySelectorAll("li.option"),
  ];
  const comTexto = candidatos.filter((el) => normalizarTexto(el.textContent).length > 0);
  if (comTexto.length > 0) {
    return comTexto;
  }

  // Confirmado ao vivo contra o Sistec real: os itens são `<div>` sem
  // nenhuma classe, um por perfil — nenhum seletor CSS acima bate. Sem
  // marcador estável no DOM, identifica pelo próprio texto: elemento-folha
  // (sem filhos) cujo conteúdo bate com o padrão fixo do rótulo do perfil.
  return Array.prototype.filter.call(document.querySelectorAll("div, li, span, a"), (el) => {
    return (
      el.children.length === 0 &&
      REGEX_TEXTO_ITEM_PERFIL.test(el.textContent) &&
      normalizarTexto(el.textContent).length > 0
    );
  });
}

async function aguardarItensDoCombobox({ intervaloMs = 300, tempoMaximoMs = 8000 } = {}) {
  // O combobox de perfis é renderizado por JS (MooTools/Choices.js) depois
  // do evento de carregamento da página (achado 3 da F0) — ao contrário do
  // Sistec simulado, que já entrega os itens prontos no HTML inicial. Sem
  // essa espera, a primeira leitura roda antes do combobox existir no DOM.
  const inicio = Date.now();
  let itens = localizarItensDoCombobox();
  while (itens.length === 0 && Date.now() - inicio < tempoMaximoMs) {
    await new Promise((resolve) => setTimeout(resolve, intervaloMs));
    itens = localizarItensDoCombobox();
  }
  return itens;
}

async function lerPerfis() {
  const itens = await aguardarItensDoCombobox();
  if (itens.length === 0) {
    return { ok: false, motivo: "nenhum_perfil" };
  }

  const perfis = itens.map((el, indice) => {
    const {
      nome_perfil: nomePerfil,
      co_unidade: coUnidade,
      cidade,
      nome_unidade: nomeUnidade,
    } = extrairPerfilDoTexto(el.textContent);
    const idPerfil = el.getAttribute("data-value") || el.getAttribute("value") || String(indice);
    return {
      id_perfil: idPerfil,
      nome_perfil: nomePerfil,
      co_unidade: coUnidade,
      cidade,
      nome_unidade: nomeUnidade,
    };
  });

  return { ok: true, perfis };
}

function pareceSessaoInvalida(resposta, primeirosBytes) {
  // §3 da interface, calibrado em 2026-09-15 (E002, primeira execução real):
  // o `Content-Type` sozinho dava falso positivo — a exportação real do
  // Sistec não garante vir com `Content-Type` de CSV, então tratá-lo como
  // sinal de sessão expirada pausava a baixa mesmo com sessão válida logo
  // após o login. O sniff dos bytes reais do corpo, abaixo, já cobre o caso
  // genuíno de sessão expirada (a página HTML de login do gov.br).
  if (resposta.redirected) {
    try {
      const host = new URL(resposta.url).hostname;
      if (host.endsWith("acesso.gov.br")) return true;
    } catch (erro) {
      // URL inválida não deveria acontecer; segue para as outras checagens.
    }
  }
  if (resposta.status === 401 || resposta.status === 403) return true;

  if (primeirosBytes) {
    const inicio = new TextDecoder("latin1").decode(primeirosBytes.slice(0, 15)).trim().toLowerCase();
    if (inicio.startsWith("<!doctype") || inicio.startsWith("<html")) return true;
  }
  return false;
}

async function trocarPerfil(par) {
  const corpo = new URLSearchParams(par.corpo_troca_perfil);
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), 60_000);
  try {
    await fetch(par.url_troca_perfil, {
      method: "POST",
      body: corpo,
      credentials: "same-origin",
      redirect: "follow",
      signal: controlador.signal,
    });
  } finally {
    clearTimeout(temporizador);
  }
}

async function exportar(par) {
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), (par.tempo_max_s || 900) * 1000);
  try {
    const resposta = await fetch(par.url_exportacao, {
      credentials: "same-origin",
      redirect: "follow",
      signal: controlador.signal,
    });

    const buffer = await resposta.arrayBuffer();
    const amostra = new Uint8Array(buffer.slice(0, 32));

    if (pareceSessaoInvalida(resposta, amostra)) {
      return { ok: false, motivo: "sessao_expirada" };
    }
    if (!resposta.ok) {
      return { ok: false, motivo: "erro_http" };
    }
    if (buffer.byteLength === 0) {
      return { ok: false, motivo: "resposta_invalida" };
    }
    return { ok: true, bytes: buffer };
  } catch (erro) {
    if (erro && erro.name === "AbortError") {
      return { ok: false, motivo: "tempo_esgotado" };
    }
    return { ok: false, motivo: "erro_http" };
  } finally {
    clearTimeout(temporizador);
  }
}

async function baixarPar(par) {
  try {
    await trocarPerfil(par);
  } catch (erro) {
    if (erro && erro.name === "AbortError") {
      return { ok: false, motivo: "tempo_esgotado" };
    }
    return { ok: false, motivo: "erro_http" };
  }

  await new Promise((resolve) => setTimeout(resolve, (par.espera_minima_s || 3) * 1000));

  return exportar(par);
}

chrome.runtime.onMessage.addListener((mensagem, remetente, enviarResposta) => {
  if (mensagem.tipo === "lerPerfis") {
    lerPerfis().then(enviarResposta);
    return true;
  }
  if (mensagem.tipo === "baixarPar") {
    baixarPar(mensagem.par).then(enviarResposta);
    return true;
  }
  return false;
});
