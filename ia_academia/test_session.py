import sys
import unittest
from unittest.mock import patch, MagicMock

# Mocka módulos com dependências externas antes de importar servidor
sys.modules["assistente"] = MagicMock()
sys.modules["assistente"].responder = MagicMock()
sys.modules["assistente"].risco_de_desistir = MagicMock(return_value=0.1)
sys.modules["mysql"] = MagicMock()
sys.modules["mysql.connector"] = MagicMock()
sys.modules["mysql.connector"].Error = Exception

from servidor import app


class TestSession(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("servidor.buscar_aluno_por_email")
    def test_login_cria_sessao(self, mock_buscar):
        mock_buscar.return_value = {
            "id_aluno": 1,
            "nome": "João Silva",
            "email": "joao@email.com",
            "senha_hash": "hash_qualquer",
            "papel": "aluno",
        }
        with patch("servidor.verificar_senha", return_value=True):
            resp = self.client.post("/login", json={
                "email": "joao@email.com",
                "senha": "Senha123",
            })
        self.assertEqual(resp.status_code, 200)

        with self.client.session_transaction() as sess:
            self.assertIn("usuario", sess)
            self.assertEqual(sess["usuario"]["email"], "joao@email.com")

    @patch("servidor.buscar_aluno_por_email")
    def test_api_me_sem_sessao(self, mock_buscar):
        resp = self.client.get("/api/me")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["erro"], "Não autenticado.")

    @patch("servidor.buscar_aluno_por_email")
    def test_api_me_com_sessao(self, mock_buscar):
        mock_buscar.return_value = {
            "id_aluno": 1,
            "nome": "João Silva",
            "email": "joao@email.com",
            "senha_hash": "hash_qualquer",
            "papel": "aluno",
        }
        with patch("servidor.verificar_senha", return_value=True):
            self.client.post("/login", json={
                "email": "joao@email.com",
                "senha": "Senha123",
            })

        resp = self.client.get("/api/me")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["usuario"]["email"], "joao@email.com")
        self.assertEqual(data["usuario"]["papel"], "aluno")

    @patch("servidor.buscar_aluno_por_email")
    def test_logout_limpa_sessao(self, mock_buscar):
        mock_buscar.return_value = {
            "id_aluno": 1,
            "nome": "João Silva",
            "email": "joao@email.com",
            "senha_hash": "hash_qualquer",
            "papel": "aluno",
        }
        with patch("servidor.verificar_senha", return_value=True):
            self.client.post("/login", json={
                "email": "joao@email.com",
                "senha": "Senha123",
            })

        resp = self.client.post("/logout")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["mensagem"], "Logout realizado com sucesso.")

        resp = self.client.get("/api/me")
        self.assertEqual(resp.status_code, 401)

    def test_logout_sem_sessao(self):
        resp = self.client.post("/logout")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
