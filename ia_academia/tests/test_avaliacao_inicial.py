"""Primeiro acesso: respostas guiadas, texto livre, revisão e +18."""
import unittest
from avaliacao_inicial import criar_estado, precisa_configurar, pergunta, responder, opcoes


class AvaliacaoInicialTest(unittest.TestCase):
    def test_novo_aluno_nao_recebe_nivel_ficticio(self):
        self.assertTrue(precisa_configurar({'nivel': None, 'objetivo': None, 'treinos_semana': None}))
        estado = criar_estado({})
        self.assertEqual(estado['etapa'], 'experiencia')
        self.assertIn('experiência', pergunta(estado))
        self.assertIn('Estou começando', [o['rotulo'] for o in opcoes(estado)])

    def test_fluxo_com_botao_e_revisao_antes_de_salvar(self):
        estado = criar_estado({})
        for resposta, etapa in (
            ('Treino de vez em quando', 'objetivo'),
            ('Ganhar massa muscular', 'frequencia'),
            ('4 dias por semana', 'duracao'),
            ('Até 30 minutos', 'personalidade'),
            ('Maromba', 'confirmacao'),
        ):
            _, acao, estado = responder(estado, resposta)
            self.assertEqual(acao, 'continuar')
            self.assertEqual(estado['etapa'], etapa)
        self.assertEqual(estado['dados']['nivel'], 'Iniciante')
        self.assertEqual(estado['dados']['treinos_semana'], 4)
        self.assertEqual(estado['dados']['minutos_por_sessao'], 30)
        self.assertEqual(estado['dados']['personalidade'], 'maromba')
        _, acao, estado = responder(estado, 'Alterar frequência')
        self.assertEqual(estado['etapa'], 'frequencia')
        _, acao, estado = responder(estado, '3 dias por semana')
        self.assertEqual(estado['etapa'], 'confirmacao')
        self.assertEqual(estado['dados']['treinos_semana'], 3)
        _, acao, _ = responder(estado, 'Confirmar e salvar')
        self.assertEqual(acao, 'confirmar')

    def test_cumprimentos_e_texto_livre_nao_travam(self):
        estado = criar_estado({})
        msg, acao, estado = responder(estado, 'olá tudo bem?')
        self.assertEqual(estado['etapa'], 'experiencia')
        self.assertIn('Oi!', msg)
        msg, acao, estado = responder(estado, 'treino de vez em quando')
        self.assertEqual(estado['etapa'], 'objetivo')
        self.assertEqual(estado['dados']['nivel'], 'Iniciante')

    def test_personalidade_mais_18_pede_data(self):
        estado = criar_estado({})
        for r in ('Estou começando', 'Emagrecer', '2 dias por semana', '45 minutos'):
            _, _, estado = responder(estado, r)
        _, acao, estado = responder(estado, 'Sem filtro (+18)')
        self.assertEqual(estado['etapa'], 'nascimento')
        self.assertNotEqual(estado['dados'].get('personalidade'), 'ofensiva')
        _, acao, estado = responder(estado, '19/11/2008')
        self.assertEqual(estado['etapa'], 'confirmacao')
        self.assertEqual(estado['dados']['personalidade'], 'ofensiva')
        self.assertEqual(estado['dados']['data_nascimento'], '2008-11-19')

    def test_menor_nao_escolhe_mais_18(self):
        estado = criar_estado({})
        for r in ('Estou começando', 'Emagrecer', '2 dias por semana', '45 minutos'):
            _, _, estado = responder(estado, r)
        _, _, estado = responder(estado, 'Sem filtro (+18)')
        msg, _, estado = responder(estado, '19/11/2010')
        self.assertEqual(estado['etapa'], 'personalidade')
        self.assertNotEqual(estado['dados'].get('personalidade'), 'ofensiva')
        self.assertIn('maiores de 18', msg)

    def test_pular_mantem_perfil_inalterado(self):
        estado = criar_estado({})
        _, acao, _ = responder(estado, 'Pular por agora')
        self.assertEqual(acao, 'pular')

    def test_perfil_completo_nao_reavalia(self):
        self.assertFalse(precisa_configurar({'nivel': 'Iniciante', 'objetivo': 'Emagrecimento', 'treinos_semana': 2}))

    def test_resposta_ambigua_mantem_opcoes(self):
        estado = criar_estado({})
        msg, acao, estado = responder(estado, 'não sei dizer')
        self.assertEqual(estado['etapa'], 'experiencia')
        self.assertIn('opções', msg)
        self.assertGreater(len(opcoes(estado)), 1)


if __name__ == '__main__':
    unittest.main()
