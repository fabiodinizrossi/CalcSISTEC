// Alterna o menu de navegação recolhido abaixo do breakpoint médio
// (`001-govbr-design-system`, T017). Vanilla JS puro — Dash carrega
// qualquer `.js` de `app/assets/` automaticamente, sem build step.
(function () {
  function attach() {
    var toggle = document.getElementById("nav-toggle");
    var menu = document.getElementById("nav-menu");
    if (!toggle || !menu || toggle.dataset.bound) {
      return;
    }
    toggle.dataset.bound = "true";
    toggle.addEventListener("click", function () {
      var aberto = menu.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", aberto ? "true" : "false");
    });
  }

  document.addEventListener("DOMContentLoaded", attach);
  // Dash re-renderiza o layout entre páginas; garante o bind mesmo se o
  // DOMContentLoaded já tiver passado quando o script for reavaliado.
  var tentativas = 0;
  var intervalo = setInterval(function () {
    attach();
    tentativas += 1;
    if (document.getElementById("nav-toggle") || tentativas > 20) {
      clearInterval(intervalo);
    }
  }, 250);
})();
