# FitFATEC — Documento de projeto

**Revisão:** 13/11/2026 · **Base:** versão fornecida pelo grupo no ZIP do mesmo dia.  
**Disciplina:** Engenharia de Software II — DSM · **Escopo:** protótipo acadêmico.

## 1. Descrição e objetivo

O FitFATEC é um protótipo de academia com uma assistente virtual chamada **Kiara**. A interface oferece conversa em português, série de exercícios conforme objetivo/nível, aquecimentos, orientação sobre treino principal/secundário e agendamento de aulas para aluno autenticado. Inclui um classificador experimental de evasão construído sobre registros sintéticos.

## 2. Persona digital

- **Nome:** Kiara.
- **Representação atual no produto:** mascote de onça-pintada simpática, ícone SVG em `public/img/kiara.svg`.
- **Identidade conceitual no prompt:** personalidade jovem adulta (~25 anos), uniforme laranja e preto, identidade visual relacionada ao FitFATEC.
- **Tom/estilo:** amigável, objetivo, motivador, português brasileiro, mensagens curtas e perguntas claras.
- **Atendimento:** pela interface web, em qualquer horário (depende de servidor ativo).
- **Acessibilidade:** ajustes de interface e linguagem devem continuar sendo avaliados; não há implementação de recursos completos de acessibilidade documentada nesta versão.

**Pendência para aprovação do grupo/professor:** o enunciado pede traços antropomórficos (pele, cabelo, olhos, formato de rosto). A persona adotada é uma **onça-mascote**; o grupo deve verificar se essa interpretação satisfaz a avaliação. Também não há prova de que o SVG atual foi **gerado por IA**, como o enunciado exige. Não marcar esses itens como entregues sem validar.

## 3. Tecnologias

| Camada | Tecnologia |
|---|---|
| Frontend | HTML/CSS/JavaScript estáticos em `public/` |
| Backend / API | Python 3.10+ e Flask |
| Autenticação | Sessão Flask + hash de senha Werkzeug |
| Dados relacionais | MySQL 8 (`bdd/bd_fitfatec.sql`) |
| IA generativa | API Gemini via `google-genai` (opcional) |
| Exercícios | Catálogo próprio + metadados ExerciseDB MIT; traduções locais por ID |
| Classificação experimental | scikit-learn / RandomForest + joblib + pandas |
| Interface alternativa/legado | Streamlit, opcional (`app.py`) |

## 4. Arquitetura e fluxo

```text
Navegador (public/index.html / public/pages/conta.html)
        | HTTP/JSON, sessão cookie Flask
        v
ia_academia/servidor.py
        |-- auth_utils.py ---> MySQL (aluno, agendamento)
        |-- assistente.py ---> Gemini (se configurado)
        |        |-- plano_kiara.py
        |        |-- biblioteca_exercicios.py + traduções / IDs
        |        `-- modelo_evasao.pkl (modelo artificial)
        `-- catalogo.py (séries demonstrativas)
```

**Segurança:** o agendamento usa `id_aluno` da sessão de login; uma matrícula fornecida pelo cliente não autoriza marcar aulas para terceiros. O arquivo `.env` é local e ignorado pelo Git. Em um sistema publicado seria necessário revisar CSRF, cookies seguros, autenticação e disponibilidade/conflitos de agendamento.

**Estado dos planos:** a Kiara mantém uma versão do treino na sessão Flask; **não existe persistência de planos em MySQL nesta entrega**. A tabela `treino` existe, mas a interface ainda não salva as sugestões nela.

## 5. Rotas principais (existentes)

- `GET /` — página inicial; `GET /conta` — cadastro/login; `GET /teste-auth` — alias legado.
- `GET /health` — saúde do servidor Flask.
- `POST /cadastro`, `POST /login`, `POST /logout`, `GET /api/me` — autenticação e sessão.
- `POST /api/chat`, `POST /api/chat/limpar` — conversa e limpeza do estado do plano.
- `POST /api/risco`, `GET /api/serie` — risco experimental e série simples.
- `GET /api/horarios`, `POST /api/agendar` — disponibilidade e agendamento.

## 6. Restrições, ética e propriedade intelectual

- Não utilizar risco sintético para tomar decisões sobre alunos reais.
- Não oferecer prescrições médicas nem garantir que todo exercício serve para qualquer aluno; consultar profissional de educação física para individualização.
- Catálogo de exercícios ampliado a partir de metadados licenciados MIT; preservar avisos de autoria da fonte e **não copiar imagens, GIFs ou conteúdo próprio do openGym**. Detalhes em `ATRIBUICOES_EXERCICIOS.md` e `TRADUCOES_E_LICENCA.md`.
- O modelo generativo é fornecido por terceiro; Kiara é a identidade e integração do FitFATEC, não um modelo fundamental treinado pelo grupo.

## 7. Entregáveis

A situação por requisito, com evidência e pendências, está em `CHECKLIST_ENTREGA.md`; os fluxos de diálogo demonstrativos estão em `FLUXOS_CONVERSA.md`; premissas de precificação estão em `PRECIFICACAO.md`. Consulte também `PROJETO_STATUS.md` para riscos e testes.
