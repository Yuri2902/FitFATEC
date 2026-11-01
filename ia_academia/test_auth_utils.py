import unittest
from auth_utils import gerar_hash_senha, verificar_senha, validar_cadastro


class TestAuthUtils(unittest.TestCase):
    def test_senha_correta(self):
        hash_senha = gerar_hash_senha("MinhaSenha123")
        self.assertTrue(verificar_senha("MinhaSenha123", hash_senha))

    def test_senha_incorreta(self):
        hash_senha = gerar_hash_senha("MinhaSenha123")
        self.assertFalse(verificar_senha("SenhaErrada", hash_senha))

    def test_cadastro_valido(self):
        valido, mensagem = validar_cadastro("João Silva", "joao@email.com", "Senha123")
        self.assertTrue(valido)
        self.assertEqual(mensagem, "Dados válidos.")

    def test_cadastro_nome_vazio(self):
        valido, mensagem = validar_cadastro("", "joao@email.com", "Senha123")
        self.assertFalse(valido)
        self.assertEqual(mensagem, "Nome é obrigatório.")

    def test_cadastro_email_invalido(self):
        valido, mensagem = validar_cadastro("João Silva", "email-invalido", "Senha123")
        self.assertFalse(valido)
        self.assertEqual(mensagem, "E-mail inválido.")

    def test_cadastro_senha_curta(self):
        valido, mensagem = validar_cadastro("João Silva", "joao@email.com", "123")
        self.assertFalse(valido)
        self.assertEqual(mensagem, "Senha deve ter no mínimo 8 caracteres.")


if __name__ == "__main__":
    unittest.main()
