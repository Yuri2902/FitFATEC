# Kiara — respostas objetivas e catálogo como referência

Atualização incremental sobre `FitFATEC_Kiara_IA_livre_academia.zip`.

- **Pediu treino:** lista direta com aproximadamente 3–5 exercícios, séries, repetições e descanso; sem introdução, encerramento ou convite automático.
- **Pediu explicação:** responde à dúvida, com poucas frases ou passos se solicitado.
- **Conversa geral:** curta, sem bloco de exercícios se o usuário não solicitou.
- **Catálogo:** consulta `biblioteca_exercicios.selecionar()` nos pedidos de treino, usando os metadados de grupo muscular e equipamento para embasar opções. É referência, não substituto do conhecimento geral do modelo.
- **Idioma:** nomes exibidos continuam em português; IDs, nomes originais e licenças continuam internos.
- **Restrições:** equipamento negado pelo aluno permanece no contexto; nunca pressupor que ele possui outro equipamento.
- **IA/offline:** o indicador anterior não é alterado. Sem Gemini a Kiara usa o catálogo offline com respostas um pouco mais curtas.

## Instalação

1. Feche o Flask (`Ctrl+C`).
2. Faça backup do arquivo `ia_academia/assistente.py`.
3. Extraia este ZIP na raiz que contém `FitFATEC`, substituindo apenas os arquivos coincidentes dentro do projeto.
4. Na pasta raiz do projeto: ` .\testar.ps1 ` e depois ` .\iniciar.ps1 `.
5. Atualize o navegador, limpe a conversa e teste pedidos de treino, explicação e pergunta geral.

**Importante:** o formato do Gemini é orientado por instruções, não uma garantia infalível. Este ajuste não cria persistência de fichas nem altera banco, login, agendamentos, HTML ou JS. O catálogo original fornece metadados, não instruções de execução completas nem avaliações profissionais.
