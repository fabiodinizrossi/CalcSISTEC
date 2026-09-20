/*
 * Confirmação de ações em br-modal, no lugar da caixa de confirmação nativa do navegador.
 *
 *   confirmarAcao(mensagem, { rotuloConfirmar }) -> Promise<boolean>
 *
 * Abre o modal do shell (`shell/_modal_confirmacao.html`), prende o foco entre
 * "Cancelar" e o botão de confirmação, fecha com Esc e devolve o foco ao
 * controle que abriu. Formulários `.confirm-form` com um `button[data-confirm]`
 * (e, opcionalmente, `data-confirm-rotulo`) passam por aqui antes de enviar.
 */
(function () {
  "use strict";

  // Índice do próximo elemento focável no ciclo do Tab; -1 é foco fora do modal.
  function proximoFoco(indice, total, shift) {
    if (indice < 0) { return shift ? total - 1 : 0; }
    if (shift) { return indice === 0 ? total - 1 : indice - 1; }
    return indice === total - 1 ? 0 : indice + 1;
  }

  function teclaFecha(tecla) {
    return tecla === "Escape";
  }

  function confirmarAcao(mensagem, opcoes) {
    var scrim = document.getElementById("modal-confirmacao");
    var texto = document.getElementById("modal-confirmacao-mensagem");
    var cancelar = document.getElementById("modal-confirmacao-cancelar");
    var confirmar = document.getElementById("modal-confirmacao-confirmar");
    if (!scrim || !texto || !cancelar || !confirmar) { return Promise.resolve(false); }

    return new Promise(function (resolver) {
      var origem = document.activeElement;
      var focaveis = [cancelar, confirmar];

      function fechar(resultado) {
        scrim.classList.remove("active");
        document.removeEventListener("keydown", aoTeclar, true);
        cancelar.removeEventListener("click", aoCancelar);
        confirmar.removeEventListener("click", aoConfirmar);
        if (origem && origem.focus) { origem.focus(); }
        resolver(resultado);
      }
      function aoCancelar() { fechar(false); }
      function aoConfirmar() { fechar(true); }
      function aoTeclar(evento) {
        if (teclaFecha(evento.key)) {
          evento.preventDefault();
          fechar(false);
        } else if (evento.key === "Tab") {
          evento.preventDefault();
          var atual = focaveis.indexOf(document.activeElement);
          focaveis[proximoFoco(atual, focaveis.length, evento.shiftKey)].focus();
        }
      }

      texto.textContent = mensagem;
      confirmar.textContent = (opcoes && opcoes.rotuloConfirmar) || "Confirmar";
      cancelar.addEventListener("click", aoCancelar);
      confirmar.addEventListener("click", aoConfirmar);
      document.addEventListener("keydown", aoTeclar, true);
      scrim.classList.add("active");
      cancelar.focus();
    });
  }

  if (typeof document !== "undefined") {
    document.addEventListener("submit", function (evento) {
      var form = evento.target;
      if (!form.matches || !form.matches("form.confirm-form")) { return; }
      var botao = form.querySelector("button[data-confirm]");
      if (!botao) { return; }
      if (form.dataset.confirmado === "1") { return; }
      evento.preventDefault();
      confirmarAcao(botao.dataset.confirm, { rotuloConfirmar: botao.dataset.confirmRotulo }).then(function (ok) {
        if (!ok) { return; }
        form.dataset.confirmado = "1";
        HTMLFormElement.prototype.submit.call(form);
      });
    });
  }

  if (typeof window !== "undefined") { window.confirmarAcao = confirmarAcao; }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { proximoFoco: proximoFoco, teclaFecha: teclaFecha };
  }
})();
