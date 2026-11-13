# FitFATEC — Status do projeto

**Atualizado:** 13/11/2026 (reorganização sobre o ZIP recebido).  
**Estado:** protótipo Flask/HTML funcional segundo os testes manuais apresentados; nesta revisão houve reorganização de arquivos e atualização de documentação, **sem migração do banco ou troca do algoritmo da IA**.

## Funcionalidades encontradas no código

| Recurso | Estado no código | Validação |
|---|---|---|
| Cadastro, login, sessão e logout | Implementado (Flask + MySQL) | Testes automatizados com mocks; MySQL real não validado neste ambiente |
| Matrícula gerada no cadastro e usada pela sessão | Implementado | Verificar manualmente com login real |
| Kiara com Gemini e fallback offline | Implementado | Gemini real depende de chave/serviço externo; testes de lógica com mocks |
| Catálogo de exercícios MIT | JSON local + avisos de licença | 1.324 registros no arquivo de origem; integridade técnica/nomes requerem revisão |
| Nomes de exercícios em português | Arquivo local por ID + tradutor Gemini opcional | Parcial: tradução automática do restante exige execução e revisão |
| Plano temporário da Kiara | `plano_kiara.py`, estado na sessão | Não há salvamento de plano em MySQL |
| Chat com campo fixo | CSS e `visual.js` | Capturas de teste; responsividade deve continuar sendo verificada |
| Agendar aula | Formulário + rotas + tabela MySQL | Testes de rota com mocks; testar com MySQL real |
| Risco de desistência | Modelo RandomForest treinado com dados sintéticos | Apenas demonstração; não representa previsão clínica/comercial confiável |
| Página de acesso | `public/pages/conta.html`, rotas `/conta` e `/teste-auth` | Tela provisória; redesenho UX pendente |
| Testes Python | `ia_academia/tests/`, comando `testar.ps1` | Consulte registro de validação da entrega; não afirmar teste de API real |

## Refatoração feita nesta revisão

- Testes `test_*.py` agrupados em `ia_academia/tests/`; mantidos os nomes dos testes e a suíte `unittest`.
- Página provisória de login organizada em `public/pages/conta.html`, preservando URL antiga `/teste-auth`.
- `visual.js` (específico do chat) removido da página de conta para evitar erro por elementos inexistentes.
- Carregamento centralizado de `.env` via `configuracao.py`/python-dotenv; variáveis já presentes no terminal prevalecem.
- Script de geração de dados e treinamento usando caminhos relativos ao código, não ao diretório atual.
- `requirements.txt` corrigido, Streamlit como dependência opcional, comandos PowerShell `configurar.ps1`, `iniciar.ps1`, `testar.ps1`.
- Guia Claude/Streamlit antigo arquivado sob `documentacao/historico/` para evitar seguir instruções obsoletas.
- Documentação de projeto, fluxos, checklist do enunciado e premissas de precificação agora incluídas.
- ZIP de entrega não leva `.git/`, `venv/` nem caches do Python; preserve o repositório Git local do grupo.

## Pendências prioritárias

1. **Testar em Windows + MySQL real**: login, cadastro, matrícula, horários, agendamento e sessão depois de aplicar a revisão.
2. **Concluir as traduções** do catálogo e validar movimentos ambíguos; manter aviso MIT.
3. **Persistir planos de treino em MySQL** para a futura página “Meus treinos”.
4. **Revisar UX da tela de conta** e criar telas de perfil/treinos/agenda; a página atual é provisória.
5. **Validar requisitos da persona**: desenho gerado por IA e adequação da mascote aos atributos físicos pedidos pelo enunciado.
6. **Gravar demonstração** e fechar estimativa numérica de precificação.
7. **Auditar segurança antes de publicar na internet**: CSRF, cookies, autorização de operações, concorrência de horários, políticas de privacidade, chaves/segredos.

## Material de referência

- `README.md` — início rápido.
- `como_executar/LEIA-ME.txt` — instalação e erros comuns.
- `documentacao/requisitos_ia.pdf` — enunciado original.
- `documentacao/CHECKLIST_ENTREGA.md` — lacunas e evidências reais.
- `documentacao/DOCUMENTO_PROJETO.md`, `FLUXOS_CONVERSA.md`, `PRECIFICACAO.md` — entregáveis textuais.
- `documentacao/ATRIBUICOES_EXERCICIOS.md` e `TRADUCOES_E_LICENCA.md` — licenças.

**Nota:** não se removeu nenhum módulo de negócio nesta revisão. A interface Streamlit foi mantida como protótipo opcional; os arquivos gerados localmente do modelo permanecem no pacote apenas para facilitar a demonstração, mas estão ignorados por `.gitignore`.
