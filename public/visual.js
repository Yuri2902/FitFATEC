/* visual.js — melhorias visuais do Assistente da Academia.
   Carregue DEPOIS do script principal do index.html. */
(function () {
  "use strict";

  const raiz = document.documentElement;
  const reduzirMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Tema claro / escuro ---------- */
  function lerTema() {
    try { return localStorage.getItem("tema"); } catch (_) { return null; }
  }
  function salvarTema(t) {
    try { localStorage.setItem("tema", t); } catch (_) { /* sem armazenamento */ }
  }

  const topo = document.querySelector("header");
  const link = topo.querySelector("a");
  const acoes = document.createElement("div");
  acoes.className = "acoes";
  const botaoTema = document.createElement("button");
  botaoTema.type = "button";
  botaoTema.className = "btn-icone";
  topo.insertBefore(acoes, link);
  acoes.append(botaoTema, link);

  function aplicarTema(t) {
    raiz.setAttribute("data-tema", t);
    botaoTema.textContent = t === "escuro" ? "☀️" : "🌙";
    const rotulo = t === "escuro" ? "Mudar para tema claro" : "Mudar para tema escuro";
    botaoTema.setAttribute("aria-label", rotulo);
    botaoTema.title = rotulo;
  }
  aplicarTema(lerTema() || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro"));
  botaoTema.addEventListener("click", () => {
    const novo = raiz.getAttribute("data-tema") === "escuro" ? "claro" : "escuro";
    aplicarTema(novo);
    salvarTema(novo);
  });

  /* ---------- Risco: contador animado + nível ---------- */
  const textoRisco = document.getElementById("riscoTexto");
  const barraRisco = textoRisco.parentNode.querySelector(".barra");
  const nivel = document.createElement("div");
  nivel.className = "risco-nivel";
  barraRisco.after(nivel);

  let exibido = 0;
  let quadro = 0;

  const observadorRisco = new MutationObserver(() => {
    const m = textoRisco.textContent.match(/^(\d+)%$/);
    if (!m) { nivel.textContent = ""; nivel.className = "risco-nivel"; exibido = 0; return; }
    animarRisco(Number(m[1]));
  });

  function animarRisco(alvo) {
    cancelAnimationFrame(quadro);
    const inicio = exibido;
    const t0 = performance.now();
    const duracao = reduzirMovimento ? 0 : 500;

    const classe = alvo > 60 ? "alto" : alvo > 35 ? "moderado" : "baixo";
    nivel.className = "risco-nivel nivel-" + classe;
    nivel.textContent = "Risco " + classe;

    function passo(agora) {
      const p = duracao ? Math.min(1, (agora - t0) / duracao) : 1;
      exibido = Math.round(inicio + (alvo - inicio) * p);
      textoRisco.textContent = exibido + "%";
      observadorRisco.takeRecords();      // ignora a própria escrita
      if (p < 1) quadro = requestAnimationFrame(passo);
    }
    quadro = requestAnimationFrame(passo);
  }
  observadorRisco.observe(textoRisco, { childList: true, characterData: true, subtree: true });

  /* ---------- Chat: "digitando…" e rolagem suave ---------- */
  const area = document.getElementById("mensagens");
  const saudacao = area.firstElementChild ? area.firstElementChild.textContent : "";

  new MutationObserver(() => {
    area.querySelectorAll(".msg.bot").forEach(m => {
      m.classList.toggle("digitando", m.textContent.trim() === "Pensando...");
    });
    area.scrollTo({ top: area.scrollHeight, behavior: reduzirMovimento ? "auto" : "smooth" });
  }).observe(area, { childList: true, subtree: true, characterData: true });

  /* ---------- Sugestões rápidas e limpar conversa ---------- */
  const form = document.getElementById("formChat");
  const campo = document.getElementById("pergunta");
  const enviar = document.getElementById("enviar");

  const barra = document.createElement("div");
  barra.className = "sugestoes";
  form.before(barra);

  ["Monte meu treino da semana", "Como evitar faltas?", "Dicas de alimentação"].forEach(texto => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.textContent = texto;
    b.addEventListener("click", () => {
      if (enviar.disabled) return;        // já há uma resposta em andamento
      campo.value = texto;
      form.requestSubmit();
    });
    barra.appendChild(b);
  });

  const limpar = document.createElement("button");
  limpar.type = "button";
  limpar.className = "chip chip-limpar";
  limpar.textContent = "Limpar conversa";
  limpar.addEventListener("click", () => {
    if (enviar.disabled) return;
    if (typeof historico !== "undefined") historico.length = 0;   // array do script principal
    area.textContent = "";
    const div = document.createElement("div");
    div.className = "msg bot";
    div.textContent = saudacao;
    area.appendChild(div);
    campo.focus();
  });
  barra.appendChild(limpar);
})();
