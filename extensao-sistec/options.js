/**
 * Opções de desenvolvimento (T061) — só a URL-base do Sistec simulado usada
 * pela extensão para abrir a aba de login/captura (`background.js`,
 * `obterBaseSistec`). As URLs de troca de perfil/exportação continuam
 * vindas do servidor CalcSISTEC (`app/sistec/urls.py`,
 * `CALCSISTEC_SISTEC_BASE_URL`), então os dois lados devem apontar para o
 * mesmo Sistec simulado durante o teste.
 */

const campoBase = document.getElementById("base-sistec");
const status = document.getElementById("status");

async function carregar() {
  const config = await chrome.storage.local.get("baseSistecDev");
  campoBase.value = config.baseSistecDev || "";
}

document.getElementById("salvar").addEventListener("click", async () => {
  const valor = campoBase.value.trim();
  if (valor) {
    await chrome.storage.local.set({ baseSistecDev: valor });
    status.textContent = `Salvo: a extensão vai abrir ${valor}.`;
  } else {
    await chrome.storage.local.remove("baseSistecDev");
    status.textContent = "Salvo: a extensão volta a usar o Sistec real.";
  }
});

document.getElementById("limpar").addEventListener("click", async () => {
  await chrome.storage.local.remove("baseSistecDev");
  campoBase.value = "";
  status.textContent = "A extensão volta a usar o Sistec real.";
});

carregar();
