"""Personalidades da Kiara (personalidades.py): catálogo, trava de idade, prompt e modo offline."""
import unittest
from datetime import date

import assistente
import personalidades as p

HOJE = date(2026, 11, 17)
ALUNO = {"idade": 25, "objetivo": "condicionamento", "nivel": "iniciante",
         "frequencia_semanal": 3, "meses_matricula": 3, "faltas_ultimo_mes": 2}


class TestCatalogo(unittest.TestCase):
    def test_modos_pedidos_existem(self):
        for codigo in ("padrao", "maromba", "nerd", "ofensiva", "coach", "zen"):
            self.assertIn(codigo, p.PERSONALIDADES)

    def test_so_o_sem_filtro_exige_maioridade(self):
        maiores = [c for c, x in p.PERSONALIDADES.items() if x["somente_maiores"]]
        self.assertEqual(maiores, ["ofensiva"])

    def test_codigo_cabe_na_coluna(self):
        self.assertTrue(all(len(codigo) <= 20 for codigo in p.PERSONALIDADES))

    def test_frases_offline_nao_parecem_exercicio(self):
        # O "Salvar este treino" trata linhas com "nome: detalhe" como exercício.
        for x in p.PERSONALIDADES.values():
            for frase in x["aberturas"] + x["fechamentos"]:
                self.assertFalse(":" in frase.rstrip(":"), frase)


class TestIdade(unittest.TestCase):
    def test_calcula_idade(self):
        self.assertEqual(p.calcular_idade("2008-11-17", HOJE), 18)
        self.assertEqual(p.calcular_idade("2008-11-18", HOJE), 17)
        self.assertEqual(p.calcular_idade(date(2000, 1, 1), HOJE), 26)

    def test_sem_data_ou_data_ruim(self):
        self.assertIsNone(p.calcular_idade(None))
        self.assertIsNone(p.calcular_idade("31/12/2000"))


class TestTravaMaioridade(unittest.TestCase):
    def test_sem_data_de_nascimento_fica_bloqueado(self):
        liberada, motivo = p.verificar_acesso("ofensiva", None)
        self.assertFalse(liberada)
        self.assertIn("data de nascimento", motivo)

    def test_menor_de_idade_fica_bloqueado(self):
        self.assertFalse(p.verificar_acesso("ofensiva", 17)[0])
        self.assertEqual(p.resolver("ofensiva", 17), "padrao")

    def test_maior_de_idade_libera(self):
        self.assertTrue(p.verificar_acesso("ofensiva", 18)[0])
        self.assertEqual(p.resolver("ofensiva", 30), "ofensiva")

    def test_outros_modos_nao_dependem_da_idade(self):
        self.assertEqual(p.resolver("maromba", None), "maromba")
        self.assertEqual(p.resolver("nerd", 14), "nerd")

    def test_codigo_desconhecido_volta_ao_padrao(self):
        self.assertEqual(p.resolver("pirata", 30), "padrao")
        self.assertEqual(p.resolver(None, 30), "padrao")

    def test_lista_para_a_tela(self):
        lista = {x["id"]: x for x in p.listar_para_aluno(16)}
        self.assertFalse(lista["ofensiva"]["liberada"])
        self.assertTrue(lista["maromba"]["liberada"])
        self.assertNotIn("prompt", lista["maromba"])


class TestPrompt(unittest.TestCase):
    def test_padrao_nao_muda_o_prompt(self):
        self.assertEqual(p.instrucoes_prompt("padrao"), "")

    def test_modo_entra_com_as_regras_fixas(self):
        texto = p.instrucoes_prompt("ofensiva")
        self.assertIn("SEM FILTRO", texto)
        self.assertIn("PROIBIDO", texto)
        self.assertIn("REGRAS QUE VALEM EM QUALQUER PERSONALIDADE", texto)

    def test_prompt_do_assistente_recebe_o_modo_e_os_treinos(self):
        aluno = dict(ALUNO, personalidade="maromba", plano_semana="- Segunda-feira: Treino A")
        instrucoes = assistente._instrucoes(aluno, 0.2, [{"role": "user", "content": "oi"}])
        self.assertIn("MAROMBA", instrucoes)
        self.assertIn("Segunda-feira: Treino A", instrucoes)

    def test_prompt_padrao_continua_igual(self):
        instrucoes = assistente._instrucoes(dict(ALUNO), 0.2, [{"role": "user", "content": "oi"}])
        self.assertNotIn("MODO DE PERSONALIDADE", instrucoes)


class TestModoOffline(unittest.TestCase):
    def test_estilo_abre_e_fecha_a_resposta(self):
        texto = p.estilizar_offline("Faça 3 x 12 de agachamento.", "maromba", "monta um treino")
        self.assertIn("Faça 3 x 12 de agachamento.", texto)
        self.assertTrue(any(texto.startswith(a) for a in p.PERSONALIDADES["maromba"]["aberturas"]))
        self.assertTrue(any(texto.endswith(f) for f in p.PERSONALIDADES["maromba"]["fechamentos"]))

    def test_padrao_nao_altera(self):
        self.assertEqual(p.estilizar_offline("Resposta.", "padrao"), "Resposta.")

    def test_assunto_sensivel_desliga_a_zoeira(self):
        texto = p.estilizar_offline("Procure um profissional.", "ofensiva", "estou com dor no joelho")
        self.assertEqual(texto, "Procure um profissional.")

    def test_dor_nao_confunde_com_outras_palavras(self):
        self.assertFalse(p.assunto_sensivel("adorei o treino, vou dormir cedo"))
        self.assertTrue(p.assunto_sensivel("sinto dores na lombar"))

    def test_resposta_offline_da_kiara_sai_no_estilo(self):
        aluno = dict(ALUNO, personalidade="ofensiva")
        historico = [{"role": "user", "content": "Quais aquecimentos existem?"}]
        original = assistente.responder_offline(dict(ALUNO), historico, 0.2)
        from unittest.mock import patch
        with patch.object(assistente, "client", None):
            texto, modo, _ = assistente.responder_com_plano(aluno, historico, None)
        self.assertEqual(modo, "offline")
        self.assertIn(original, texto)
        self.assertNotEqual(original, texto)


class TestTreinoSalvoNoModoOffline(unittest.TestCase):
    PLANO = "Seus treinos salvos:\n- Terça-feira, Treino B (Pernas)"

    def responder(self, mensagem, plano=PLANO):
        from unittest.mock import patch
        aluno = dict(ALUNO, personalidade="padrao", plano_semana=plano)
        with patch.object(assistente, "client", None):
            return assistente.responder_com_plano(aluno, [{"role": "user", "content": mensagem}], None)[0]

    def test_pergunta_do_treino_de_hoje_usa_o_plano_salvo(self):
        self.assertEqual(self.responder("Qual é o meu treino de hoje?"), self.PLANO)

    def test_pedido_de_treino_novo_nao_e_desviado(self):
        self.assertNotIn("Seus treinos salvos", self.responder("Quero um treino de bíceps"))

    def test_sem_plano_salvo_segue_o_fluxo_normal(self):
        self.assertNotEqual(self.responder("Qual é o meu treino de hoje?", plano=""), "")


if __name__ == "__main__":
    unittest.main()
