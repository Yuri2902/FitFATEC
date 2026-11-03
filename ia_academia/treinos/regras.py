from .catalogo import NIVEIS, sem_acento

OBJETIVOS = ("hipertrofia", "emagrecimento", "condicionamento", "saude")
LOCAIS = ("academia", "casa")
RESTRICOES = ("joelho", "lombar", "ombro", "punho")
DIAS_SEMANA = ("seg", "ter", "qua", "qui", "sex", "sab", "dom")

NOMES_DIAS = {
    "seg": "segunda", "ter": "terça", "qua": "quarta", "qui": "quinta",
    "sex": "sexta", "sab": "sábado", "dom": "domingo",
}
NOMES_OBJETIVOS = {
    "hipertrofia": "ganho de massa muscular",
    "emagrecimento": "emagrecimento",
    "condicionamento": "condicionamento físico",
    "saude": "saúde geral",
}
NOMES_NIVEIS = {"iniciante": "iniciante", "intermediario": "intermediário", "avancado": "avançado"}

SINONIMOS_OBJETIVO = {
    "hipertrofia": "hipertrofia",
    "ganhar massa muscular": "hipertrofia",
    "ganhar massa": "hipertrofia",
    "massa muscular": "hipertrofia",
    "emagrecimento": "emagrecimento",
    "emagrecer": "emagrecimento",
    "perder peso": "emagrecimento",
    "condicionamento": "condicionamento",
    "condicionamento fisico": "condicionamento",
    "resistencia": "condicionamento",
    "saude": "saude",
    "saude geral": "saude",
    "qualidade de vida": "saude",
}

DIAS_PADRAO = {
    1: ("seg",),
    2: ("seg", "qui"),
    3: ("seg", "qua", "sex"),
    4: ("seg", "ter", "qui", "sex"),
    5: ("seg", "ter", "qua", "qui", "sex"),
    6: ("seg", "ter", "qua", "qui", "sex", "sab"),
    7: DIAS_SEMANA,
}

MINUTOS_PADRAO = 60
MINUTOS_MIN = 20
MINUTOS_MAX = 120
MAX_DIAS_INICIANTE = 4
MAX_DIAS_TREINO = 6
MIN_EXERCICIOS = 3
MAX_EXERCICIOS = {"iniciante": 6, "intermediario": 7, "avancado": 8}

# (séries, repetições, descanso em segundos) do treino principal
PRESCRICAO = {
    "hipertrofia": {
        "iniciante": (3, "10-12", 60),
        "intermediario": (4, "8-12", 75),
        "avancado": (4, "6-10", 90),
    },
    "emagrecimento": {
        "iniciante": (2, "12-15", 45),
        "intermediario": (3, "12-15", 40),
        "avancado": (3, "15-20", 30),
    },
    "condicionamento": {
        "iniciante": (2, "12-15", 45),
        "intermediario": (3, "15", 30),
        "avancado": (4, "15-20", 20),
    },
    "saude": {
        "iniciante": (2, "10-12", 60),
        "intermediario": (3, "10-12", 60),
        "avancado": (3, "8-12", 60),
    },
}

ORIENTACAO_CARGA = {
    "hipertrofia": "Use uma carga que deixe só 1 ou 2 repetições sobrando no fim da série.",
    "emagrecimento": "Carga moderada e ritmo constante, descansando só o tempo indicado.",
    "condicionamento": "Carga leve a moderada, priorizando o ritmo e pouco descanso.",
    "saude": "Carga confortável, com execução controlada e sem chegar à falha.",
}

SEGUNDOS_ISOMETRIA = {"iniciante": 20, "intermediario": 30, "avancado": 45}

# (minutos, como fazer) do cardio no fim do treino
CARDIO_FINAL = {
    "emagrecimento": {
        "iniciante": (15, "Ritmo leve a moderado, em que ainda dá para conversar."),
        "intermediario": (20, "Ritmo moderado e constante."),
        "avancado": (20, "Intervalado: 1 minuto forte e 1 minuto leve."),
    },
    "condicionamento": {
        "iniciante": (10, "Ritmo moderado e constante."),
        "intermediario": (12, "Intervalado: 30 segundos forte e 60 segundos leve."),
        "avancado": (15, "Intervalado: 40 segundos forte e 20 segundos leve."),
    },
    "saude": {
        "iniciante": (10, "Ritmo confortável."),
        "intermediario": (10, "Ritmo moderado."),
        "avancado": (15, "Ritmo moderado."),
    },
}

# tipo de sessão: (nome, foco do aquecimento, grupos na ordem em que entram no treino)
SESSOES = {
    "corpo_inteiro": ("Corpo inteiro", "geral",
                      ("quadriceps", "peito", "costas", "posterior", "ombros", "gluteos", "biceps", "triceps")),
    "empurrar": ("Peito, ombros e tríceps", "superior",
                 ("peito", "ombros", "peito", "triceps", "ombros", "triceps", "peito", "ombros")),
    "puxar": ("Costas e bíceps", "superior",
              ("costas", "costas", "biceps", "costas", "biceps", "costas", "biceps")),
    "pernas": ("Pernas e glúteos", "inferior",
               ("quadriceps", "posterior", "gluteos", "quadriceps", "panturrilha", "posterior", "gluteos", "quadriceps")),
    "superiores": ("Membros superiores", "superior",
                   ("peito", "costas", "ombros", "costas", "peito", "biceps", "triceps", "ombros")),
    "inferiores": ("Membros inferiores", "inferior",
                   ("quadriceps", "posterior", "gluteos", "quadriceps", "panturrilha", "posterior", "gluteos")),
}

EXPLICACAO_NIVEL = {
    "iniciante": "Começando agora ou voltando depois de um tempo parado. O foco é aprender a execução, "
                 "com máquinas e cargas leves.",
    "intermediario": "Já treina com regularidade há alguns meses. Dá para dividir o treino por grupos "
                     "musculares e aumentar o volume.",
    "avancado": "Treina há mais de um ano com constância e tem boa base de força. Aguenta mais volume "
                "e exercícios livres mais técnicos.",
}


class ErroPerfil(ValueError):
    pass


def _inteiro(valor, campo, minimo=0):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ErroPerfil(f"Valor inválido para {campo}.")
    if numero < minimo:
        raise ErroPerfil(f"Valor inválido para {campo}.")
    return numero


def _sim(valor):
    if isinstance(valor, str):
        return sem_acento(valor) in ("sim", "s", "true", "1")
    return bool(valor)


def normalizar_objetivo(valor):
    objetivo = SINONIMOS_OBJETIVO.get(sem_acento(valor or ""))
    if objetivo is None:
        raise ErroPerfil("Objetivo inválido. Use hipertrofia, emagrecimento, condicionamento ou saude.")
    return objetivo


def normalizar_nivel(valor):
    nivel = sem_acento(valor or "")
    if nivel not in NIVEIS:
        raise ErroPerfil("Nível inválido. Use iniciante, intermediario ou avancado.")
    return nivel


def normalizar_dia(valor):
    if isinstance(valor, int) or (isinstance(valor, str) and valor.strip().isdigit()):
        numero = int(valor)
        if 1 <= numero <= 7:
            return DIAS_SEMANA[numero - 1]
    else:
        dia = sem_acento(valor)[:3]
        if dia in DIAS_SEMANA:
            return dia
    raise ErroPerfil(f"Dia da semana inválido: {valor}.")


def _normalizar_dias(lista, quantidade):
    if lista:
        if isinstance(lista, str):
            lista = lista.split(",")
        escolhidos = {normalizar_dia(d) for d in lista}
        return [d for d in DIAS_SEMANA if d in escolhidos]
    if quantidade in (None, ""):
        quantidade = 3
    quantidade = _inteiro(quantidade, "dias_por_semana")
    if not 1 <= quantidade <= 7:
        raise ErroPerfil("Informe de 1 a 7 dias por semana.")
    return list(DIAS_PADRAO[quantidade])


def _normalizar_restricoes(lista):
    if isinstance(lista, str):
        lista = lista.split(",")
    escolhidas = set()
    for item in lista:
        restricao = sem_acento(item)
        if not restricao:
            continue
        if restricao not in RESTRICOES:
            raise ErroPerfil(f"Restrição desconhecida: {item}. Use joelho, lombar, ombro ou punho.")
        escolhidas.add(restricao)
    return [r for r in RESTRICOES if r in escolhidas]


def normalizar_perfil(dados):
    if not isinstance(dados, dict):
        raise ErroPerfil("Envie os dados do perfil como um objeto JSON.")
    minutos = _inteiro(dados.get("minutos_por_sessao") or MINUTOS_PADRAO, "minutos_por_sessao")
    if not MINUTOS_MIN <= minutos <= MINUTOS_MAX:
        raise ErroPerfil(f"O tempo por sessão deve ficar entre {MINUTOS_MIN} e {MINUTOS_MAX} minutos.")
    local = sem_acento(dados.get("local") or "academia")
    if local not in LOCAIS:
        raise ErroPerfil("Local inválido. Use academia ou casa.")
    return {
        "objetivo": normalizar_objetivo(dados.get("objetivo")),
        "nivel": normalizar_nivel(dados.get("nivel")),
        "dias_semana": _normalizar_dias(dados.get("dias_semana"), dados.get("dias_por_semana")),
        "minutos_por_sessao": minutos,
        "local": local,
        "restricoes": _normalizar_restricoes(dados.get("restricoes") or []),
    }


def prescricao(objetivo, nivel):
    series, repeticoes, intervalo = PRESCRICAO[objetivo][nivel]
    return {
        "series": series,
        "repeticoes": repeticoes,
        "intervalo_seg": intervalo,
        "carga": ORIENTACAO_CARGA[objetivo],
    }


def montar_divisao(quantidade_dias, nivel):
    """Devolve o nome da divisão e uma lista (tipo de sessão, variação) com um item por dia."""
    limite = MAX_DIAS_INICIANTE if nivel == "iniciante" else MAX_DIAS_TREINO
    treinos = min(quantidade_dias, limite)

    if treinos <= 2 or (treinos == 3 and nivel == "iniciante"):
        nome = "Corpo inteiro"
        sequencia = [("corpo_inteiro", i % 2) for i in range(treinos)]
    elif treinos == 3:
        nome = "ABC (empurrar, puxar e pernas)"
        sequencia = [("empurrar", 0), ("puxar", 0), ("pernas", 0)]
    elif treinos == 4:
        nome = "Superiores e inferiores"
        sequencia = [("superiores", 0), ("inferiores", 0), ("superiores", 1), ("inferiores", 1)]
    elif treinos == 5:
        nome = "ABC com superiores e inferiores"
        sequencia = [("empurrar", 0), ("puxar", 0), ("pernas", 0), ("superiores", 0), ("inferiores", 0)]
    else:
        nome = "ABC duas vezes por semana"
        sequencia = [("empurrar", 0), ("puxar", 0), ("pernas", 0),
                     ("empurrar", 1), ("puxar", 1), ("pernas", 1)]

    # dias que sobram viram recuperação ativa, intercalados com os treinos
    extras = quantidade_dias - treinos
    if extras:
        intercalada = []
        for sessao in sequencia:
            intercalada.append(sessao)
            if extras:
                intercalada.append(("recuperacao", 0))
                extras -= 1
        intercalada.extend([("recuperacao", 0)] * extras)
        sequencia = intercalada
    return nome, sequencia


def avaliar_nivel(respostas):
    respostas = respostas or {}
    meses = _inteiro(respostas.get("meses_treinando") or 0, "meses_treinando")
    vezes = _inteiro(respostas.get("treinos_por_semana") or 0, "treinos_por_semana")
    flexoes = _inteiro(respostas.get("flexoes") or 0, "flexoes")
    aerobico = _sim(respostas.get("aguenta_20min_aerobico"))

    pontos = 0
    pontos += 0 if meses < 3 else 1 if meses < 12 else 2
    pontos += 0 if vezes <= 1 else 1 if vezes <= 3 else 2
    pontos += 0 if flexoes < 10 else 1 if flexoes < 25 else 2
    pontos += 1 if aerobico else 0

    if meses < 3 or pontos <= 2:
        nivel = "iniciante"
    elif meses < 12 or pontos <= 5:
        nivel = "intermediario"
    else:
        nivel = "avancado"
    return {
        "nivel": nivel,
        "pontos": pontos,
        "pontuacao_maxima": 7,
        "explicacao": EXPLICACAO_NIVEL[nivel],
    }
