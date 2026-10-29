# IA para Academia em Python: guia completo

Este guia monta um **Assistente Inteligente de Academia** que mistura duas coisas:

1. **Machine Learning (scikit-learn):** analisa os dados dos alunos e prevê o risco de desistência.
2. **Chatbot com IA pronta (API do Claude):** conversa com o aluno, monta treinos e ajusta o tom da conversa de acordo com o risco previsto pelo modelo.

Fluxo geral:

```
dados dos alunos (CSV)
        |
        v
[Modelo de ML] --> risco de desistir (ex.: 72%)
        |
        v
[Chatbot Claude] recebe os dados + o risco --> resposta personalizada
        |
        v
[Interface Streamlit] --> o aluno conversa pelo navegador
```

---

## 1. Preparação do ambiente

### 1.1 Requisitos
- Python 3.9 ou superior
- Uma chave de API da Anthropic (criada em console.anthropic.com)

### 1.2 Criar a pasta e o ambiente virtual

```bash
mkdir ia_academia
cd ia_academia
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 1.3 Instalar as bibliotecas

```bash
pip install pandas numpy scikit-learn joblib anthropic streamlit
```

O que cada uma faz:

| Biblioteca | Para que serve |
|---|---|
| pandas | Ler e manipular tabelas de dados (CSV) |
| numpy | Cálculos numéricos e geração de números aleatórios |
| scikit-learn | Treinar o modelo de machine learning |
| joblib | Salvar e carregar o modelo treinado |
| anthropic | Conectar com a API do Claude |
| streamlit | Criar a interface web de forma simples |

### 1.4 Configurar a chave de API

Nunca escreva a chave direto no código. Use uma variável de ambiente:

```bash
# Windows (PowerShell):
setx ANTHROPIC_API_KEY "sua_chave_aqui"

# Linux/Mac:
export ANTHROPIC_API_KEY="sua_chave_aqui"
```

Feche e abra o terminal depois de configurar no Windows.

### 1.5 Estrutura final de pastas

```
ia_academia/
├── dados/
│   └── alunos.csv
├── gerar_dados.py        # cria dados fictícios para teste
├── treinar_modelo.py     # treina e salva o modelo de ML
├── assistente.py         # junta o modelo + o chatbot
├── app.py                # interface web
└── modelo_evasao.pkl     # criado automaticamente ao treinar
```

Crie a pasta `dados` antes de rodar o próximo passo.

---

## 2. Gerar dados fictícios (`gerar_dados.py`)

Se você ainda não tem dados reais de uma academia, este script cria 1000 alunos fictícios. A coluna `desistiu` é calculada com uma regra simples: quem frequenta pouco e falta muito tem mais chance de desistir. Assim o modelo tem algo real para aprender.

```python
import numpy as np
import pandas as pd

np.random.seed(42)
n = 1000

df = pd.DataFrame({
    "idade": np.random.randint(16, 65, n),
    "frequencia_semanal": np.random.randint(0, 7, n),   # vezes por semana
    "meses_matricula": np.random.randint(1, 36, n),
    "faltas_ultimo_mes": np.random.randint(0, 20, n),
})

# Pontuação de risco: mais faltas e menos frequência = mais risco
risco = (
    0.08 * df["faltas_ultimo_mes"]
    - 0.25 * df["frequencia_semanal"]
    - 0.01 * df["meses_matricula"]
    + np.random.normal(0, 0.3, n)   # um pouco de aleatoriedade
)

# Transforma a pontuação em 0 (continuou) ou 1 (desistiu)
df["desistiu"] = (risco > risco.median()).astype(int)

df.to_csv("dados/alunos.csv", index=False)
print("Arquivo dados/alunos.csv criado com", n, "alunos.")
print(df.head())
```

Rode com:

```bash
python gerar_dados.py
```

**Observação:** com dados reais, basta substituir o `alunos.csv` por um arquivo com as mesmas colunas. A coluna `desistiu` deve ser 1 para quem saiu e 0 para quem continua.

---

## 3. Treinar o modelo de ML (`treinar_modelo.py`)

Aqui o computador "aprende" a reconhecer o padrão de quem costuma desistir.

```python
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# 1. Carregar os dados
df = pd.read_csv("dados/alunos.csv")

# 2. Separar: X = informações de entrada, y = o que queremos prever
colunas = ["idade", "frequencia_semanal", "meses_matricula", "faltas_ultimo_mes"]
X = df[colunas]
y = df["desistiu"]

# 3. Separar 80% para treinar e 20% para testar
X_treino, X_teste, y_treino, y_teste = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4. Criar e treinar o modelo
modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_treino, y_treino)

# 5. Avaliar com os dados que o modelo nunca viu
previsoes = modelo.predict(X_teste)
print("Acurácia:", round(modelo.score(X_teste, y_teste), 3))
print(classification_report(y_teste, previsoes))

# 6. Ver quais colunas mais influenciam a previsão
for nome, importancia in zip(colunas, modelo.feature_importances_):
    print(f"{nome}: {importancia:.2f}")

# 7. Salvar o modelo para usar depois
joblib.dump(modelo, "modelo_evasao.pkl")
print("Modelo salvo em modelo_evasao.pkl")
```

Rode com:

```bash
python treinar_modelo.py
```

### Explicação das partes

- **Random Forest:** o modelo cria muitas "árvores de decisão" e junta os votos delas. É confiável e funciona bem sem muito ajuste.
- **Treino e teste:** separamos parte dos dados para testar. Se testássemos com os mesmos dados do treino, o resultado seria enganoso.
- **Acurácia:** porcentagem de acertos. Com dados fictícios o valor será alto, e com dados reais costuma ser menor.
- **Importância das colunas:** mostra o que mais pesa na decisão (útil para a academia saber o que observar).
- **joblib.dump:** guarda o modelo em um arquivo, para não precisar treinar de novo toda vez.

---

## 4. Juntar o modelo e o chatbot (`assistente.py`)

Este é o "cérebro" do sistema. Ele calcula o risco com o modelo e passa essa informação para o Claude.

```python
import os
import joblib
import pandas as pd
import anthropic

# Conexão com a API (lê a chave da variável de ambiente)
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Carrega o modelo treinado
modelo = joblib.load("modelo_evasao.pkl")


def risco_de_desistir(aluno):
    """Retorna a probabilidade (0 a 1) de o aluno desistir."""
    dados = pd.DataFrame([{
        "idade": aluno["idade"],
        "frequencia_semanal": aluno["frequencia_semanal"],
        "meses_matricula": aluno["meses_matricula"],
        "faltas_ultimo_mes": aluno["faltas_ultimo_mes"],
    }])
    return modelo.predict_proba(dados)[0][1]


def responder(aluno, historico):
    """
    aluno: dicionário com os dados do aluno
    historico: lista de mensagens [{"role": "user"/"assistant", "content": "..."}]
    """
    risco = risco_de_desistir(aluno)

    instrucoes = f"""Você é um assistente virtual de academia, simpático e motivador.

Dados do aluno:
- Idade: {aluno['idade']}
- Objetivo: {aluno['objetivo']}
- Nível: {aluno['nivel']}
- Frequência: {aluno['frequencia_semanal']}x por semana
- Meses de matrícula: {aluno['meses_matricula']}
- Faltas no último mês: {aluno['faltas_ultimo_mes']}

Risco estimado de desistência (calculado pelo modelo): {risco:.0%}

Regras:
- Monte treinos de acordo com objetivo, nível e dias disponíveis.
- Se o risco for alto (acima de 60%), seja mais acolhedor, sugira treinos
  curtos, metas pequenas e pergunte o que está dificultando a rotina.
- Se o risco for baixo, incentive a progressão de carga e desafios novos.
- Nunca dê diagnóstico médico. Em caso de dor, lesão ou doença,
  oriente procurar um profissional de saúde.
- Responda em português do Brasil, de forma clara e objetiva.
- Não mencione ao aluno a porcentagem de risco; use-a só para ajustar o tom."""

    resposta = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=instrucoes,
        messages=historico,
    )
    return resposta.content[0].text


# Teste rápido pelo terminal
if __name__ == "__main__":
    aluno = {
        "idade": 25,
        "objetivo": "ganhar massa muscular",
        "nivel": "iniciante",
        "frequencia_semanal": 2,
        "meses_matricula": 3,
        "faltas_ultimo_mes": 8,
    }
    historico = [{"role": "user", "content": "Monte meu treino da semana"}]
    print("Risco:", f"{risco_de_desistir(aluno):.0%}")
    print(responder(aluno, historico))
```

### Pontos importantes

- **O prompt do sistema (`instrucoes`)** define a personalidade e as regras do chatbot. É a parte que mais vale ajustar.
- **O risco entra no prompt**, e o Claude adapta o tom. Isso é a "mistura" entre ML e IA pronta.
- **O histórico** permite conversas com várias mensagens, porque a API não guarda memória sozinha: você envia a conversa toda a cada chamada.
- **A regra de segurança** (não dar diagnóstico) é importante em qualquer app de saúde e exercício.

Teste no terminal:

```bash
python assistente.py
```

---

## 5. Interface web com Streamlit (`app.py`)

```python
import streamlit as st
from assistente import responder, risco_de_desistir

st.set_page_config(page_title="Assistente da Academia", page_icon="🏋️")
st.title("🏋️ Assistente da Academia")

# Barra lateral: dados do aluno
st.sidebar.header("Dados do aluno")
aluno = {
    "idade": st.sidebar.number_input("Idade", 14, 90, 25),
    "objetivo": st.sidebar.selectbox(
        "Objetivo",
        ["ganhar massa muscular", "emagrecer", "condicionamento", "saúde geral"],
    ),
    "nivel": st.sidebar.selectbox("Nível", ["iniciante", "intermediário", "avançado"]),
    "frequencia_semanal": st.sidebar.slider("Treinos por semana", 0, 7, 3),
    "meses_matricula": st.sidebar.number_input("Meses de matrícula", 0, 120, 3),
    "faltas_ultimo_mes": st.sidebar.number_input("Faltas no último mês", 0, 30, 4),
}

# Painel para o instrutor (mostra o risco calculado)
risco = risco_de_desistir(aluno)
st.sidebar.metric("Risco de desistência", f"{risco:.0%}")

# Guarda o histórico da conversa na sessão
if "historico" not in st.session_state:
    st.session_state.historico = []

# Mostra as mensagens anteriores
for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Campo de entrada do chat
pergunta = st.chat_input("Como posso ajudar no seu treino?")
if pergunta:
    st.session_state.historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.write(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resposta = responder(aluno, st.session_state.historico)
        st.write(resposta)

    st.session_state.historico.append({"role": "assistant", "content": resposta})
```

Rode com:

```bash
streamlit run app.py
```

O navegador abrirá em `http://localhost:8501`. Mude os dados na barra lateral (por exemplo, aumente as faltas) e veja o risco e o tom das respostas mudarem.

---

## 6. Ordem para executar tudo

```bash
python gerar_dados.py       # 1. cria os dados fictícios
python treinar_modelo.py    # 2. treina e salva o modelo
python assistente.py        # 3. (opcional) testa no terminal
streamlit run app.py        # 4. abre a interface web
```

---

## 7. Possíveis erros comuns

| Erro | Causa provável | Solução |
|---|---|---|
| `KeyError: 'ANTHROPIC_API_KEY'` | Variável de ambiente não configurada | Refazer o passo 1.4 e reabrir o terminal |
| `FileNotFoundError: dados/alunos.csv` | Pasta `dados` não existe | Criar a pasta e rodar `gerar_dados.py` |
| `FileNotFoundError: modelo_evasao.pkl` | Modelo ainda não treinado | Rodar `treinar_modelo.py` |
| `ModuleNotFoundError` | Biblioteca não instalada | Rodar o `pip install` do passo 1.3 |
| Erro de autenticação (401) | Chave de API inválida | Gerar uma nova chave no console |

---

## 8. Próximas melhorias

1. **Banco de dados:** trocar o aluno fixo por uma consulta em SQLite ou PostgreSQL, buscando o aluno pelo ID.
2. **Dados reais:** substituir os dados fictícios por registros da academia (com autorização e respeitando a LGPD).
3. **Painel do instrutor:** uma página listando os alunos com maior risco de desistência, para o time entrar em contato.
4. **Mais previsões:** além da desistência, prever evolução de carga ou melhor horário de treino de cada aluno.
5. **Análise de movimento:** com OpenCV e MediaPipe, avaliar a postura pela câmera durante os exercícios.
6. **Hospedagem:** publicar o app no Streamlit Community Cloud ou em um servidor próprio.

## 9. Cuidados importantes

- **Saúde:** a IA sugere, mas não substitui um profissional de Educação Física ou um médico. Mantenha os avisos no prompt.
- **Privacidade:** dados de alunos são dados pessoais. Armazene com segurança e peça consentimento.
- **Dados fictícios:** o modelo treinado neles só serve para aprender e testar. Para uso real, treine com dados reais.
- **Custos:** a API do Claude cobra por uso. Acompanhe o consumo no console da Anthropic.
