"""Kiara — assistente virtual da FitFATEC.

Junta três coisas:
1. modelo de machine learning (risco de desistência);
2. catálogo de treinos (catalogo.py), usado como fonte de verdade;
3. IA generativa (Google Gemini). Sem chave de API, a Kiara continua
   funcionando em modo offline com respostas baseadas em regras.

Variáveis de ambiente:
    GEMINI_API_KEY  chave da API do Gemini (opcional)
    GEMINI_MODEL    modelo a usar (padrão: gemini-2.5-flash)
"""
import os
import re
import joblib
import pandas as pd

import catalogo

# ---------------------------------------------------------------- Gemini
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
MODELO_GEMINI = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

client = None
_types = None
if API_KEY:
    try:
        from google import genai
        from google.genai import types as _types
        client = genai.Client(api_key=API_KEY)
    except ImportError:  # pacote google-genai não instalado
        client = None

# ---------------------------------------------------------------- Modelo ML
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "modelo_evasao.pkl")
modelo = joblib.load(MODEL_PATH)


def risco_de_desistir(aluno: dict) -> float:
    dados = pd.DataFrame([{
        "idade": aluno["idade"],
        "frequencia_semanal": aluno["frequencia_semanal"],
        "meses_matricula": aluno["meses_matricula"],
        "faltas_ultimo_mes": aluno["faltas_ultimo_mes"],
    }])
    return float(modelo.predict_proba(dados)[0][1])


# ---------------------------------------------------------------- Persona
PERSONA = """\
Você é a KIARA, assistente virtual da academia FitFATEC.
- Identidade: onça-pintada simpática, aparência de jovem adulta (cerca de 25 anos),
  uniforme institucional laranja e preto com o logotipo da FitFATEC.
- Tom de voz: amigável, jovem e motivador; nunca ríspida nem institucional demais.
- Estilo: frases curtas, no máximo 2 emojis por resposta, uma pergunta por vez,
  listas curtas para exercícios. Chame o aluno pelo nome quando souber.
- Atendimento 24h, na academia ou remoto.
"""

REGRAS = """\
SERVIÇOS QUE VOCÊ ATENDE:
1. Agendar horário de aula -> oriente o aluno a usar o botão "Agendar aula" do painel
   (informe que precisa da matrícula, data e horário).
2. Ofertar série de exercícios conforme a necessidade do aluno.
3. Informar modalidades de aquecimento.
4. Informar treino principal e treino secundário.
5. Informar/ajustar o nível de condicionamento (iniciante, intermediário ou avançado).

REGRAS:
- Use SOMENTE os exercícios do CATÁLOGO abaixo; não invente séries nem exercícios.
- Se o aluno pedir uma série, ofereça começar pelo aquecimento e depois o treino principal e o secundário.
- Se o risco de desistência for superior a 60%, seja acolhedora e sugira treinos curtos e realistas.
- Nunca apresente o risco como diagnóstico ou certeza e nunca mencione o percentual ao aluno.
- Nunca dê diagnósticos médicos. Pergunte sobre lesões e limitações quando for relevante.
- Oriente procurar um profissional de educação física para individualização.
- Se a pergunta fugir do tema academia, diga gentilmente que só ajuda com treinos e a rotina da FitFATEC.
- Responda em português do Brasil.
"""


def _instrucoes(aluno: dict, risco: float) -> str:
    return f"""{PERSONA}
{REGRAS}
DADOS DO ALUNO:
- Idade: {aluno['idade']} | Objetivo: {aluno['objetivo']} | Nível: {aluno['nivel']}
- Frequência: {aluno['frequencia_semanal']}x por semana | Matrícula há {aluno['meses_matricula']} meses
- Faltas no último mês: {aluno['faltas_ultimo_mes']}
- Risco estimado de desistência (uso interno): {risco:.0%}

CATÁLOGO (nível e objetivo atuais do aluno):
{catalogo.texto_serie(aluno['nivel'], aluno['objetivo'])}
"""


# ---------------------------------------------------------------- Modo offline
def _ultima(historico, papel):
    for msg in reversed(historico):
        if msg.get("role") == papel:
            return msg.get("content", "")
    return ""


def _contem(texto, palavras):
    return any(p in texto for p in palavras)


def responder_offline(aluno: dict, historico: list, risco: float) -> str:
    """Respostas baseadas em regras, usadas quando não há chave do Gemini."""
    texto = _ultima(historico, "user").lower().strip()
    anterior = _ultima(historico, "assistant").lower()
    nivel, objetivo = aluno["nivel"], aluno["objetivo"]
    leve = risco > 0.6
    prefixo = "Estou aqui com você, sem pressa. " if leve else ""

    # Fluxo: o aluno respondeu a matrícula pedida antes
    if "matrícula" in anterior and re.fullmatch(r"\d{4,12}", texto):
        return (f"Matrícula {texto} recebida! 🐆 Aqui está sua série de hoje:\n\n"
                f"{catalogo.texto_serie(nivel, objetivo)}\n\n"
                "Quer agendar uma aula para treinar com um instrutor?")

    if _contem(texto, ["agend", "marcar", "horário", "horario", "reservar"]):
        return ("Vamos agendar! Use o botão \"Agendar aula\" no painel: "
                "informe sua matrícula, a data e o horário. "
                "Atendemos das 06h às 21h; escolha o horário que preferir.")

    if _contem(texto, ["aquec"]):
        return (f"Modalidades de aquecimento para o nível {nivel}:\n\n"
                f"{catalogo.texto_aquecimento(nivel)}\n\nQuer ver o treino principal agora?")

    if _contem(texto, ["secund"]) or (_contem(texto, ["principal"]) and "treino" in texto):
        s = catalogo.montar_serie(nivel, objetivo)
        return (f"Treino principal — {s['principal']['foco']}:\n{catalogo._linhas(s['principal'])}\n\n"
                f"Treino secundário — {s['secundario']['foco']}:\n{catalogo._linhas(s['secundario'])}")

    if _contem(texto, ["nível", "nivel", "condicionamento físico", "iniciante", "avançado", "intermediário"]):
        sugerido = catalogo.classificar_nivel(aluno["meses_matricula"], aluno["frequencia_semanal"])
        return (f"Pelos seus dados (matrícula há {aluno['meses_matricula']} meses e "
                f"{aluno['frequencia_semanal']}x por semana), eu sugiro o nível {sugerido}. "
                f"Hoje você está como {nivel}. Para mudar, ajuste o campo \"Nível\" no painel.")

    if _contem(texto, ["série", "serie", "treino", "exercício", "exercicio", "condicionamento"]):
        if "matrícula" not in anterior:
            return (f"{prefixo}Posso ajudar! Você deseja começar com aquecimento?\n"
                    "Se preferir, informe seu número de matrícula para eu montar a série completa.")
        return f"{prefixo}Aqui vai:\n\n{catalogo.texto_serie(nivel, objetivo)}"

    if _contem(texto, ["sim", "quero", "pode", "ok", "bora"]) and "aquecimento" in anterior:
        return "Perfeito! Informe seu número de matrícula para prosseguir."

    if _contem(texto, ["falta", "desanim", "sem tempo", "cansad", "preguiça", "desist"]):
        return ("Acontece com todo mundo, e voltar é o que importa! 💪 "
                "Que tal um treino de 20 minutos hoje? Aquecimento leve e só o treino principal. "
                "Se preferir, agende uma aula com um instrutor para ter companhia.")

    if _contem(texto, ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"]):
        return ("Oi! Eu sou a Kiara, assistente da FitFATEC. 🐆 Posso agendar sua aula, "
                "montar sua série, explicar o aquecimento e os treinos principal e secundário. "
                "O que você precisa?")

    return ("Posso ajudar com: agendar aula, montar sua série, aquecimento, "
            "treino principal e secundário ou nível de condicionamento. O que você prefere?")


# ---------------------------------------------------------------- Resposta
def responder(aluno: dict, historico: list):
    if not historico:
        return "Erro: nenhuma mensagem foi enviada."
    risco = risco_de_desistir(aluno)

    if client is None:
        return responder_offline(aluno, historico, risco)

    conteudo = [
        _types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[_types.Part(text=m["content"])],
        )
        for m in historico if m.get("role") in ("user", "assistant")
    ]
    try:
        resposta = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=conteudo,
            config=_types.GenerateContentConfig(
                system_instruction=_instrucoes(aluno, risco),
                temperature=0.6,
                max_output_tokens=700,
            ),
        )
        return resposta.text or responder_offline(aluno, historico, risco)
    except Exception:
        # Falha de rede/cota: a Kiara não pode ficar muda
        return responder_offline(aluno, historico, risco)


if __name__ == "__main__":
    aluno = {"idade": 25, "objetivo": "ganhar massa muscular", "nivel": "iniciante",
             "frequencia_semanal": 2, "meses_matricula": 3, "faltas_ultimo_mes": 8}
    print("Modo:", "Gemini" if client else "offline")
    print(responder(aluno, [{"role": "user", "content": "Quero uma série de condicionamento"}]))
