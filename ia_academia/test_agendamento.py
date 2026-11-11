import sys
import unittest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

sys.modules["assistente"] = MagicMock()
sys.modules["assistente"].responder = MagicMock()
sys.modules["assistente"].risco_de_desistir = MagicMock(return_value=0.1)
sys.modules["mysql"] = MagicMock()
sys.modules["mysql.connector"] = MagicMock()
sys.modules["mysql.connector"].Error = Exception

import servidor
from servidor import app

AMANHA = str(date.today() + timedelta(days=1))


class TestAgendamento(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def agendar(self, **extra):
        corpo = {"matricula": "20260001", "data": AMANHA, "horario": "18:00", "modalidade": "musculação"}
        corpo.update(extra)
        return self.client.post("/api/agendar", json=corpo)

    def test_matricula_invalida(self):
        self.assertEqual(self.agendar(matricula="abc").status_code, 400)

    def test_data_passada(self):
        ontem = str(date.today() - timedelta(days=1))
        self.assertEqual(self.agendar(data=ontem).status_code, 400)

    def test_horario_fora_do_expediente(self):
        self.assertEqual(self.agendar(horario="23:00").status_code, 400)

    def test_modalidade_invalida(self):
        self.assertEqual(self.agendar(modalidade="boxe").status_code, 400)

    @patch.object(servidor, "buscar_aluno_por_matricula", return_value=None)
    def test_matricula_inexistente(self, _):
        self.assertEqual(self.agendar().status_code, 404)

    @patch.object(servidor, "contar_ocupacao", return_value={"18:00": 10})
    @patch.object(servidor, "buscar_aluno_por_matricula", return_value={"id_aluno": 1, "nome": "Ana"})
    def test_horario_lotado(self, *_):
        self.assertEqual(self.agendar().status_code, 409)

    @patch.object(servidor, "inserir_agendamento", return_value=7)
    @patch.object(servidor, "contar_ocupacao", return_value={})
    @patch.object(servidor, "buscar_aluno_por_matricula", return_value={"id_aluno": 1, "nome": "Ana"})
    def test_agendamento_ok(self, *_):
        resp = self.agendar()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["id_agendamento"], 7)

    @patch.object(servidor, "contar_ocupacao", return_value={"07:00": 4})
    def test_horarios_com_vagas(self, _):
        resp = self.client.get(f"/api/horarios?data={AMANHA}")
        itens = {h["horario"]: h["vagas"] for h in resp.get_json()["horarios"]}
        self.assertEqual(itens["07:00"], 6)
        self.assertEqual(itens["08:00"], 10)

    def test_horarios_data_invalida(self):
        self.assertEqual(self.client.get("/api/horarios?data=hoje").status_code, 400)


class TestSerie(unittest.TestCase):
    def test_serie_tem_aquecimento_principal_secundario(self):
        resp = app.test_client().get("/api/serie?nivel=avançado&objetivo=emagrecer")
        corpo = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        for chave in ("aquecimento", "principal", "secundario"):
            self.assertIn(chave, corpo)

    def test_nivel_invalido_cai_em_iniciante(self):
        corpo = app.test_client().get("/api/serie?nivel=xyz").get_json()
        self.assertEqual(corpo["nivel"], "iniciante")


if __name__ == "__main__":
    unittest.main()
