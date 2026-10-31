# FitFATEC — Status do Dev 1

**Responsável:** Dev 1 — Infraestrutura e autenticação  
**Última atualização:** 31/10/2026  
**Situação:** Backend inicial funcionando; autenticação pendente.

## 1. O que já foi realizado

- Ambiente Python configurado e testado.
- Dependências organizadas em `requirements.txt`.
- Servidor Flask funcionando localmente.
- Correção do caminho para `public/index.html`.
- Ajuste para iniciar sem a chave da API Anthropic.
- Geração de dados fictícios e treinamento do modelo de previsão de desistência.
- Implementação e teste da rota `GET /health`.
- Configuração de `.gitignore` para ignorar arquivos temporários e ambientes virtuais.

## 2. Como executar o projeto

**Pré-requisito:** Python instalado no computador.

No terminal, a partir da pasta principal `FitFATEC`:

```powershell
cd ia_academia
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python servidor.py
```

Caso o arquivo `modelo_evasao.pkl` não esteja disponível, execute antes de iniciar o servidor:

```powershell
python gerar_dados.py
python treinar_modelo.py
```

Depois, acesse:

- Interface: http://localhost:5000
- Verificação do servidor: http://localhost:5000/health

O servidor utiliza o Flask em modo de desenvolvimento, não sendo adequado para disponibilização pública sem configurações adicionais.

## 3. Rotas disponíveis

| Método | Rota | Função |
|---|---|---|
| GET | `/` | Abrir a interface web |
| GET | `/health` | Verificar o servidor |
| POST | `/api/risco` | Calcular risco de desistência |
| POST | `/api/chat` | Processar mensagens do chatbot |

**Observação:** o chatbot depende de uma API de IA configurada. Sem `ANTHROPIC_API_KEY`, retorna uma mensagem de indisponibilidade. A previsão de desistência continua funcionando.

## 4. O que falta desenvolver — Dev 1

- Implementar cadastro de usuários.
- Implementar login e logout.
- Implementar armazenamento seguro e verificação das senhas.
- Implementar autenticação e proteção das rotas necessárias.
- Integrar a autenticação ao banco definido pelo Dev 5.
- Documentar as novas rotas para integração com o frontend.

## 5. Integração com a equipe

**Dev 2 — IA:** integração com o provedor de IA e funcionamento do chatbot.

**Dev 3 — Treinos:** criação e gerenciamento dos planos de exercício.

**Dev 4 — Frontend:** interface web, telas de acesso, apresentação de exercícios e integração com as APIs.

**Dev 5 — Banco de dados:** tabelas, relacionamentos, persistência e testes de integração.

As rotas de autenticação devem ser combinadas com o Dev 4 e a estrutura de usuários com o Dev 5.

## 6. Arquivos importantes

- `ia_academia/servidor.py` — servidor Flask.
- `ia_academia/assistente.py` — chatbot e previsão de desistência.
- `ia_academia/requirements.txt` — dependências.
- `ia_academia/modelo_evasao.pkl` — modelo treinado.
- `public/index.html` — interface web.
- `bdd/bd_fitfatec.sql` — esquema inicial do banco.
- `documentacao/requisitos_ia.pdf` — requisitos acadêmicos.

## 7. Observações para os próximos desenvolvedores

O projeto já pode ser executado localmente, mas ainda não possui autenticação nem integração completa com o banco.

O ambiente virtual `venv` não deve ser enviado ao GitHub. Cada desenvolvedor deverá preparar o próprio ambiente.

Os dados do modelo de desistência são fictícios, utilizados apenas para fins acadêmicos.

**Este documento registra o estado atual da aplicação e deve ser atualizado conforme novas funcionalidades forem implementadas.**