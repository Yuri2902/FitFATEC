/* Fluxo de planos semanais na conversa: prévia, revisão e confirmação explícita. */
(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const qs = new URLSearchParams(location.search);
  const caixa = () => $('#mensagens');
  const criar = (tag, texto, classe) => {
    const el = document.createElement(tag);
    if (texto !== undefined) el.textContent = texto;
    if (classe) el.className = classe;
    return el;
  };
  const bloco = (txt) => { const el=criar('div',txt,'msg bot');caixa()?.append(el);el.scrollIntoView({block:'nearest'});return el; };
  const aviso = (txt,tipo='info') => window.FitApp?.ui?.toast(txt,tipo);
  const DIAS=[['seg','Seg'],['ter','Ter'],['qua','Qua'],['qui','Qui'],['sex','Sex'],['sab','Sáb'],['dom','Dom']];
  const DIA_NOME={seg:'segunda',ter:'terça',qua:'quarta',qui:'quinta',sex:'sexta',sab:'sábado',dom:'domingo'};
  const PADRAO={1:['seg'],2:['seg','qui'],3:['seg','qua','sex'],4:['seg','ter','qui','sex'],5:['seg','ter','qua','qui','sex'],6:['seg','ter','qua','qui','sex','sab'],7:DIAS.map(x=>x[0])};
  const normalizar = texto => (texto||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const diasNoTexto = texto => {
    // Em "segunda já tenho, faz terça e quinta", não seleciona segunda.
    const trecho=normalizar(texto).split(/\b(?:faz|faca|monte|monta|para|apenas|somente|so)\b/).at(-1);
    const encontrados=[];
    const exp=/\b(segunda(?:-feira)?|terca(?:-feira)?|quarta(?:-feira)?|quinta(?:-feira)?|sexta(?:-feira)?|sabado|domingo)\b/g;
    let m;
    while((m=exp.exec(trecho))!==null){
      const dia=DIAS.find(([codigo])=>m[1].startsWith(normalizar(DIA_NOME[codigo]).slice(0,3)));
      if(dia && !encontrados.includes(dia[0])) encontrados.push(dia[0]);
    }
    return DIAS.map(d=>d[0]).filter(d=>encontrados.includes(d));
  };
  const reconhecer = text => {
    const t=normalizar(text);
    return /\b(?:semanal|semana|plano\s+de\s+treinos?|rotina\s+de\s+treinos?)\b/.test(t)
      || (diasNoTexto(text).length >= 2 && /\b(?:treino|treinar|faz|faca|monta|monte|quero|cria)\b/.test(t));
  };
  const parametros = text => {
    const t=normalizar(text);
    const dias=t.match(/\b([1-7])\s*(?:dias?|vezes?)\b/);
    const porExtenso=t.match(/\b(um|uma|dois|duas|tres|quatro|cinco|seis|sete)\s*(?:dias?|vezes?)\b/);
    const numeros={um:1,uma:1,dois:2,duas:2,tres:3,quatro:4,cinco:5,seis:6,sete:7};
    const mins=t.match(/\b(20|30|45|60|75|90)\s*(?:min(?:utos?)?)\b/);
    return {dias:dias?Number(dias[1]):porExtenso?numeros[porExtenso[1]]:undefined,
            minutos:mins?Number(mins[1]):/meia hora/.test(t)?30:/uma hora/.test(t)?60:undefined};
  };
  function opcoesSelect(label, valores, selecionado) {
    const wrapper=criar('label',label);wrapper.style.cssText='display:grid;grid-template-rows:auto auto;align-content:start;gap:6px;font-size:.82rem;min-width:0;';
    const select=criar('select');select.style.cssText='width:100%;min-width:0;padding:10px 6px;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--borda-forte);border-radius:9px;';
    valores.forEach(([v,t])=>select.add(new Option(t,v)));
    if (selecionado) select.value=String(selecionado);
    wrapper.append(select);return {wrapper,select};
  }
  async function abrirPlano(pedido='',revisarId=null) {
    if (!caixa()) return;
    // Nunca usar uma revisão de ficha individual como destino de um plano novo.
    window.kiaraTreinoEmEdicao=null;
    if(window.kiaraControlePlano?.card) {
      window.kiaraControlePlano.card.querySelectorAll('button, input, select').forEach(el=>el.disabled=true);
    }
    const u=window.FitApp.sessao.aluno || {};
    const parsed=parametros(pedido);
    let planoAntigo=null, fichasAntigas=[];
    if (revisarId) {
      try {
        const [rp,rt]=await Promise.all([FitApp.api('/api/planos'),FitApp.api('/api/treinos')]);
        planoAntigo=(rp.planos||[]).find(p=>p.id===Number(revisarId));
        if(!planoAntigo){aviso('Plano não encontrado.','erro');return;}
        fichasAntigas=(rt.treinos||[]).filter(t=>t.plano_id===Number(revisarId));
      } catch(err){aviso(err.message,'erro');return;}
    }
    bloco(planoAntigo
      ? `Estou com o plano "${planoAntigo.titulo}" aberto (${fichasAntigas.length} fichas). Você pode manter uma ficha e refazer as outras, ajustar dias e duração ou editar uma ficha específica comigo. O plano original só muda após confirmar.`
      : 'Vamos montar sua semana! Escolha a quantidade de dias e o tempo disponível. Primeiro mostro todas as fichas; só salvo quando você confirmar.');
    if (planoAntigo){
      const atual=criar('details');atual.className='msg bot';
      atual.style.cssText='max-width:100%;padding:13px 16px;border:1px solid var(--borda-forte);border-radius:12px;';
      atual.append(criar('summary',`Ver as ${fichasAntigas.length} fichas atuais do plano (antes de revisar)`));
      fichasAntigas.forEach(t=>{
        const secao=criar('div');secao.style.cssText='padding:10px 0;border-bottom:1px solid var(--borda);';
        secao.append(criar('strong',`${t.titulo} — ${t.dia_semana||'Dia não definido'}`));
        (t.exercicios||[]).forEach(ex=>secao.append(criar('div',`• ${ex.nome_exercicio}: ${ex.series}×${ex.repeticoes} (${ex.descanso_segundos}s)`,'')));
        const link=criar('a','Editar esta ficha com a Kiara');link.href=`/index.html?editar_treino=${t.id}`;
        link.style.cssText='display:inline-block;margin-top:6px;color:var(--accent-primary);';secao.append(link);atual.append(secao);
      });
      caixa().append(atual);
    }
    const card=criar('section',undefined,'msg bot');
    card.style.cssText='display:flex;flex-direction:column;gap:12px;max-width:100%;';
    const campos=criar('div'); campos.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;width:100%;align-items:start;';
    const dia=opcoesSelect('Frequência',Array.from({length:7},(_,i)=>[i+1,`${i+1} dia${i?'s':''}`]),parsed.dias||planoAntigo?.dias_semana||u.treinos_semana||3);
    const dur=opcoesSelect('Duração',[20,30,45,60,75,90].map(i=>[i,`${i} min`]),parsed.minutos||planoAntigo?.minutos_sessao||u.minutos_por_sessao||45);
    campos.append(dia.wrapper,dur.wrapper);card.append(campos);
    const diasBox=criar('fieldset');diasBox.className='kiara-dias-semana';
    const legenda=criar('legend','Dias em que deseja treinar');diasBox.append(legenda);
    const diasGrid=criar('div');diasGrid.className='kiara-dias-grid';
    const checkDias=new Map();
    const diasPedido=diasNoTexto(pedido);
    const diasAnteriores=fichasAntigas.map(t=>{
      const dia=normalizar(t.dia_semana);
      return DIAS.find(([cod])=>dia.startsWith(normalizar(DIA_NOME[cod]).slice(0,3)))?.[0];
    }).filter(Boolean);
    const iniciais=diasPedido.length?diasPedido:
      (revisarId && diasAnteriores.length ? diasAnteriores:PADRAO[Number(dia.select.value)]);
    if(diasPedido.length)dia.select.value=String(diasPedido.length);
    DIAS.forEach(([cod,nome])=>{
      const lab=criar('label');lab.className='kiara-dia-opcao';
      const check=criar('input');check.type='checkbox';check.value=cod;
      check.checked=iniciais.includes(cod);checkDias.set(cod,check);
      lab.append(check,document.createTextNode(nome));diasGrid.append(lab);
      check.addEventListener('change',()=>atualizarContagem());
    });
    diasBox.append(diasGrid);
    const limpar=criar('button','Limpar dias','kiara-limpar-dias');
    limpar.type='button';diasBox.append(limpar);
    limpar.addEventListener('click',()=>{checkDias.forEach(c=>c.checked=false);atualizarContagem();});
    const dicaDias=criar('small');diasBox.append(dicaDias);card.append(diasBox);
    const selecionados=()=>DIAS.filter(([cod])=>checkDias.get(cod).checked).map(([cod])=>cod);
    const atualizarContagem=()=>{
      const qtd=selecionados().length,esperados=Number(dia.select.value);
      dicaDias.textContent=`${qtd} de ${esperados} dias selecionados. ${qtd!==esperados?'Ajuste os dias ou a frequência.':''}`;
      dicaDias.style.color=qtd!==esperados?'#f59e0b':'var(--text-secondary)';
    };
    const ajustarDias=(lista)=>{
      checkDias.forEach((check,cod)=>{check.checked=lista.includes(cod);});
      dia.select.value=String(lista.length);
      atualizarContagem();
    };
    dia.select.addEventListener('change',()=>{
      const qtd=Number(dia.select.value),atual=selecionados();
      const novos=atual.slice(0,qtd);
      for(const cod of PADRAO[qtd])if(novos.length<qtd&&!novos.includes(cod))novos.push(cod);
      for(const [cod] of DIAS)if(novos.length<qtd&&!novos.includes(cod))novos.push(cod);
      ajustarDias(novos);
    });
    atualizarContagem();
    const nomeLabel=criar('label','Nome do plano');nomeLabel.style.cssText='display:grid;gap:6px;font-size:.82rem;';
    const nome=criar('input');nome.placeholder='Ex.: Hipertrofia';nome.value=planoAntigo?.titulo||'';
    nome.style.cssText='padding:10px;width:100%;background:var(--bg-input);color:var(--text-primary);border:1px solid var(--borda-forte);border-radius:9px;';
    nomeLabel.append(nome);card.append(nomeLabel);
    const mantidos=criar('div');
    if (fichasAntigas.length) {
      mantidos.append(criar('strong','Manter fichas sem alterações:'));
      fichasAntigas.forEach(t=>{
        const label=criar('label');label.style.cssText='display:flex;gap:8px;align-items:center;margin:7px 0;';
        const check=criar('input');check.type='checkbox';check.value=t.id;
        check.checked=String(t.id)===qs.get('manter');
        label.append(check,document.createTextNode(t.titulo));mantidos.append(label);
      });
      card.append(mantidos);
    }
    const botoes=criar('div');botoes.style.cssText='display:flex;flex-wrap:wrap;gap:8px;';
    const gerar=criar('button','Ver proposta','fit-btn-outline-orange');gerar.type='button';
    botoes.append(gerar);card.append(botoes);
    const saida=criar('div');saida.style.cssText='display:flex;flex-direction:column;gap:9px;';card.append(saida);
    caixa().append(card);card.scrollIntoView({block:'nearest'});
    window.kiaraControlePlano={dia:dia.select,dur:dur.select,mantidos,gerar,fichasAntigas,ajustarDias,card};
    gerar.onclick=async()=>{
      const preservados=[...mantidos.querySelectorAll('input:checked')].map(x=>Number(x.value));
      const escolhas=selecionados();
      if (escolhas.length!==Number(dia.select.value)) {
        atualizarContagem();aviso('Selecione a quantidade de dias indicada.','erro');return;
      }
      gerar.disabled=true;gerar.textContent='Montando sua semana...';saida.replaceChildren();
      try {
        const res=await FitApp.api('/api/planos/previsualizar',{method:'POST',body:{dias_por_semana:Number(dia.select.value),dias_semana:escolhas,minutos_por_sessao:Number(dur.select.value),titulo:nome.value.trim()||undefined,plano_id_edicao:planoAntigo?.id||undefined,preservar_ids:preservados}});
        const p=res.preview;
        saida.append(criar('strong',`${p.titulo} — ${p.fichas.length} sessões`));
        saida.append(criar('small',`Divisão: ${p.divisao}. Nenhuma alteração foi salva ainda. ${planoAntigo?'Os agendamentos existentes não serão reprogramados automaticamente.':''}`));
        p.fichas.forEach(f=>{
          const details=criar('details');details.style.cssText='padding:9px;border:1px solid var(--borda-forte);border-radius:8px;';
          details.append(criar('summary',`${f.dia.toUpperCase()} • ${f.titulo} (${f.exercicios.length} exercícios)${f.origem_preservada?' • preservado':''}`));
          f.exercicios.forEach(ex=>details.append(criar('div',`${ex.nome_exercicio}: ${ex.series}×${ex.repeticoes} (${ex.descanso_segundos}s)`,'')));
          saida.append(details);
        });
        (p.observacoes||[]).forEach(obs=>saida.append(criar('small',obs)));
        const salvar=criar('button','Confirmar e salvar plano','fit-btn-primary');salvar.type='button';saida.append(salvar);
        salvar.onclick=async()=>{
          if(!confirm(`Salvar ${p.fichas.length} fichas em "${p.titulo}"? Os planos existentes serão mantidos.`))return;
          salvar.disabled=true;
          try {
            const resposta=await FitApp.api('/api/planos/salvar',{method:'POST',body:{preview:p,assinatura:res.assinatura}});
            aviso(resposta.mensagem,'sucesso');saida.append(criar('p',resposta.mensagem));
            salvar.remove();
            const ver=criar('a','Abrir Meus treinos');ver.href='/pages/treinos.html';saida.append(ver);
            if(typeof window.carregarDashboard==='function')window.carregarDashboard();
          } catch(err){salvar.disabled=false;aviso(err.message,'erro');}
        };
      }catch(err){aviso(err.message,'erro');saida.append(criar('p',`Não foi possível montar: ${err.message}`));}
      finally{gerar.disabled=false;gerar.textContent='Gerar outra proposta';}
    };
    // Na revisão, não cria nova proposta automaticamente: mostra primeiro as fichas reais.
  }
  document.addEventListener('DOMContentLoaded',async()=>{
    if (!caixa())return;
    const f=$('#formChat');
    f?.addEventListener('submit',event=>{
      const texto=$('#pergunta')?.value.trim()||'';
      if (!window.FitApp?.sessao?.aluno)return;
      const controle=window.kiaraControlePlano;
      const config=parametros(texto);
      const trocarFicha=/\b(?:altere|alterar|edite|editar|mude|mudar|troque|trocar|substitua|substituir)\b.{0,55}?\btreino\s*([A-G])\b/i.exec(normalizar(texto));
      if(controle?.fichasAntigas?.length && trocarFicha){
        const letra=trocarFicha[1].toUpperCase();
        const treino=controle.fichasAntigas.find(t=>new RegExp(`\\btreino\\s*${letra}\\b`,'i').test(t.titulo));
        if(treino){event.preventDefault();event.stopImmediatePropagation();
          location.href=`/index.html?editar_treino=${treino.id}`;return;}
      }
      const manter=texto.match(/(?:mant(?:er|enha|ém|em)|preserv(?:ar|e))\s+(?:o\s+)?(?:treino\s+)?([A-G])\b/i);
      const manterSelecionado=/\b(?:manter|mantenha|mantem|preservar|preserve)\b.*\b(?:esse|este|essa|esta|atual)\b/.test(normalizar(texto));
      const diasTexto=diasNoTexto(texto);
      const novoPlanoExplicito=/\b(?:novo|outro|criar|crie|gera|gerar|monte|montar)\b.*\b(?:plano|semanal|semana)\b/i.test(normalizar(texto));
      if(controle && (manter || manterSelecionado || config.dias || config.minutos || diasTexto.length) && (!reconhecer(texto) || (diasTexto.length && !novoPlanoExplicito))){
        event.preventDefault();event.stopImmediatePropagation();
        caixa().append(criar('div',texto,'msg user'));$('#pergunta').value='';
        const diasPedido=diasNoTexto(texto);
        if(diasPedido.length) controle.ajustarDias(diasPedido);
        else if(config.dias){controle.dia.value=String(config.dias);controle.dia.dispatchEvent(new Event('change'));}
        if(config.minutos)controle.dur.value=String(config.minutos);
        if(manterSelecionado && !manter){
          const escolhido=controle.fichasAntigas.find(t=>String(t.id)===qs.get('manter'))
            || (controle.fichasAntigas.length===1?controle.fichasAntigas[0]:null);
          if(escolhido){
            const input=[...controle.mantidos.querySelectorAll('input')].find(x=>Number(x.value)===escolhido.id);
            if(input)input.checked=true;
          } else aviso('Escolha qual ficha manter nas opções do plano; não vou adivinhar.','info');
        }
        if(manter){
          const letra=manter[1].toUpperCase();
          const candidato=controle.fichasAntigas.find(t=>new RegExp(`\\bTreino ${letra}\\b`,'i').test(t.titulo));
          if(candidato){const input=[...controle.mantidos.querySelectorAll('input')].find(x=>Number(x.value)===candidato.id);
            if(input)input.checked=true;
          }else aviso('Não encontrei essa ficha no plano. Selecione-a na lista.','info');
        }
        bloco('Vou aplicar essas escolhas à proposta. Revise antes de salvar.');
        controle.gerar.click();return;
      }
      if (!reconhecer(texto))return;
      event.preventDefault();event.stopImmediatePropagation();
      const u=criar('div',texto,'msg user');caixa().append(u);$('#pergunta').value='';
      abrirPlano(texto);
    },true);
    window.abrirPlanoSemanal=abrirPlano;
    if(qs.has('editar_treino')){
      const id=Number(qs.get('editar_treino'));
      try{
        const res=await FitApp.api('/api/treinos');
        const ficha=(res.treinos||[]).find(t=>t.id===id);
        if(ficha){window.kiaraTreinoEmEdicao=id;
          const linhas=(ficha.exercicios||[]).map(ex=>`- ${ex.nome_exercicio}: ${ex.series}×${ex.repeticoes} (${ex.descanso_segundos}s)`);
          // Exibe o treino vindo do banco: não é uma nova sugestão da IA.
          const original=criar('details');original.className='msg bot';original.style.cssText='max-width:100%;';
          original.append(criar('summary',`Ficha original — ${ficha.titulo} (${linhas.length} exercícios)`));
          original.append(criar('pre',linhas.join('\n')));caixa().append(original);
          bloco(`Estou editando "${ficha.titulo}". Qual exercício, série ou descanso você quer modificar? Vou te mostrar a ficha completa revisada antes de salvar. Você também pode salvar como novo treino.`);
        }
      }catch(err){aviso(err.message,'erro');}
    }else if(qs.has('revisar_plano')){
      abrirPlano('',Number(qs.get('revisar_plano')));
    }else if(qs.get('plano')==='novo')abrirPlano();
    else if(qs.get('treino')==='novo'){
      window.kiaraTreinoEmEdicao=null;
      bloco('Vamos criar uma ficha individual. Qual grupo muscular ou objetivo você quer trabalhar? Depois você poderá salvar a ficha em Meus treinos.');
    }
  });
})();
