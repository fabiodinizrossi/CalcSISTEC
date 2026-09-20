/*
 * Complementa o menu do DS (`br-menu`) no que o `core-init.min.js` não faz: manter
 * `aria-expanded` do botão do cabeçalho em dia e devolver o foco a ele quando o menu
 * fecha (Esc ou botão de fechar). Abrir por Enter, Espaço ou clique, e levar o foco
 * ao primeiro item, o DS já faz.
 */
(function () {
  "use strict";

  // Devolve o foco ao botão quando o menu acabou de fechar e o foco ficou perdido
  // (no corpo da página ou dentro do menu, agora oculto).
  function deveDevolverFoco(estavaAberto, estaAberto, focoPerdido) {
    return Boolean(estavaAberto) && !estaAberto && Boolean(focoPerdido);
  }

  function valorAriaExpanded(estaAberto) {
    return estaAberto ? "true" : "false";
  }

  if (typeof document !== "undefined") {
    var menu = document.querySelector(".br-menu");
    var botao = document.getElementById("botao-menu");
    if (menu && botao && typeof MutationObserver === "function") {
      var estavaAberto = menu.classList.contains("active");
      new MutationObserver(function () {
        var estaAberto = menu.classList.contains("active");
        botao.setAttribute("aria-expanded", valorAriaExpanded(estaAberto));
        var anterior = estavaAberto;
        estavaAberto = estaAberto;
        if (!anterior || estaAberto) { return; }
        setTimeout(function () {
          var ativo = document.activeElement;
          var perdido = ativo === document.body || ativo === null || menu.contains(ativo);
          if (deveDevolverFoco(anterior, estaAberto, perdido)) { botao.focus(); }
        }, 0);
      }).observe(menu, { attributes: true, attributeFilter: ["class"] });
    }
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { deveDevolverFoco: deveDevolverFoco, valorAriaExpanded: valorAriaExpanded };
  }
})();
