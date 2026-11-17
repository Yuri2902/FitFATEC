(function () {
  "use strict";

  window.FitApp = {
    historicoChat: [],

    api: async function (url, options = {}) {
      options.credentials = "same-origin";
      if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
        options.headers = { ...options.headers, "Content-Type": "application/json" };
        options.body = JSON.stringify(options.body);
      }
      const response = await fetch(url, options);
      let data = {};
      try {
        data = await response.json();
      } catch (_) {}

      if (!response.ok) {
        const err = new Error(data.erro || data.message || "Erro na requisição");
        err.status = response.status;
        throw err;
      }
      return data;
    },

    sessao: {
      aluno: null,
      init: async function () {
        const naTelaLogin = window.location.pathname.endsWith("conta.html") || window.location.pathname === "/conta";
        try {
          const res = await window.FitApp.api("/api/me");
          this.aluno = res.usuario || res.aluno || null;
          if (this.aluno && naTelaLogin) {
            window.location.href = "/index.html";
            return this.aluno;
          }
          this.aplicarPreferencias();
          this.atualizarNavbar();
          this.preencherDadosComuns();
        } catch (_) {
          if (!naTelaLogin) {
            window.location.href = "/pages/conta.html";
            return null;
          }
        }
        return this.aluno;
      },
      aplicarPreferencias: function () {
        if (!this.aluno) return;
        document.documentElement.setAttribute("data-theme", this.aluno.tema || "escuro");
        document.documentElement.setAttribute("data-acessibilidade", this.aluno.acessibilidade || "padrao");
      },
      atualizarNavbar: function () {
        const authBtn = document.getElementById("navAuthBtn");
        if (!authBtn || !this.aluno) return;
        const primeiroNome = (this.aluno.nome || "Aluno").split(" ")[0];
        const avatarHtml = this.aluno.avatar_url
          ? `<img src="${this.aluno.avatar_url}" alt="${primeiroNome}" style="width:22px; height:22px; border-radius:50%; object-fit:cover; border:1px solid var(--accent-primary);">`
          : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
             </svg>`;

        authBtn.innerHTML = `
          ${avatarHtml}
          <span>${primeiroNome}</span>
        `;
        authBtn.href = "/pages/perfil.html";

        if (!document.getElementById("navLogoutBtn") && authBtn.parentNode) {
          const logoutBtn = document.createElement("button");
          logoutBtn.id = "navLogoutBtn";
          logoutBtn.type = "button";
          logoutBtn.className = "fit-btn-auth";
          logoutBtn.title = "Sair da conta";
          logoutBtn.style.marginLeft = "8px";
          logoutBtn.style.cursor = "pointer";
          logoutBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            <span>Sair</span>
          `;
          logoutBtn.addEventListener("click", () => window.FitApp.auth.sair());
          authBtn.parentNode.appendChild(logoutBtn);
        }
      },
      preencherDadosComuns: function () {
        if (!this.aluno) return;
        const matInput = document.getElementById("alunoMatricula");
        if (matInput) matInput.value = this.aluno.matricula || "20260001";
        const objEl = document.getElementById("alunoObjetivo");
        if (objEl && this.aluno.objetivo) objEl.textContent = this.aluno.objetivo;
        const nivEl = document.getElementById("alunoNivel");
        if (nivEl && this.aluno.nivel) nivEl.textContent = this.aluno.nivel;
      }
    },

    ui: {
      toast: function (msg, tipo = "info") {
        const toastEl = document.createElement("div");
        toastEl.className = `fit-toast ${tipo}`;
        toastEl.textContent = msg;
        document.body.appendChild(toastEl);
        setTimeout(() => toastEl.remove(), 3200);
      },
      copiarTexto: function (texto, botaoEl) {
        if (!texto) {
          this.toast("Nada para copiar.", "info");
          return;
        }
        navigator.clipboard.writeText(texto);
        this.toast("Matrícula copiada!", "sucesso");
        if (botaoEl) {
          const original = botaoEl.innerHTML;
          botaoEl.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
          setTimeout(() => (botaoEl.innerHTML = original), 1800);
        }
      }
    },

    auth: {
      iniciarTransicaoLogin: function (nomeUsuario) {
        const primeiroNome = (nomeUsuario || "Aluno").split(" ")[0];
        const overlay = document.createElement("div");
        overlay.className = "fit-transition-overlay";
        overlay.innerHTML = `
          <div class="fit-transition-logo">
            <img src="/img/kiara-logo.png" alt="FitFATEC" width="44" height="44">
            <span><span class="brand-fit">Fit</span><span class="brand-fatec">FATEC</span></span>
          </div>
          <div class="fit-transition-bar">
            <div class="fit-transition-bar-fill"></div>
          </div>
          <div class="fit-transition-text">Bem-vindo de volta, ${primeiroNome}! Preparando seu painel...</div>
        `;
        document.body.appendChild(overlay);

        requestAnimationFrame(() => {
          overlay.classList.add("ativo");
        });

        setTimeout(() => {
          window.location.href = "/index.html";
        }, 850);
      },
      fazerLogin: async function (identificador, senha) {
        try {
          const res = await window.FitApp.api("/api/login", {
            method: "POST",
            body: { email: identificador, matricula: identificador, identificador, senha }
          });
          const nome = res.usuario && res.usuario.nome ? res.usuario.nome : "Aluno";
          this.iniciarTransicaoLogin(nome);
        } catch (err) {
          window.FitApp.ui.toast(err.message || "Credenciais inválidas.", "erro");
        }
      },
      fazerCadastro: async function (nome, matricula, email, senha) {
        try {
          await window.FitApp.api("/api/cadastro", {
            method: "POST",
            body: { nome, matricula, email, senha }
          });
          window.FitApp.ui.toast("Conta criada! Entrando...", "sucesso");
          await this.fazerLogin(email || matricula, senha);
        } catch (err) {
          window.FitApp.ui.toast(err.message || "Erro ao cadastrar.", "erro");
        }
      },
      sair: async function () {
        try {
          await window.FitApp.api("/logout", { method: "POST" });
        } catch (_) {}
        window.location.href = "/pages/conta.html";
      }
    },

    agendamento: {
      agendarAula: async function (data, modalidade, horario, observacoes) {
        const horarioFormatado = (horario || "").split("–")[0].trim().replace("h", ":");
        try {
          const res = await window.FitApp.api("/api/agendamentos", {
            method: "POST",
            body: {
              data,
              modalidade: (modalidade || "musculação").toLowerCase(),
              horario: horarioFormatado,
              observacoes
            }
          });
          window.FitApp.ui.toast(res.mensagem || "Aula agendada com sucesso!", "sucesso");
          return true;
        } catch (err) {
          window.FitApp.ui.toast(err.message || "Erro ao agendar.", "erro");
          return false;
        }
      }
    }
  };

  window.salvarTreinoDoChat = async function (textoTreino, btnEl) {
    try {
      if (btnEl) {
        btnEl.disabled = true;
        btnEl.textContent = "Salvando...";
      }
      const res = await window.FitApp.api("/api/treinos/salvar-do-chat", {
        method: "POST",
        body: { texto: textoTreino }
      });
      window.FitApp.ui.toast(res.mensagem || "Treino salvo em Meus treinos!", "sucesso");
      if (btnEl) {
        btnEl.innerHTML = "✓ Salvo em Meus treinos";
        btnEl.style.borderColor = "#22C55E";
        btnEl.style.color = "#22C55E";
      }
    } catch (err) {
      if (btnEl) {
        btnEl.disabled = false;
        btnEl.textContent = "Salvar este treino";
      }
      window.FitApp.ui.toast(err.message || "Erro ao salvar treino.", "erro");
    }
  };

  document.addEventListener("DOMContentLoaded", async () => {
    await window.FitApp.sessao.init();

    const form = document.getElementById("formChat");
    const input = document.getElementById("pergunta");
    const boxMensagens = document.getElementById("mensagens");

    function pareceTreino(texto) {
      const t = (texto || "").toLowerCase();
      return t.includes("aquecimento:") || t.includes("treino principal") || (t.includes("séries") && t.includes("descanso"));
    }

    function adicionarMensagem(texto, remetente, comBotaoSalvar = false) {
      if (!boxMensagens) return null;
      const div = document.createElement("div");
      div.className = `msg ${remetente}`;
      div.textContent = texto;

      if (remetente === "bot" && (comBotaoSalvar || pareceTreino(texto))) {
        const acoesDiv = document.createElement("div");
        acoesDiv.style.cssText = "margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.08); display:flex; justify-content:flex-end;";
        const btnSalvar = document.createElement("button");
        btnSalvar.type = "button";
        btnSalvar.className = "fit-btn-outline-orange";
        btnSalvar.style.cssText = "padding:6px 12px; font-size:0.8rem; min-height:auto;";
        btnSalvar.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          <span>Salvar este treino</span>
        `;
        btnSalvar.onclick = () => window.salvarTreinoDoChat(texto, btnSalvar);
        acoesDiv.appendChild(btnSalvar);
        div.appendChild(acoesDiv);
      }

      boxMensagens.appendChild(div);
      boxMensagens.scrollTop = boxMensagens.scrollHeight;
      return div;
    }

    if (boxMensagens && window.FitApp.sessao.aluno) {
      try {
        const histRes = await window.FitApp.api("/api/chat/historico");
        if (histRes.ok && Array.isArray(histRes.mensagens) && histRes.mensagens.length > 0) {
          histRes.mensagens.forEach((m) => {
            const role = m.role === "user" ? "user" : "bot";
            window.FitApp.historicoChat.push({ role: m.role, content: m.content });
            adicionarMensagem(m.content, role, Boolean(m.eh_treino));
          });
        }
      } catch (_) {}
    }

    if (form && input) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const texto = input.value.trim();
        if (!texto) return;

        adicionarMensagem(texto, "user");
        window.FitApp.historicoChat.push({ role: "user", content: texto });
        input.value = "";
        const loading = adicionarMensagem("Kiara está analisando...", "bot");

        const u = window.FitApp.sessao.aluno || {};
        const payloadAluno = {
          idade: u.idade || 22,
          objetivo: u.objetivo || "Ganhar massa muscular",
          nivel: u.nivel || "Intermediário",
          frequencia_semanal: u.treinos_semana || 3,
          meses_matricula: u.meses_matricula || 1,
          faltas_ultimo_mes: u.faltas_ultimo_mes || 0
        };

        try {
          const res = await window.FitApp.api("/api/chat", {
            method: "POST",
            body: {
              mensagem: texto,
              pergunta: texto,
              aluno: payloadAluno,
              historico: window.FitApp.historicoChat
            }
          });
          if (loading) loading.remove();
          const respostaTexto = res.resposta || res.mensagem || "Pronto!";
          adicionarMensagem(respostaTexto, "bot", Boolean(res.eh_treino));
          window.FitApp.historicoChat.push({ role: "assistant", content: respostaTexto });

          if (typeof window.carregarDashboard === "function") {
            window.carregarDashboard();
          }
        } catch (err) {
          if (loading) loading.remove();
          window.FitApp.historicoChat.pop();
          adicionarMensagem(
            err.status === 401
              ? "Para salvar treinos e consultar sua ficha, clique em Entrar no canto superior direito."
              : `Não foi possível responder agora: ${err.message}`,
            "bot"
          );
        }
      });
    }
  });
})();