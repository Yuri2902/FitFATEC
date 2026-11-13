"""Regressões da mudança: Gemini principal, catálogo somente offline/referência."""
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import assistente

ALUNO = {
    "idade": 25, "objetivo": "ganhar massa muscular", "nivel": "iniciante",
    "frequencia_semanal": 3, "meses_matricula": 3, "faltas_ultimo_mes": 2,
}


def tipos_simulados():
    return SimpleNamespace(
        Content=lambda **v: SimpleNamespace(**v),
        Part=lambda **v: SimpleNamespace(**v),
        GenerateContentConfig=lambda **v: SimpleNamespace(**v),
    )


class GeminiPrimeiro(unittest.TestCase):
    def _chamar(self, fala, resposta):
        cliente = MagicMock()
        cliente.models.generate_content.return_value.text = resposta
        historico = [{"role": "user", "content": fala}]
        with patch.object(assistente, "client", cliente), \
                patch.object(assistente, "_types", tipos_simulados()), \
                patch.object(assistente, "risco_de_desistir", return_value=0.2), \
                patch.object(assistente.plano_kiara, "tratar") as planner:
            texto, modo, estado = assistente.responder_com_plano(ALUNO, historico)
            planner.assert_not_called()
        config = cliente.models.generate_content.call_args.kwargs["config"]
        return texto, modo, estado, config.system_instruction

    def test_gemini_responde_inteiro_em_pedido_treino(self):
        conteudo = "Você pode treinar bíceps com rosca, resistência e ajustes de movimento."
        resposta, modo, estado, prompt = self._chamar("Quero alternativas para bíceps", conteudo)
        self.assertEqual(modo, "gemini")
        self.assertEqual(resposta, conteudo)
        self.assertEqual(estado["exercicios"], [])
        self.assertIn("conhecimento geral", prompt)
        self.assertNotIn("Use SOMENTE exercícios", prompt)
        self.assertNotIn("CATÁLOGO BÁSICO (nível e objetivo atuais do aluno):", prompt)

    def test_kiara_conversa_anatomia_sem_ficha_fixa(self):
        conteudo = "O bíceps braquial participa da flexão do cotovelo e da supinação."
        resposta, modo, _, prompt = self._chamar("Explique a função do bíceps na supinação", conteudo)
        self.assertEqual(modo, "gemini")
        self.assertEqual(resposta, conteudo)
        self.assertIn("anatomia funcional", prompt)
        self.assertIn("Não é necessário consultar exercícios específicos", prompt)

    def test_restricao_anteriores_informadas_no_prompt(self):
        historico = [{"role":"user", "content":"Sem halteres, quero treino de bíceps"},
                     {"role":"assistant", "content":"Você pode usar peso corporal."},
                     {"role":"user", "content":"Agora quero pernas sem máquinas"}]
        prompt = assistente._instrucoes(ALUNO, 0.2, historico)
        self.assertIn("EQUIPAMENTOS PROIBIDOS", prompt)
        self.assertIn("dumbbell", prompt)
        self.assertIn("cable", prompt)

    def test_falha_gemini_continua_offline(self):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = RuntimeError("indisponível")
        historico = [{"role":"user", "content":"Quero treino de bíceps"}]
        with patch.object(assistente, "client", cliente), \
             patch.object(assistente, "_types", tipos_simulados()), \
             patch.object(assistente, "risco_de_desistir", return_value=0.2):
            texto, modo, estado = assistente.responder_com_plano(ALUNO, historico)
        self.assertEqual(modo, "offline")
        self.assertIn("Bíceps", texto)
        self.assertTrue(estado["exercicios"])

    def test_indicador_ia_so_com_resposta_gerada(self):
        cliente = MagicMock()
        cliente.models.generate_content.return_value.text = ""
        historico = [{"role":"user", "content":"Quero treino de bíceps"}]
        with patch.object(assistente, "client", cliente), \
             patch.object(assistente, "_types", tipos_simulados()), \
             patch.object(assistente, "risco_de_desistir", return_value=0.2):
            texto, modo, estado = assistente.responder_com_plano(ALUNO, historico)
        self.assertEqual(modo, "offline")
        self.assertTrue(estado["exercicios"])


if __name__ == "__main__":
    unittest.main()
