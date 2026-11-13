"""Testes da conexão entre o filtro e a Kiara sem internet/Gemini real."""
import unittest
from unittest.mock import MagicMock, patch

import assistente
import biblioteca_exercicios as b

ALUNO = {"idade": 25, "objetivo": "ganhar massa muscular", "nivel": "iniciante",
         "frequencia_semanal": 3, "meses_matricula": 3, "faltas_ultimo_mes": 2}
DADOS = [
    {"id": "001", "name": "Curl with band", "category": "upper arms", "target": "biceps", "equipment": "band", "secondary_muscles": []},
    {"id": "002", "name": "Dumbbell curl", "category": "upper arms", "target": "biceps", "equipment": "dumbbell", "secondary_muscles": []},
]


class Integracao(unittest.TestCase):
    def test_prompt_nao_oferece_halteres(self):
        historico = [{"role": "user", "content": "Treino de bíceps sem halteres"}]
        with patch.object(b, "carregar", return_value=DADOS):
            txt = assistente._instrucoes(ALUNO, 0.2, historico)
        self.assertIn("Rosca de bíceps com elástico", txt)
        self.assertNotIn("[002] Dumbbell curl", txt)
        self.assertIn("EQUIPAMENTOS PROIBIDOS", txt)

    def test_valida_plano_substituido_sem_perder_exercicio(self):
        historico = [
            {"role": "assistant", "content": "- Rosca direta: 2x10\n- Leg press: 2x10\n- Agachamento assistido: 2x10"},
            {"role": "user", "content": "Substitua leg press e mantenha os demais"},
        ]
        errado = "- Rosca direta: 2x10\n- Agachamento assistido: 2x10"
        certo = "- Rosca direta: 2x10\n- Agachamento assistido: 2x10\n- Afundo livre: 2x10"
        self.assertFalse(assistente._validar_substituicao(historico, errado))
        self.assertTrue(assistente._validar_substituicao(historico, certo))
        self.assertFalse(assistente._validar_substituicao(historico, certo+"\n- Rosca direta: 2x10"))

    def test_gemini_tenta_corrigir_resposta_inconsistente(self):
        historico = [
            {"role": "assistant", "content": "- Rosca direta: 2x10\n- Leg press: 2x10\n- Agachamento assistido: 2x10"},
            {"role": "user", "content": "Substitua leg press e mantenha os demais"},
        ]
        ruim = MagicMock(text="- Rosca direta: 2x10\n- Agachamento assistido: 2x10")
        bom = MagicMock(text="- Rosca direta: 2x10\n- Agachamento assistido: 2x10\n- Afundo livre: 2x10")
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = [ruim, bom]
        with patch.object(assistente, "client", cliente), patch.object(assistente, "_types", MagicMock()):
            resposta, modo = assistente.responder_com_modo(ALUNO, historico)
        self.assertEqual(modo, "gemini")
        self.assertIn("Afundo livre", resposta)
        self.assertEqual(cliente.models.generate_content.call_count, 2)

    def test_gemini_nao_finge_sucesso_se_duas_respostas_falham(self):
        historico = [
            {"role": "assistant", "content": "- Leg press: 3x12\n- Agachamento: 3x12"},
            {"role": "user", "content": "Substitua leg press por outro exercício"},
        ]
        ruim = MagicMock(text="- Agachamento: 3x12")
        cliente = MagicMock()
        cliente.models.generate_content.return_value = ruim
        with patch.object(assistente, "client", cliente), patch.object(assistente, "_types", MagicMock()):
            resposta, modo = assistente.responder_com_modo(ALUNO, historico)
        self.assertIn("Não consegui garantir", resposta)
        self.assertEqual(modo, "gemini")


if __name__ == "__main__":
    unittest.main()
