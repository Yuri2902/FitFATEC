"""Testa os 5 fluxos conversacionais da Kiara no modo offline (sem API)."""
import unittest

import assistente

ALUNO = {"idade": 25, "objetivo": "condicionamento", "nivel": "iniciante",
         "frequencia_semanal": 3, "meses_matricula": 3, "faltas_ultimo_mes": 2}


def kiara(*falas):
    """Simula a conversa; falas ímpares são do aluno. Devolve a última resposta."""
    hist = []
    resp = ""
    for fala in falas:
        hist.append({"role": "user", "content": fala})
        resp = assistente.responder_offline(ALUNO, hist, 0.2)
        hist.append({"role": "assistant", "content": resp})
    return resp


class TestFluxos(unittest.TestCase):
    def test_fluxo1_serie_sem_pedir_matricula(self):
        r1 = kiara("Quero uma série de condicionamento")
        self.assertIn("Treino principal", r1)
        self.assertNotIn("informe seu número de matrícula", r1.lower())
        r2 = kiara("Quais aquecimentos existem?", "Sim")
        self.assertIn("Treino principal", r2)
        self.assertNotIn("informe seu número de matrícula", r2.lower())

    def test_resposta_marca_modo_offline(self):
        from unittest.mock import patch
        with patch.object(assistente, "client", None):
            resposta, modo = assistente.responder_com_modo(ALUNO, [{"role":"user","content":"treino de bíceps"}])
        self.assertEqual(modo, "offline")
        self.assertIn("bíceps", resposta)

    def test_resposta_marca_modo_gemini_mockado(self):
        from unittest.mock import patch, MagicMock
        cliente = MagicMock()
        cliente.models.generate_content.return_value.text = "Resposta gerada de exemplo"
        with patch.object(assistente, "client", cliente), patch.object(assistente, "_types", MagicMock()):
            resposta, modo = assistente.responder_com_modo(ALUNO, [{"role":"user","content":"oi"}])
        self.assertEqual(modo, "gemini")
        self.assertEqual(resposta, "Resposta gerada de exemplo")

    def test_agendamento_sem_pedir_matricula(self):
        resp = kiara("Quero agendar uma aula")
        self.assertIn("conta já está identificada", resp)
        self.assertNotIn("informe sua matrícula", resp)

    def test_pedido_biceps_nao_repete_corpo_inteiro(self):
        aluno = dict(ALUNO, objetivo="ganhar massa muscular")
        hist = [
            {"role": "assistant", "content": "Matrícula 20260001 recebida! Aqui está sua série."},
            {"role": "user", "content": "treino de biceps por favor"},
        ]
        resp = assistente.responder_offline(aluno, hist, 0.2)
        self.assertIn("Treino de bíceps", resp)
        self.assertIn("Rosca direta", resp)
        self.assertNotIn("Leg press", resp)

    def test_pedido_alternativa_biceps(self):
        resp = kiara("outro treino de bíceps por favor")
        self.assertIn("Rosca concentrada", resp)
        self.assertNotIn("Rosca direta", resp)

    def test_outro_treino_geral_nao_finge_gerar_novo(self):
        resp = kiara("Quero uma série", "Quero outro treino diferente")
        self.assertIn("não quero repetir", resp)
        self.assertNotIn("Leg press", resp)

    def test_pedido_triceps_sem_acento(self):
        resp = kiara("Me passa um treino de triceps")
        self.assertIn("Treino de tríceps", resp)
        self.assertNotIn("Caminhada/trote", resp)

    def test_fluxo2_agendar_aula(self):
        self.assertIn("Agendar aula", kiara("Quero marcar uma aula"))

    def test_fluxo3_aquecimento(self):
        self.assertIn("esteira", kiara("Quais aquecimentos existem?").lower())

    def test_fluxo4_treino_principal_e_secundario(self):
        r = kiara("Qual o treino principal e o secundário?")
        self.assertIn("Treino principal", r)
        self.assertIn("Treino secundário", r)

    def test_fluxo5_nivel_de_condicionamento(self):
        self.assertIn("nível", kiara("Qual meu nível de condicionamento?").lower())

    def test_fluxo_motivacional(self):
        self.assertIn("20 minutos", kiara("Estou desanimado, faltei muito"))

    def test_risco_alto_nao_exibe_percentual(self):
        hist = [{"role": "user", "content": "Quero um treino"}]
        resp = assistente.responder_offline(ALUNO, hist, 0.9)
        self.assertNotIn("%", resp)


if __name__ == "__main__":
    unittest.main()
