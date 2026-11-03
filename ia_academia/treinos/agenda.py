from datetime import datetime, time, timedelta

from .regras import DIAS_SEMANA, NOMES_DIAS

# dia da semana (0 = segunda): (hora que abre, hora que fecha). Domingo fechado.
FUNCIONAMENTO = {0: (6, 22), 1: (6, 22), 2: (6, 22), 3: (6, 22), 4: (6, 22), 5: (8, 14)}

# grade None = horário livre, com reserva de hora em hora enquanto a academia estiver aberta
ATIVIDADES = {
    "musculacao": {
        "nome": "Musculação",
        "duracao_min": 60,
        "vagas": 25,
        "grade": None,
    },
    "funcional": {
        "nome": "Treino funcional",
        "duracao_min": 45,
        "vagas": 15,
        "grade": {0: ("07:00", "19:00"), 2: ("07:00", "19:00"), 4: ("07:00", "19:00")},
    },
    "spinning": {
        "nome": "Spinning",
        "duracao_min": 45,
        "vagas": 20,
        "grade": {1: ("07:00", "20:00"), 3: ("07:00", "20:00"), 5: ("09:00",)},
    },
    "alongamento": {
        "nome": "Alongamento e mobilidade",
        "duracao_min": 30,
        "vagas": 15,
        "grade": {0: ("18:00",), 2: ("18:00",), 5: ("10:30",)},
    },
}

ANTECEDENCIA_MIN_HORAS = 1
JANELA_DIAS = 14
PRAZO_CANCELAMENTO_HORAS = 2
LIMITE_POR_DIA = 2


class ErroAgenda(ValueError):
    pass


def validar_atividade(codigo):
    if codigo not in ATIVIDADES:
        opcoes = ", ".join(ATIVIDADES)
        raise ErroAgenda(f"Atividade inválida. Opções: {opcoes}.")
    return ATIVIDADES[codigo]


def horarios_do_dia(atividade, dia):
    config = validar_atividade(atividade)
    semana = dia.weekday()
    if semana not in FUNCIONAMENTO:
        return []
    if config["grade"] is None:
        abre, fecha = FUNCIONAMENTO[semana]
        return [datetime.combine(dia, time(hora)) for hora in range(abre, fecha)]
    return [datetime.combine(dia, time.fromisoformat(h)) for h in config["grade"].get(semana, ())]


def horarios_disponiveis(atividade, dia, ocupacao, agora):
    """ocupacao: dicionário {inicio: quantidade de agendamentos ativos}."""
    vagas_total = validar_atividade(atividade)["vagas"]
    primeiro = agora + timedelta(hours=ANTECEDENCIA_MIN_HORAS)
    ultimo = agora + timedelta(days=JANELA_DIAS)
    livres = []
    for inicio in horarios_do_dia(atividade, dia):
        if inicio < primeiro or inicio > ultimo:
            continue
        vagas = vagas_total - ocupacao.get(inicio, 0)
        if vagas > 0:
            livres.append({"inicio": inicio.isoformat(timespec="minutes"), "vagas": vagas})
    return livres


def _fim(atividade, inicio):
    duracao = ATIVIDADES.get(atividade, {}).get("duracao_min", 60)
    return inicio + timedelta(minutes=duracao)


def validar_agendamento(atividade, inicio, agendamentos_do_dia, ocupados, agora):
    """Levanta ErroAgenda se o aluno não puder reservar esse horário.

    agendamentos_do_dia: agendamentos do aluno na mesma data (com atividade, inicio e status).
    ocupados: quantas reservas ativas já existem nessa atividade e horário.
    """
    config = validar_atividade(atividade)
    if inicio < agora + timedelta(hours=ANTECEDENCIA_MIN_HORAS):
        raise ErroAgenda(f"O agendamento precisa ser feito com pelo menos {ANTECEDENCIA_MIN_HORAS}h de antecedência.")
    if inicio > agora + timedelta(days=JANELA_DIAS):
        raise ErroAgenda(f"Só dá para agendar com até {JANELA_DIAS} dias de antecedência.")
    if inicio not in horarios_do_dia(atividade, inicio.date()):
        raise ErroAgenda(f"{config['nome']} não tem horário nesse dia e hora. Consulte os horários livres.")
    if ocupados >= config["vagas"]:
        raise ErroAgenda("Esse horário está lotado.")

    ativos = [a for a in agendamentos_do_dia if a["status"] == "agendado"]
    fim = _fim(atividade, inicio)
    for outro in ativos:
        if inicio < _fim(outro["atividade"], outro["inicio"]) and outro["inicio"] < fim:
            raise ErroAgenda("Você já tem um agendamento que coincide com esse horário.")
    if len(ativos) >= LIMITE_POR_DIA:
        raise ErroAgenda(f"Limite de {LIMITE_POR_DIA} agendamentos por dia atingido.")


def validar_cancelamento(agendamento, agora):
    if agendamento["status"] != "agendado":
        raise ErroAgenda("Esse agendamento não está ativo.")
    if agendamento["inicio"] - agora < timedelta(hours=PRAZO_CANCELAMENTO_HORAS):
        raise ErroAgenda(f"O cancelamento só pode ser feito até {PRAZO_CANCELAMENTO_HORAS}h antes do horário.")


def _texto_funcionamento():
    partes = []
    for semana, (abre, fecha) in FUNCIONAMENTO.items():
        partes.append(f"{NOMES_DIAS[DIAS_SEMANA[semana]]} das {abre:02d}:00 às {fecha:02d}:00")
    fechados = [NOMES_DIAS[DIAS_SEMANA[d]] for d in range(7) if d not in FUNCIONAMENTO]
    texto = "; ".join(partes)
    if fechados:
        texto += "; fechado: " + ", ".join(fechados)
    return texto


def listar_atividades():
    atividades = []
    for codigo, config in ATIVIDADES.items():
        grade = None
        if config["grade"] is not None:
            grade = {DIAS_SEMANA[d]: list(h) for d, h in config["grade"].items()}
        atividades.append({
            "codigo": codigo,
            "nome": config["nome"],
            "duracao_min": config["duracao_min"],
            "vagas": config["vagas"],
            "grade": grade,
        })
    return {
        "funcionamento": {DIAS_SEMANA[d]: [f"{a:02d}:00", f"{f:02d}:00"] for d, (a, f) in FUNCIONAMENTO.items()},
        "atividades": atividades,
        "regras": {
            "antecedencia_minima_horas": ANTECEDENCIA_MIN_HORAS,
            "janela_dias": JANELA_DIAS,
            "prazo_cancelamento_horas": PRAZO_CANCELAMENTO_HORAS,
            "limite_por_dia": LIMITE_POR_DIA,
        },
    }


def resumo_agenda():
    linhas = [f"Funcionamento: {_texto_funcionamento()}."]
    for config in ATIVIDADES.values():
        if config["grade"] is None:
            linhas.append(f"{config['nome']}: horário livre, reservas de hora em hora, {config['vagas']} vagas por horário.")
            continue
        dias = "; ".join(
            f"{NOMES_DIAS[DIAS_SEMANA[d]]} às {' e '.join(h)}" for d, h in config["grade"].items()
        )
        linhas.append(f"{config['nome']} ({config['duracao_min']} min, {config['vagas']} vagas): {dias}.")
    linhas.append(
        f"Regras: reservar com pelo menos {ANTECEDENCIA_MIN_HORAS}h de antecedência e no máximo {JANELA_DIAS} dias antes; "
        f"cancelar até {PRAZO_CANCELAMENTO_HORAS}h antes; no máximo {LIMITE_POR_DIA} reservas por dia."
    )
    return "\n".join(linhas)
