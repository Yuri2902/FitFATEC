# FitFATEC

Aplicação web acadêmica para **criar, organizar e acompanhar treinos pessoais**, com a assistente virtual **Kiara**, biblioteca de exercícios e calendário de agendamentos.

**Tecnologias:** Python (Flask), MySQL 8+, HTML, CSS e JavaScript. A Kiara utiliza a API do Google Gemini quando configurada; sem a API, o projeto dispõe de respostas locais com recursos mais limitados. A fala da Kiara é sintetizada localmente pelo Kokoro TTS (voz brasileira `pf_dora`), sem serviço externo durante a reprodução.

## Funcionalidades

- **Conta:** cadastro, login por e-mail ou matrícula, perfil e recuperação de senha.
- **Kiara:** conversa, avaliação inicial, personalidades configuráveis, apoio à criação de treinos e voz neural local em português brasileiro.
- **Meus treinos:** fichas individuais, planos semanais, prévia antes de salvar, cores por ficha/plano, exercícios com séries, repetições e descansos, registro de conclusão e arquivamento.
- **Agendamentos:** calendário pessoal, programação de fichas e planos, repetição nos dias da semana escolhidos, cancelamento de ocorrências e interrupção de repetições.
- **Meu perfil e Configurações:** dados pessoais e preferências de treino no perfil; tema, acessibilidade, notificações e personalidade da Kiara nas configurações.

As fichas arquivadas deixam de aparecer na biblioteca, mas seus registros de execução são preservados. Cancelar um agendamento **não exclui a ficha**.

O chat inicia uma conversa nova a cada login; atualizar a página durante a mesma sessão mantém a conversa em andamento. A opção **Limpar conversa** apaga o histórico de mensagens do usuário no banco, sem apagar suas fichas ou agendamentos.

## Requisitos

- **Python 3.10 a 3.13** (o motor Kokoro ONNX ainda não oferece suporte a Python 3.14);
- **MySQL 8 ou superior** (MySQL Workbench é opcional, mas facilita a configuração);
- **Git** para clonar e atualizar o repositório;
- **Windows com PowerShell** para os scripts `.ps1` abaixo. Outros sistemas podem executar o backend manualmente.
- Conexão com a internet durante a instalação para instalar dependências e baixar os modelos de voz (aprox. 142 MB); o Gemini também exige internet durante o uso online.

## Instalação do zero (Windows)

> **Atenção:** estas instruções são para uma **instalação nova**. Se você já usa o banco `fitfatec` e tem contas, planos ou treinos salvos, consulte [Banco de dados existente](#banco-de-dados-existente) antes de executar qualquer SQL.

1. Clone o repositório ou abra a pasta baixada no VS Code. No PowerShell, entre na **raiz do projeto** (onde estão `configurar.ps1` e `iniciar.ps1`).

   ```powershell
   git clone https://github.com/Yuri2902/FitFATEC.git
   cd FitFATEC
   ```

   Se já possui a pasta, não precisa cloná-la novamente.

2. No MySQL Workbench, conecte-se ao MySQL e execute **`bdd/bd_fitfatec.sql`** apenas para preparar uma instalação nova. O arquivo cria o banco `fitfatec` e suas tabelas, sem inserir alunos fictícios.

3. Prepare o ambiente Python:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\configurar.ps1
   ```

   Esse script instala as dependências em **`ia_academia/.venv`**, baixa os arquivos do Kokoro para `ia_academia/modelos/kiara_voz/` e, se não existir, cria **`.env` na raiz** a partir de `.env.example`, com uma `SECRET_KEY` aleatória. O download dos modelos é feito apenas uma vez; um `.env` existente **não é sobrescrito**.

4. Abra o `.env` e confira suas configurações (exemplo **sem credenciais reais**):

   ```dotenv
   DB_HOST=localhost
   DB_NAME=fitfatec
   DB_USER=root
   DB_PASSWORD=SUA_SENHA_DO_MYSQL
   SECRET_KEY=SUA_CHAVE_ALEATORIA
   GEMINI_API_KEY=
   GEMINI_MODEL=gemini-3.5-flash-lite
   FLASK_DEBUG=0
   ```

   Troque os valores de exemplo pelos do seu computador. Para usar o Gemini, preencha `GEMINI_API_KEY` com sua chave; ela é opcional. A `SECRET_KEY` deve ser mantida privada e estável entre reinicializações. **Nunca publique o `.env`.**

5. Inicie o servidor, ainda na raiz:

   ```powershell
   .\iniciar.ps1
   ```

6. Abra **http://localhost:5000**. Faça seu cadastro e entre na conta. A matrícula é gerada no cadastro; não é necessário digitá-la ao criar agendamentos.

   A rota **http://localhost:5000/health** verifica se o Flask está respondendo, **não** se o MySQL está conectado.

**Nas próximas execuções:** com Python, MySQL e `.env` já configurados, normalmente basta iniciar o serviço MySQL (caso não esteja ativo) e executar ` .\iniciar.ps1 ` na raiz. Mantenha o terminal aberto enquanto utiliza o sistema; `Ctrl+C` encerra o Flask.

## Voz neural offline da Kiara

A voz utiliza o modelo [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) via [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), com a voz feminina brasileira `pf_dora`. Os pesos do modelo são Apache 2.0 e o adaptador ONNX é MIT. O modelo é executado no próprio computador pelo Flask, usando CPU/ONNX Runtime; não usa Gemini, chave de API ou serviço de voz online. Na primeira instalação, `configurar.ps1` baixa o modelo quantizado e o pacote de vozes (aprox. 142 MB). A primeira reprodução pode demorar um pouco porque o modelo é carregado na memória; as seguintes reutilizam o motor já carregado.

Para testar a independência da internet, conclua `configurar.ps1`, inicie o FitFATEC, ative a voz da Kiara e faça uma pergunta. Depois, desconecte a internet e repita o teste. **A fala continuará funcionando offline**, desde que os arquivos do modelo permaneçam na pasta `ia_academia/modelos/kiara_voz/`. As respostas geradas pelo Gemini, por outro lado, continuam dependendo da internet e da chave `GEMINI_API_KEY`; sem ela, o chat utiliza os recursos locais já existentes.

Se o projeto for levado para outro computador, execute `configurar.ps1` nesse computador antes da apresentação para instalar as dependências e baixar os pesos de voz.

## Banco de dados existente

**Não recrie o banco e não importe novamente `bdd/bd_fitfatec.sql` sobre um banco com dados.** Esse arquivo representa o esquema canônico de uma instalação nova. A instrução `CREATE TABLE IF NOT EXISTS` **não atualiza** automaticamente colunas ou relações antigas.

Se você já aplicou a refatoração do esquema em seu MySQL, não precisa executar outro SQL para apenas atualizar o README ou iniciar o sistema.

Se o banco ainda estiver em uma versão antiga, faça um **backup completo (estrutura e dados)** no MySQL Workbench antes de utilizar uma migração compatível com a sua versão. A atualização avulsa da refatoração de novembro de 2026 foi fornecida **separadamente** e não faz parte deste repositório. Ela remove estruturas antigas, portanto não deve ser executada por tentativa e erro nem reaplicada sem verificar o estado do banco. Em caso de falha, interrompa a migração e confira quais operações já foram executadas.

A versão atual **não utiliza** gestão de instrutores/administradores, registro de presença ou previsão de evasão. O campo `treinos.ativo` é necessário para o arquivamento de fichas; **não** representa desistência de alunos.

## Como usar

1. **Início:** converse com a Kiara e, no primeiro acesso, informe preferências como objetivo, experiência e frequência de treino.
2. **Gerar treino ou plano semanal:** defina as opções e revise a prévia antes de confirmar o salvamento.
3. **Meus treinos:** consulte fichas individuais e planos, selecione uma ficha para ver os exercícios e use os ícones de **lápis** (editar/revisar com a Kiara), **calendário** (agendar) e **lixeira** (arquivar, com confirmação).
4. **Agendamentos:** escolha uma ficha e data, ou programe um plano. Para repetição semanal, selecione os dias desejados; o calendário apresenta as ocorrências sem gerar compromissos infinitos no banco.
5. **Meu perfil / Configurações:** ajuste seus dados de treino e as preferências da interface e da Kiara.

A edição e a geração pela Kiara precisam ser revisadas pelo usuário antes de confirmar um novo treino ou alteração de ficha. A agenda não é automaticamente reprogramada quando o plano é revisado.

## Testes

Na raiz do projeto, depois de executar `configurar.ps1`:

```powershell
.\testar.ps1
```

Os testes automatizados incluem simulações de componentes externos e **não substituem** a verificação com seu próprio MySQL e sua chave de API.

**QA manual mínimo:** cadastrar ou entrar em uma conta existente → abrir Meus treinos → consultar fichas e planos → agendar uma ficha → verificar o calendário → conversar com a Kiara → fazer logout e login novamente e confirmar que o chat começa limpo. Para testar exclusão ou edição, prefira criar uma ficha de teste.

## Estrutura do projeto

```text
FitFATEC/
├── bdd/                  # SQL canônico para instalação nova
├── ia_academia/          # Flask, Kiara, catálogo, regras, testes e dependências
│   ├── dados/            # Catálogo de exercícios e arquivos de licença
│   ├── modelos/kiara_voz/ # Pesos locais do Kokoro (baixados na configuração)
│   ├── tests/            # Testes automatizados
│   ├── requirements.txt
│   ├── servidor.py
│   └── voz_kiara.py      # Síntese neural local da Kiara
├── public/               # Interface web (HTML, CSS, JavaScript e imagens)
│   └── pages/            # Login, perfil, configurações, treinos e agenda
├── como_executar/        # Instruções complementares de execução
├── documentacao/         # Documentos acadêmicos e atribuições do catálogo
├── .env.example          # Modelo de configuração; pode ser enviado ao Git
├── .gitignore            # Regras para ignorar segredos e arquivos locais
├── configurar.ps1        # Prepara Python, dependências e .env
├── iniciar.ps1           # Inicia o Flask
├── testar.ps1            # Executa os testes
└── README.md
```

**Arquivos locais:** `.env` (na raiz), `ia_academia/.venv` e `.git` não devem ser copiados de outro computador como parte de uma atualização do código. A pasta `.git` é criada/mantida pelo Git; `.env` contém credenciais e **não deve ser versionado**.

O projeto utiliza um catálogo de exercícios com atribuição e licença própria. Consulte `documentacao/ATRIBUICOES_EXERCICIOS.md` e os arquivos de licença/NOTICE em `ia_academia/dados/` antes de redistribuir esse conteúdo.

## Problemas comuns

| Problema | O que conferir |
| --- | --- |
| Login ou cadastro falha | MySQL iniciado, banco `fitfatec`, `DB_USER` e `DB_PASSWORD` no `.env`; reinicie o Flask após mudar o arquivo. |
| `Access denied` no MySQL | Credenciais e privilégios do usuário configurado no `.env`. |
| `ModuleNotFoundError` | Execute ` .\configurar.ps1 ` na raiz; o ambiente Python fica em `ia_academia/.venv`. |
| Voz da Kiara indisponível | Execute ` .\configurar.ps1 ` para instalar o Kokoro e baixar os arquivos de voz; confirme que `ia_academia/modelos/kiara_voz/` contém os dois arquivos do modelo. |
| PowerShell bloqueia scripts | Execute `Set-ExecutionPolicy -Scope Process Bypass` no terminal atual. |
| Página ou estilo antigo | Atualize com `Ctrl+F5`; se necessário, reinicie o Flask. |
| Kiara não usa o Gemini | Confira `GEMINI_API_KEY`, modelo configurado, internet e eventuais limites da API. |
| Tabela/coluna não encontrada | Verifique se o código e o banco seguem o mesmo esquema. Não recrie o banco nem execute migração repetidamente. |

## Observações

- O FitFATEC é um **projeto acadêmico**, não uma plataforma de reservas de academia física e nem uma orientação profissional individualizada de saúde ou educação física.
- O Flask executado por `iniciar.ps1` é um **servidor local de desenvolvimento**. Disponibilizar a aplicação publicamente exige configuração de hospedagem e banco acessível com segurança.
- Antes de um `git push`, revise `git status` e verifique se `.env`, credenciais, bancos exportados ou outros arquivos privados não estão sendo enviados.