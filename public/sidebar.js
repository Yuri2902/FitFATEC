/** Navegação compartilhada do FitFATEC. Mantém os links e a autenticação existentes. */
(() => {
  "use strict";
  const aside = document.getElementById("fitSidebar");
  if (!aside) return; // A tela pública de login mantém seu cabeçalho próprio.
  const page = document.body.dataset.activePage || "home";
  const icones = {
    home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-9.5z"/>',
    perfil: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    treinos: '<path d="M6.5 6.5v11M17.5 6.5v11M3 9v6M21 9v6M6.5 12h11"/>',
    agendamentos: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M8 2v4M16 2v4M3 10h18"/>',
    menu: '<path d="m9 18 6-6-6-6"/>',
    settings: '<path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 2l-2.1 2.1a1.8 1.8 0 0 0-2-.36l-.7.3-.6 2.4H9.6L9 19l-.7-.3a1.8 1.8 0 0 0-2 .36l-2.1-2.1a1.8 1.8 0 0 0 .36-2L4.2 14l-2.2-.6v-3l2.2-.6.36-.9a1.8 1.8 0 0 0-.36-2L6.3 4.8a1.8 1.8 0 0 0 2 .36l.7-.3.6-2.4h4.8l.6 2.4.7.3a1.8 1.8 0 0 0 2-.36l2.1 2.1a1.8 1.8 0 0 0-.36 2l.3.9 2.3.6v3l-2.3.6z"/>',
  };
  const svg=(path)=>`<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`;
  const links=[
    ['home','Início','/index.html'],
    ['treinos','Meus treinos','/pages/treinos.html'],
    ['agendamentos','Agendamentos','/pages/agendamentos.html'],
    ['perfil','Meu perfil','/pages/perfil.html'],
  ];
  aside.innerHTML=`
    <div class="fit-sidebar-top">
      <a href="/index.html" class="sidebar-brand" title="FitFATEC — Início" aria-label="FitFATEC, voltar ao início"><span class="brand-fit">Fit</span><span class="brand-fatec">FATEC</span></a>
      <button id="sidebarToggle" class="sidebar-toggle" type="button" aria-label="Recolher menu" aria-expanded="true" aria-controls="sidebarNavigation" title="Recolher menu">${svg(icones.menu)}</button>
    </div>
    <nav id="sidebarNavigation" class="sidebar-navigation" aria-label="Páginas do FitFATEC">
      ${links.map(([id,text,href])=>`<a href="${href}" class="sidebar-link${page===id?' ativo':''}" ${page===id?'aria-current="page"':''} title="${text}">${svg(icones[id])}<span class="sidebar-label">${text}</span></a>`).join('')}
    </nav>
    <div class="sidebar-footer" id="sidebarUserActions">
      <a href="/pages/configuracoes.html" class="sidebar-link sidebar-settings${page==='configuracoes'?' ativo':''}" ${page==='configuracoes'?'aria-current="page"':''} title="Configurações">${svg(icones.settings)}<span class="sidebar-label">Configurações</span></a>
      <a id="navAuthBtn" href="/pages/conta.html" class="fit-btn-auth" title="Meu perfil"><span>Entrar</span></a>
    </div>`;
  const button=document.getElementById('sidebarToggle');
  const overlay=document.getElementById('sidebarBackdrop');
  const small=()=>window.matchMedia('(max-width: 740px)').matches;
  const saved=(()=>{ try{return localStorage.getItem('fit-sidebar-collapsed')==='1';}catch{return false;} })();
  const apply=(collapsed,persist)=>{
    document.body.classList.toggle('sidebar-collapsed',collapsed);
    button.setAttribute('aria-expanded',String(!collapsed));
    button.setAttribute('aria-label',collapsed?'Expandir menu':'Recolher menu');
    button.title=collapsed?'Expandir menu':'Recolher menu';
    if(persist && !small()){try{localStorage.setItem('fit-sidebar-collapsed',collapsed?'1':'0');}catch(_){}}
  };
  apply(small()?true:saved,false);
  button.addEventListener('click',()=>apply(!document.body.classList.contains('sidebar-collapsed'),true));
  overlay?.addEventListener('click',()=>apply(true,false));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&small())apply(true,false);});
  window.addEventListener('resize',()=>{
    if(small())apply(true,false);
    else apply((()=>{try{return localStorage.getItem('fit-sidebar-collapsed')==='1';}catch{return false;}})(),false);
  });
})();
