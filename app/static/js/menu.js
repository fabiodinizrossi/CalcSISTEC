/*
 * Complementa o menu do DS (`br-menu`) no que o `core-init.min.js` não faz.
 *
 * Abaixo de 992px o menu é sobreposto: o DS abre e fecha (classe `active`), e aqui se
 * mantém `aria-expanded` do botão do cabeçalho e se devolve o foco a ele ao fechar.
 * A partir de 992px o menu é uma barra lateral fixa (CSS em `style.css`), sem botão
 * hambúrguer, então aqui só o comportamento sobreposto é necessário.
 */
(function () {
  "use strict";

  // Devolve o foco ao botão quando o menu sobreposto acabou de fechar e o foco ficou
  // perdido (no corpo da página ou dentro do menu, agora oculto).
  function deveDevolverFoco(estavaAberto, estaAberto, focoPerdido) {
    return Boolean(estavaAberto) && !estaAberto && Boolean(focoPerdido);
  }

  function valorAriaExpanded(estaAberto) {
    return estaAberto ? "true" : "false";
  }

  if (typeof document !== "undefined") {
    var menu = document.querySelector(".br-menu");
    var botao = document.getElementById("botao-menu");
    if (menu && botao) {
      var sincronizar = function () {
        botao.setAttribute("aria-expanded", valorAriaExpanded(menu.classList.contains("active")));
      };
      window.addEventListener("resize", sincronizar);
      sincronizar();

      if (typeof MutationObserver === "function") {
        var estavaAberto = menu.classList.contains("active");
        new MutationObserver(function () {
          var estaAberto = menu.classList.contains("active");
          var anterior = estavaAberto;
          estavaAberto = estaAberto;
          sincronizar();
          if (!anterior || estaAberto) { return; }
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
      deveDevolverFoco: deveDevolverFoco,
      valorAriaExpanded: valorAriaExpanded,
    };
  }
})();
