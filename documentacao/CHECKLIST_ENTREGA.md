# FitFATEC — Checklist interno de entrega

**Atualização:** 20/11/2026. **Finalidade:** orientar a conferência da aplicação antes da apresentação. Este documento **não comprova, por si só, o cumprimento do enunciado**. A comparação final com `requisitos_ia.pdf` será feita separadamente.

| Item | Implementação ou evidência disponível | Verificação pendente |
|---|---|---|
| Cadastro, login e recuperação de senha | Rotas em `ia_academia/servidor.py` e interface web | Testar no MySQL usado na demonstração |
| Perfil e preferências | Perfil, tema, acessibilidade e personalidade da Kiara | Conferir persistência após novo login |
| Assistente Kiara | Integração com Gemini e alternativas locais para alguns fluxos | Testar respostas com a chave configurada; distinguir resposta da IA de retorno local |
| Identidade da personagem | Personalidades em `ia_academia/personalidades.py` e elementos visuais em `public/` | Verificar evidência de criação da imagem exigida pelo professor |
| Fichas individuais | Geração/edição e persistência em `treinos` e `treino_exercicios` | Criar, salvar e reabrir uma ficha |
| Planos semanais | Agrupamento de fichas em `plano_treino` | Salvar, reabrir e revisar um plano |
| Revisão com a Kiara | Ações na biblioteca de treinos e fluxo de conversa | Validar contexto da ficha e confirmação antes de salvar alterações |
| Exercícios e aquecimento | Catálogo e orientações da Kiara | Testar nível e restrições de equipamento |
| Agendamento pessoal de treinos | Calendário, data avulsa, recorrências e cancelamento de ocorrência | Testar datas e dias da semana; comparar a adaptação com o requisito do professor |
| Histórico de execução | Tabela `treino_execucoes` | Concluir um treino de teste e reabrir histórico |
| Conversa e logout | Histórico da sessão e chat novo ao entrar novamente | Confirmar que logout não reutiliza a conversa anterior |
| Fluxos conversacionais | Exemplos em `FLUXOS_CONVERSA.md` | Executar pelo menos cinco fluxos e registrar evidências reais |
| Vídeo ou apresentação | Material produzido separadamente pela equipe | Confirmar arquivo final de entrega |
| Precificação | **Documento separado, fora deste repositório** | Conferir a entrega separada pelo grupo |

## Observações

- O calendário do FitFATEC é **pessoal**: ele agenda fichas salvas, não reserva vagas em aulas de academia. A aderência ao enunciado deve ser avaliada na revisão específica do PDF.
- Os fluxos de `FLUXOS_CONVERSA.md` são **roteiros de teste**, não transcrições de conversas reais nem prova de que todas as respostas foram produzidas pelo Gemini.
- Para quem já usa o banco `fitfatec`, **não reimportar o SQL canônico** durante os testes. Preservar os dados existentes.
- Antes da apresentação, conferir o projeto com `README.md`, `como_executar/LEIA-ME.txt` e `documentacao/requisitos_ia.pdf`.
