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
        if (matInput) matInput.value = this.aluno.matricula || "";
        const objEl = document.getElementById("alunoObjetivo");
        if (objEl) objEl.textContent = this.aluno.objetivo || "Não definido";
        const nivEl = document.getElementById("alunoNivel");
        if (nivEl) nivEl.textContent = this.aluno.nivel || "Não definido";
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
          window.FitApp.historicoChat = [];
          window.kiaraTreinoEmEdicao = null;
          window.FitApp.sessao.aluno = null;
          window.location.replace("/pages/conta.html");
        } catch (err) {
          // Não mostrar a tela de login como se o logout tivesse funcionado.
          window.FitApp.ui.toast(err.message || "Não foi possível sair. Tente novamente.", "erro");
        }
      }
    },


  };

  window.salvarTreinoDoChat = async function (textoTreino, btnEl) {
    try {
      if (btnEl) {
        btnEl.disabled = true;
        btnEl.textContent = "Salvando...";
      }
      const titulo = window.kiaraTreinoEmEdicao ? '' : prompt('Nome do treino (opcional):', '');
      if (titulo === null) { if (btnEl) {btnEl.disabled=false;btnEl.textContent='Salvar este treino';} return; }
      const res = await window.FitApp.api("/api/treinos/salvar-do-chat", {
        method: "POST",
        body: { texto: textoTreino, titulo: titulo.trim(), substituir_id: window.kiaraTreinoEmEdicao || undefined }
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
    const botaoVoz = document.getElementById("alternarVozKiara");
    const botaoPararVoz = document.getElementById("pararVozKiara");
    let vozAtivada = false;
    let vozFalandoAgora = false;
    let vozCarregando = false;
    let vozSelecionada = "Neural pt-BR — Francisca";
    let audioAtual = null;
    let urlAudioAtual = null;
    let idFala = 0;
    let concluirTrechoAtual = null;
    let revelacaoAtual = null;
    const pedidosVoz = new Set();
    let erroOfflineAvisado = null;

    function atualizarControlesVoz() {
      if (botaoVoz) {
        botaoVoz.setAttribute("aria-pressed", String(vozAtivada));
        botaoVoz.classList.toggle("voz-ativa", vozAtivada);
        botaoVoz.classList.toggle("voz-desligada", !vozAtivada);
        botaoVoz.classList.toggle("voz-falando", vozAtivada && vozFalandoAgora);
        botaoVoz.title = vozAtivada ? `Voz: ${vozSelecionada}` : "Ativar voz da Kiara";
        botaoVoz.setAttribute("aria-label", vozAtivada ? "Desativar voz da Kiara" : "Ativar voz da Kiara");
      }
      if (botaoPararVoz) {
        const podeParar = vozAtivada && (vozCarregando || vozFalandoAgora);
        botaoPararVoz.disabled = !podeParar;
        botaoPararVoz.classList.toggle("pode-parar", podeParar);
        botaoPararVoz.title = podeParar ? "Parar a voz agora" : "Kiara em silêncio";
      }
    }

    // A resposta fica invisível enquanto o áudio não toca. Cada palavra
    // aparece DEPOIS de seu tempo real de início no MP3, com pequeno atraso.
    function prepararRevelacao(elemento, texto, id) {
      if (!elemento?._kiaraTextoNode) return null;
      const no = elemento._kiaraTextoNode;
      const completo = String(texto || "");
      const fimPalavras = Array.from(completo.matchAll(/\S+/gu), m => m.index + m[0].length);
      no.nodeValue = "";
      let exibidas = 0;
      const controle = {
        id,
        total: fimPalavras.length,
        mostrar(quantidade) {
          if (id !== idFala) return;
          const n = Math.max(exibidas, Math.min(fimPalavras.length, Math.floor(quantidade)));
          if (n <= exibidas) return;
          exibidas = n;
          no.nodeValue = completo.slice(0, fimPalavras[n - 1]);
          if (boxMensagens) boxMensagens.scrollTop = boxMensagens.scrollHeight;
        },
        concluir() { no.nodeValue = completo; }
      };
      return controle;
    }

    function concluirRevelacao() {
      if (!revelacaoAtual) return;
      revelacaoAtual.concluir();
      revelacaoAtual = null;
    }

    function pararAudioKiara() {
      // O texto completo aparece após Parar, mesmo se a fala for interrompida.
      concluirRevelacao();
      idFala += 1;
      vozFalandoAgora = false;
      vozCarregando = false;
      for (const controller of pedidosVoz) controller.abort();
      pedidosVoz.clear();
      if (audioAtual) {
        audioAtual.onended = null;
        audioAtual.onerror = null;
        audioAtual.pause();
        audioAtual.removeAttribute("src");
        audioAtual.load();
        audioAtual = null;
      }
      if (urlAudioAtual) {
        URL.revokeObjectURL(urlAudioAtual);
        urlAudioAtual = null;
      }
      if (concluirTrechoAtual) {
        const terminar = concluirTrechoAtual;
        concluirTrechoAtual = null;
        terminar();
      }
      try { window.speechSynthesis?.cancel(); } catch (_) {}
      atualizarControlesVoz();
    }

    // Envia frases completas ao TTS: cada chamada corresponde a uma unidade de fala.
    // O serviço neural aceita no máximo 240 caracteres; usar margem de segurança.
    function dividirFala(texto) {
      const limpo = String(texto || "")
        .replace(/https?:\/\/\S+/g, "link")
        .replace(/[*_#`]/g, "")
        .replace(/\s+/g, " ").trim();
      const frases = limpo.match(/[^.!?;]+[.!?;]?/g) || [];
      const limite = 220;
      const trechos = [];
      let atual = "";
      function anexar(parte) {
        parte = parte.trim();
        if (!parte) return;
        if (atual && (atual.length + parte.length + 1 > limite)) {
          trechos.push(atual);
          atual = "";
        }
        atual += (atual ? " " : "") + parte;
      }
      for (const original of frases) {
        const frase = original.trim();
        if (!frase) continue;
        if (frase.length <= limite) {
          anexar(frase);
          continue;
        }
        // Somente frases excepcionalmente longas são subdivididas;
        // preferir vírgulas e outros intervalos naturais antes das palavras.
        if (atual) { trechos.push(atual); atual = ""; }
        const partes = frase.split(/(?<=,)\s+/);
        for (const parte of partes) {
          if (parte.length <= limite) { anexar(parte); continue; }
          if (atual) { trechos.push(atual); atual = ""; }
          for (const palavra of parte.split(/\s+/)) {
            if (atual && atual.length + palavra.length + 1 > limite) {
              trechos.push(atual); atual = "";
            }
            atual += (atual ? " " : "") + palavra;
          }
        }
      }
      if (atual) trechos.push(atual);
      return trechos;
    }

    async function buscarVozOnline(texto) {
      const ctrl = new AbortController();
      pedidosVoz.add(ctrl);
      try {
        const res = await fetch("/api/kiara/voz/neural", {
          method: "POST", credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ texto }), signal: ctrl.signal,
        });
        const data = await res.json();
        if (!res.ok || !data.audio_b64) throw new Error(data.erro || "Voz neural indisponível");
        const bin = atob(data.audio_b64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        return { blob: new Blob([bytes], { type: "audio/mpeg" }),
          marcacoes: Array.isArray(data.marcacoes) ? data.marcacoes : [],
          origem: "neural", nome: data.voz || "Francisca" };
      } finally {
        pedidosVoz.delete(ctrl);
      }
    }

    async function buscarVozLocal(texto) {
      const ctrl = new AbortController();
      pedidosVoz.add(ctrl);
      try {
        const res = await fetch("/api/kiara/voz", {
          method: "POST", credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ texto }), signal: ctrl.signal,
        });
        if (!res.ok) throw new Error("Voz local indisponível");
        return { blob: await res.blob(), marcacoes: [], origem: "local", nome: "Kokoro (reserva)" };
      } finally {
        pedidosVoz.delete(ctrl);
      }
    }

    async function buscarAudioTrecho(texto) {
      try { return await buscarVozOnline(texto); }
      catch (erro) {
        if (erro.name === "AbortError") throw erro;
        console.warn("[Kiara][voz] Voz neural indisponível, tentando reserva:", erro.message);
        return buscarVozLocal(texto);
      }
    }

    async function tocarTrecho(dados, id, inicioPalavras, nPalavras) {
      if (id !== idFala || !vozAtivada) return;
      vozSelecionada = dados.nome;
      const url = URL.createObjectURL(dados.blob);
      const audio = new Audio(url);
      urlAudioAtual = url;
      audioAtual = audio;
      const marcacoes = dados.marcacoes;
      let monitor = null;
      try {
        await new Promise((resolve, reject) => {
          concluirTrechoAtual = resolve;
          const atualizar = () => {
            if (id !== idFala || !revelacaoAtual) return;
            if (marcacoes.length) {
              // A palavra só aparece 130ms DEPOIS do início real no áudio.
              const t = Math.max(0, audio.currentTime - 0.13);
              const ditas = marcacoes.filter(m => Number(m.seg) <= t).length;
              revelacaoAtual.mostrar(inicioPalavras + Math.min(nPalavras, ditas));
            }
          };
          audio.onplaying = () => {
            vozFalandoAgora = true;
            vozCarregando = false;
            atualizarControlesVoz();
            monitor = setInterval(atualizar, 55);
          };
          audio.onended = () => {
            if (revelacaoAtual) revelacaoAtual.mostrar(inicioPalavras + nPalavras);
            resolve();
          };
          audio.onerror = () => reject(new Error("Falha ao reproduzir o MP3."));
          audio.play().catch(reject);
        });
      } finally {
        if (monitor) clearInterval(monitor);
        if (concluirTrechoAtual) concluirTrechoAtual = null;
        audio.pause();
        audio.onplaying = null;
        audio.onended = null;
        audio.onerror = null;
        if (audioAtual === audio) audioAtual = null;
        URL.revokeObjectURL(url);
        if (urlAudioAtual === url) urlAudioAtual = null;
        vozFalandoAgora = false;
        atualizarControlesVoz();
      }
    }

    async function falarComoKiara(texto, elementoMensagem = null) {
      if (!vozAtivada || !texto) return;
      pararAudioKiara();
      const id = idFala;
      // Texto completo desde o início. Sem efeito palavra por palavra:
      // evita a mensagem vazia enquanto uma ficha já oferece o botão de salvar.
      revelacaoAtual = null;
      vozCarregando = true;
      atualizarControlesVoz();
      const trechos = dividirFala(texto);
      let faladas = 0;
      let proxima = trechos.length ? buscarAudioTrecho(trechos[0]) : null;
      // Evita rejeição não tratada caso o usuário clique em Parar.
      if (proxima) proxima.catch(() => {});
      try {
        for (let i = 0; i < trechos.length; i++) {
          const dados = await proxima;
          if (id !== idFala || !vozAtivada) return;
          proxima = i + 1 < trechos.length ? buscarAudioTrecho(trechos[i + 1]) : null;
          if (proxima) proxima.catch(() => {});
          const n = (trechos[i].match(/\S+/g) || []).length;
          await tocarTrecho(dados, id, faladas, n);
          faladas += n;
          if (id !== idFala || !vozAtivada) return;
          vozCarregando = Boolean(proxima);
          atualizarControlesVoz();
        }
      } catch (erro) {
        if (id === idFala && erro.name !== "AbortError") {
          console.warn("[Kiara][voz] Falha de síntese:", erro.message);
          window.FitApp.ui.toast("Voz indisponível. Resposta exibida em texto.", "erro");
        }
      } finally {
        if (id === idFala) pararAudioKiara();
      }
    }

    if (botaoVoz) {
      botaoVoz.title = "Ativar respostas faladas da Kiara";
      botaoVoz.addEventListener("click", () => {
        vozAtivada = !vozAtivada;
        if (!vozAtivada) pararAudioKiara();
        atualizarControlesVoz();
      });
    }
    if (botaoPararVoz) botaoPararVoz.addEventListener("click", pararAudioKiara);
    window.addEventListener("beforeunload", pararAudioKiara);
    atualizarControlesVoz();

    function atualizarIndicadorIA(modo, aviso = null) {
      const indicador = document.getElementById("indicadorModoIA");
      if (!indicador) return;
      indicador.classList.remove("ia-ativa", "ia-offline", "ia-configuracao");
      if (modo === "gemini") {
        indicador.classList.add("ia-ativa");
        indicador.textContent = "IA ativa";
        indicador.title = "Esta resposta foi gerada pela IA online";
      } else if (modo === "offline") {
        indicador.classList.add("ia-offline");
        indicador.textContent = "IA offline";
        indicador.title = aviso && aviso.mensagem
          ? "Gemini indisponível: " + aviso.mensagem
          : "Esta resposta foi gerada com recursos locais";
      } else if (modo === "configuracao") {
        indicador.classList.add("ia-configuracao");
        indicador.textContent = "Configurando perfil";
        indicador.title = "Perguntas iniciais do FitFATEC, sem geração pela IA";
      } else if (modo === "local") {
        indicador.classList.add("ia-ativa");
        indicador.textContent = "Ação local";
        indicador.title = "A ficha anterior foi recuperada da conversa, sem nova geração pela IA";
      } else {
        indicador.textContent = "IA: aguardando";
        indicador.title = "Aguardando a primeira resposta da Kiara";
      }
    }

    function parecePlanoSemanal(texto) {
      const titulos = (texto || '').match(/(?:^|\n)\s*(?:[-•*]\s*)?(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)(?:-feira)?\s*[:(—-]/gim) || [];
      return titulos.length >= 2;
    }

    function pareceTreino(texto) {
      // Reconhece fichas por repetições (3x10) OU duração (20 min, 3x2 min).
      // Exige prescrição junto ao nome do exercício, não apenas o título "Cardio".
      const linhas = String(texto || '').split(/\n/);
      const prescricao = /^\s*(?:[-•*]\s*)?[^\n:]{3,100}:\s*(?:\d+\s*[xX×]\s*\d+|\d+\s*min(?:utos?)?\b)/i;
      // Uma linha isolada pode ser exemplo ou um rascunho parcial.
      return linhas.filter(linha => prescricao.test(linha)).length >= 2;
    }

    function adicionarMensagem(texto, remetente, comBotaoSalvar = false, opcoes = [], etapa = null, treinoAnterior = null) {
      if (!boxMensagens) return null;
      const div = document.createElement("div");
      div.className = `msg ${remetente}`;
      // Nó exclusivo para o texto: a revelação progressiva não remove
      // os botões de salvar treino e outras ações desta mensagem.
      const textoNo = document.createTextNode(texto);
      div.appendChild(textoNo);
      if (remetente === "bot") div._kiaraTextoNode = textoNo;

      // Se o aluno pediu para salvar a ficha anterior, o servidor devolve o
      // texto exato da ficha, sem pedir ao Gemini que gere uma nova.
      const textoAlvo = treinoAnterior || texto;
      if (remetente === "bot" && (pareceTreino(textoAlvo) || parecePlanoSemanal(textoAlvo))) {
        const acoesDiv = document.createElement("div");
        acoesDiv.style.cssText = "margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.08); display:flex; justify-content:flex-end;";
        const btnSalvar = document.createElement("button");
        btnSalvar.type = "button";
        btnSalvar.className = "fit-btn-outline-orange";
        btnSalvar.style.cssText = "padding:6px 12px; font-size:0.8rem; min-height:auto;";
        const multiplosDias=parecePlanoSemanal(textoAlvo);
        btnSalvar.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          <span>Salvar este treino</span>
        `;
        if (multiplosDias) {
          btnSalvar.querySelector('span').textContent='Criar prévia semanal';
          btnSalvar.title='Abre a prévia estruturada dos dias e exercícios; não salva o texto automaticamente';
          btnSalvar.onclick=()=>window.abrirPlanoSemanal?.(textoAlvo);
          const nota=document.createElement('small');
          nota.textContent='A prévia usa o gerador do FitFATEC e pode ser diferente do texto acima.';
          nota.style.cssText='display:block;font-size:.72rem;color:var(--text-secondary);margin:5px 0;';
          div.appendChild(nota);
        } else {
          btnSalvar.onclick = () => window.salvarTreinoDoChat(textoAlvo, btnSalvar);
          if (treinoAnterior) btnSalvar.querySelector("span").textContent="Salvar treino anterior";
          if (window.kiaraTreinoEmEdicao) btnSalvar.querySelector("span").textContent="Salvar alterações";
        }
        acoesDiv.appendChild(btnSalvar);
        if (!multiplosDias && window.kiaraTreinoEmEdicao) {
          const comoNovo=document.createElement('button');comoNovo.type='button';comoNovo.className='fit-btn-outline-orange';
          comoNovo.textContent='Salvar como novo';comoNovo.onclick=()=>{
            const anterior=window.kiaraTreinoEmEdicao;window.kiaraTreinoEmEdicao=null;
            window.salvarTreinoDoChat(textoAlvo,comoNovo).finally(()=>{window.kiaraTreinoEmEdicao=anterior;});
          };acoesDiv.append(comoNovo);
        }
        div.appendChild(acoesDiv);
      }

      // Durante o primeiro acesso, a resposta da Kiara oferece opções clicáveis.
      // Botões enviam a mesma resposta validada pelo backend que o usuário digitaria.
      if (remetente === "bot" && Array.isArray(opcoes) && opcoes.length) {
        const grupo = document.createElement("div");
        grupo.className = "kiara-opcoes";
        grupo.setAttribute("aria-label", "Respostas sugeridas pela Kiara");
        opcoes.forEach((opcao) => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "kiara-escolha";
          btn.textContent = opcao.rotulo;
          btn.addEventListener("click", () => {
            // Evita dois cliques e mantém o contexto da etapa atual.
            grupo.querySelectorAll("button").forEach((b) => b.disabled = true);
            window.enviarKiara(opcao.valor);
          });
          grupo.appendChild(btn);
        });
        if (etapa === "nascimento") {
          const rotulo = document.createElement("label");
          rotulo.textContent = "Data de nascimento";
          rotulo.className = "kiara-data-label";
          const campoData = document.createElement("input");
          campoData.type = "date";
          campoData.className = "kiara-data";
          campoData.max = new Date().toISOString().slice(0, 10);
          const confirmarData = document.createElement("button");
          confirmarData.type = "button";
          confirmarData.className = "kiara-escolha";
          confirmarData.textContent = "Verificar idade";
          confirmarData.addEventListener("click", () => {
            if (!campoData.value) return;
            grupo.querySelectorAll("button").forEach((b) => b.disabled = true);
            window.enviarKiara(campoData.value);
          });
          rotulo.appendChild(campoData);
          grupo.prepend(rotulo);
          grupo.appendChild(confirmarData);
        }
        div.appendChild(grupo);
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

    if (boxMensagens && window.FitApp.sessao.aluno) {
      try {
        const boasVindas = await window.FitApp.api("/api/kiara/inicio");
        if (boasVindas.pendente) {
          // A pergunta vem do backend, não de um nível fixo no HTML.
          if (!window.FitApp.historicoChat.length) boxMensagens.replaceChildren();
          const ultima = window.FitApp.historicoChat.at(-1);
          if (!ultima || ultima.content !== boasVindas.mensagem) {
            adicionarMensagem(boasVindas.mensagem, "bot", false, boasVindas.opcoes, boasVindas.etapa);
          }
          atualizarIndicadorIA("configuracao");
        }
      } catch (err) {
        if (err.status === 401) window.location.href = "/pages/conta.html";
      }
    }

    const limparConversa = document.getElementById("limparConversa");
    if (limparConversa && boxMensagens) {
      limparConversa.addEventListener("click", async () => {
        if (!window.confirm("Limpar todo o histórico da conversa com a Kiara? Seus treinos, planos e agendamentos continuarão salvos.")) return;
        limparConversa.disabled = true;
        try {
          await window.FitApp.api("/api/chat/limpar", { method: "POST" });
          boxMensagens.replaceChildren();
          window.FitApp.historicoChat = [];
          window.kiaraTreinoEmEdicao = null;
          atualizarIndicadorIA("aguardando");
          adicionarMensagem("Conversa limpa. Como posso te ajudar?", "bot");
          window.FitApp.ui.toast("Conversa limpa.", "sucesso");
        } catch (err) {
          window.FitApp.ui.toast(err.message || "Não foi possível limpar a conversa.", "erro");
        } finally { limparConversa.disabled = false; }
      });
    }

    if (form && input) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const texto = input.value.trim();
        if (!texto) return;

        // Só a última pergunta da avaliação pode ficar clicável.
        document.querySelectorAll("#mensagens .kiara-opcoes button").forEach(b => b.disabled = true);
        adicionarMensagem(texto, "user");
        window.FitApp.historicoChat.push({ role: "user", content: texto });
        input.value = "";
        const loading = adicionarMensagem("Kiara está analisando...", "bot");

        const u = window.FitApp.sessao.aluno || {};
        const payloadAluno = {
          idade: u.idade || 22,
          objetivo: u.objetivo || "Não definido",
          nivel: u.nivel || "Não definido",
          frequencia_semanal: u.treinos_semana || 3,
          minutos_por_sessao: u.minutos_por_sessao || null
        };

        try {
          const res = await window.FitApp.api("/api/chat", {
            method: "POST",
            body: {
              mensagem: texto,
              pergunta: texto,
              aluno: payloadAluno,
              historico: window.FitApp.historicoChat,
              editar_treino_id: window.kiaraTreinoEmEdicao || undefined
            }
          });
          if (loading) loading.remove();
          const respostaTexto = res.resposta || res.mensagem || "Pronto!";
          document.querySelectorAll("#mensagens .kiara-opcoes").forEach(el => el.remove());
          const mensagemKiara = adicionarMensagem(respostaTexto, "bot", Boolean(res.eh_treino), res.opcoes, res.etapa, res.treino_anterior_texto || null);
          falarComoKiara(respostaTexto, mensagemKiara);
          window.FitApp.historicoChat.push({ role: "assistant", content: respostaTexto });
          atualizarIndicadorIA(res.modo, res.ia_aviso);
          if (res.modo === "offline" && res.ia_aviso &&
              erroOfflineAvisado !== res.ia_aviso.codigo) {
            erroOfflineAvisado = res.ia_aviso.codigo;
            window.FitApp.ui.toast(res.ia_aviso.mensagem, "erro");
          } else if (res.modo === "gemini") {
            erroOfflineAvisado = null;
          }
          if (res.usuario) {
            window.FitApp.sessao.aluno = res.usuario;
            window.FitApp.sessao.preencherDadosComuns();
          }

          if (typeof window.carregarDashboard === "function") {
            window.carregarDashboard();
          }
        } catch (err) {
          if (loading) loading.remove();
          window.FitApp.historicoChat.pop();
          document.querySelectorAll("#mensagens .kiara-opcoes button").forEach(b => b.disabled = false);
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