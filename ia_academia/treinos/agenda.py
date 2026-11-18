"""Regras de agendamento de aulas (Dev 3).

O servidor.py já confere o básico: formato da data, horário entre 06:00 e 21:00,
modalidade conhecida e vagas no horário. Este módulo junta as regras que faltavam,
sem depender de banco, para poderem ser testadas sozinhas:

- antecedência mínima: não dá para marcar um horário que já passou nem um que
  começa em menos de 1 hora (antes, dava para marcar hoje às 06:00 às 15:00);
- sem conflito: o aluno não pode ter duas aulas começando com menos de 1 hora
  de diferença no mesmo dia;
- limite diário: no máximo 2 aulas ativas por dia para cada aluno;
- cancelamento: só aulas ativas e só até 2 horas antes do início.
"""
import re
from datetime import datetime, time, timedelta

ANTECEDENCIA_MINIMA_HORAS = 1
LIMITE_AULAS_POR_DIA = 2
PRAZO_CANCELAMENTO_HORAS = 2
DURACAO_AULA_MINUTOS = 60

# O banco aceita os dois jeitos de escrever o status (legado e novo).
STATUS_ATIVOS = ("agendada", "agendado")


class ErroAgenda(ValueError):
    """Regra de agendamento não atendida. A mensagem é mostrada para o aluno."""


def horario_inicio(horario):
    """Converte o horário salvo em datetime.time.

    Aceita os formatos que aparecem no projeto: "18:00" (rota /api/agendar),
    "08:00 - 09:00" (tabela grade_horarios), "18h00 às 19h00" com traço (texto da tela)
    e o timedelta que o mysql-connector devolve para colunas do tipo TIME.
    """
    if isinstance(horario, timedelta):
        minutos = int(horario.total_seconds() // 60)
        return time(minutos // 60, minutos % 60)
    texto = str(horario or "").strip().lower().replace("h", ":")
    inicio = re.split(r"\s*[-\u2013]\s*", texto)[0]
    try:
        horas, _, minutos = inicio.partition(":")
        return time(int(horas), int(minutos or 0))
    except ValueError:
        raise ErroAgenda("Horário inválido.")


def inicio_da_aula(data_aula, horario):
    return datetime.combine(data_aula, horario_inicio(horario))


def aulas_ativas(agendamentos):
    return [a for a in agendamentos if a.get("status") in STATUS_ATIVOS]


def validar_novo_agendamento(data_aula, horario, agendamentos_do_dia, agora=None):
    """Levanta ErroAgenda se o aluno não puder marcar essa aula.

    agendamentos_do_dia: aulas do próprio aluno na mesma data (data_aula, horario, status).
    agora: só é passado nos testes; na rota vale o horário do servidor.
    """
    agora = agora or datetime.now()
    inicio = inicio_da_aula(data_aula, horario)

    if inicio < agora + timedelta(hours=ANTECEDENCIA_MINIMA_HORAS):
        raise ErroAgenda(
            f"Esse horário já passou ou começa em menos de {ANTECEDENCIA_MINIMA_HORAS}h. "
            "Escolha um horário mais tarde."
        )

    ativas = aulas_ativas(agendamentos_do_dia)
    for aula in ativas:
        outra = inicio_da_aula(aula["data_aula"], aula["horario"])
        if abs((outra - inicio).total_seconds()) < DURACAO_AULA_MINUTOS * 60:
            raise ErroAgenda(f"Você já tem uma aula às {outra:%H:%M} nesse dia.")

    if len(ativas) >= LIMITE_AULAS_POR_DIA:
        raise ErroAgenda(
            f"Você já tem {LIMITE_AULAS_POR_DIA} aulas agendadas nesse dia. Cancele uma para marcar outra."
        )


def validar_cancelamento(agendamento, agora=None):
    """Levanta ErroAgenda se a aula não puder mais ser cancelada."""
    agora = agora or datetime.now()
    if agendamento.get("status") not in STATUS_ATIVOS:
        raise ErroAgenda("Esse agendamento já foi cancelado ou concluído.")
    inicio = inicio_da_aula(agendamento["data_aula"], agendamento["horario"])
    if inicio - agora < timedelta(hours=PRAZO_CANCELAMENTO_HORAS):
        raise ErroAgenda(
            f"O cancelamento só pode ser feito até {PRAZO_CANCELAMENTO_HORAS}h antes da aula."
        )
