/**
 * Service worker da extensão Baixador Sistec (`002-baixador-planilhas-
 * sistec`, T045, D-01, D-02, D-15, D-16).
 *
 * Trata as mensagens de `externally_connectable` vindas da página
 * administrativa do CalcSISTEC (`interfaces/api-extensao-calcsistec.md`
 * §2): ping, abrirLogin, executar, capturar, parar. A cada `execucao_id`/
 * `captura_id` em andamento, faz o polling de `/api/sistec/.../proximo`,
 * delega a baixa em si ao script de conteúdo (`sistec-content.js`, que roda
 * dentro da aba do Sistec e faz os `fetch` de mesma origem) e envia os
 * bytes recebidos ao servidor CalcSISTEC.
 *
 * Nunca lê, guarda ou encaminha senha. A sessão do Sistec é sempre limpa
 * (D-15) antes de abrir o login e ao chegar a qualquer estado terminal.
 */

const VERSAO = "1.0.0";
const INTERVALO_AGUARDAR_MS = 5000;

// Estado em memória do service worker — perdido se o navegador o encerrar
// (comportamento esperado do MV3; a fonte de verdade da execução é o
// servidor CalcSISTEC, D-02, então perder este estado só interrompe o
// polling local, sem corromper nada).
const execucoesAtivas = new Map(); // execucao_id -> { pararSolicitado, tabId }
const capturasAtivas = new Map(); // captura_id -> { tabId }

async function obterBaseSistec() {
  const config = await chrome.storage.local.get("baseSistecDev");
  return config.baseSistecDev || "https://sistec.mec.gov.br";
}

async function limparCookiesDominio(dominio) {
  // `chrome.cookies.getAll({ domain })` já cobre subdomínios (ao contrário de
  // `browsingData.remove`, que não aceita wildcard em `origins`), então dá
  // para limpar só *.acesso.gov.br sem tocar em cookies de outros sites —
  // inclusive o próprio CalcSISTEC, que fica na mesma máquina do navegador.
  const cookies = await chrome.cookies.getAll({ domain: dominio });
  await Promise.all(
    cookies.map((cookie) => {
      const protocolo = cookie.secure ? "https://" : "http://";
      const url = `${protocolo}${cookie.domain.replace(/^\./, "")}${cookie.path}`;
      return chrome.cookies.remove({ url, name: cookie.name }).catch(() => {});
    })
  );
}

async function limparSessaoSistec() {
  // D-15: remove cookies das origens do Sistec e do login gov.br, antes de
  // abrir o login e ao fim de toda captura/execução. Nunca mexe em cookies
  // de outras origens (em especial o próprio CalcSISTEC).
  await chrome.browsingData.remove(
    { origins: ["https://sistec.mec.gov.br"] },
    { cookies: true }
  );
  await limparCookiesDominio("acesso.gov.br");
}

async function fecharAba(tabId) {
  if (!tabId) return;
  try {
    await chrome.tabs.remove(tabId);
  } catch (erro) {
    // Aba já pode ter sido fechada pela pessoa usuária (RN: "aba_fechada").
  }
}

async function chamarApi(apiBase, token, caminho, opcoes) {
  const resposta = await fetch(`${apiBase}${caminho}`, {
    ...opcoes,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(opcoes && opcoes.headers),
    },
  });
  return resposta;
}

async function pedirAoContentScript(tabId, mensagem) {
  return chrome.tabs.sendMessage(tabId, mensagem);
}

async function executarPar(apiBase, token, execucaoId, tabId, par) {
  let resultadoDownload;
  try {
    resultadoDownload = await pedirAoContentScript(tabId, {
      tipo: "baixarPar",
      par,
    });
  } catch (erro) {
    resultadoDownload = { ok: false, motivo: "aba_fechada" };
  }

  if (!resultadoDownload || !resultadoDownload.ok) {
    const motivo = (resultadoDownload && resultadoDownload.motivo) || "erro_http";
    await chamarApi(apiBase, token, `/api/sistec/execucoes/${execucaoId}/pares/${par.n}/falha`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ motivo }),
    });
    return;
  }

  const bytes = new Uint8Array(resultadoDownload.bytes);
  await chamarApi(apiBase, token, `/api/sistec/execucoes/${execucaoId}/pares/${par.n}`, {
    method: "PUT",
    headers: { "Content-Type": "application/octet-stream" },
    body: bytes,
  });
}

async function loopExecucao(execucaoId, token, apiBase) {
  const estado = execucoesAtivas.get(execucaoId);
  if (!estado) return;

  while (!estado.pararSolicitado) {
    let resposta;
    try {
      resposta = await chamarApi(apiBase, token, `/api/sistec/execucoes/${execucaoId}/proximo`, {
        method: "POST",
      });
    } catch (erro) {
      await new Promise((resolve) => setTimeout(resolve, INTERVALO_AGUARDAR_MS));
      continue;
    }

    if (!resposta.ok) {
      await new Promise((resolve) => setTimeout(resolve, INTERVALO_AGUARDAR_MS));
      continue;
    }

    const corpo = await resposta.json();

    if (corpo.acao === "encerrar") {
      break;
    }
    if (corpo.acao === "aguardar") {
      await new Promise((resolve) => setTimeout(resolve, INTERVALO_AGUARDAR_MS));
      continue;
    }
    if (corpo.acao === "baixar" && estado.tabId) {
      await executarPar(apiBase, token, execucaoId, estado.tabId, corpo.par);
    }
  }

  await limparSessaoSistec();
  await fecharAba(estado.tabId);
  execucoesAtivas.delete(execucaoId);
}

async function navegarEAguardarCarregar(tabId, url) {
  return new Promise((resolve, reject) => {
    const ouvinte = (idAtualizada, mudanca) => {
      if (idAtualizada === tabId && mudanca.status === "complete") {
        chrome.tabs.onUpdated.removeListener(ouvinte);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(ouvinte);
    chrome.tabs.update(tabId, { url }).catch((erro) => {
      chrome.tabs.onUpdated.removeListener(ouvinte);
      reject(erro);
    });
  });
}

async function iniciarCaptura(capturaId, token, apiBase, tabId) {
  // §2.1 (interface, 🟡): a página de seleção de perfil é um combobox
  // renderizado por JS (MooTools), não um `<select>` no HTML estático —
  // o script de conteúdo precisa estar de fato carregado nessa página para
  // ler o DOM já renderizado (`document`), não um `fetch` do HTML cru.
  let leitura;
  try {
    const baseSistec = await obterBaseSistec();
    await navegarEAguardarCarregar(tabId, `${baseSistec}/index/selecionarinstituicao/alterar/perfil`);
    leitura = await pedirAoContentScript(tabId, { tipo: "lerPerfis" });
  } catch (erro) {
    leitura = { ok: false, motivo: "aba_fechada" };
  }

  if (!leitura || !leitura.ok || !leitura.perfis || leitura.perfis.length === 0) {
    const motivo = (leitura && leitura.motivo) || "nenhum_perfil";
    await chamarApi(apiBase, token, `/api/sistec/capturas/${capturaId}/falha`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ motivo }),
    });
  } else {
    await chamarApi(apiBase, token, `/api/sistec/capturas/${capturaId}/perfis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ perfis: leitura.perfis }),
    });
  }

  await limparSessaoSistec();
  await fecharAba(tabId);
  capturasAtivas.delete(capturaId);
}

chrome.runtime.onMessageExternal.addListener((mensagem, remetente, enviarResposta) => {
  (async () => {
    if (mensagem.tipo === "ping") {
      enviarResposta({ ok: true, versao: VERSAO });
      return;
    }

    if (mensagem.tipo === "abrirLogin") {
      await limparSessaoSistec();
      const baseSistec = await obterBaseSistec();
      const aba = await chrome.tabs.create({ url: baseSistec });
      enviarResposta({ ok: true, tabId: aba.id });
      return;
    }

    if (mensagem.tipo === "executar") {
      const { execucao_id: execucaoId, token, api_base: apiBase, tab_id: tabId } = mensagem;
      execucoesAtivas.set(execucaoId, { pararSolicitado: false, tabId });
      enviarResposta({ ok: true });
      loopExecucao(execucaoId, token, apiBase);
      return;
    }

    if (mensagem.tipo === "capturar") {
      const { captura_id: capturaId, token, api_base: apiBase, tab_id: tabId } = mensagem;
      capturasAtivas.set(capturaId, { tabId });
      enviarResposta({ ok: true });
      iniciarCaptura(capturaId, token, apiBase, tabId);
      return;
    }

    if (mensagem.tipo === "parar") {
      const estado = execucoesAtivas.get(mensagem.execucao_id);
      if (estado) {
        estado.pararSolicitado = true;
      }
      await limparSessaoSistec();
      if (estado) {
        await fecharAba(estado.tabId);
      }
      enviarResposta({ ok: true });
      return;
    }

    enviarResposta({ ok: false, erro: "mensagem_desconhecida" });
  })();

  return true; // resposta assíncrona (chrome.runtime.onMessageExternal).
});
