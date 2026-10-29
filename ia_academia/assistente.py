import os
import joblib
import pandas as pd
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
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
    """historico: lista de mensagens [{"role": "user"/"assistant", "content": "..."}]"""
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


if __name__ == "__main__":
    aluno = {
        "idade": 25, "objetivo": "ganhar massa muscular", "nivel": "iniciante",
        "frequencia_semanal": 2, "meses_matricula": 3, "faltas_ultimo_mes": 8,
    }
    historico = [{"role": "user", "content": "Monte meu treino da semana"}]
    print("Risco:", f"{risco_de_desistir(aluno):.0%}")
    print(responder(aluno, historico))
