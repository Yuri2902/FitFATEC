# Kiara com IA generativa como resposta principal

## O que mudou

Anteriormente, `responder_com_plano()` chamava `plano_kiara.tratar()` **antes** do Gemini. Sempre que detectava termos como treino, grupo muscular, combinar ou substituir, a função local devolvia uma lista predefinida e o Gemini só escrevia a frase de abertura. Além disso, o prompt `REGRAS` restringia todas as sugestões aos exercícios contidos no catálogo. Isso causava respostas repetitivas e poucas alternativas.

Nesta atualização, **quando a API do Gemini está funcionando**, o modelo gera a resposta inteira, considerando as mensagens anteriores e as regras de contexto. Ele pode usar conhecimento geral sobre músculos, biomecânica, exercícios, hipertrofia, recuperação, aquecimento e hábitos de treino. As opções do catálogo são referências, e não o universo total de exercícios possíveis.

O conteúdo do dataset original e suas licenças permanecem inalterados. O servidor continua sem baixar imagens ou códigos do openGym.

## O que continua igual

- Login e matrícula pela sessão Flask; o chat não pede matrícula.
- Agendamento real apenas pela interface e pelo endpoint próprio.
- Histórico da conversa enviado pelo navegador, permitindo continuar um assunto.
- `IA ativa` apenas quando houve resposta do Gemini. Se a API falha, `Modo offline`.
- Nomes dos exercícios em português quando o modelo respeita as instruções; nomes reconhecidos do dataset são traduzidos pelo pós-processamento.
- O planejador baseado em catálogo continua disponível para **modo offline**.

## Limitações

**Respostas livres não são fichas estruturadas salvas.** A Kiara mantém contexto enquanto o navegador envia o histórico, mas ainda não há persistência de treinos gerados no MySQL. A futura tela `Meus treinos` deve usar uma saída estruturada e validação antes de salvar ou editar um plano.

A IA pode cometer erros ou sugerir movimentos incompatíveis com uma condição não informada. Restrições de equipamento e lesões devem ser checadas; sugestões não substituem orientação profissional. A presença de uma sugestão na conversa **não** comprova validação clínica nem registro no catálogo local.

## Instalação

Copie `ia_academia/assistente.py` e os dois testes incluídos em `ia_academia/tests/` para o FitFATEC refatorado. Mantenha os outros arquivos existentes. Reinicie o Flask (`Ctrl+C` e `./iniciar.ps1` no PowerShell) e atualize o navegador com `Ctrl+F5`. Não precisa instalar dependências nem alterar `.env`, banco, CSS ou JavaScript.

## Testes

Na raiz do projeto no PowerShell:

```powershell
.\testar.ps1
```

No chat, teste em sequência:
1. `Explique a diferença entre bíceps braquial e braquial.`
2. `Quero um treino de pernas sem máquinas.`
3. `Pode sugerir duas alternativas para o segundo exercício?`
4. `Por que esses exercícios são adequados para meu objetivo?`
5. `Explique o que é hipertrofia e como o descanso influencia.`

As respostas devem variar conforme a pergunta; o chat não deve retornar a mesma ficha em todas elas.
