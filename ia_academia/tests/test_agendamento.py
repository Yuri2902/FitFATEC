import unittest
from datetime import date, timedelta
from unittest.mock import patch


import servidor
from servidor import app

AMANHA = str(date.today() + timedelta(days=1))


class TestAgendamento(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["usuario"] = {"id_aluno": 17, "nome": "Ana", "matricula": "20260017", "papel": "aluno"}

    def agendar(self, **extra):
        corpo = {"data": AMANHA, "horario": "18:00", "modalidade": "musculação"}
        corpo.update(extra)
        return self.client.post("/api/agendar", json=corpo)

    def test_sem_login(self):
        resp = app.test_client().post("/api/agendar", json={
            "data": AMANHA, "horario": "18:00", "modalidade": "musculação"})
        self.assertEqual(resp.status_code, 401)

    def test_sessao_sem_id_aluno(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = {"nome": "Ana"}
        self.assertEqual(self.agendar().status_code, 401)

    def test_data_passada(self):
        ontem = str(date.today() - timedelta(days=1))
        self.assertEqual(self.agendar(data=ontem).status_code, 400)

    def test_horario_fora_do_expediente(self):
        self.assertEqual(self.agendar(horario="23:00").status_code, 400)

    def test_modalidade_invalida(self):
        self.assertEqual(self.agendar(modalidade="boxe").status_code, 400)

    @patch.object(servidor, "contar_ocupacao", return_value={"18:00": 10})
    def test_horario_lotado(self, *_):
        self.assertEqual(self.agendar().status_code, 409)

    @patch.object(servidor, "inserir_agendamento", return_value=7)
    @patch.object(servidor, "contar_ocupacao", return_value={})
    def test_agendamento_ok(self, *_):
        resp = self.agendar()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["id_agendamento"], 7)

    @patch.object(servidor, "inserir_agendamento", return_value=7)
    @patch.object(servidor, "contar_ocupacao", return_value={})
    def test_matricula_falsa_no_json_ignorada(self, _, inserir):
        resp = self.agendar(matricula="20269999")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(inserir.call_args.args[0], 17)  # ID vem da sessão, não do JSON

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
