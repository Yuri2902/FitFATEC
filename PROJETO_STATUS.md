# FitFATEC — Estado atual

## Implementado nesta versão

- Esquema MySQL canônico com `aluno`, `treinos`, `treino_exercicios`, `agendamento` e `treino_execucoes`.
- Calendário pessoal que vincula data a treino previamente salvo. Excluir agenda preserva ficha.
- Consulta de dados reais no dashboard, sem cartões de treino ou aulas fictícios.
- Salvar ficha do chat com nome opcional quando há prescrição estruturada.
- Tema claro com melhorias de contraste e indicador de modo Gemini/offline após cada resposta.
- Conclusão de treino registra execução sem apagar a ficha.
- Testes de agendamento atualizados para o novo contrato com mocks.

## Validação pendente

- Importação do SQL e execução das rotas com MySQL 8 local.
- Testes manuais de cadastro, perfil, treino, agendamento, conclusão, exclusão e duas opções de tema.
- Verificação da estratégia de primeiros acessos e nível não definido (onboarding da Kiara).
- Revisão de documentos históricos em `documentacao/`, que podem mencionar o modelo antigo de aulas.

Não existem scripts de migração/atualização. O `bdd/bd_fitfatec.sql` representa a instalação limpa.

## Planos semanais e calendário pessoal (19/11/2026)

- Plano semanal agora tem ID próprio (`plano_treino`) e agrupa fichas em `treinos.plano_id`.
- Prévia gerada com dias/duração escolhidos (1–7 dias; o gerador intercala recuperação ativa quando pertinente). Confirmação separada do salvamento.
- Nova rotina semanal pode coexistir com a anterior. Revisão de plano permite preservar fichas específicas e confirma antes de trocar as demais; compromissos existentes não mudam automaticamente.
- Repetição semanal para fichas individuais ou todas as fichas do plano. Cancelamento de uma data não remove as outras nem a ficha.
- A edição de ficha individual passa o ID da ficha e exercícios para a Kiara; salvar alterações só quando a resposta incluir ficha reconhecível, com confirmação.
- SQL atualizado para instalação limpa; scripts de migração não fazem parte do projeto.
- Testes sintáticos e do gerador executados no ambiente de edição; Flask/MySQL real precisam de QA no PC do aluno.
