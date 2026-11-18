"""Dev 3: regras de agendamento (treinos/agenda.py), sem banco."""
import unittest
from datetime import date, datetime, time, timedelta

from treinos.agenda import ErroAgenda, horario_inicio, validar_cancelamento, validar_novo_agendamento

DIA = date(2026, 11, 20)
AGORA = datetime(2026, 11, 20, 12, 0)


def aula(horario, status="agendada", dia=DIA):
    return {"data_aula": dia, "horario": horario, "status": status}


class TestHorario(unittest.TestCase):
    def test_formatos_usados_no_projeto(self):
        self.assertEqual(horario_inicio("18:00"), time(18, 0))
        self.assertEqual(horario_inicio("08:00 - 09:00"), time(8, 0))
        self.assertEqual(horario_inicio("18h00 \u2013 19h00"), time(18, 0))  # traço usado na tela
        self.assertEqual(horario_inicio(timedelta(hours=7, minutes=30)), time(7, 30))

    def test_horario_invalido(self):
        with self.assertRaises(ErroAgenda):
            horario_inicio("amanhã cedo")


class TestNovoAgendamento(unittest.TestCase):
    def test_agendamento_valido(self):
        validar_novo_agendamento(DIA, "18:00", [], AGORA)

    def test_horario_que_ja_passou(self):
        with self.assertRaises(ErroAgenda):
            validar_novo_agendamento(DIA, "08:00", [], AGORA)

    def test_menos_de_uma_hora_de_antecedencia(self):
        with self.assertRaises(ErroAgenda):
            validar_novo_agendamento(DIA, "12:00", [], datetime(2026, 11, 20, 11, 30))

    def test_amanha_cedo_pode(self):
        validar_novo_agendamento(DIA + timedelta(days=1), "06:00", [], AGORA)

    def test_conflito_com_outra_aula(self):
        with self.assertRaises(ErroAgenda):
            validar_novo_agendamento(DIA, "18:00", [aula("18:00 - 19:00")], AGORA)

    def test_aula_seguinte_pode(self):
        validar_novo_agendamento(DIA, "19:00", [aula("18:00")], AGORA)

    def test_limite_de_duas_aulas_por_dia(self):
        with self.assertRaises(ErroAgenda):
            validar_novo_agendamento(DIA, "20:00", [aula("14:00"), aula("17:00")], AGORA)

    def test_aula_cancelada_nao_conta(self):
        validar_novo_agendamento(DIA, "18:00", [aula("18:00", "cancelado"), aula("14:00", "cancelada")], AGORA)


class TestCancelamento(unittest.TestCase):
    def test_cancelamento_valido(self):
        validar_cancelamento(aula("18:00"), AGORA)

    def test_menos_de_duas_horas_antes(self):
        with self.assertRaises(ErroAgenda):
            validar_cancelamento(aula("13:30"), AGORA)

    def test_aula_ja_cancelada(self):
        with self.assertRaises(ErroAgenda):
            validar_cancelamento(aula("18:00", "cancelado"), AGORA)


if __name__ == "__main__":
    unittest.main()
