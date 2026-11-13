
(function () {
  "use strict";

  const raiz = document.documentElement;
  const reduzirMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;


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

  /* ---------- Chat: histórico rolável, campo ancorado ---------- */
  const area = document.getElementById("mensagens");
  const saudacao = area.firstElementChild ? area.firstElementChild.textContent : "";

  // A área de mensagens ocupa o espaço restante da coluna do chat.
  // A barra de sugestões e o campo de texto ficam fora dessa rolagem.
  const viewport = document.createElement("div");
  viewport.className = "mensagens-viewport";
  area.before(viewport);
  viewport.appendChild(area);

  const voltarFim = document.createElement("button");
  voltarFim.type = "button";
  voltarFim.className = "btn-voltar-fim";
  voltarFim.textContent = "↓ Voltar à conversa";
  voltarFim.setAttribute("aria-label", "Ir para as últimas mensagens");
  voltarFim.hidden = true;
  viewport.appendChild(voltarFim);

  const pertoDoFim = () => area.scrollHeight - area.scrollTop - area.clientHeight <= 110;
  let seguindoFim = true;
  function atualizarEstadoRolagem() {
    seguindoFim = pertoDoFim();
    voltarFim.hidden = seguindoFim;
  }
  area.addEventListener("scroll", atualizarEstadoRolagem, { passive: true });
  voltarFim.addEventListener("click", () => {
    seguindoFim = true;
    area.scrollTo({ top: area.scrollHeight, behavior: reduzirMovimento ? "auto" : "smooth" });
    voltarFim.hidden = true;
  });

  new MutationObserver(() => {
    area.querySelectorAll(".msg.bot").forEach(m => {
      m.classList.toggle("digitando", m.textContent.trim() === "Pensando...");
    });
    // Só rolar automaticamente se a pessoa já estava no final.
    // Ao ler mensagens antigas, oferecemos o botão para voltar.
    if (seguindoFim) {
      requestAnimationFrame(() => {
        if (seguindoFim) area.scrollTop = area.scrollHeight;
      });
    } else {
      voltarFim.hidden = false;
    }
  }).observe(area, { childList: true, subtree: true, characterData: true });

  /* ---------- Sugestões rápidas e limpar conversa ---------- */
  const form = document.getElementById("formChat");
  const campo = document.getElementById("pergunta");
  const enviar = document.getElementById("enviar");

  const barra = document.createElement("div");
  barra.className = "sugestoes";
  form.before(barra);

  ["Quero uma série de condicionamento", "Quero agendar uma aula", "Quais são os aquecimentos?", "Treino principal e secundário", "Qual meu nível?"].forEach(texto => {
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
  limpar.addEventListener("click", async () => {
    if (enviar.disabled) return;
    if (typeof usuarioSessao !== "undefined" && usuarioSessao) {
      try {
        const r = await fetch("/api/chat/limpar", { method: "POST", credentials: "same-origin" });
        if (!r.ok) throw new Error("Falha ao limpar o plano no servidor.");
      } catch (_) {
        // Não apague o histórico se o plano anterior ainda estiver no servidor.
        return;
      }
    }
    if (typeof historico !== "undefined") historico.length = 0;   // array do script principal
    const modo = document.getElementById("modoKiara");
    if (modo) { modo.hidden = true; modo.textContent = ""; delete modo.dataset.modo; }
    area.textContent = "";
    const div = document.createElement("div");
    div.className = "msg bot";
    div.textContent = saudacao;
    area.appendChild(div);
    campo.focus();
  });
  barra.appendChild(limpar);
})();
