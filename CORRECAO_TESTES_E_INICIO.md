# Correção pontual da refatoração

Esta atualização corrige **os testes que contaminavam o carregamento de módulos** e um teste de chat que chamava uma função antiga. Não altera a lógica da Kiara, o banco nem as credenciais.

## Aplicação

1. Faça backup da pasta atual.
2. Extraia o conteúdo do ZIP por cima da pasta `FitFATEC` **do projeto refatorado**, mantendo a estrutura.
3. Não apague `.env`, `ia_academia/.venv` nem seus dados locais.
4. Na raiz, execute `./testar.ps1` (no PowerShell use `.\testar.ps1`). Ao final, procure `OK` e `TESTES APROVADOS`.
5. Em outro terminal, execute `.\iniciar.ps1` e **deixe o terminal aberto**; só abra `http://localhost:5000` quando aparecer `Running on`.

Se o servidor voltar imediatamente ao prompt ou mostrar `Traceback`, o Flask não iniciou: copie a mensagem completa do terminal. A tela do navegador apenas revela que não houve conexão, não a causa.

## Validação

A sintaxe dos arquivos Python foi verificada. Como Flask e mysql-connector-python não estão disponíveis neste ambiente de execução, a suíte completa que depende desses pacotes deve ser executada no Windows do usuário.
