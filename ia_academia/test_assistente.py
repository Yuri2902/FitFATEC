"""Testa os 5 fluxos conversacionais da Kiara no modo offline (sem API)."""
import sys
import unittest

# Outros testes substituem "assistente" por um mock; aqui queremos o módulo real
sys.modules.pop("assistente", None)
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
    def test_fluxo1_serie_de_condicionamento(self):
        r1 = kiara("Quero uma série de condicionamento")
        self.assertIn("aquecimento", r1.lower())
        r2 = kiara("Quero uma série de condicionamento", "Sim")
        self.assertIn("matrícula", r2.lower())
        r3 = kiara("Quero uma série de condicionamento", "Sim", "20260001")
        self.assertIn("Treino principal", r3)

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
