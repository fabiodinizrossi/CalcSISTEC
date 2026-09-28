/*
 * Botão de tema claro e escuro.
 *
 * O script inline de `shell/_head.html` já definiu `data-tema` em <html> antes da
 * primeira pintura. Aqui ficam o clique do botão (troca o tema, atualiza
 * `aria-pressed` e o rótulo, guarda a escolha) e o acompanhamento da preferência
 * do sistema enquanto não houver escolha guardada.
 */
(function () {
  "use strict";

  var CHAVE = "calcsistec-tema";

  function resolverTema(salvo, sistemaEscuro) {
    if (salvo === "claro" || salvo === "escuro") { return salvo; }
    return sistemaEscuro ? "escuro" : "claro";
  }

  function alternarTema(atual) {
    return atual === "escuro" ? "claro" : "escuro";
  }

  function rotuloDoBotao(tema) {
    return tema === "escuro" ? "Tema claro" : "Tema escuro";
  }

  function lerTemaSalvo(storage) {
    try {
      var salvo = storage.getItem(CHAVE);
      return salvo === "claro" || salvo === "escuro" ? salvo : null;
    } catch (erro) {
      return null;
    }
  }

  function gravarTema(tema, storage) {
    try {
      storage.setItem(CHAVE, tema);
      return true;
    } catch (erro) {
      return false;
    }
  }

  function aplicarTema(tema) {
    document.documentElement.setAttribute("data-tema", tema);
    var botao = document.getElementById("botao-tema");
    if (!botao) { return; }
    botao.setAttribute("aria-pressed", tema === "escuro" ? "true" : "false");
    var rotulo = botao.querySelector("span");
    if (rotulo) { rotulo.textContent = rotuloDoBotao(tema); }
  }

  if (typeof document !== "undefined") {
    var consulta = typeof matchMedia === "function" ? matchMedia("(prefers-color-scheme: dark)") : null;
    var armazenamento = null;
    try { armazenamento = window.localStorage; } catch (erro) { armazenamento = null; }

    aplicarTema(document.documentElement.getAttribute("data-tema") === "escuro" ? "escuro" : "claro");

    var botao = document.getElementById("botao-tema");
    if (botao) {
      botao.addEventListener("click", function () {
        var novo = alternarTema(document.documentElement.getAttribute("data-tema"));
        aplicarTema(novo);
        if (armazenamento) { gravarTema(novo, armazenamento); }
      });
    }

    if (consulta && consulta.addEventListener) {
      consulta.addEventListener("change", function () {
        if (armazenamento && lerTemaSalvo(armazenamento)) { return; }
        aplicarTema(resolverTema(null, consulta.matches));
      });
    }
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      resolverTema: resolverTema,
      alternarTema: alternarTema,
      rotuloDoBotao: rotuloDoBotao,
      lerTemaSalvo: lerTemaSalvo,
      gravarTema: gravarTema,
    };
  }
})();
