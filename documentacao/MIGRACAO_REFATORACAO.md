# Como adotar esta refatoração sem perder trabalho do grupo

1. Faça **backup** da pasta FitFATEC que contém `.git/`, `.env` e qualquer arquivo local não enviado no ZIP.
2. Extraia o novo ZIP em uma **outra pasta** e abra lado a lado no VS Code; os arquivos de produção, banco e regras de IA devem ser comparados antes de incorporar.
3. Ao levar as mudanças para o seu repositório atual, mantenha seu `.git/` original e **não substitua `.env`**. Não copie `.venv/`, `venv/` ou caches.
4. Os testes antigos `ia_academia/test_*.py` foram **movidos** para `ia_academia/tests/`: apague/mova as versões antigas se fizer a integração manual, para evitar duplicados.
5. `public/teste-auth.html` foi movida para `public/pages/conta.html`; o servidor continua atendendo `/teste-auth` e agora também `/conta`. Exclua o HTML antigo depois de validar `/conta`.
6. `ia_academia/ia_academia_guia.md` foi arquivado em `documentacao/historico/guia_antigo_claude_streamlit.md`; retire o original para não manter dois tutoriais conflitantes.
7. Compare `servidor.py`, `assistente.py`, `traduzir_exercicios.py` e `public/index.html` antes de aplicar sobre commits posteriores do grupo. Esta revisão partiu do **ZIP recebido em 13/11/2026**, não do Git remoto.
8. Reinstale dependências em ambiente virtual próprio. Não importe novamente `bdd/bd_fitfatec.sql` em um banco com dados sem planejar a migração e fazer backup.
9. Execute os testes e confira manualmente login, matrícula, agendamento, classificação do risco, conversa e botão Limpar conversa.
10. Faça commit apenas após validar no seu computador. A pasta `.git/` não foi incluída de propósito.

## Arquivos que não foram apagados

- `ia_academia/app.py`: é alternativa Streamlit antiga, não usada pelo Flask principal. O grupo pode decidir removê-la depois da avaliação.
- `ia_academia/modelo_evasao.pkl` e `ia_academia/dados/alunos.csv`: mantidos no ZIP para facilitar a demonstração; ignorados para próximos commits.
- `public/CSS.css`, `public/kiara-ajustes.css`: mantidos separados para reduzir risco de regressão; consolidação de CSS pode ser feita depois de testes visuais.

## Validação realizada nesta revisão

- `compileall` no código Python: **passou**.
- `node --check` em JS e scripts inline da interface: **passou**.
- 46 testes com dependências Python disponíveis em seis suítes de catálogo, traduções, plano e assistente: **passaram**.
- Testes Flask/MySQL (`test_cadastro`, `test_login`, `test_session`, `test_agendamento`, `test_chat_sessao`, `test_auth_utils`) **não puderam ser executados aqui**, pois Flask, Werkzeug e mysql-connector-python não estavam instalados e a instalação de pacotes estava indisponível. Execute `.\testar.ps1` na máquina local.
- API Gemini real, MySQL real e browser com servidor Flask: **não testados nesta execução**.
- Foi observado aviso `InconsistentVersionWarning` ao carregar `modelo_evasao.pkl` com scikit-learn local diferente da versão de treinamento. Caso apareça no seu ambiente, regenere o modelo com os scripts e a versão que você instalou — só com dados sintéticos, e nunca a partir de arquivos não confiáveis.
