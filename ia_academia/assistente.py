import os
import joblib
import pandas as pd
from google import genai

# ==========================================
# 1. CONFIGURAÇÃO DO GEMINI
# ==========================================

API_KEY = "INSIRA AQUI"

client = genai.Client(api_key=API_KEY)

MODELO_GEMINI = "gemini-3.8-flash"



# ==========================================
# 2. CARREGAMENTO DO MODELO DE MACHINE LEARNING
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

caminho_modelo = os.path.join(BASE_DIR, "modelo_evasao.pkl")

modelo = joblib.load(caminho_modelo)

# ==========================================
# 3. CÁLCULO DO RISCO DE DESISTÊNCIA
# ==========================================

def risco_de_desistir(aluno):
    """
    Retorna a probabilidade (0 a 1)
    de o aluno desistir da academia.
    """

    dados = pd.DataFrame([{
        "idade": aluno["idade"],
        "frequencia_semanal": aluno["frequencia_semanal"],
        "meses_matricula": aluno["meses_matricula"],
        "faltas_ultimo_mes": aluno["faltas_ultimo_mes"],
    }])

    return modelo.predict_proba(dados)[0][1]

# ==========================================
# 4. CONVERSÃO DO HISTÓRICO
# ==========================================

def converter_historico(historico):
    """
    Transforma o histórico em texto
    para enviar ao Gemini.
    """

    mensagens = []

    for msg in historico:
        if msg["role"] == "assistant":
            mensagens.append("Assistente: " + msg["content"])

        elif msg["role"] == "user":
            mensagens.append("Aluno: " + msg["content"])

    return "\n".join(mensagens)

# ==========================================
# 5. RESPOSTA DO ASSISTENTE
# ==========================================

def responder(aluno, historico):

    if client is None:
        return "O chatbot está indisponível no momento porque a chave da API do Gemini não está configurada. O serviço de risco de desistência continua funcionando."

    if not historico:
        return "Erro: nenhuma mensagem foi enviada."

    risco = risco_de_desistir(aluno)

    instrucoes = f"""
    Você é um assistente virtual de academia,
    simpático, motivador e responsável.

    DADOS DO ALUNO:

    - Idade: {aluno['idade']}
    - Objetivo: {aluno['objetivo']}
    - Nível: {aluno['nivel']}
    - Frequência: {aluno['frequencia_semanal']}x por semana
    - Meses de matrícula: {aluno['meses_matricula']}
    - Faltas no último mês: {aluno['faltas_ultimo_mes']}

    Risco estimado de desistência:
    {risco:.0%}

    REGRAS:

    - Monte sugestões de treino de acordo com
      objetivo, nível e dias disponíveis.
    - Se o risco for superior a 60%, seja acolhedor
      e sugira treinos curtos e realistas.
    - Não apresente o risco de desistência como
      um diagnóstico ou certeza.
    - Nunca dê diagnósticos médicos.
    - Pergunte sobre lesões e limitações quando
      isso for relevante para a segurança.
    - Oriente o aluno a procurar um profissional
      de educação física para individualização.
    - Responda em português do Brasil.
    """

    # Converte todo o histórico da conversa
    conversa = converter_historico(historico)

    # Junta as instruções e o histórico
    mensagem_completa = f"""
    {instrucoes}

    HISTÓRICO DA CONVERSA:

    {conversa}

    Continue a conversa respondendo à última mensagem do aluno.
    """

    # Envia a solicitação ao Gemini
    resposta = client.interactions.create(
        model=MODELO_GEMINI,
        input=mensagem_completa
    )

    return resposta.output_text

# ==========================================
# 6. TESTE DO ASSISTENTE
# ==========================================

if __name__ == "__main__":

    aluno = {
        "idade": 25,
        "objetivo": "ganhar massa muscular",
        "nivel": "iniciante",
        "frequencia_semanal": 2,
        "meses_matricula": 3,
        "faltas_ultimo_mes": 8,
    }

    historico = [
        {
            "role": "user",
            "content": "Monte meu treino da semana."
        }
    ]

    print("Testando conexão com Gemini...")

    try:
        resultado = responder(aluno, historico)

        print("\nResposta do assistente:")
        print(resultado)

        print("\nSucesso!")

    except Exception as erro:
        print(f"\nErro ao executar o assistente: {erro}")