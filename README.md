# FitFATEC — Kiara, assistente virtual para academia

Protótipo acadêmico com **Flask + MySQL + Google Gemini**, catálogo licenciado de exercícios e modelo **experimental** de risco de desistência treinado com dados **sintéticos**. A interface principal está em `public/`.

## Começar no Windows (PowerShell)

Requer **Python 3.10 ou superior** (recomendado Python 3.11–3.13), MySQL 8 e internet para instalar pacotes.

No terminal do VS Code, **na pasta raiz `FitFATEC`**:

```powershell
.\configurar.ps1
```

Abra o `.env` criado na raiz, configure pelo menos `DB_USER`, `DB_PASSWORD` e confira `SECRET_KEY` (o configurador gera uma chave aleatória). Para IA generativa, preencha `GEMINI_API_KEY`; sem ela, a Kiara usa o modo offline.

No MySQL Workbench, **somente se ainda não existe o banco**, execute `bdd/bd_fitfatec.sql` (veja o aviso sobre banco existente nas instruções). Depois:

```powershell
.\iniciar.ps1
```

Abra **http://localhost:5000**. Para cadastro/login: **http://localhost:5000/conta**.

Se o PowerShell bloquear scripts locais, use a alternativa **sem scripts** em [como_executar/LEIA-ME.txt](como_executar/LEIA-ME.txt). Não altere a política de segurança do Windows só para executar o projeto.

## Testes

```powershell
.\testar.ps1
```

Ou, dentro de `ia_academia`, com o ambiente virtual ativo:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

## Organização

```text
FitFATEC/
├── README.md                    ← você está aqui
├── configurar.ps1               ← instalação inicial Windows
├── iniciar.ps1                  ← iniciar o servidor Flask
├── testar.ps1                   ← rodar testes
├── .env.example                 ← exemplo, sem dados reais
├── bdd/bd_fitfatec.sql          ← esquema MySQL (importar uma vez)
├── ia_academia/                ← backend, IA, importação e tradução
│   ├── servidor.py
│   ├── assistente.py
│   ├── plano_kiara.py
│   ├── biblioteca_exercicios.py
│   ├── traduzir_exercicios.py
│   ├── dados/                   ← biblioteca de exercícios + licenças
│   ├── tests/                   ← testes separados do código de produção
│   └── requirements.txt
├── public/                      ← HTML/CSS/JS da aplicação
│   ├── index.html
│   ├── pages/conta.html         ← acesso provisório
│   └── img/kiara.svg
├── como_executar/LEIA-ME.txt    ← instruções completas e solução de erros
├── documentacao/                ← requisitos, fluxos, fontes e precificação
└── PROJETO_STATUS.md            ← status real e pendências
```

## Segurança e limitações

- **Nunca compartilhe** `.env` (senhas, tokens), históricos de conversa ou arquivos da pasta `.git`.
- A Kiara utiliza IA generativa quando a chave está configurada e a API funciona. A seleção de exercícios é controlada por catálogo. **Não** substitui orientação profissional.
- O risco de desistência vem de **dados artificiais**, não serve como diagnóstico ou decisão individual real.
- O plano de treino fica temporariamente na sessão Flask; **ainda não é persistido em MySQL**.
- O Streamlit em `ia_academia/app.py` é **alternativo/legado**; a aplicação principal é Flask.
- A licença e a origem dos metadados de exercícios estão em `documentacao/ATRIBUICOES_EXERCICIOS.md`; não redistribuímos imagens/GIFs de terceiros.

> **Integrando em projeto já existente?** Consulte `documentacao/MIGRACAO_REFATORACAO.md` antes de copiar arquivos sobre o repositório do grupo.
