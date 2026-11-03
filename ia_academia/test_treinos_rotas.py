import sys
import unittest
from datetime import date, datetime, time, timedelta
from unittest.mock import MagicMock, patch

sys.modules["assistente"] = MagicMock()
sys.modules["assistente"].risco_de_desistir = MagicMock(return_value=0.1)
sys.modules["mysql"] = MagicMock()
sys.modules["mysql.connector"] = MagicMock()
sys.modules["mysql.connector"].Error = Exception

from servidor import app
from treinos.gerador import gerar_plano
from treinos.rotas import contexto_para_chat

ALUNO = {"id_aluno": 7, "nome": "Ana", "email": "ana@email.com", "papel": "aluno"}


def proximo(dia_semana, hora):
    dia = date.today() + timedelta(days=2)
    while dia.weekday() != dia_semana:
        dia += timedelta(days=1)
    return datetime.combine(dia, time(hora))


class BaseRotas(unittest.TestCase):
    def setUp(self):
        app.config["TREINOS_CONEXAO_BD"] = MagicMock()
        self.client = app.test_client()

    def logar(self):
        with self.client.session_transaction() as sess:
            sess["usuario"] = dict(ALUNO)


class TestCatalogoRotas(BaseRotas):
    def test_lista_com_filtro(self):
        resp = self.client.get("/api/treinos/exercicios?grupo=peito&nivel=iniciante")
        self.assertEqual(resp.status_code, 200)
        exercicios = resp.get_json()["exercicios"]
        self.assertTrue(exercicios)
        self.assertTrue(all(e["grupo"] == "peito" and e["nivel"] == "iniciante" for e in exercicios))

    def test_detalhe(self):
        resp = self.client.get("/api/treinos/exercicios/leg_press")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("execucao", resp.get_json()["exercicio"])
        self.assertEqual(self.client.get("/api/treinos/exercicios/nao_existe").status_code, 404)

    def test_aquecimento(self):
        modalidades = self.client.get("/api/treinos/aquecimento").get_json()["modalidades"]
        self.assertEqual([m["codigo"] for m in modalidades], ["geral", "mobilidade", "especifico"])

    def test_nivel(self):
        resp = self.client.post("/api/treinos/nivel", json={"meses_treinando": 0})
        self.assertEqual(resp.get_json()["nivel"], "iniciante")


class TestPlanoRotas(BaseRotas):
    def test_simular_sem_login(self):
        resp = self.client.post("/api/treinos/plano/simular", json={"objetivo": "emagrecer", "nivel": "iniciante"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["plano"]["perfil"]["objetivo"], "emagrecimento")

    def test_simular_com_dados_invalidos(self):
        resp = self.client.post("/api/treinos/plano/simular", json={"objetivo": "voar", "nivel": "iniciante"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Objetivo inválido", resp.get_json()["erro"])

    def test_salvar_exige_login(self):
        resp = self.client.post("/api/treinos/plano", json={"objetivo": "saude", "nivel": "iniciante"})
        self.assertEqual(resp.status_code, 401)

    @patch("treinos.repositorio.salvar_plano", return_value=42)
    def test_salvar_plano(self, mock_salvar):
        self.logar()
        resp = self.client.post("/api/treinos/plano", json={"objetivo": "saude", "nivel": "iniciante"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["plano"]["id_plano"], 42)
        self.assertEqual(mock_salvar.call_args.args[1], 7)

    @patch("treinos.repositorio.buscar_plano_ativo", return_value=None)
    def test_sem_plano_salvo(self, _):
        self.logar()
        self.assertEqual(self.client.get("/api/treinos/plano").status_code, 404)

    @patch("treinos.repositorio.buscar_plano_ativo")
    def test_treino_do_dia(self, mock_buscar):
        mock_buscar.return_value = gerar_plano({"objetivo": "hipertrofia", "nivel": "iniciante", "dias_por_semana": 3})
        self.logar()
        segunda = self.client.get("/api/treinos/plano/hoje?data=2026-11-09").get_json()
        terca = self.client.get("/api/treinos/plano/hoje?data=2026-11-10").get_json()
        self.assertFalse(segunda["descanso"])
        self.assertEqual(segunda["sessao"]["letra"], "A")
        self.assertTrue(terca["descanso"])

    def test_banco_fora_do_ar(self):
        app.config["TREINOS_CONEXAO_BD"] = MagicMock(side_effect=Exception("sem conexão"))
        self.logar()
        resp = self.client.get("/api/treinos/plano")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json()["erro"], "Erro ao acessar o banco de dados.")


class TestAgendaRotas(BaseRotas):
    def test_atividades(self):
        dados = self.client.get("/api/agenda/atividades").get_json()
        self.assertIn("spinning", [a["codigo"] for a in dados["atividades"]])

    @patch("treinos.repositorio.ocupacao_do_dia", return_value={})
    def test_horarios(self, _):
        dia = proximo(1, 20).date().isoformat()
        resp = self.client.get(f"/api/agenda/horarios?atividade=spinning&data={dia}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["horarios"][-1]["inicio"], f"{dia}T20:00")

    def test_horarios_atividade_invalida(self):
        self.assertEqual(self.client.get("/api/agenda/horarios?atividade=boxe").status_code, 400)

    def test_agendar_exige_login(self):
        self.assertEqual(self.client.post("/api/agenda", json={}).status_code, 401)

    @patch("treinos.repositorio.criar_agendamento", return_value=99)
    @patch("treinos.repositorio.ocupacao_do_dia", return_value={})
    @patch("treinos.repositorio.listar_agendamentos", return_value=[])
    def test_agendar(self, _listar, _ocupacao, mock_criar):
        self.logar()
        inicio = proximo(1, 20)
        resp = self.client.post("/api/agenda", json={"atividade": "spinning", "inicio": inicio.isoformat()})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["agendamento"]["id_agendamento"], 99)
        mock_criar.assert_called_once()

    @patch("treinos.repositorio.criar_agendamento")
    @patch("treinos.repositorio.ocupacao_do_dia", return_value={})
    @patch("treinos.repositorio.listar_agendamentos")
    def test_agendar_com_conflito(self, mock_listar, _ocupacao, mock_criar):
        inicio = proximo(1, 20)
        mock_listar.return_value = [{"id_agendamento": 1, "atividade": "musculacao", "inicio": inicio, "status": "agendado"}]
        self.logar()
        resp = self.client.post("/api/agenda", json={"atividade": "spinning", "inicio": inicio.isoformat()})
        self.assertEqual(resp.status_code, 400)
        mock_criar.assert_not_called()

    def test_agendar_horario_mal_formatado(self):
        self.logar()
        resp = self.client.post("/api/agenda", json={"atividade": "spinning", "inicio": "amanhã às 8"})
        self.assertEqual(resp.status_code, 400)

    @patch("treinos.repositorio.cancelar_agendamento")
    @patch("treinos.repositorio.buscar_agendamento")
    def test_cancelar(self, mock_buscar, mock_cancelar):
        mock_buscar.return_value = {"id_agendamento": 5, "atividade": "spinning", "inicio": proximo(1, 20), "status": "agendado"}
        self.logar()
        self.assertEqual(self.client.post("/api/agenda/5/cancelar").status_code, 200)
        mock_cancelar.assert_called_once()

    @patch("treinos.repositorio.buscar_agendamento", return_value=None)
    def test_cancelar_de_outro_aluno(self, _):
        self.logar()
        self.assertEqual(self.client.post("/api/agenda/5/cancelar").status_code, 404)


class TestContextoParaChat(BaseRotas):
    def test_sem_login_usa_plano_sugerido(self):
        aluno = {"objetivo": "ganhar massa muscular", "nivel": "iniciante", "frequencia_semanal": 2}
        with app.test_request_context():
            texto = contexto_para_chat(aluno)
        self.assertIn("ainda não foi salvo", texto)
        self.assertIn("Corpo inteiro", texto)

    @patch("treinos.repositorio.buscar_plano_ativo")
    def test_com_login_usa_plano_salvo(self, mock_buscar):
        mock_buscar.return_value = gerar_plano({"objetivo": "saude", "nivel": "iniciante"})
        with app.test_request_context():
            from flask import session
            session["usuario"] = dict(ALUNO)
            texto = contexto_para_chat({"objetivo": "emagrecer", "nivel": "iniciante", "frequencia_semanal": 3})
        self.assertIn("Plano de treino salvo do aluno", texto)

    def test_dados_ruins_nao_quebram_o_chat(self):
        with app.test_request_context():
            texto = contexto_para_chat({"objetivo": "???", "nivel": "iniciante"})
        self.assertIn("ainda não tem plano", texto)


if __name__ == "__main__":
    unittest.main()
