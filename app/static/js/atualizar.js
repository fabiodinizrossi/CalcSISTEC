/**
 * Tela "Atualizar dados" (`002-baixador-planilhas-sistec`, D-12, RF-08).
 *
 * Botão único "Atualizar do Sistec": o servidor abre o Sistec no navegador de
 * sempre da pessoa (`app/sistec/navegador.py`), ela faz o login gov.br e
 * confirma aqui; o servidor então manda abrir as URLs de cada campus e vigia a
 * pasta onde o navegador salva. É a mecânica do script R.
 *
 * A lista de campi e o identificador de perfil de cada um são cadastrados em
 * Configurações; a atualização se recusa a começar se algum estiver inválido.
 *
 * Esta tela só dispara as ações e acompanha o estado por polling de
 * `GET /admin/atualizar/execucao` a cada 2 s — nunca recebe bytes de planilha.
 * Quem usa é leigo: o passo a passo e a barra de progresso existem para nada
 * acontecer em silêncio.
 */
(function () {
  const INTERVALO_POLL_MS = 2000;
  const ESTADOS_TERMINAIS = new Set([
    "salva", "descartada", "cancelada", "falhou_consolidacao", "encerrada_pausa", "interrompida", "sem_resultado", "falhou",
  ]);
  const ROTULO_TIPO = { ciclo: "Ciclos", matricula: "Matrículas" };
  const ROTULO_STATUS = {
    pendente: "Na fila",
    em_andamento: "Baixando…",
    baixado: "Baixado",
    falhou: "Falhou",
    cancelado: "Cancelado",
  };
  const ROTULO_MOTIVO = {
    tempo_esgotado: "tempo esgotado",
    erro_http: "erro de comunicação com o Sistec",
    resposta_invalida: "resposta inesperada do Sistec",
    sessao_expirada: "sessão expirada",
    aba_fechada: "aba fechada",
    colunas_ausentes: "planilha sem as colunas esperadas",
    leitura_csv: "planilha ilegível",
  };
  const ROTULO_ESTADO = {
    aguardando_login: "aguardando login",
    baixando: "baixando",
    pausada: "pausada",
    consolidando: "consolidando",
    previa: "prévia pronta",
    salva: "salva na versão interna",
    descartada: "descartada",
    cancelada: "cancelada",
    falhou_consolidacao: "falha na consolidação",
  };

  const $ = (id) => document.getElementById(id);
  const elStatus = $("status-navegador");
  const elBarraArea = $("barra-area");
  const elBarra = $("barra-progresso");
  const elBarraRotulo = $("barra-rotulo");
  const elPassos = $("passos-navegador");
  const elAvisos = $("avisos-navegador");
  const elProgresso = $("atualizar-progresso");
  const elProgressoResumo = $("progresso-resumo");
  const elProgressoPares = $("progresso-pares");
  const elPrevia = $("atualizar-previa");
  const elPreviaResumo = $("previa-resumo");
  const elPreviaCabecalho = $("previa-cabecalho");
  const elPreviaLinhas = $("previa-linhas");
  const elStatusSalvar = $("status-salvar");
  const elStatusPublicacao = $("status-publicacao");

  const btnAtualizar = $("btn-atualizar-sistec");
  const btnLoginFeito = $("btn-login-feito");
  const btnCancelar = $("btn-cancelar");
  const btnSalvar = $("btn-salvar");
  const btnDescartar = $("btn-descartar");
  const btnPublicar = $("btn-publicar");
  const btnDesfazer = $("btn-desfazer");

  let estadoAtual = null;
  let passosMostrados = 0;

  function postar(caminho) {
    return fetch(caminho, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  }

  function celula(linha, texto) {
    const td = document.createElement("td");
    td.textContent = texto === null || texto === undefined ? "" : String(texto);
    linha.appendChild(td);
  }

  function renderizarPassos(passos) {
    if (passos.length < passosMostrados) {
      elPassos.innerHTML = "";
      passosMostrados = 0;
    }
    for (let i = passosMostrados; i < passos.length; i += 1) {
      const li = document.createElement("li");
      li.textContent = `${passos[i].hora} — ${passos[i].texto}`;
      if (passos[i].tipo === "erro") li.style.color = "#b30000";
      if (passos[i].tipo === "aviso") li.style.color = "#8a6d00";
      elPassos.appendChild(li);
    }
    passosMostrados = passos.length;
    if (passos.length > 0) elPassos.lastChild.scrollIntoView({ block: "nearest" });
  }

  function renderizarBarra(navegador, estado) {
    const progresso = (navegador && navegador.progresso) || { feitos: 0, total: 0 };
    const ativo = Boolean(navegador && navegador.ativa);
    if (!progresso.total) {
      // Sem fila ainda: barra indeterminada enquanto algo estiver rodando.
      elBarraArea.hidden = !ativo;
      elBarra.removeAttribute("value");
      elBarraRotulo.textContent = "Trabalhando…";
      return;
    }
    elBarraArea.hidden = !ativo && estado !== "previa";
    elBarra.max = progresso.total;
    elBarra.value = progresso.feitos;
    const porcento = Math.round((progresso.feitos / progresso.total) * 100);
    elBarraRotulo.textContent = `${progresso.feitos} de ${progresso.total} planilhas (${porcento}%)`;
  }

  function renderizarNavegador(navegador, estado) {
    let mensagem = navegador ? navegador.mensagem : "";
    if (!(navegador && navegador.ativa) && estado === "previa" && !mensagem) {
      mensagem = "Há uma prévia pendente: salve ou descarte antes de uma nova atualização.";
    }
    elStatus.textContent = mensagem || "";
    renderizarBarra(navegador, estado);
    renderizarPassos((navegador && navegador.passos) || []);

    const avisos = (navegador && navegador.avisos) || [];
    elAvisos.innerHTML = "";
    avisos.forEach((aviso) => {
      const li = document.createElement("li");
      li.textContent = aviso;
      elAvisos.appendChild(li);
    });
    elAvisos.hidden = avisos.length === 0;
  }

  function renderizarPares(pares) {
    elProgressoPares.innerHTML = "";
    pares.forEach((par) => {
      const linha = document.createElement("tr");
      let status = ROTULO_STATUS[par.status] || par.status;
      if (par.status === "falhou" && par.motivo) status += ` (${ROTULO_MOTIVO[par.motivo] || par.motivo})`;
      celula(linha, par.n);
      celula(linha, ROTULO_TIPO[par.tipo] || par.tipo);
      celula(linha, par.nome_perfil);
      celula(linha, status);
      celula(linha, par.linhas);
      elProgressoPares.appendChild(linha);
    });
  }

  function renderizarPrevia(previa, estado) {
    if (!previa || estado !== "previa") {
      elPrevia.hidden = true;
      return;
    }
    elPrevia.hidden = false;
    elPreviaResumo.textContent =
      `${previa.ciclos} ciclo(s) e ${previa.matriculas} matrícula(s) consolidados.` +
      (previa.campi_falhos.length
        ? ` Unidades com falha (os dados anteriores delas são mantidos): ${previa.campi_falhos.join(", ")}.`
        : "");

    const amostra = previa.amostra || [];
    elPreviaCabecalho.innerHTML = "";
    elPreviaLinhas.innerHTML = "";
    if (amostra.length === 0) return;

    const colunas = Object.keys(amostra[0]);
    const linhaCabecalho = document.createElement("tr");
    colunas.forEach((coluna) => {
      const th = document.createElement("th");
      th.textContent = coluna;
      linhaCabecalho.appendChild(th);
    });
    elPreviaCabecalho.appendChild(linhaCabecalho);
    amostra.forEach((registro) => {
      const linha = document.createElement("tr");
      colunas.forEach((coluna) => celula(linha, registro[coluna]));
      elPreviaLinhas.appendChild(linha);
    });
  }

  function atualizarBotoes(corpo) {
    const navegador = corpo.navegador;
    const navegadorAtivo = Boolean(navegador && navegador.ativa);
    const execucaoAberta = Boolean(corpo.estado) && !ESTADOS_TERMINAIS.has(corpo.estado);
    btnAtualizar.hidden = navegadorAtivo || corpo.estado === "previa";
    btnLoginFeito.hidden = !(navegador && navegador.fase === "aguardando_login");
    btnCancelar.hidden = !(navegadorAtivo || (execucaoAberta && corpo.estado !== "previa"));
  }

  async function poll() {
    try {
      const resposta = await fetch("/admin/atualizar/execucao");
      const corpo = await resposta.json();
      estadoAtual = corpo;

      renderizarNavegador(corpo.navegador, corpo.estado);
      atualizarBotoes(corpo);

      if (!corpo.estado) {
        elProgresso.hidden = true;
        renderizarPrevia(null, null);
        return;
      }
      elProgresso.hidden = false;
      elProgressoResumo.textContent =
        `Situação: ${ROTULO_ESTADO[corpo.estado] || corpo.estado} ` +
        `(${corpo.progresso.concluidos} de ${corpo.progresso.total} planilhas)` +
        (corpo.erro_consolidacao ? ` — ${corpo.erro_consolidacao}` : "");
      renderizarPares(corpo.pares);
      renderizarPrevia(corpo.previa, corpo.estado);
    } catch (erro) {
      // Falha de rede pontual no polling não interrompe o ciclo — tenta de novo.
    }
  }

  btnAtualizar.addEventListener("click", async () => {
    btnAtualizar.disabled = true;
    elStatusSalvar.textContent = "";
    try {
      const resposta = await postar("/admin/atualizar/sistec");
      if (resposta.status === 409) {
        const corpo = await resposta.json();
        elStatus.textContent =
          corpo.erro === "previa_pendente"
            ? "Há uma prévia pendente: salve ou descarte antes de uma nova atualização."
            : "Já existe uma atualização em andamento. Use Cancelar se ela estiver presa.";
        btnCancelar.hidden = corpo.erro === "previa_pendente";
        return;
      }
      elStatus.textContent = resposta.ok ? "Abrindo o Sistec no seu navegador…" : "Não foi possível iniciar a atualização.";
      await poll();
    } finally {
      btnAtualizar.disabled = false;
    }
  });

  btnLoginFeito.addEventListener("click", async () => {
    await postar("/admin/atualizar/sistec/login-feito");
    await poll();
  });

  btnCancelar.addEventListener("click", async () => {
    if (!confirm(btnCancelar.dataset.confirm)) return;
    await postar("/admin/atualizar/sistec/cancelar");
    await poll();
  });

  btnSalvar.addEventListener("click", async () => {
    if (!estadoAtual || !estadoAtual.execucao_id) return;
    btnSalvar.disabled = true;
    elStatusSalvar.textContent = "Salvando…";
    try {
      const resposta = await postar(`/admin/atualizar/execucoes/${estadoAtual.execucao_id}/salvar`);
      if (resposta.ok) {
        const resumo = await resposta.json();
        elStatusSalvar.textContent =
          `Salvo na versão interna: ${resumo.ciclos} ciclo(s) e ${resumo.matriculas} matrícula(s). ` +
          "Clique em Publicar para levar ao painel público.";
      } else {
        elStatusSalvar.textContent = "Não foi possível salvar.";
      }
      await poll();
    } finally {
      btnSalvar.disabled = false;
    }
  });

  btnDescartar.addEventListener("click", async () => {
    if (!estadoAtual || !estadoAtual.execucao_id) return;
    if (!confirm(btnDescartar.dataset.confirm)) return;
    await postar(`/admin/atualizar/execucoes/${estadoAtual.execucao_id}/descartar`);
    elStatusSalvar.textContent = "Prévia descartada.";
    await poll();
  });

  btnPublicar.addEventListener("click", async () => {
    if (!confirm(btnPublicar.dataset.confirm)) return;
    const resposta = await postar("/admin/atualizar/publicar");
    elStatusPublicacao.textContent = resposta.ok ? "Publicado." : "Não foi possível publicar.";
  });

  btnDesfazer.addEventListener("click", async () => {
    if (!confirm(btnDesfazer.dataset.confirm)) return;
    const resposta = await postar("/admin/atualizar/desfazer");
    elStatusPublicacao.textContent = resposta.ok ? "Publicação desfeita." : "Não havia o que desfazer.";
  });

  setInterval(poll, INTERVALO_POLL_MS);
  poll();
})();
