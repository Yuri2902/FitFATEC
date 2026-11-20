# FitFATEC — Fluxos de conversa e uso (roteiros de teste)

Estes exemplos descrevem **o comportamento esperado** do protótipo, e não transcrições verificadas de conversas com a Kiara. Cada fluxo deve ser testado na versão a apresentar; registrar eventuais falhas e não assumir que toda resposta é gerada pelo Gemini.

## Fluxo 1 — Primeira conversa e preferências

1. O aluno entra com sua conta.
2. Confere as informações de treino no **Meu perfil** e a personalidade da Kiara em **Configurações**.
3. Abre o chat e pede: “Quero começar com exercícios leves, sem equipamentos”.
4. Verifica se a Kiara considera o nível e as restrições informadas, sem exigir que a matrícula seja digitada na conversa.

## Fluxo 2 — Criar e guardar uma ficha individual

1. Aluno: “Monte um treino individual de pernas, sem máquinas”.
2. Kiara: apresenta exercícios com séries, repetições e descanso adequados à solicitação, quando o fluxo de geração permitir.
3. O aluno confere a proposta e **confirma o salvamento**.
4. Em **Meus treinos**, verifica se a ficha foi registrada e se seus exercícios continuam disponíveis após recarregar a página.

## Fluxo 3 — Criar e consultar um plano semanal

1. Aluno: “Quero um plano semanal com três dias de treino”.
2. Kiara e interface oferecem uma proposta de divisão semanal.
3. O aluno confere os dias e as fichas e confirma o salvamento.
4. Em **Meus treinos**, abre o plano e verifica suas fichas agrupadas.

## Fluxo 4 — Revisar uma ficha existente

1. Em **Meus treinos**, o aluno escolhe uma ficha e usa o ícone **Editar com a Kiara**.
2. Confere se a conversa recebe **a ficha correta, com os exercícios atuais**.
3. Aluno: “Troque apenas o primeiro exercício por uma alternativa sem equipamento; mantenha os demais”.
4. Verifica se a proposta preserva os outros exercícios e **não sobrescreve a ficha antes da confirmação**.
5. Confirma as alterações, se estiverem corretas, e reabre a ficha para conferir o resultado.

> **Teste obrigatório:** a passagem do contexto da ficha e a confirmação de alterações precisam ser verificadas na aplicação real.

## Fluxo 5 — Agendar uma ficha e repetir por dias escolhidos

1. Em **Agendamentos**, o aluno seleciona uma ficha **já salva**; os treinos individuais aparecem antes das fichas agrupadas por plano.
2. Escolhe a data inicial e, se desejar repetição, os dias da semana (por exemplo, terça e quinta).
3. Salva e confere as ocorrências no calendário.
4. Cancela uma ocorrência de teste e verifica se a ficha continua em **Meus treinos** e se as outras repetições permanecem.

**Nota:** não há reserva de vagas, lotação ou aulas presenciais; trata-se de um calendário pessoal de treinos.

## Fluxo 6 — Encerrar sessão sem apagar treinos

1. O aluno troca mensagens com a Kiara.
2. Atualiza a página e confirma que a conversa ainda está disponível na sessão ativa.
3. Usa **Sair**, faz login novamente e verifica que o chat abriu sem a conversa anterior.
4. Confere que perfil, fichas, planos e agendamentos continuam salvos.

## Como registrar a validação

Para cada fluxo, anotar **data, resultado (passou/falhou), evidência e erro observado**, se houver. As respostas do modelo podem variar; validar o comportamento e a persistência dos dados, não apenas a redação da resposta.
