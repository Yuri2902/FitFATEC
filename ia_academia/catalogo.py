"""Catálogo de treinos 
Conteúdo fixo e revisável: aquecimento, treino principal e treino secundário
por nível de condicionamento e objetivo. A IA generativa usa este catálogo como
fonte de verdade (não inventa exercícios) e o modo offline responde com ele.
"""

NIVEIS = ["iniciante", "intermediário", "avançado"]
OBJETIVOS = ["ganhar massa muscular", "emagrecer", "condicionamento", "saúde geral"]

AQUECIMENTOS = {
    "esteira": {"nome": "Caminhada/trote leve na esteira", "duracao_min": 8,
                "descricao": "Ritmo confortável, subindo a velocidade aos poucos."},
    "bicicleta": {"nome": "Bicicleta ergométrica", "duracao_min": 8,
                  "descricao": "Carga leve, cadência constante."},
    "mobilidade": {"nome": "Mobilidade articular", "duracao_min": 5,
                   "descricao": "Círculos de ombro, quadril e tornozelo; rotação de tronco."},
    "dinamico": {"nome": "Alongamento dinâmico", "duracao_min": 5,
                 "descricao": "Afundo com rotação, agachamento livre, elevação de joelhos."},
    "corda": {"nome": "Pular corda", "duracao_min": 5,
              "descricao": "Ritmo leve a moderado, pausas curtas se precisar."},
}

AQUECIMENTO_POR_NIVEL = {
    "iniciante": ["esteira", "mobilidade"],
    "intermediário": ["bicicleta", "dinamico"],
    "avançado": ["corda", "dinamico", "mobilidade"],
}

# (exercício, séries, repetições/tempo, descanso em segundos)
TREINOS = {
    "ganhar massa muscular": {
        "iniciante": {
            "principal": {"foco": "Corpo inteiro (máquinas guiadas)", "exercicios": [
                ("Leg press", 3, "12", 60), ("Supino máquina", 3, "12", 60),
                ("Remada sentada", 3, "12", 60), ("Desenvolvimento máquina", 2, "12", 60)]},
            "secundario": {"foco": "Core e estabilidade", "exercicios": [
                ("Prancha", 3, "20s", 45), ("Abdominal curto", 3, "15", 45)]},
        },
        "intermediário": {
            "principal": {"foco": "Divisão superior (peito, costas, ombro)", "exercicios": [
                ("Supino reto", 4, "10", 75), ("Puxada frontal", 4, "10", 75),
                ("Desenvolvimento com halteres", 3, "10", 75), ("Remada curvada", 3, "10", 75)]},
            "secundario": {"foco": "Braços", "exercicios": [
                ("Rosca direta", 3, "12", 60), ("Tríceps corda", 3, "12", 60)]},
        },
        "avançado": {
            "principal": {"foco": "Pernas e glúteos (alto volume)", "exercicios": [
                ("Agachamento livre", 5, "6-8", 120), ("Stiff", 4, "8-10", 90),
                ("Leg press 45°", 4, "10", 90), ("Cadeira extensora (drop-set)", 3, "10+10", 75)]},
            "secundario": {"foco": "Panturrilha e abdômen", "exercicios": [
                ("Panturrilha em pé", 4, "15", 45), ("Abdominal na polia", 4, "12", 45)]},
        },
    },
    "emagrecer": {
        "iniciante": {
            "principal": {"foco": "Aeróbico contínuo", "exercicios": [
                ("Esteira (caminhada inclinada)", 1, "25 min", 0),
                ("Bicicleta ergométrica", 1, "10 min", 0)]},
            "secundario": {"foco": "Força básica em circuito", "exercicios": [
                ("Agachamento no banco", 2, "12", 45), ("Remada sentada", 2, "12", 45),
                ("Flexão inclinada", 2, "10", 45)]},
        },
        "intermediário": {
            "principal": {"foco": "Intervalado (HIIT moderado)", "exercicios": [
                ("Esteira 1 min forte / 2 min leve", 8, "ciclos", 0)]},
            "secundario": {"foco": "Circuito de força", "exercicios": [
                ("Agachamento com halteres", 3, "15", 30), ("Remada unilateral", 3, "12", 30),
                ("Afundo alternado", 3, "12", 30)]},
        },
        "avançado": {
            "principal": {"foco": "HIIT avançado", "exercicios": [
                ("Sprint 30s / 30s leve", 12, "ciclos", 0), ("Remo ergômetro", 4, "500 m", 60)]},
            "secundario": {"foco": "Força metabólica", "exercicios": [
                ("Levantamento terra", 4, "8", 90), ("Kettlebell swing", 4, "15", 45),
                ("Burpee", 3, "10", 45)]},
        },
    },
    "condicionamento": {
        "iniciante": {
            "principal": {"foco": "Base aeróbica", "exercicios": [
                ("Caminhada/trote na esteira", 1, "20 min", 0), ("Elíptico", 1, "10 min", 0)]},
            "secundario": {"foco": "Resistência muscular leve", "exercicios": [
                ("Agachamento livre", 2, "15", 45), ("Remada elástico", 2, "15", 45),
                ("Prancha", 2, "20s", 45)]},
        },
        "intermediário": {
            "principal": {"foco": "Intervalado aeróbico", "exercicios": [
                ("Corrida 3 min moderada / 1 min forte", 6, "ciclos", 0)]},
            "secundario": {"foco": "Circuito funcional", "exercicios": [
                ("Polichinelo", 3, "40s", 20), ("Agachamento com salto", 3, "12", 30),
                ("Remo ergômetro", 3, "3 min", 45)]},
        },
        "avançado": {
            "principal": {"foco": "Alta intensidade contínua", "exercicios": [
                ("Corrida de ritmo (tempo run)", 1, "30 min", 0)]},
            "secundario": {"foco": "Funcional avançado", "exercicios": [
                ("Thruster", 4, "12", 45), ("Box jump", 4, "10", 45),
                ("Battle rope", 4, "40s", 30)]},
        },
    },
    "saúde geral": {
        "iniciante": {
            "principal": {"foco": "Movimento diário e mobilidade", "exercicios": [
                ("Caminhada na esteira", 1, "20 min", 0), ("Mobilidade de quadril", 2, "10", 30)]},
            "secundario": {"foco": "Força leve", "exercicios": [
                ("Agachamento assistido", 2, "12", 45), ("Remada sentada", 2, "12", 45)]},
        },
        "intermediário": {
            "principal": {"foco": "Força geral em máquinas e halteres", "exercicios": [
                ("Leg press", 3, "12", 60), ("Supino máquina", 3, "12", 60),
                ("Puxada frontal", 3, "12", 60)]},
            "secundario": {"foco": "Aeróbico leve", "exercicios": [
                ("Bicicleta ergométrica", 1, "20 min", 0)]},
        },
        "avançado": {
            "principal": {"foco": "Força e estabilidade", "exercicios": [
                ("Agachamento livre", 4, "8", 90), ("Barra fixa assistida", 3, "8", 90),
                ("Supino com halteres", 4, "8", 90)]},
            "secundario": {"foco": "Mobilidade e core", "exercicios": [
                ("Prancha lateral", 3, "30s", 30), ("Mobilidade de ombro e quadril", 2, "10", 30)]},
        },
    },
}



# Exercícios previamente definidos para pedidos por grupo muscular.
# O modo offline consulta esta lista em vez de devolver a série completa.
TREINOS_POR_GRUPO = {
    "bíceps": ["Rosca direta", "Rosca martelo", "Rosca alternada", "Rosca concentrada"],
    "tríceps": ["Tríceps corda", "Tríceps com halter acima da cabeça", "Tríceps testa com halteres"],
    "peito": ["Supino máquina", "Flexão inclinada", "Supino reto"],
    "costas": ["Remada sentada", "Puxada frontal", "Remada curvada"],
    "ombros": ["Desenvolvimento máquina", "Elevação lateral", "Desenvolvimento com halteres"],
    "pernas": ["Leg press", "Agachamento assistido", "Cadeira extensora"],
    "abdômen": ["Prancha", "Abdominal curto", "Prancha lateral"],
    "glúteos": ["Elevação pélvica", "Agachamento assistido", "Afundo alternado"],
    "panturrilhas": ["Panturrilha em pé", "Panturrilha sentado"],
}


def texto_treino_grupo(grupo, nivel, alternativo=False):
    """Treino demonstrativo com exercícios catalogados para um grupo muscular."""
    nivel = normalizar_nivel(nivel)
    exercicios = TREINOS_POR_GRUPO.get(grupo)
    if exercicios is None:
        raise ValueError(f"Grupo muscular não catalogado: {grupo}")
    # O pedido por uma alternativa apresenta outros exercícios quando disponíveis.
    if alternativo and len(exercicios) >= 4:
        escolhidos = exercicios[-2:]
    else:
        escolhidos = exercicios[:2 if nivel == "iniciante" else 3]

    series = 2 if nivel == "iniciante" else 3
    linhas = []
    for nome in escolhidos:
        if nome.lower().startswith("prancha"):
            linhas.append(f"- {nome}: {series}x 20s (descanso 45s)")
        else:
            linhas.append(f"- {nome}: {series}x 10–12 (descanso 60s)")
    return f"Treino de {grupo} — nível {nivel}:\n" + "\n".join(linhas)


def texto_catalogo_por_grupo(nivel):
    """Lista de opções de foco que o Gemini também pode consultar."""
    return "\n\n".join(texto_treino_grupo(grupo, nivel) for grupo in TREINOS_POR_GRUPO)


def normalizar_nivel(nivel):
    nivel = (nivel or "").strip().lower()
    return nivel if nivel in NIVEIS else "iniciante"


def normalizar_objetivo(objetivo):
    objetivo = (objetivo or "").strip().lower()
    return objetivo if objetivo in OBJETIVOS else "saúde geral"


def montar_serie(nivel, objetivo):
    """Devolve aquecimento + treino principal + treino secundário em um dict."""
    nivel = normalizar_nivel(nivel)
    objetivo = normalizar_objetivo(objetivo)
    treino = TREINOS[objetivo][nivel]

    def lista(bloco):
        return [{"exercicio": e, "series": s, "repeticoes": r, "descanso_s": d}
                for (e, s, r, d) in bloco["exercicios"]]

    return {
        "nivel": nivel,
        "objetivo": objetivo,
        "aquecimento": [AQUECIMENTOS[k] for k in AQUECIMENTO_POR_NIVEL[nivel]],
        "principal": {"foco": treino["principal"]["foco"], "exercicios": lista(treino["principal"])},
        "secundario": {"foco": treino["secundario"]["foco"], "exercicios": lista(treino["secundario"])},
    }


def _linhas(bloco):
    out = []
    for x in bloco["exercicios"]:
        desc = f" (descanso {x['descanso_s']}s)" if x["descanso_s"] else ""
        out.append(f"- {x['exercicio']}: {x['series']}x {x['repeticoes']}{desc}")
    return "\n".join(out)


def texto_aquecimento(nivel):
    nivel = normalizar_nivel(nivel)
    linhas = [f"- {a['nome']} ({a['duracao_min']} min): {a['descricao']}"
              for a in (AQUECIMENTOS[k] for k in AQUECIMENTO_POR_NIVEL[nivel])]
    return "\n".join(linhas)


def texto_serie(nivel, objetivo):
    s = montar_serie(nivel, objetivo)
    return (
        f"Aquecimento:\n{texto_aquecimento(s['nivel'])}\n\n"
        f"Treino principal — {s['principal']['foco']}:\n{_linhas(s['principal'])}\n\n"
        f"Treino secundário — {s['secundario']['foco']}:\n{_linhas(s['secundario'])}"
    )


def classificar_nivel(meses_matricula, frequencia_semanal):
    """Sugestão simples de nível de condicionamento (o aluno pode corrigir)."""
    if meses_matricula < 3 or frequencia_semanal <= 2:
        return "iniciante"
    if meses_matricula < 12 or frequencia_semanal <= 4:
        return "intermediário"
    return "avançado"
