"""Garantias de formato, consulta ao catálogo e continuidade da conversa."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import assistente

ALUNO = {"idade": 25, "objetivo": "ganhar massa muscular", "nivel": "iniciante",
         "frequencia_semanal": 3, "meses_matricula": 3, "faltas_ultimo_mes": 1}


def tipos():
    return SimpleNamespace(Content=lambda **x: SimpleNamespace(**x),
                           Part=lambda **x: SimpleNamespace(**x),
                           GenerateContentConfig=lambda **x: SimpleNamespace(**x))


class RespostasObjetivas(unittest.TestCase):
    def test_continua_pedido_curto(self):
        self.assertEqual(assistente._tipo_de_resposta("agora de tríceps"), "treino")
        self.assertEqual(assistente._tipo_de_resposta("junto os dois"), "treino")

    def test_treino_sem_intro_final(self):
        prompt = assistente._instrucoes(ALUNO, .2,
             [{"role":"user","content":"Quero um treino de pernas"}])
        self.assertIn("FICHA OBJETIVA", prompt)
        self.assertIn("NÃO escreva introduções", prompt)
        self.assertIn("NÃO escreva conclusão", prompt)

    def test_explicacao_tem_formato_proprio(self):
        prompt = assistente._instrucoes(ALUNO, .2,
             [{"role":"user","content":"Explique como executar afundo caminhando"}])
        self.assertIn("EXPLICAÇÃO SOB DEMANDA", prompt)
        self.assertNotIn("FICHA OBJETIVA", prompt)

    def test_conversa_curta(self):
        prompt = assistente._instrucoes(ALUNO, .2,
             [{"role":"user","content":"Oi Kiara!"}])
        self.assertIn("CONVERSA CURTA", prompt)

    def test_catologo_e_consultado_no_treino(self):
        hist = [{"role":"user","content":"Treino para bíceps sem halteres"}]
        fake = {"itens": [{"nome_pt":"Rosca com elástico", "target":"biceps", "equipment":"band"}]}
        with patch.object(assistente.biblioteca_exercicios,"selecionar",return_value=fake) as m:
            prompt=assistente._instrucoes(ALUNO,.2,hist)
        m.assert_called_once()
        self.assertIn("Rosca com elástico",prompt)
        self.assertIn("referência, não limite exclusivo",prompt)

    def test_resgata_grupos_anteriores_para_montar(self):
        hist=[{"role":"user","content":"Quero bíceps"},
              {"role":"assistant","content":"Rosca"},
              {"role":"user","content":"Agora pernas"},
              {"role":"assistant","content":"Agachamento"},
              {"role":"user","content":"Monte um treino usando o que conversamos"}]
        self.assertEqual(set(assistente._grupos_do_contexto(hist,hist[-1]['content'])),
                         {"biceps","pernas"})
        with patch.object(assistente.biblioteca_exercicios,"selecionar",return_value={"itens":[]}) as m:
            assistente._instrucoes(ALUNO,.2,hist)
        self.assertIn("biceps",m.call_args.args[0][-1]["content"])
        self.assertIn("pernas",m.call_args.args[0][-1]["content"])

    def test_modelo_produz_resposta_e_nao_ficha_python(self):
        client = MagicMock()
        client.models.generate_content.return_value.text = "Pernas:\n- Afundo: 3x10 (60s)"
        hist=[{"role":"user","content":"Monte um treino de pernas"}]
        with patch.object(assistente,"client",client), \
             patch.object(assistente,"_types",tipos()), \
             patch.object(assistente,"risco_de_desistir",return_value=.2), \
             patch.object(assistente.plano_kiara,"tratar") as planner:
            resposta, modo, _ = assistente.responder_com_plano(ALUNO,hist)
        self.assertEqual(modo,"gemini")
        self.assertEqual(resposta,"Pernas:\n- Afundo: 3x10 (60s)")
        planner.assert_not_called()
        self.assertLessEqual(client.models.generate_content.call_args.kwargs['config'].max_output_tokens,800)

    def test_restricoes_seguem_no_contexto(self):
        hist=[{"role":"user","content":"sem halteres, quero treinar bíceps"},
              {"role":"assistant","content":"certo"},
              {"role":"user","content":"agora pernas sem máquinas"}]
        prompt=assistente._instrucoes(ALUNO,.2,hist)
        self.assertIn("dumbbell",prompt)
        self.assertIn("cable",prompt)

if __name__=="__main__":
    unittest.main()
