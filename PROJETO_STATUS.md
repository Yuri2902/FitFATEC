# FitFATEC — Status do Projeto

**Projeto:** FitFATEC — Assistente Inteligente para Academia  
**Última atualização:** 01/11/2026  
**Situação:** Backend com autenticação implementado e testado com MySQL real; frontend principal operacional; banco integrado; rotas públicas mantidas (/api/risco e /api/chat sem autenticação por enquanto).

---

## 1. Objetivo e Estrutura do Projeto

### Objetivo
Sistema para academia que combina previsão de risco de desistência (machine learning com scikit-learn) com chatbot baseado em IA (Claude/Anthropic), montando treinos personalizados e ajustando o tom da conversa conforme o risco de desistência do aluno.

### Estrutura de diretórios

```
FitFATEC/
├── ia_academia/              # Backend Python + Flask + IA
│   ├── servidor.py           # Servidor Flask com rotas e autenticação
│   ├── assistente.py         # Chatbot Claude + modelo de risco de desistência
│   ├── auth_utils.py         # Utilitários de senha (hash/verificação) e validação de cadastro
│   ├── gerar_dados.py        # Gera dados fictícios de alunos
│   ├── treinar_modelo.py     # Treina modelo RandomForest de evasão
│   ├── app.py                # Interface Streamlit (alternativa)
│   ├── requirements.txt      # Dependências Python
│   ├── test_auth_utils.py    # Testes unitários de auth (6 testes)
│   ├── test_cadastro.py      # Testes de cadastro (6 testes)
│   ├── test_login.py         # Testes de login (4 testes)
│   ├── test_session.py       # Testes de sessão/logout (5 testes)
│   ├── modelo_evasao.pkl     # Modelo treinado (gerado localmente)
│   └── dados/                # Dados fictícios (gerado localmente)
├── bdd/                      # Banco de dados
│   └── bd_fitfatec.sql       # Esquema SQL (MySQL)
├── documentacao/
│   └── requisitos_ia.pdf     # Requisitos acadêmicos
├── como_executar/
│   └── LEIA-ME.txt           # Instruções de execução
├── public/
│   ├── index.html            # Frontend principal (chat + risco)
│   └── teste-auth.html       # Página provisória de teste de autenticação
└── PROJETO_STATUS.md         # Este documento
```

---

## 2. O que já foi implementado e testado

### ✅ Implementado e testado (Dev 1)

#### Autenticação — implementado e validado

| Componente | Função | Status |
|------------|--------|--------|
| `auth_utils.py` | `gerar_hash_senha()`, `verificar_senha()`, `validar_cadastro()` | ✅ 6 testes unitários OK (com mock) |
| `POST /cadastro` | Valida dados, hash de senha, insere no MySQL, impede e-mail duplicado | ✅ Código implementado + teste manual com banco real |
| `POST /login` | Busca aluno por e-mail, verifica senha, cria sessão Flask | ✅ Código implementado + teste manual com banco real |
| `POST /logout` | Limpa sessão | ✅ Código implementado + teste manual com banco real |
| `GET /api/me` | Consulta usuário autenticado, protegido por `@login_obrigatorio` | ✅ Código implementado + teste manual com banco real |
| `@login_obrigatorio` | Decorador de proteção de rotas por sessão | ✅ Implementado |
| `app.secret_key` | Via variável de ambiente `SECRET_KEY` (fallback `os.urandom(24)`) | ✅ Implementado |

**Testes automatizados (unitários com mock):** 21 testes passando
(`test_auth_utils.py`, `test_cadastro.py`, `test_login.py`, `test_session.py`).
Esses testes mockam `assistente/anthropic` e `mysql`, não exigem banco real.

**Testes manuais com banco MySQL real:** cadastro, login, sessão e logout
executados com sucesso contra o MySQL local, confirmando que as rotas de
autenticação se integram corretamente ao banco `fitfatec`.

#### Servidor Flask existente (preservado)

| Rota | Método | Função | Status |
|------|--------|--------|--------|
| `/` | GET | Serve `public/index.html` (caminho absoluto corrigido) | ✅ Existente |
| `/health` | GET | Status do servidor | ✅ Implementado |
| `/teste-auth` | GET | Serve página provisória de teste de autenticação | ✅ Implementado |
| `/api/risco` | POST | Risco de desistência (funciona sem chave da IA) | ✅ Existente |
| `/api/chat` | POST | Chatbot Claude (indisponível sem `ANTHROPIC_API_KEY`) | ✅ Existente |

#### Banco de dados — integrado e testado com MySQL real

- `bd_fitfatec.sql`: tabela `aluno` estendida com `senha_hash`, `papel`, `created_at`, `updated_at`; tabelas `frequencia`, `exercicio`, `treino` preservadas
- `data_criacao` corrigida de `DATE` para `DATETIME` (compatível com `DEFAULT CURRENT_TIMESTAMP`)
- Cadastro, login, sessão e logout testados com sucesso no banco MySQL real

#### Frontend

- `public/index.html`: frontend principal com botão "Entrar" direcionando para `/teste-auth`
- `public/teste-auth.html`: página provisória de autenticação (cadastro, login, consultar usuário, logout) com feedback visual por ação

---

## 3. Funcionalidades ainda pendentes

| Item | Status | Responsável sugerido |
|------|--------|---------------------|
| Integração do frontend Dev 4 com rotas de autenticação | Pendente | Dev 4 |
| Módulos de treino/plano de exercício (Dev 3) | Pendente | Dev 3 |
| Ativar chatbot com `ANTHROPIC_API_KEY` real | Pendente | Dev 2 |

---

## 4. Responsabilidades dos Devs 1 a 5

| Dev | Responsabilidade | Estado atual |
|-----|------------------|--------------|
| **Dev 1** | Backend e autenticação — infraestrutura Flask, rotas de auth, validação, hash de senha, sessões, conexão MySQL, testes unitários, página de teste | ✅ Implementado e testado com banco real |
| **Dev 2** | IA — integração com provedor de IA (Claude/Anthropic), funcionamento do chatbot, chave de API | ⏳ Não verificado |
| **Dev 3** | Treinos — criação e gerenciamento de planos de exercício | ⏳ Não verificado |
| **Dev 4** | Frontend — interface web, telas de acesso, apresentação de exercícios, integração com APIs (substituirá `teste-auth.html`) | ⏳ Não verificado |
| **Dev 5** | Banco de dados — tabelas, relacionamentos, persistência, execução do `bd_fitfatec.sql`, testes de integração com banco | ⏳ Não verificado |

*Não há informações confirmadas sobre o progresso dos Devs 2 a 5 neste documento.*

---

## 5. Integrações necessárias e próximos passos

1. **Dev 4**: substituir `public/teste-auth.html` pelo frontend oficial de autenticação.
2. **Dev 2**: configurar `ANTHROPIC_API_KEY` para ativar o chatbot.
3. **Dev 3**: implementar módulos de treino/plano de exercício.

---

### Classificação de status

| Categoria | Critério | Exemplos neste projeto |
|-----------|----------|------------------------|
| ✅ Testado (automatizado, com mock) | 21 testes unitários passando, mockam dependências externas | auth_utils, cadastro, login, sessão, logout, /api/me |
| ✅ Validado manualmente (MySQL real) | Cadastro, login, sessão e logout executados contra banco MySQL local | Rotas `/cadastro`, `/login`, `/logout`, `/api/me` |
| 📦 Existente sem validação | Código implementado mas não testado contra banco real | — (nenhum no momento) |
| ⏳ Pendente | Não implementado ou não integrado | Frontend oficial Dev 4, módulos Dev 3, ativação chatbot Dev 2 |

---
