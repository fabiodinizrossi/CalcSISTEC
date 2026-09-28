/** Expansao progressiva da matriz hierarquica de matriculas. */
(function (raiz, fabrica) {
  var api = fabrica();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (raiz && raiz.document) api.iniciar(raiz.document);
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  function descendentes(tabela, id) {
    var resultado = [];
    var fila = [id];
    while (fila.length) {
      var pai = fila.shift();
      Array.from(tabela.querySelectorAll('tbody tr[data-parent-id="' + pai + '"]')).forEach(function (linha) {
        resultado.push(linha);
        fila.push(linha.dataset.groupId);
      });
    }
    return resultado;
  }

  function alternar(botao) {
    var linha = botao.closest("tr[data-group-id]");
    var tabela = linha && linha.closest("table.tabela-hierarquica");
    if (!tabela) return;
    var expandido = botao.getAttribute("aria-expanded") === "true";
    botao.setAttribute("aria-expanded", String(!expandido));
    botao.setAttribute("title", expandido ? "Expandir grupo" : "Recolher grupo");
    var rotulo = linha.querySelector(".matriz-rotulo span:last-child");
    botao.setAttribute("aria-label", (expandido ? "Expandir " : "Recolher ") + (rotulo ? rotulo.textContent : "grupo"));
    descendentes(tabela, linha.dataset.groupId).forEach(function (filha) {
      filha.hidden = expandido;
      if (!expandido) {
        var ancestral = filha.dataset.parentId;
        while (ancestral && ancestral !== linha.dataset.groupId) {
          var pai = tabela.querySelector('tbody tr[data-group-id="' + ancestral + '"]');
          var expansor = pai && pai.querySelector(".matriz-expansor");
          if (expansor && expansor.getAttribute("aria-expanded") === "false") filha.hidden = true;
          ancestral = pai && pai.dataset.parentId;
        }
      }
    });
  }

  function iniciar(documento) {
    documento.addEventListener("click", function (evento) {
      var botao = evento.target.closest && evento.target.closest(".matriz-expansor");
      if (botao) alternar(botao);
    });
  }

  return { alternar: alternar, descendentes: descendentes, iniciar: iniciar };
});
