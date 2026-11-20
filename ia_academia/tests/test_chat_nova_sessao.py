"""Regressão: logout/login inicia chat novo, sem apagar o banco."""
import unittest
from unittest.mock import patch, MagicMock
from servidor import app, ultimo_id_mensagem


class TestChatNovaSessao(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("servidor.buscar_aluno_por_identificador")
    @patch("servidor.verificar_senha", return_value=True)
    @patch("servidor.ultimo_id_mensagem", side_effect=[8, 10])
    def test_relogin_abre_nova_conversa(self, ultimo, senha, buscar):
        buscar.return_value = {
            "id_aluno": 17, "nome": "Teste", "email": "teste@fatec.sp.gov.br",
            "senha_hash": "hash",
        }
        credenciais = {"identificador": "teste@fatec.sp.gov.br", "senha": "123"}
        self.assertEqual(self.client.post("/api/login", json=credenciais).status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["chat_inicio_id"], 8)
        self.assertEqual(self.client.post("/logout").status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertNotIn("chat_inicio_id", sess)
            self.assertNotIn("usuario", sess)
        self.assertEqual(self.client.post("/api/login", json=credenciais).status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["chat_inicio_id"], 10)
        self.assertEqual(ultimo.call_count, 2)

    @patch("servidor.get_db_connection")
    def test_historico_filtra_mensagens_anteriores(self, conexao):
        cursor = conexao.return_value.cursor.return_value
        cursor.fetchall.return_value = [
            {"id": 12, "role": "user", "content": "mensagem nova", "eh_treino": 0},
        ]
        with self.client.session_transaction() as sess:
            sess["usuario"] = {"id_aluno": 17}
            sess["chat_inicio_id"] = 11
        resp = self.client.get("/api/chat/historico")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["mensagens"][0]["content"], "mensagem nova")
        sql, params = cursor.execute.call_args.args
        self.assertIn("id > %s", sql)
        self.assertEqual(params, (17, 11))

    @patch("servidor.get_db_connection")
    def test_marco_usa_ultima_mensagem_existente(self, conexao):
        cursor = conexao.return_value.cursor.return_value
        cursor.fetchone.return_value = (42,)
        self.assertEqual(ultimo_id_mensagem(17), 42)
        sql, params = cursor.execute.call_args.args
        self.assertIn("MAX(id)", sql)
        self.assertEqual(params, (17,))
        cursor.fetchone.return_value = (0,)
        self.assertEqual(ultimo_id_mensagem(17), 0)


if __name__ == "__main__":
    unittest.main()
