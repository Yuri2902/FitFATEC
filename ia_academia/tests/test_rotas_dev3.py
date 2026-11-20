"""Dev 3: rotas do plano semanal, personalidades da Kiara, agenda e treino de hoje (banco simulado)."""
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import servidor
from servidor import app
from treinos import plano_semanal

SESSAO = {"id_aluno": 17, "nome": "Ana", "matricula": "20260017", "papel": "aluno"}
ALUNO_DB = {"id_aluno": 17, "nome": "Ana", "objetivo": "Emagrecimento", "nivel": "Iniciante",
            "treinos_semana": 4, "personalidade": "padrao", "data_nascimento": None}
CHAT = {"aluno": {"idade": 22, "objetivo": "Emagrecimento", "nivel": "Iniciante", "frequencia_semanal": 3,
                  "meses_matricula": 1, "faltas_ultimo_mes": 0},
        "historico": [{"role": "user", "content": "oi"}]}
AMANHA = date.today() + timedelta(days=1)


class BaseRotas(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["usuario"] = dict(SESSAO)


@patch.object(servidor, 'get_db_connection', MagicMock())
@patch.object(servidor, 'buscar_aluno_por_id', return_value=dict(ALUNO_DB))
class TestGerarPlano(BaseRotas):
    def test_previa_nao_salva_automaticamente(self, _):
        resp=self.client.post('/api/planos/previsualizar',json={'dias_por_semana':3,'minutos_por_sessao':30})
        self.assertEqual(resp.status_code,200)
        resultado=resp.get_json()
        self.assertTrue(resultado['assinatura'])
        self.assertEqual(len(resultado['preview']['fichas']),3)
        self.assertEqual(resultado['preview']['minutos_por_sessao'],30)

    def test_sem_corpo_usa_frequencia_do_perfil(self, _):
        resp=self.client.post('/api/planos/previsualizar')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(len(resp.get_json()['preview']['fichas']),4)

    def test_opcao_invalida(self, _):
        self.assertEqual(self.client.post('/api/planos/previsualizar',json={'dias_por_semana':9}).status_code,400)

    def test_exige_login(self, _):
        self.assertEqual(app.test_client().post('/api/planos/previsualizar').status_code,401)


class TestPersonalidadeRotas(BaseRotas):
    @patch.object(servidor, "buscar_aluno_por_id", return_value=dict(ALUNO_DB))
    def test_lista_mostra_modo_mais_18_bloqueado_sem_data(self, _):
        corpo = self.client.get("/api/personalidades").get_json()
        lista = {x["id"]: x for x in corpo["personalidades"]}
        self.assertEqual(corpo["atual"], "padrao")
        self.assertFalse(lista["ofensiva"]["liberada"])
        self.assertTrue(lista["nerd"]["liberada"])

    @patch.object(servidor, "salvar_personalidade")
    @patch.object(servidor, "buscar_aluno_por_id", return_value=dict(ALUNO_DB))
    def test_menor_ou_sem_data_nao_escolhe_sem_filtro(self, _, salvar):
        resp = self.client.put("/api/perfil/personalidade", json={"personalidade": "ofensiva"})
        self.assertEqual(resp.status_code, 403)
        salvar.assert_not_called()

    @patch.object(servidor, "salvar_personalidade")
    @patch.object(servidor, "buscar_aluno_por_id", return_value=dict(ALUNO_DB, data_nascimento=date(1995, 5, 10)))
    def test_maior_escolhe_sem_filtro(self, _, salvar):
        resp = self.client.put("/api/perfil/personalidade", json={"personalidade": "ofensiva"})
        self.assertEqual(resp.status_code, 200)
        salvar.assert_called_once_with(17, "ofensiva")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["usuario"]["personalidade"], "ofensiva")

    @patch.object(servidor, "salvar_personalidade")
    @patch.object(servidor, "buscar_aluno_por_id", return_value=dict(ALUNO_DB))
    def test_modo_qualquer_nao_precisa_de_idade(self, _, salvar):
        self.assertEqual(self.client.put("/api/perfil/personalidade", json={"personalidade": "maromba"}).status_code, 200)

    def test_personalidade_inexistente(self):
        self.assertEqual(self.client.put("/api/perfil/personalidade", json={"personalidade": "pirata"}).status_code, 400)


@patch.object(servidor, "get_db_connection", MagicMock())
@patch.object(servidor, "resumo_treinos_para_kiara", return_value="- Segunda-feira: Treino A")
@patch.object(servidor, "risco_de_desistir", return_value=0.2)
class TestChatComPersonalidade(BaseRotas):
    @patch.object(servidor, "responder_com_plano", return_value=("Resposta", "offline", {"exercicios": []}))
    @patch.object(servidor, "buscar_aluno_por_id",
                  return_value=dict(ALUNO_DB, personalidade="ofensiva", data_nascimento=date(1990, 1, 1)))
    def test_maior_recebe_o_modo_escolhido(self, _, ia, *__):
        resp = self.client.post("/api/chat", json=CHAT)
        self.assertEqual(resp.status_code, 200)
        aluno = ia.call_args.args[0]
        self.assertEqual(aluno["personalidade"], "ofensiva")
        self.assertGreaterEqual(aluno["idade"], 36)
        self.assertEqual(aluno["plano_semana"], "- Segunda-feira: Treino A")
        self.assertEqual(resp.get_json()["personalidade"], "ofensiva")

    @patch.object(servidor, "responder_com_plano", return_value=("Resposta", "offline", {"exercicios": []}))
    @patch.object(servidor, "buscar_aluno_por_id",
                  return_value=dict(ALUNO_DB, personalidade="ofensiva", data_nascimento=date(2015, 1, 1)))
    def test_menor_volta_para_o_padrao_mesmo_com_ofensiva_salva(self, _, ia, *__):
        self.client.post("/api/chat", json=CHAT)
        self.assertEqual(ia.call_args.args[0]["personalidade"], "padrao")


class TestPerfilDataNascimento(BaseRotas):
    def test_data_no_futuro_e_recusada(self):
        resp = self.client.put("/api/perfil", json={"data_nascimento": "2999-01-01"})
        self.assertEqual(resp.status_code, 400)

    @patch.object(servidor, "get_db_connection", MagicMock())
    @patch.object(servidor, "salvar_personalidade")
    @patch.object(servidor, "buscar_aluno_por_id",
                  return_value=dict(ALUNO_DB, personalidade="ofensiva", data_nascimento=date(2012, 3, 3)))
    def test_data_de_menor_tira_o_modo_sem_filtro(self, _, salvar):
        resp = self.client.put("/api/perfil", json={"data_nascimento": "2012-03-03"})
        self.assertEqual(resp.status_code, 200)
        salvar.assert_called_once_with(17, "padrao")
        self.assertEqual(resp.get_json()["aluno"]["personalidade"], "padrao")
        self.assertEqual(resp.get_json()["aluno"]["data_nascimento"], "2012-03-03")


class TestTreinoDeHoje(BaseRotas):
    @patch.object(servidor, "buscar_aluno_por_id", return_value=dict(ALUNO_DB))
    def test_painel_procura_o_dia_em_portugues(self, _):
        conn = MagicMock()
        conn.cursor.return_value.fetchone.return_value = None
        conn.cursor.return_value.fetchall.return_value = []
        with patch.object(servidor, "get_db_connection", return_value=conn):
            resp = self.client.get("/api/dashboard")
        self.assertEqual(resp.status_code, 200)
        consulta, parametros = conn.cursor.return_value.execute.call_args_list[0].args
        self.assertIn("JOIN treinos", consulta)
        self.assertIn("data_treino = CURDATE()", consulta)
        self.assertEqual(parametros, (17,))


if __name__ == "__main__":
    unittest.main()
