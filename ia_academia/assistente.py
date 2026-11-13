"""
Variáveis de ambiente:
    GEMINI_API_KEY  chave da API do Gemini (opcional)
    GEMINI_MODEL    modelo a usar (padrão: gemini-3.5-flash-lite)
"""
import os
import configuracao  # prepara GEMINI_API_KEY a partir do .env, se existir
import re
import logging
import unicodedata
import joblib
import pandas as pd

import catalogo
import biblioteca_exercicios
import plano_kiara
from nomes_exercicios_pt import nome_pt as traduzir_nome_exercicio

logger = logging.getLogger(__name__)

# Gemini
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
MODELO_GEMINI = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

client = None
_types = None
if API_KEY:
    try:
        from google import genai
        from google.genai import types as _types
        client = genai.Client(api_key=API_KEY)
    except ImportError:  # pacote google-genai não instalado
        logger.warning("Chave Gemini encontrada, mas google-genai não está instalado; usando modo offline.")
        client = None

#  Modelo ML(machine learning)
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


#Persona(ela ta com essa personalidade por conta dos critério)
PERSONA = """\
Você é a KIARA, assistente virtual da academia FitFATEC.
- Identidade: onça-pintada simpática, aparência de jovem adulta (cerca de 25 anos),
  uniforme institucional laranja e preto com o logotipo da FitFATEC.
- Tom de voz: amigável, jovem e motivador; nunca ríspida nem institucional demais.
- Estilo: conversa natural e direta. Não transforme uma pergunta simples em
  apresentação, palestra ou propaganda. Evite emojis em respostas técnicas;
  não faça perguntas de acompanhamento por hábito. Chame o aluno pelo nome
  somente quando isso melhorar a resposta, nunca em toda mensagem.
- Atendimento 24h, na academia ou remoto.
"""

REGRAS = """\
ESPECIALIDADE DA KIARA:
- Você é uma assistente de IA conversacional voltada para musculação, fitness e academia.
- Responda com liberdade e profundidade adequada ao pedido sobre músculos e suas funções,
  anatomia funcional, biomecânica, hipertrofia, força, resistência, mobilidade,
  alongamento, execução de exercícios, variações, equipamentos, organização de
  treinos, recuperação, hábitos e alimentação esportiva geral.
- Responda ao que foi pedido, sem adicionar seções que o aluno não solicitou.
  Só explique os motivos das sugestões se o aluno pedir justificativa ou houver
  uma restrição essencial que exija esclarecimento. Nunca force uma introdução,
  depois uma ficha e depois uma despedida.
- O catálogo local fornecido é REFERÊNCIA ADICIONAL, não uma lista exaustiva nem
  uma autorização exclusiva. Você PODE usar seu conhecimento geral para explicar e
  sugerir outros exercícios conhecidos. NÃO invente IDs, equipamentos, dados ou
  fontes e nunca afirme que um exercício está no catálogo se não estiver listado.
- Quando um exercício do catálogo estiver disponível, prefira seu nome português
  para manter consistência; os nomes originais servem apenas para vinculação interna.
  Exiba ao aluno somente nomes de exercícios em português do Brasil.

ATENDIMENTO E CONTEXTO:
- Quando pedirem um grupo muscular, foque nele; quando pedirem uma alternativa,
  proponha opções realmente diferentes que trabalhem o foco pedido.
- Leve em conta nível, objetivo e histórico. Preserve restrições de equipamentos
  expressas na conversa. Não presuma que o aluno tenha acessórios não mencionados.
- Ao combinar treinos, mantenha os grupos musculares e restrições anteriores.
- Ao substituir um exercício de uma série já descrita, preserve os outros e a
  quantidade, evite repetição e explique brevemente o motivo da troca. Se o pedido
  estiver ambíguo e não houver como identificar o exercício, peça esclarecimento.
- Quando não houver alternativa para as restrições, explique o motivo e pergunte
  por equipamentos disponíveis; não invente uma substituição inadequada.
- Para sugestões de treino, use séries, repetições e descansos como referências
  ajustáveis. Não descreva uma ficha gerada como avaliação profissional individual.
- O aluno já está autenticado: nunca solicite matrícula, senha ou dados de login.
  Para agendar, oriente a usar o botão "Agendar aula" do painel. Não afirme ter
  agendado, salvo ou alterado treinos no banco apenas por conversar sobre eles.
- Explique nível de treinamento de modo aproximado, sem tratá-lo como diagnóstico.
  Se perguntarem sobre fadiga ou desistência, responda com sensibilidade sem citar
  probabilidades de risco ou conclusões clínicas.

SEGURANÇA E ESCOPO:
- Não dê diagnósticos, prescrição medicamentosa nem planos clínicos. Se houver
  lesão, dor ou doença, não incentive a treinar apesar da dor; sugira avaliação
  por profissional qualificado e adaptações gerais seguras quando apropriadas.
- Para dúvidas pessoais complexas de dieta, lesões ou treinamento especializado,
  deixe claros os limites da orientação geral e quando procurar um profissional.
- Não apresente estimativas de risco de desistência como certeza ou diagnóstico.
- Mantenha o foco em academia, músculos, exercícios e bem-estar ligado ao treino.
  Para temas alheios, redirecione gentilmente ao assunto da FitFATEC.
- Responda sempre em português brasileiro, sem incluir traduções em inglês.
"""


def _tipo_de_resposta(mensagem: str) -> str:
    """Direciona o TAMANHO/formato da resposta, sem engessar o conteúdo do Gemini."""
    texto = biblioteca_exercicios.normalizar(mensagem)
    explicar = (
        "explique", "explica", "como executar", "como fazer", "como funciona",
        "o que e", "por que", "porque", "qual a diferenca", "para que serve",
        "como devo", "me ensine", "ensine", "qual musculo", "quais musculos",
    )
    if any(p in texto for p in explicar):
        return "explicacao"
    treino = (
        "treino", "serie", "ficha", "monte", "monta", "montar", "combina",
        "junt", "substitu", "troque", "trocar", "exercic",
        "alternativ", "variac", "opcoes", "outros movimentos",
    )
    if any(p in texto for p in treino):
        return "treino"
    # Pedidos curtos como "agora de tríceps" continuam o treino anterior.
    if re.search(r"\bagora\s+(?:quero\s+)?(?:de|para)\s+\w+", texto):
        if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", texto)
               for aliases in biblioteca_exercicios.GRUPOS.values() for alias in aliases):
            return "treino"
    return "conversa"


def _orientacao_formato(tipo: str) -> str:
    """Instruções específicas: treino é ficha; explicação só se solicitada."""
    if tipo == "treino":
        return """FORMATO PARA ESTE PEDIDO: FICHA OBJETIVA.
- Entregue diretamente os exercícios. Comece pelo título curto do grupo muscular
  (ex.: "Pernas:") e siga com lista simples: "- Agachamento: 3x10–12 (60s)".
- Se o aluno não definir quantidade, escolha aproximadamente 3 a 5 exercícios
  apropriados. Não aumente a lista só para parecer completa.
- NÃO escreva introduções como "Com certeza", "Preparei", "Vamos lá".
- NÃO escreva conclusão, convite para agendar, pergunta automática, aviso de
  profissional repetido ou parágrafos de motivação. NÃO explique cada exercício
  salvo quando isso for pedido.
- Se não for possível atender às restrições, explique em UMA frase o obstáculo e
  faça no máximo UMA pergunta necessária. Para dor, lesão ou risco específico,
  uma ressalva curta de segurança pode ser apropriada.
- Quando solicitado a modificar uma ficha anterior, preserve os demais itens;
  mostre a lista atualizada, não recapitule toda a conversa."""
    if tipo == "explicacao":
        return """FORMATO PARA ESTE PEDIDO: EXPLICAÇÃO SOB DEMANDA.
- Responda diretamente à pergunta em 2 a 5 frases curtas.
- Se o aluno solicitar PASSO A PASSO, use até 4 etapas numeradas.
- Explique como executar, quais músculos são trabalhados e os cuidados relevantes
  apenas na medida da pergunta; consulte metadados do catálogo quando disponíveis.
- Não anexe ficha de treino, convite para agendar, introdução ou despedida."""
    return """FORMATO PARA ESTE PEDIDO: CONVERSA CURTA.
- Dê a resposta direta em até 3 frases, se suficiente.
- Sem ficha de exercícios, avisos genéricos ou perguntas no fim por hábito.
- Aprofunde somente se o aluno pedir ou se isso for necessário para responder."""


def _grupos_do_contexto(historico: list, ultimo: str) -> list[str]:
    """Encontra os grupos anteriores quando 'monte usando o que conversamos'."""
    grupos = biblioteca_exercicios.grupos_relevantes(historico)
    normalizado = biblioteca_exercicios.normalizar(ultimo)
    referencia_passado = any(p in normalizado for p in (
        "conversamos", "anteriores", "anterior", "dois", "ambos", "ambas",
        "que voce sugeriu", "que me mostrou", "que acabamos", "que falamos",
        "mesmo treino", "treino atualizado", "treino completo",
    ))
    if not grupos and referencia_passado:
        # Só lê mensagens do aluno para inferir os grupos. Não assume que nomes
        # mencionados pela IA sejam preferências ou restrições reais.
        partes = [m.get("content", "") for m in historico[-12:]
                  if m.get("role") == "user"]
        nomes = []
        for texto in reversed(partes):
            norm = biblioteca_exercicios.normalizar(texto)
            for grupo, aliases in biblioteca_exercicios.GRUPOS.items():
                if grupo not in nomes and any(
                    re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", norm)
                    for alias in aliases):
                    nomes.append(grupo)
        grupos = nomes[:4]
    return grupos


def _metadados_exercicio_mencionado(historico: list, limite: int = 3) -> list[str]:
    """Busca exercícios nomeados pelo aluno, sem copiar instruções não licenciadas.

    Apenas metadados locais (nome em português, alvo, equipamento, secundários).
    Não interpreta esses metadados como instruções técnicas de execução.
    """
    ultima = _ultima(historico, "user")
    norm = biblioteca_exercicios.normalizar(ultima)
    # Também cobre 'explique o primeiro exercício': procura no último treino
    # citado no histórico, sem prometer que a escolha está salva no banco.
    referencial = any(p in norm for p in ("primeiro exercicio", "segundo exercicio",
                   "terceiro exercicio", "como executar", "como fazer"))
    if referencial:
        anterior = _ultima(historico, "assistant")
        norm += " " + biblioteca_exercicios.normalizar(anterior)
    encontrados = []
    for item in biblioteca_exercicios.carregar():
        nome = traduzir_nome_exercicio(item.get("name", ""), item.get("id"))
        if not nome or len(nome) < 8:
            continue
        if biblioteca_exercicios.normalizar(nome) in norm:
            alvo = item.get("target", "não informado")
            equip = item.get("equipment", "não informado")
            secundario = item.get("secondary_muscles") or []
            encontrados.append(f"- {nome}: alvo={alvo}; equipamento={equip}; "
                              f"músculos secundários={', '.join(secundario) if secundario else 'não informados'}")
            if len(encontrados) >= limite:
                break
    return encontrados


def _instrucoes(aluno: dict, risco: float, historico: list | None = None) -> str:
    """Gemini responde; catálogo local fornece evidências pontuais e filtradas."""
    historico = historico or []
    ultima = _ultima(historico, "user")
    tipo = _tipo_de_resposta(ultima)
    grupos = _grupos_do_contexto(historico, ultima)
    proibidos = biblioteca_exercicios.restricoes_equipamento(historico)
    restricoes = ("EQUIPAMENTOS PROIBIDOS pelo aluno: " + ", ".join(sorted(proibidos))
                  if proibidos else "Nenhum equipamento vetado explicitamente.")

    # Consulta efetiva ao catálogo para pedidos de treinos, inclusive os que
    # referenciam grupos citados anteriormente em vez de repeti-los na mensagem.
    linhas_catalogo = []
    if tipo == "treino":
        consulta = historico
        if grupos and not biblioteca_exercicios.grupos_relevantes(historico):
            # Reproduz os grupos resgatados no final sem perder as restrições
            # anteriores, que são lidas do histórico completo do aluno.
            consulta = list(historico) + [{"role": "user", "content":
                "Combine treino de " + " e ".join(grupos)}]
        selecao = biblioteca_exercicios.selecionar(consulta, limite=10)
        for ex in selecao.get("itens", []):
            if ex.get("nome_pt"):
                linhas_catalogo.append(f"- {ex['nome_pt']} | alvo: {ex.get('target', '?')}"
                                       f" | equipamento: {ex.get('equipment', '?')}")
    elif tipo == "explicacao":
        linhas_catalogo = _metadados_exercicio_mencionado(historico)

    referencia = "\n".join(linhas_catalogo) if linhas_catalogo else (
        "Não é necessário consultar exercícios específicos nesta pergunta."
        if tipo != "treino" else "Nenhum exercício específico encontrado na consulta atual.")

    return f"""{PERSONA}
{REGRAS}
{_orientacao_formato(tipo)}

CONTEXTO DO ALUNO (campos da tela podem estar desatualizados):
- Nome: {aluno.get('nome') or 'Aluno'}
- Idade: {aluno['idade']} | Objetivo: {aluno['objetivo']} | Nível: {aluno['nivel']}
- Frequência informada: {aluno['frequencia_semanal']}x por semana
- Meses de matrícula: {aluno['meses_matricula']}
- Risco interno estimado (NÃO mencionar ao aluno): {risco:.0%}

RESTRIÇÕES ATIVAS:
{restricoes}

CATÁLOGO LOCAL CONSULTADO (referência, não limite exclusivo):
{referencia}

O catálogo traz metadados (nome, grupo muscular, equipamento), NÃO instruções
completas de execução nem avaliação individual. Se o exercício estiver presente,
use os metadados para conferir alvo e equipamento; explique com conhecimento
próprio, deixando claro o que é sugestão geral. Para nomes ausentes, pode
recorrer ao seu conhecimento geral, sem fingir que estão catalogados.
Responda à última mensagem, respeitando o formato escolhido e as restrições.
"""


# Os aliases são normalizados sem acentos para reconhecer "bíceps" e "biceps".
GRUPOS = {
    "bíceps": ("biceps",),
    "tríceps": ("triceps",),
    "peito": ("peito", "peitoral"),
    "costas": ("costas", "dorsal", "dorsais"),
    "ombros": ("ombro", "ombros"),
    "pernas": ("perna", "pernas", "quadriceps"),
    "abdômen": ("abdomen", "abdominal", "abdominais", "core"),
    "glúteos": ("gluteo", "gluteos"),
    "panturrilhas": ("panturrilha", "panturrilhas"),
}


def detectar_grupos(texto):
    sem_acentos = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                           if unicodedata.category(c) != "Mn")
    return [grupo for grupo, aliases in GRUPOS.items()
            if any(re.search(r"\b" + re.escape(nome) + r"\b", sem_acentos)
                   for nome in aliases)]


#  Modo offline
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

    if _contem(texto, ["agend", "marcar", "horário", "horario", "reservar"]):
        return ("Vamos agendar! Sua conta já está identificada. "
                "Clique no botão 'Agendar aula' e escolha a data, a modalidade e o horário. "
                "Atendemos das 06h às 21h, conforme as vagas disponíveis.")

    # Pedidos por músculo têm prioridade sobre a resposta genérica de "treino".
    grupos = detectar_grupos(texto)
    if grupos and _contem(texto, ["treino", "série", "serie", "exerc", "malhar", "trabalhar"]):
        alternativa = _contem(texto, ["outro", "outra", "diferente", "alternativ", "variar"])
        blocos = [catalogo.texto_treino_grupo(grupo, nivel, alternativa) for grupo in grupos]
        return "\n\n".join(blocos)

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
        if _contem(texto, ["outro", "outra", "diferente", "alternativ", "variar"]):
            return ("No modo offline, tenho uma série geral cadastrada para seu objetivo e nível, "
                    "e não quero repetir a mesma fingindo que é uma nova. "
                    "Posso sugerir exercícios por músculo: bíceps, tríceps, peito, costas, "
                    "ombros, pernas, glúteos, panturrilhas ou abdômen. Qual você prefere?")
        return catalogo.texto_serie(nivel, objetivo)

    if _contem(texto, ["sim", "quero", "pode", "ok", "bora"]) and "aquecimento" in anterior:
        return (f"Perfeito! Sua conta já está identificada. Aqui está a série completa:\n\n"
                f"{catalogo.texto_serie(nivel, objetivo)}")

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


def _exercicios_na_resposta(texto: str) -> list[str]:
    """Extrai nomes de exercícios de listas '- Nome: 2x10'. É uma heurística.

    Planos ainda não são armazenados em formato estruturado no banco, logo
    verificamos apenas substituições explícitas no texto do histórico.
    """
    nomes = []
    for linha in texto.splitlines():
        achou = re.match(r"^\s*[-•]\s*([^:]{3,90})\s*:\s*\d", linha)
        if achou:
            nomes.append(biblioteca_exercicios.normalizar(achou.group(1).strip()))
    return nomes


def _validar_substituicao(historico: list, resposta: str) -> bool:
    """Rejeita remoção sem reposição, repetição e alterações não solicitadas.

    Só ativa quando o aluno menciona um exercício presente no plano anterior
    e pede a troca. Não confunda esta checagem com validação por profissional.
    """
    pergunta = biblioteca_exercicios.normalizar(_ultima(historico, "user"))
    if not any(v in pergunta for v in ("substitu", "troque", "trocar", "no lugar")):
        return True
    antigos = _exercicios_na_resposta(_ultima(historico, "assistant"))
    if len(antigos) < 2:
        return True
    removidos = {nome for nome in antigos if nome in pergunta}
    if not removidos:
        return True
    novos = _exercicios_na_resposta(resposta)
    if len(novos) != len(antigos) or len(set(novos)) != len(novos):
        return False
    if any(nome not in novos for nome in antigos if nome not in removidos):
        return False
    if any(nome in novos for nome in removidos):
        return False
    return True




def _portugues_na_resposta(texto: str) -> str:
    """Remove referências a nomes ingleses conhecidos em respostas livres.

    O planejador já utiliza exclusivamente nome_pt. Isso cobre respostas
    conversacionais que eventualmente repitam um nome do dataset original.
    """
    registros = biblioteca_exercicios.carregar()
    if not registros or not isinstance(texto, str):
        return texto
    candidatos = []
    texto_casefold = texto.casefold()
    for x in registros:
        original = str(x.get('name', '')).strip()
        if len(original) < 4 or original.casefold() not in texto_casefold:
            continue
        pt = traduzir_nome_exercicio(original, x.get('id'))
        if pt and biblioteca_exercicios.normalizar(pt) != biblioteca_exercicios.normalizar(original):
            candidatos.append((original, pt))
    for original, pt in sorted(candidatos, key=lambda par: len(par[0]), reverse=True):
        texto = re.sub(r'(?<!\w)' + re.escape(original) + r'(?!\w)',
                       lambda m: pt, texto, flags=re.IGNORECASE)
    return texto


# Resposta com origem explícita, para distinguir uma geração real do catálogo offline.
def responder_com_modo(aluno: dict, historico: list) -> tuple[str, str]:
    if not historico:
        return "Erro: nenhuma mensagem foi enviada.", "offline"
    risco = risco_de_desistir(aluno)

    if client is None:
        return responder_offline(aluno, historico, risco), "offline"

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
                system_instruction=_instrucoes(aluno, risco, historico),
                temperature=0.6,
                max_output_tokens=800,
            ),
        )
        if resposta.text and resposta.text.strip():
            texto = resposta.text.strip()
            if not _validar_substituicao(historico, texto):
                logger.info("Primeira substituição não preservou o plano: solicitando correção ao modelo")
                nova = client.models.generate_content(
                    model=MODELO_GEMINI,
                    contents=conteudo,
                    config=_types.GenerateContentConfig(
                        system_instruction=_instrucoes(aluno, risco, historico)
                        + "\nATENÇÃO: no pedido atual, preserve todos os exercícios não substituídos "
                          "e a quantidade original de itens. Acrescente UMA alternativa inédita. "
                          "Escreva linhas no padrão '- Exercício: 2x10 (descanso 60s)'.",
                        temperature=0.15,
                        max_output_tokens=800,
                    ),
                )
                if not nova.text or not _validar_substituicao(historico, nova.text):
                    return ("Não consegui garantir uma substituição sem remover outros "
                            "exercícios ou repetir um já existente. Peça ao instrutor "
                            "uma alternativa para essa troca.", "gemini")
                texto = nova.text.strip()
            return _portugues_na_resposta(texto), "gemini"
        logger.warning("Gemini retornou resposta vazia; usando o catálogo offline.")
    except Exception as erro:
        # Não expõe no log a API key, mensagens privadas nem dados do aluno.
        codigo = getattr(erro, "status_code", None) or getattr(erro, "code", None)
        logger.warning("Falha no Gemini (%s; código=%s). Usando modo offline.",
                       type(erro).__name__, codigo or "desconhecido")
    return responder_offline(aluno, historico, risco), "offline"


def responder_com_plano(aluno: dict, historico: list, plano_atual: dict | None = None):
    """Gemini responde integralmente; catálogo só assume no modo offline.

    Quando o Gemini funciona, suas respostas vêm do modelo e do histórico
    (não são uma frase criada em cima de uma ficha fixa). O plano estruturado
    antigo não representa com segurança treinos livres gerados pela IA, então
    não afirmamos tê-los salvo. A futura tela Meus treinos terá persistência.
    """
    # O método já faz a chamada real e retorna "offline" caso a API falhe.
    texto, modo = responder_com_modo(aluno, historico)
    if modo == "gemini":
        # Nenhuma estrutura inventada do catálogo como se fosse o treino da IA.
        return texto, modo, {"exercicios": []}

    # Sem Gemini, preserve o planejador determinístico e suas verificações.
    # A interface continua mostrando "Modo offline", sem fingir IA ativa.
    planejamento = plano_kiara.tratar(historico, plano_atual)
    if planejamento is not None:
        resposta, novo_plano = planejamento
        return resposta, "offline", novo_plano
    return texto, "offline", plano_atual or {"exercicios": []}


def responder(aluno: dict, historico: list):
    """Mantém compatibilidade com quem usa a função de resposta simples."""
    return responder_com_modo(aluno, historico)[0]


if __name__ == "__main__":
    aluno = {"idade": 25, "objetivo": "ganhar massa muscular", "nivel": "iniciante",
             "frequencia_semanal": 2, "meses_matricula": 3, "faltas_ultimo_mes": 8}
    print("Modo:", "Gemini" if client else "offline")
    print(responder(aluno, [{"role": "user", "content": "Quero uma série de condicionamento"}]))
