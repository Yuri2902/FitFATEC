"""Testes sem internet e sem Gemini para o filtro do dataset MIT."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import biblioteca_exercicios as b
import importar_exercicios_mit as imp

DADOS = [
    {"id": "001", "name": "Biceps cable curl", "category": "upper arms", "target": "biceps", "equipment": "cable", "secondary_muscles": []},
    {"id": "002", "name": "Dumbbell curl", "category": "upper arms", "target": "biceps", "equipment": "dumbbell", "secondary_muscles": []},
    {"id": "003", "name": "Band curl", "category": "upper arms", "target": "biceps", "equipment": "band", "secondary_muscles": []},
    {"id": "004", "name": "Bodyweight squat", "category": "upper legs", "target": "quads", "equipment": "body weight", "secondary_muscles": []},
    {"id": "005", "name": "Leg press", "category": "upper legs", "target": "quads", "equipment": "leverage machine", "secondary_muscles": []},
    {"id": "006", "name": "Bodyweight lunge", "category": "upper legs", "target": "quads", "equipment": "body weight", "secondary_muscles": []},
    {"id": "007", "name": "Barbell squat", "category": "upper legs", "target": "quads", "equipment": "barbell", "secondary_muscles": []},
]


def conversa(*textos):
    return [{"role": "user", "content": m} for m in textos]


class BibliotecaTest(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(b, "carregar", return_value=DADOS)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_biceps_sem_halteres(self):
        result = b.selecionar(conversa("Quero treino de bíceps sem halteres"))
        self.assertEqual(result["grupos"], ["biceps"])
        self.assertTrue(all(x["equipment"] != "dumbbell" for x in result["itens"]))
        self.assertIn("band", [x["equipment"] for x in result["itens"]])

    def test_sem_equipamento_apenas_corpo_livre(self):
        result = b.selecionar(conversa("Treino de pernas sem equipamentos"))
        self.assertEqual({x["equipment"] for x in result["itens"]}, {"body weight"})

    def test_pedido_combinado_respeita_restricao_anterior(self):
        result = b.selecionar(conversa("treino de bíceps sem halteres",
                                          "agora treino de pernas", "pode gerar um treino com ambas"))
        self.assertEqual(set(result["grupos"]), {"biceps", "pernas"})
        self.assertFalse(any(x["equipment"] == "dumbbell" for x in result["itens"]))
        self.assertTrue(any(x["target"] == "biceps" for x in result["itens"]))
        self.assertTrue(any(x["target"] == "quads" for x in result["itens"]))

    def test_troca_leg_press_nao_oferece_o_mesmo(self):
        result = b.selecionar(conversa("treino de pernas", "Substitua leg press por outro"))
        self.assertFalse(any("leg press" in x["name"].lower() for x in result["itens"]))

    def test_saude_nao_despeja_catalogo(self):
        result = b.selecionar(conversa("Oi, tudo bem?"))
        self.assertEqual(result["itens"], [])
        self.assertFalse(result["aplicavel"])

    def test_unico_id_no_retorno(self):
        result = b.selecionar(conversa("treino de pernas e glúteos"))
        self.assertEqual(len({x["id"] for x in result["itens"]}), len(result["itens"]))

    def test_falha_de_arquivo_nao_inventa(self):
        with patch.object(b, "carregar", return_value=[]):
            result = b.selecionar(conversa("treino biceps"))
        self.assertFalse(result["disponivel"])
        self.assertIn("NÃO importada", b.resumo_para_ia(result))

    def test_importador_joga_fora_urls_e_midia(self):
        fixture = [{**DADOS[0], "id": str(i), "image": "forbidden.jpg", "gif_url": "forbidden.gif",
                    "instructions": {"en": "texto que não devemos importar"}}
                   for i in range(132)]
        saida = imp.extrair_metadados(fixture)
        self.assertEqual(len(saida), 132)
        for item in saida:
            self.assertEqual(set(item), set(imp.CAMPOS))
            self.assertNotIn("image", item)
            self.assertNotIn("gif_url", item)
            self.assertNotIn("instructions", item)


if __name__ == "__main__":
    unittest.main()
