/*
 * Complementa o menu do DS (`br-menu`) no que o `core-init.min.js` não faz.
 *
 * Abaixo de 992px o menu é sobreposto: o DS abre e fecha (classe `active`), e aqui se
 * mantém `aria-expanded` do botão do cabeçalho e se devolve o foco a ele ao fechar.
 * A partir de 992px o menu é persistente e começa aberto; o botão do cabeçalho o
 * recolhe (classe `menu-recolhido`) e o mostra de novo. Abrir por Enter, Espaço ou
 * clique e levar o foco ao primeiro item, o DS já faz.
 */
(function () {
  "use strict";

  var LARGURA_PERSISTENTE = 992;

  function menuPersistente(largura) {
    return largura >= LARGURA_PERSISTENTE;
  }

  // Devolve o foco ao botão quando o menu sobreposto acabou de fechar e o foco ficou
  // perdido (no corpo da página ou dentro do menu, agora oculto).
  function deveDevolverFoco(estavaAberto, estaAberto, focoPerdido) {
    return Boolean(estavaAberto) && !estaAberto && Boolean(focoPerdido);
  }

  function valorAriaExpanded(estaAberto) {
    return estaAberto ? "true" : "false";
  }

  // O menu está expandido? Persistente: quando não foi recolhido. Sobreposto: quando o DS o abriu.
  function menuExpandido(largura, ativoNoDS, recolhido) {
    return menuPersistente(largura) ? !recolhido : Boolean(ativoNoDS);
  }

  if (typeof document !== "undefined") {
    var menu = document.querySelector(".br-menu");
    var botao = document.getElementById("botao-menu");
    if (menu && botao) {
      var largura = function () { return window.innerWidth; };
      var sincronizar = function () {
        botao.setAttribute(
          "aria-expanded",
          valorAriaExpanded(menuExpandido(largura(), menu.classList.contains("active"), menu.classList.contains("menu-recolhido")))
        );
      };

      var alternarRecolhido = function () {
        if (!menuPersistente(largura())) { return; }
        menu.classList.toggle("menu-recolhido");
        sincronizar();
      };
      botao.addEventListener("click", alternarRecolhido);
      botao.addEventListener("keydown", function (evento) {
        if (evento.code === "Enter" || evento.code === "Space") { alternarRecolhido(); }
      });
      window.addEventListener("resize", sincronizar);
      sincronizar();

      if (typeof MutationObserver === "function") {
        var estavaAberto = menu.classList.contains("active");
        new MutationObserver(function () {
          var estaAberto = menu.classList.contains("active");
          var anterior = estavaAberto;
          estavaAberto = estaAberto;
          sincronizar();
          if (menuPersistente(largura()) || !anterior || estaAberto) { return; }
          setTimeout(function () {
            var ativo = document.activeElement;
            var perdido = ativo === document.body || ativo === null || menu.contains(ativo);
            if (deveDevolverFoco(anterior, estaAberto, perdido)) { botao.focus(); }
          }, 0);
        }).observe(menu, { attributes: true, attributeFilter: ["class"] });
      }
    }
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      menuPersistente: menuPersistente,
      menuExpandido: menuExpandido,
      deveDevolverFoco: deveDevolverFoco,
      valorAriaExpanded: valorAriaExpanded,
    };
  }
})();
