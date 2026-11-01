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


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("servidor.buscar_aluno_por_email")
    def test_login_sucesso(self, mock_buscar):
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
        data = resp.get_json()
        self.assertEqual(data["mensagem"], "Login realizado com sucesso.")
        self.assertEqual(data["usuario"]["id_aluno"], 1)
        self.assertEqual(data["usuario"]["email"], "joao@email.com")
        self.assertNotIn("senha_hash", data["usuario"])

    @patch("servidor.buscar_aluno_por_email")
    def test_login_email_inexistente(self, mock_buscar):
        mock_buscar.return_value = None
        resp = self.client.post("/login", json={
            "email": "naoexiste@email.com",
            "senha": "Senha123",
        })
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["erro"], "Credenciais inválidas.")

    @patch("servidor.buscar_aluno_por_email")
    def test_login_senha_errada(self, mock_buscar):
        mock_buscar.return_value = {
            "id_aluno": 1,
            "nome": "João Silva",
            "email": "joao@email.com",
            "senha_hash": "hash_qualquer",
            "papel": "aluno",
        }
        with patch("servidor.verificar_senha", return_value=False):
            resp = self.client.post("/login", json={
                "email": "joao@email.com",
                "senha": "SenhaErrada",
            })
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["erro"], "Credenciais inválidas.")

    def test_login_campos_obrigatorios(self):
        resp = self.client.post("/login", json={"email": "joao@email.com"})
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post("/login", json={"senha": "Senha123"})
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post("/login", json={})
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
