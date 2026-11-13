"""Garante que o chat exige login e não aceita matrícula enviada pelo navegador."""
import unittest
from unittest.mock import patch
from servidor import app

ALUNO = {"idade": 25, "objetivo": "condicionamento", "nivel": "iniciante",
         "frequencia_semanal": 3, "meses_matricula": 3, "faltas_ultimo_mes": 2}
HIST = [{"role": "user", "content": "treino de bíceps"}]

class TestChatSessao(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_chat_sem_login(self):
        r = self.client.post("/api/chat", json={"aluno": ALUNO, "historico": HIST})
        self.assertEqual(r.status_code, 401)

    @patch("servidor.risco_de_desistir", return_value=0.25)
    @patch("servidor.responder_com_plano", return_value=("Treino de bíceps", "gemini", {"exercicios": []}))
    def test_chat_com_login_e_modo(self, ia, _):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {"id_aluno": 17, "nome": "Ana", "matricula": "20260017", "papel": "aluno"}
        r = self.client.post("/api/chat", json={"aluno": dict(ALUNO, matricula="99999999"), "historico": HIST})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["modo"], "gemini")
        self.assertEqual(r.get_json()["resposta"], "Treino de bíceps")
        self.assertEqual(ia.call_args.args[0]["nome"], "Ana")
        self.assertNotIn("matricula", ia.call_args.args[0])

    def test_historico_invalido(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {"id_aluno": 17}
        r = self.client.post("/api/chat", json={"aluno": ALUNO, "historico": [{"role":"model","content":"x"}]})
        self.assertEqual(r.status_code, 400)

if __name__ == "__main__":
    unittest.main()
