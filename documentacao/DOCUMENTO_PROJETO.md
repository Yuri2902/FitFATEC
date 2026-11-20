# FitFATEC — Documento de projeto

**Revisão:** 20/11/2026. **Contexto:** protótipo acadêmico de planejamento de treinos pessoais.

## Visão geral

O FitFATEC oferece cadastro e autenticação de alunos, configuração de perfil,
assistente Kiara (Gemini, com modo offline), geração de fichas e planos semanais,
biblioteca pessoal de treinos, agendamentos por data e repetição, registro de execução
e histórico da conversa. Não gerencia frequência presencial, instrutores ou desistência.

## Tecnologias

- Frontend: HTML/CSS/JavaScript em `public/`
- Backend: Flask (`ia_academia/servidor.py`), sessão e hash de senha Werkzeug
- Banco: MySQL 8 (`bdd/bd_fitfatec.sql`)
- IA generativa: Gemini via `google-genai` (opcional, usa catálogo local na indisponibilidade)
- Biblioteca de exercícios: metadados ExerciseDB licenciados MIT, traduções locais

## Principais fluxos

1. Cadastro/login -> avaliação inicial/edição do perfil e das preferências.
2. Conversa com a Kiara -> sugestão, revisão e confirmação de treino.
3. Meus treinos -> fichas individuais e agrupadas em planos semanais; fichas arquivadas
   não desaparecem do histórico de execução.
4. Agendamentos -> data individual, regras semanais e exceções de ocorrência.
5. Logout -> encerra a conversa atual; novo login começa com chat limpo.

## Limitações e segurança

A IA não substitui professor de educação física ou avaliação de saúde. Publicação
na Internet exige revisão de CSRF, cookies seguros, autenticação, backups e acesso
aos dados pessoais. Manter `GEMINI_API_KEY` e credenciais do banco fora do Git.

Consulte `README.md`, `CHECKLIST_ENTREGA.md`, `ATRIBUICOES_EXERCICIOS.md`
e `TRADUCOES_E_LICENCA.md` para procedimentos, requisitos e atribuição das fontes.
