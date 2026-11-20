"""Regressão: sugestão informal de cardio deve virar ficha salvável, sem troca de treino."""
import unittest
from unittest.mock import patch

from servidor import (
    app,
    _ficha_de_dica_informal,
    _pedido_para_salvar_ficha_anterior,
    _ultima_ficha_no_historico,
)


class TestSalvarContextoDoChat(unittest.TestCase):
    sugestao = (
        "Bora buscar esse pump no cardio, monstro! Manda ver em 20 minutos "
        "de esteira em ritmo moderado para fechar o treino com chave de ouro."
    )

    def setUp(self):
        self.client = app.test_client()

    def test_dica_informal_gera_somente_exercicio_sugerido(self):
        ficha = _ficha_de_dica_informal(self.sugestao)
        self.assertEqual(ficha, "Cardio sugerido:\n- Esteira: 1x20 min")
        self.assertNotIn("perna", ficha.lower())

    def test_nao_converte_mensagem_sem_prescricao_ou_proibicao(self):
        self.assertIsNone(_ficha_de_dica_informal("Bom dia! Você já fez cardio?"))
        self.assertIsNone(_ficha_de_dica_informal("Evite 20 minutos de esteira hoje."))

    def test_separa_pedido_de_salvar_de_treino_novo(self):
        self.assertTrue(_pedido_para_salvar_ficha_anterior(
            "ok pode me passar o treino para eu salvar então"))
        self.assertTrue(_pedido_para_salvar_ficha_anterior(
            "agora me passa para eu salvar esse treino"))
        self.assertFalse(_pedido_para_salvar_ficha_anterior(
            "me passa um treino de costas para eu salvar"))

    @patch("servidor.responder_com_plano")
    @patch("servidor.resumo_treinos_para_kiara", return_value=[])
    @patch("servidor.buscar_aluno_por_id")
    @patch("servidor.get_db_connection")
    def test_pedido_reaproveita_dica_sem_chamar_gemini_ou_salvar_ficha(
        self, conexao, buscar, resumo, gemini
    ):
        buscar.return_value = {"id_aluno": 17, "nome": "Teste", "personalidade": "padrao"}
        with self.client.session_transaction() as sess:
            sess["usuario"] = {"id_aluno": 17, "nome": "Teste"}
            sess["avaliacao_pulada"] = True
        historico = [
            {"role": "user", "content": "me passa um cardiozinho"},
            {"role": "assistant", "content": self.sugestao},
            {"role": "user", "content": "ok pode me passar o treino para eu salvar então"},
        ]
        resp = self.client.post("/api/chat", json={
            "historico": historico,
            "aluno": {"idade": 25, "objetivo": "condicionamento",
                      "nivel": "iniciante", "frequencia_semanal": 3},
        })
        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertEqual(dados["modo"], "local")
        self.assertTrue(dados["eh_treino"])
        self.assertIn("- Esteira: 1x20 min", dados["resposta"])
        self.assertEqual(dados["treino_anterior_texto"],
                         "Cardio sugerido:\n- Esteira: 1x20 min")
        gemini.assert_not_called()
        comandos = [call.args[0] for call in
                    conexao.return_value.cursor.return_value.execute.call_args_list]
        self.assertEqual(sum("INSERT INTO chat_mensagens" in q for q in comandos), 2)
        self.assertFalse(any("INSERT INTO treinos " in q for q in comandos))

    def test_busca_apenas_ultima_resposta_da_kiara(self):
        hist = [
            {"role": "assistant", "content": "Cardio:\n- Esteira: 1x20 min"},
            {"role": "user", "content": "outra dúvida"},
            {"role": "assistant", "content": "Claro, qual sua dúvida?"},
            {"role": "user", "content": "agora salva o treino"},
        ]
        self.assertIsNone(_ultima_ficha_no_historico(hist))


if __name__ == "__main__":
    unittest.main()
