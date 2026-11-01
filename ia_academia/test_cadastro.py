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


class TestCadastro(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_cadastro_nome_vazio(self):
        resp = self.client.post("/cadastro", json={
            "nome": "", "email": "joao@email.com", "senha": "Senha123"
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["erro"], "Nome é obrigatório.")

    def test_cadastro_email_invalido(self):
        resp = self.client.post("/cadastro", json={
            "nome": "João", "email": "invalido", "senha": "Senha123"
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["erro"], "E-mail inválido.")

    def test_cadastro_senha_curta(self):
        resp = self.client.post("/cadastro", json={
            "nome": "João", "email": "joao@email.com", "senha": "123"
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["erro"], "Senha deve ter no mínimo 8 caracteres.")

    @patch("servidor.salvar_aluno_no_banco")
    def test_cadastro_sucesso(self, mock_salvar):
        mock_salvar.return_value = 1
        resp = self.client.post("/cadastro", json={
            "nome": "João Silva", "email": "joao@email.com", "senha": "Senha123"
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["mensagem"], "Cadastro realizado com sucesso.")
        mock_salvar.assert_called_once_with("João Silva", "joao@email.com", unittest.mock.ANY)

    @patch("servidor.salvar_aluno_no_banco")
    def test_cadastro_email_duplicado(self, mock_salvar):
        mock_salvar.side_effect = ValueError("E-mail já cadastrado.")
        resp = self.client.post("/cadastro", json={
            "nome": "João", "email": "joao@email.com", "senha": "Senha123"
        })
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.get_json()["erro"], "E-mail já cadastrado.")

    @patch("servidor.salvar_aluno_no_banco")
    def test_cadastro_erro_banco(self, mock_salvar):
        mock_salvar.side_effect = Exception("Erro de conexão")
        resp = self.client.post("/cadastro", json={
            "nome": "João", "email": "joao@email.com", "senha": "Senha123"
        })
        self.assertEqual(resp.status_code, 500)


if __name__ == "__main__":
    unittest.main()
