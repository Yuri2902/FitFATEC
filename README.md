# FitFATEC — Kiara e calendário pessoal de treinos

Projeto acadêmico em **Python/Flask, MySQL 8, HTML/CSS/JavaScript**. A Kiara pode usar Google Gemini ou respostas locais quando a IA estiver indisponível.

## Atualização: Configurações, agendamento simplificado e exclusão segura (20/11/2026)

**Atualização de uma instalação com o menu lateral já funcionando (sem perder dados):**

1. Pare o Flask com `Ctrl+C` e faça backup da pasta e do banco `fitfatec`.
2. Extraia esta versão e substitua os arquivos do projeto (ou trabalhe em uma pasta nova).
3. Preserve `.env` e `.venv` atuais. Se usar outra pasta, copie ambos do projeto atual.
4. **Não execute `DROP`, `ALTER` ou importe o SQL.** O esquema `bdd/bd_fitfatec.sql` é idêntico ao da versão anterior com menu lateral.
5. Inicie com `.\iniciar.ps1` e atualize o Firefox com `Ctrl+F5`. Não precisa sair da conta nem limpar a sessão.

### Alterações desta versão

- **Menu:** Meu perfil continua na navegação principal. Configurações fica no rodapé, acima de Sair. Com o menu recolhido, o nome do aluno não duplica o ícone de perfil.
- **Meu perfil:** dados pessoais e de treinamento. Preferências de personalidade, tema, notificações e acessibilidade agora estão em **Configurações**. Ambos usam as rotas originais para persistir no MySQL.
- **Programar treino:** escolha treino e data. O horário e as observações foram retirados do formulário; o banco mantém essas colunas para compatibilidade. Se marcar repetição, selecione explicitamente os dias da semana (de segunda a domingo). Os dias são regras recorrentes, não milhares de linhas geradas antecipadamente.
- **Programar plano inteiro:** permanece na mesma página, agora recolhido para reduzir a poluição visual.
- **Meus treinos:** pode programar a repetição de um treino individual, arquivar uma ficha ou arquivar um plano completo. A remoção de um plano retira todas suas fichas da biblioteca.
- **Arquivamento:** exclusão da biblioteca faz `ativo=0` (não apaga exercícios ou registros de execuções já concluídas). Se houver compromissos futuros, a API recusa primeiro e pede uma segunda confirmação, que cancela os agendamentos futuros e as regras de repetição antes de arquivar. Ocorrências históricas armazenadas somente como exceções da regra recorrente deixam de ser exibidas quando a regra é cancelada, mas registros em `treino_execucoes` continuam no banco.
- **Revisão com a Kiara:** ao editar ficha, mostra a ficha atual do banco; ao revisar plano, mostra todas as fichas originais e permite abrir uma ficha individualmente ou preservar fichas selecionadas e gerar outra proposta. O treino só é alterado após o usuário salvar. O gerador de prévia e o Gemini continuam componentes diferentes.

**Verificações locais realizadas:** sintaxe Python e JavaScript, estrutura de HTML e igualdade do SQL. Esta execução não teve Flask/MySQL disponível para testes integrados; **valide antes do `git push`**. O teste de navegação em navegador automático não foi possível neste ambiente.

**Ordem sugerida para QA:** Configurações → salvar tema e personalidade → Meu perfil sem preferências → agendar treino individual com repetição terça/quinta → navegar no calendário → excluir ficha (testar com e sem agendamento) → excluir plano → abrir uma ficha pelo botão Editar com a Kiara e conferir se os exercícios originais aparecem.

---

## Atualização da interface com menu lateral

Esta versão mantém o **mesmo SQL, tabelas e dados** da versão anterior `FitFATEC_correcoes_dias_e_chat.zip`.
Para atualizar o projeto existente:

1. Encerre o Flask (`Ctrl+C`) e faça uma cópia da pasta do projeto.
2. Substitua os arquivos do projeto pela versão nova, **preservando o `.env` e a `.venv`**.
3. **Não execute nenhum SQL, DROP, ALTER ou importação no Workbench.** Nenhuma alteração do MySQL é necessária nesta atualização.
4. Execute `./iniciar.ps1` no PowerShell (ou `.\iniciar.ps1` no Windows) e atualize o navegador com `Ctrl+F5`.
5. Não precisa criar outra conta, sair ou limpar a sessão.

### Navegação e Chat

- O menu principal agora fica **na lateral esquerda**, com opção de recolher para mostrar apenas os ícones. O estado é lembrado no navegador em desktops. Na tela pequena o menu abre sobre a página, e pode ser fechado pelo botão, clique fora ou tecla Escape.
- A tela **Início** dá prioridade à Kiara: matrícula, estatísticas e cartões duplicados foram retirados da Home, mas o acesso a perfil, fichas e calendário continua disponível no menu.
- Apenas **Gerar treino** e **Gerar plano semanal** continuam como atalhos de criação abaixo da conversa. Há links discretos para **Meus treinos** e **Agendamentos** no cabeçalho da Kiara.
- **Limpar conversa** pede confirmação, remove as mensagens desse usuário em `chat_mensagens` e limpa o contexto da sessão; **não exclui** planos, treinos, perfil ou agendamentos. A exclusão do histórico de mensagens é permanente.
- **Meu perfil, Meus treinos e Agendamentos** preservam formulários e operações existentes; só a navegação e os ajustes responsivos foram alterados.

**Verificações:** sintaxe JavaScript/Python e layout das quatro telas em cinco larguras. O comportamento visual foi inspecionado em navegador sem servidor; a integração de banco e API precisa ser conferida no seu MySQL real.

## Instalação limpa

1. Instale Python 3.10+ e MySQL 8.
2. Clone o repositório e abra a pasta `FitFATEC` no VS Code.
3. No Workbench, crie o banco executando **`bdd/bd_fitfatec.sql`**. É a única estrutura oficial; não há scripts de migração.
4. Execute `configurar.ps1` para preparar `.venv` e `.env`, ou siga `como_executar/LEIA-ME.txt`.
5. Configure `DB_USER`, `DB_PASSWORD`, `SECRET_KEY` e opcionalmente `GEMINI_API_KEY` no `.env`. **Nunca publique esse arquivo.**
6. Execute `iniciar.ps1` e abra `http://localhost:5000`.

Se o PowerShell bloquear scripts, use **apenas no terminal atual**:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\configurar.ps1
.\iniciar.ps1
```

### Já existe um banco de teste com a estrutura antiga?

**Faça backup antes de qualquer exclusão.** Como o novo modelo de dados não é compatível com os antigos `treino`/`grade_hrarios`, não execute o SQL novo sobre tabelas antigas. Se **todos os dados forem descartáveis**, no Workbench rode `DROP DATABASE fitfatec;` e execute `bdd/bd_fitfatec.sql` para criar um banco limpo. Isso apaga todos os cadastros, conversas e agendamentos anteriores. Se os dados não forem descartáveis, não apague: será necessária uma migração planejada separadamente.

## Fluxos principais

- **Meus treinos:** planos semanais são blocos com fichas por dia. Fichas individuais ficam em seção separada. Uma ficha preservada durante uma revisão mantém os exercícios originais; só após confirmar a prévia o plano é atualizado.
- **Salvar este treino:** surge apenas em respostas com exercícios e prescrições reconhecíveis. O aluno pode dar um nome à ficha antes de salvar.
- **Agendamentos:** escolha uma ficha e uma data. Marque **Repetir semanalmente** para criar uma regra sem data final ou selecione um plano inteiro. É possível excluir só uma ocorrência ou parar a repetição; nenhuma dessas ações apaga a ficha. O sistema exibe ocorrências recorrentes dentro de uma janela de calendário, sem criar infinitas linhas no banco.
- **Plano semanal dinâmico:** no chat, peça "plano semanal de 4 dias, 30 minutos", ou clique em **Gerar com a Kiara**. A prévia mostra cada sessão e seus exercícios. Mude dias/minutos e clique **Confirmar e salvar** somente quando concordar. Gerar um plano novo não substitui os anteriores.
- **Revisar plano:** em Meus treinos, use "Revisar plano com a Kiara". Escolha dias e duração, marque as fichas a preservar, confira a prévia e confirme. Também pode abrir uma ficha e escolher "Reorganizar plano mantendo esta ficha". Agendamentos antigos não são reprogramados automaticamente; fichas antigas com compromissos são mantidas como individuais.
- **Editar ficha:** abra uma ficha e clique "Editar esta ficha com a Kiara". Ela recebe os exercícios atuais como contexto. Uma resposta completa com séries/repetições permite salvar mudanças na mesma ficha ou como treino individual novo. O resultado do Gemini exige revisão humana antes de confirmar.
- **Início:** a Kiara ocupa a área principal. O perfil, as fichas e os compromissos são consultados em suas respectivas páginas.
- **Kiara:** o indicador mostra “IA ativa” se o Gemini respondeu, “IA offline” quando usa a alternativa local; antes da primeira resposta, “IA: aguardando”. A personalidade pode ser alterada em **Configurações**.
- **Tema:** as preferências de claro/escuro são salvas no banco e aplicadas no navegador.

### Cores de treinos e visualização semanal

- Cada **plano semanal** possui uma cor própria, editável em **Meus treinos → Cor do plano**. Todas as fichas do mesmo plano compartilham essa cor.
- Cada **treino individual** possui sua própria cor editável. Escolher a cor de um treino não modifica outro plano ou outra ficha.
- O **calendário** mostra marcadores coloridos para cada ocorrência, identificando as fichas A/B/C quando possível. Em um dia com vários treinos, exibe múltiplos marcadores.
- **Meus agendamentos** lista apenas a semana selecionada; as setas navegam entre semanas. Repetições futuras continuam visíveis no calendário sem criar compromissos infinitos no banco.
- O formulário de plano da Kiara usa campos de **Frequência** e **Duração** alinhados; o nome do plano tem rótulo próprio.

**Atualizando somente a versão anterior de planos semanais dinâmicos (sem perder dados):** depois do backup, execute **uma única vez** no Workbench, antes de reiniciar o Flask:

```sql
ALTER TABLE fitfatec.plano_treino ADD COLUMN cor_hex CHAR(7) NOT NULL DEFAULT '#F97316';
ALTER TABLE fitfatec.treinos ADD COLUMN cor_hex CHAR(7) NOT NULL DEFAULT '#06B6D4';
```

Esses comandos são necessários **somente se as colunas ainda não existirem**. Não execute novamente depois de aplicá-los. Se estiver criando um banco novo, **não execute esses ALTERs**: o `bdd/bd_fitfatec.sql` já contém os campos. Nenhum script de migração é entregue no repositório.

## Testes

```powershell
.\testar.ps1
```

A suíte automatizada usa simulações em vários casos: **não substitui os testes de integração com MySQL real.** Confirme manualmente: cadastrar → gerar prévia de 3 dias → salvar → rever 4 dias preservando ficha B → conferir agrupamento → repetir plano na agenda → cancelar só uma data → conferir que a ficha e demais datas continuam. Também teste uma ficha individual recorrente.

## Observações

Este projeto não representa uma academia física: não possui reserva de vagas, professores ou horários de aulas. A IA auxilia no planejamento e não substitui orientações de profissionais de saúde e educação física. Os dados de risco de desistência são sintéticos e experimentais. O Streamlit em `ia_academia/app.py` é uma alternativa legada; o servidor principal é o Flask em `ia_academia/servidor.py`.


### Primeiro acesso e perfil de treino

No cadastro novo, `objetivo`, `nivel` e `treinos_semana` ficam vazios.
No primeiro contato, a Kiara oferece **botões no próprio chat** para experiência,
objetivo, dias por semana, duração da sessão e personalidade. O aluno também
pode responder com texto livre. Ao final, recebe um resumo e pode editar cada
resposta, confirmar ou pular. **Somente confirmar grava no banco.**

A duração escolhida é aplicada ao gerador quando não houver uma opção específica
na tela de treinos. As personalidades alteram o tom da conversa, não as regras
nem a segurança do treino. Para escolher **Sem filtro (+18)**, é obrigatório
informar uma data de nascimento válida que confirme a maioridade; a idade é
verificada novamente pelo backend antes de salvar. O modo pode usar gírias e
palavrões bem-humorados, mas não humilhação real ou ataques discriminatórios.

O script `bdd/bd_fitfatec.sql` representa uma **instalação nova** e agora inclui
`aluno.minutos_por_sessao`. Ele não altera bancos existentes automaticamente.
Para recriar um banco descartável, faça backup antes e depois importe o SQL
oficial. Não há script de migração. A avaliação pode ser editada depois em
**Meu perfil** (objetivo, nível e frequência); a personalidade fica em **Configurações**; a duração também
pode ser escolhida diretamente ao gerar o treino.

### Geração semanal com dias escolhidos

Na Home, **Gerar treino** cria uma ficha individual; **Gerar plano semanal** abre
uma prévia de 1 a 7 dias, com duração e dias específicos selecionáveis (por exemplo,
terça e quinta). A prévia só entra no MySQL após **Confirmar e salvar plano**.
No chat, pedidos como "monta um plano semanal para terça e quinta" abrem o mesmo
formulário; a edição de uma ficha individual não é usada como destino desse plano.
Para reorganizar um plano salvo, use **Revisar plano com a Kiara**, marque as fichas
que devem permanecer e confira a prévia. A agenda não é alterada automaticamente.
A escolha de cores continua livre e funciona no seletor nativo, agora circular.
Estas alterações de frontend e backend não modificam o esquema do banco existente.

### Interface de Meus treinos — atualização visual (20/11/2026)

- Os treinos continuam separados em planos semanais e fichas individuais.
- Ícones de lápis, calendário e lixeira abrem respectivamente a edição com a Kiara, a programação da ficha ou do plano e a remoção com confirmação.
- Para criar novos treinos, use **+ Criar treino** (plano, individual ou manual; acesso à biblioteca).
- A cor é editável por plano semanal ou por ficha individual, como antes.
- A tabela de exercícios permanece na área de detalhes; o botão de conclusão registra a execução e mantém a ficha salva.
- Esta atualização modifica apenas `public/pages/treinos.html`: não há mudança de SQL, API ou dependências. Preserve `.env` e `.venv`.
