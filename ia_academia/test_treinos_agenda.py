import unittest
from datetime import date, datetime

from treinos.agenda import (
    ErroAgenda,
    horarios_disponiveis,
    horarios_do_dia,
    listar_atividades,
    validar_agendamento,
    validar_cancelamento,
)

SEGUNDA = date(2026, 11, 9)
TERCA = date(2026, 11, 10)
SABADO = date(2026, 11, 14)
DOMINGO = date(2026, 11, 15)
AGORA = datetime(2026, 11, 8, 12, 0)


def reserva(atividade, inicio, status="agendado"):
    return {"atividade": atividade, "inicio": inicio, "status": status}


class TestHorarios(unittest.TestCase):
    def test_musculacao_segue_o_funcionamento(self):
        dias_uteis = horarios_do_dia("musculacao", SEGUNDA)
        self.assertEqual(dias_uteis[0], datetime(2026, 11, 9, 6, 0))
        self.assertEqual(dias_uteis[-1], datetime(2026, 11, 9, 21, 0))
        self.assertEqual(len(horarios_do_dia("musculacao", SABADO)), 6)
        self.assertEqual(horarios_do_dia("musculacao", DOMINGO), [])

    def test_aula_coletiva_segue_a_grade(self):
        self.assertEqual(horarios_do_dia("spinning", SEGUNDA), [])
        self.assertEqual(
            horarios_do_dia("spinning", TERCA),
            [datetime(2026, 11, 10, 7, 0), datetime(2026, 11, 10, 20, 0)],
        )

    def test_atividade_inexistente(self):
        with self.assertRaises(ErroAgenda):
            horarios_do_dia("boxe", SEGUNDA)

    def test_disponiveis_mostra_vagas_e_esconde_lotados(self):
        ocupacao = {datetime(2026, 11, 10, 7, 0): 20, datetime(2026, 11, 10, 20, 0): 5}
        livres = horarios_disponiveis("spinning", TERCA, ocupacao, AGORA)
        self.assertEqual(livres, [{"inicio": "2026-11-10T20:00", "vagas": 15}])

    def test_disponiveis_esconde_horarios_que_ja_passaram(self):
        agora = datetime(2026, 11, 9, 10, 30)
        livres = horarios_disponiveis("musculacao", SEGUNDA, {}, agora)
        self.assertEqual(livres[0]["inicio"], "2026-11-09T12:00")

    def test_listar_atividades(self):
        dados = listar_atividades()
        codigos = [a["codigo"] for a in dados["atividades"]]
        self.assertIn("funcional", codigos)
        self.assertNotIn("dom", dados["funcionamento"])


class TestValidarAgendamento(unittest.TestCase):
    def test_agendamento_valido(self):
        validar_agendamento("funcional", datetime(2026, 11, 9, 19, 0), [], 0, AGORA)

    def test_antecedencia_minima(self):
        agora = datetime(2026, 11, 9, 18, 30)
        with self.assertRaises(ErroAgenda):
            validar_agendamento("funcional", datetime(2026, 11, 9, 19, 0), [], 0, agora)

    def test_janela_maxima(self):
        with self.assertRaises(ErroAgenda):
            validar_agendamento("musculacao", datetime(2026, 11, 30, 10, 0), [], 0, AGORA)

    def test_horario_fora_da_grade(self):
        with self.assertRaises(ErroAgenda):
            validar_agendamento("spinning", datetime(2026, 11, 9, 19, 0), [], 0, AGORA)
        with self.assertRaises(ErroAgenda):
            validar_agendamento("musculacao", datetime(2026, 11, 9, 10, 30), [], 0, AGORA)

    def test_horario_lotado(self):
        with self.assertRaises(ErroAgenda):
            validar_agendamento("funcional", datetime(2026, 11, 9, 19, 0), [], 15, AGORA)

    def test_conflito_com_outra_reserva(self):
        existentes = [reserva("musculacao", datetime(2026, 11, 9, 18, 0))]
        with self.assertRaises(ErroAgenda):
            validar_agendamento("alongamento", datetime(2026, 11, 9, 18, 0), existentes, 0, AGORA)

    def test_aula_logo_depois_da_musculacao_pode(self):
        existentes = [reserva("musculacao", datetime(2026, 11, 9, 18, 0))]
        validar_agendamento("funcional", datetime(2026, 11, 9, 19, 0), existentes, 0, AGORA)

    def test_limite_por_dia(self):
        existentes = [
            reserva("musculacao", datetime(2026, 11, 9, 7, 0)),
            reserva("alongamento", datetime(2026, 11, 9, 18, 0)),
        ]
        with self.assertRaises(ErroAgenda):
            validar_agendamento("funcional", datetime(2026, 11, 9, 19, 0), existentes, 0, AGORA)

    def test_reserva_cancelada_nao_conta(self):
        existentes = [
            reserva("musculacao", datetime(2026, 11, 9, 19, 0), status="cancelado"),
            reserva("musculacao", datetime(2026, 11, 9, 7, 0), status="cancelado"),
        ]
        validar_agendamento("funcional", datetime(2026, 11, 9, 19, 0), existentes, 0, AGORA)


class TestCancelamento(unittest.TestCase):
    def test_cancelamento_valido(self):
        validar_cancelamento(reserva("funcional", datetime(2026, 11, 9, 19, 0)), AGORA)

    def test_prazo_de_cancelamento(self):
        agora = datetime(2026, 11, 9, 17, 30)
        with self.assertRaises(ErroAgenda):
            validar_cancelamento(reserva("funcional", datetime(2026, 11, 9, 19, 0)), agora)

    def test_nao_cancela_o_que_nao_esta_ativo(self):
        with self.assertRaises(ErroAgenda):
            validar_cancelamento(reserva("funcional", datetime(2026, 11, 9, 19, 0), status="cancelado"), AGORA)


if __name__ == "__main__":
    unittest.main()
