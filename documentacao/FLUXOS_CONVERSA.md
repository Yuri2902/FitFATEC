# FitFATEC — Fluxos de conversação (exemplos para documentação)

**Nota:** estes seis roteiros representam o comportamento esperado do produto; não são transcrições literais de testes no Gemini. Para validar, executar na interface e registrar as evidências da versão apresentada.

## Fluxo 1 — Pedir treino por grupo muscular

1. Aluno autenticado: "Quero um treino de bíceps sem halteres."
2. Kiara: identifica bíceps, aplica restrição de equipamento e oferece opções compatíveis do catálogo em português.
3. Aluno: "Qual o primeiro exercício?"
4. Kiara: explica o exercício selecionado; quando necessário, orienta obter ajuda profissional.

## Fluxo 2 — Montar treino combinado

1. Aluno: "Quero um treino de bíceps sem halteres."
2. Kiara: oferece exercícios compatíveis.
3. Aluno: "Agora quero pernas sem máquinas."
4. Kiara: monta parte de pernas respeitando as novas limitações.
5. Aluno: "Combine os dois."
6. Kiara: recupera os grupos, descarta exercícios com equipamento proibido, evita duplicados e informa limitações.

## Fluxo 3 — Substituir exercício mantendo a série

1. Aluno: "Substitua um exercício sem repetir os outros."
2. Kiara: seleciona alternativa do catálogo e preserva os demais itens do plano temporário.
3. Aluno: "Mostre o treino completo atualizado."
4. Kiara: retorna o conjunto atual com a substituição registrada na sessão.

## Fluxo 4 — Aquecimento

1. Aluno: "Que aquecimento posso fazer antes do treino?"
2. Kiara: explica opções de aquecimento segundo nível e objetivo, indicando que a proposta é demonstrativa.
3. Aluno: "Preciso de algo mais leve."
4. Kiara: adapta a explicação sem exigir matrícula na conversa.

## Fluxo 5 — Treino principal, secundário e nível

1. Aluno: "Qual o meu nível de condicionamento?"
2. Kiara: explica os critérios aproximados baseados nos dados informados, sem tratar como avaliação clínica.
3. Aluno: "Qual a diferença entre treino principal e secundário?"
4. Kiara: explica a divisão e oferece exemplos.

## Fluxo 6 — Agendar horário

1. Aluno entra com e-mail e senha na página `/conta`.
2. Aluno: "Quero agendar uma aula."
3. Kiara: orienta a usar o botão **Agendar aula**.
4. Aluno escolhe data, horário e modalidade; a matrícula vem automaticamente da sessão.
5. Servidor verifica capacidade e grava agendamento no MySQL; a tela informa sucesso ou motivo de recusa.

## Critérios de qualidade da demonstração

Verificar: nomes de exercícios só em pt-BR, restrições preservadas, contexto do plano, indicadores IA/offline coerentes, nenhuma solicitação de matrícula no chat, agendamento autenticado e ausência de duplicação após substituições. Faça testes manuais e registre o que falhou, em vez de afirmar conformidade por causa do roteiro.
