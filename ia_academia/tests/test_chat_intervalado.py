"""Regressões: preservar intervalos dentro de uma única ficha, sem inventar exercícios."""
import unittest
from unittest.mock import MagicMock, patch

from servidor import app, _ficha_de_dica_informal, _parece_ficha_chat


class TestConversaoCardioIntervalado(unittest.TestCase):
    dica = (
        "Bora colocar o coração para trabalhar, parça! Manda ver em "
        "30 minutos de esteira intervalada, alternando 1 minuto de trote forte "
        "com 1 minuto de caminhada leve, e depois me conta como ficou esse cardio."
    )
    ficha = (
        "Cardio intervalado:\n"
        "- Esteira intervalada: 1x30 min "
        "(alternando 1 minuto de trote forte com 1 minuto de caminhada leve)"
    )

    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["usuario"] = {"id_aluno": 17, "nome": "Teste"}
            sess["avaliacao_pulada"] = True

    def test_recupera_um_exercicio_com_protocolo_integral(self):
        ficha = _ficha_de_dica_informal(self.dica)
        self.assertEqual(ficha, self.ficha)
        self.assertTrue(_parece_ficha_chat(ficha))
        self.assertEqual(ficha.count("\n- "), 1)

    def test_outras_proporcoes_de_intervalo(self):
        ficha = _ficha_de_dica_informal(
            "Faça 25 min de esteira, alternando 2 min de corrida e 3 min de caminhada."
        )
        self.assertIn("Esteira intervalada: 1x25 min", ficha)
        self.assertIn("alternando 2 min de corrida e 3 min de caminhada", ficha)
        self.assertEqual(ficha.count("\n- "), 1)

    def test_preserva_exercicios_realmente_separados(self):
        ficha = _ficha_de_dica_informal(
            "Caminhada na esteira por 20 minutos e bicicleta durante 10 min."
        )
        self.assertEqual(
            ficha,
            "Cardio sugerido:\n- Caminhada na esteira: 1x20 min\n- Bicicleta: 1x10 min",
        )

    def test_nao_inventa_ficha_a_partir_de_subintervalos(self):
        self.assertIsNone(_ficha_de_dica_informal(
            "Alterne 1 minuto de caminhada com 1 minuto de trote."
        ))
        self.assertIsNone(_ficha_de_dica_informal("Evite 20 minutos de esteira."))

    @patch("servidor.responder_com_plano")
    @patch("servidor.resumo_treinos_para_kiara", return_value=[])
    @patch("servidor.buscar_aluno_por_id")
    @patch("servidor.get_db_connection")
    def test_reutiliza_sugestao_e_salva_um_item_com_observacao(
        self, conectar, buscar, resumo, gemini
    ):
        buscar.return_value = {"id_aluno": 17, "nome": "Teste", "personalidade": "padrao"}
        conexao = conectar.return_value
        cursor = conexao.cursor.return_value
        cursor.fetchone.return_value = (0,)
        cursor.lastrowid = 123
        historico = [
            {"role": "user", "content": "Me passa um cardio"},
            {"role": "assistant", "content": self.dica},
            {"role": "user", "content": "Me passa para eu salvar"},
        ]
        resposta = self.client.post("/api/chat", json={
            "historico": historico,
            "aluno": {"idade": 25, "objetivo": "condicionamento",
                      "nivel": "iniciante", "frequencia_semanal": 3},
        })
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()
        self.assertEqual(dados["treino_anterior_texto"], self.ficha)
        gemini.assert_not_called()
        comandos = [c.args[0] for c in cursor.execute.call_args_list]
        self.assertFalse(any("INSERT INTO treinos " in sql for sql in comandos))

        resposta_salvar = self.client.post("/api/treinos/salvar-do-chat", json={
            "texto": dados["treino_anterior_texto"], "titulo": "Cardio intervalado"
        })
        self.assertEqual(resposta_salvar.status_code, 200)
        self.assertTrue(resposta_salvar.get_json()["ok"])

        registros = [c.args[1] for c in cursor.execute.call_args_list
                     if "INSERT INTO treino_exercicios" in c.args[0]]
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0][1:5], ("Esteira intervalada", 1, "30 min", 0))
        fichas = [c.args[1] for c in cursor.execute.call_args_list
                  if "INSERT INTO treinos " in c.args[0]]
        self.assertEqual(len(fichas), 1)
        self.assertIn("alternando 1 minuto de trote forte com 1 minuto de caminhada leve",
                      fichas[0][-1])


if __name__ == "__main__":
    unittest.main()
