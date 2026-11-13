"""Testa o problema real: treino combinado, troca e nomes em português."""
import unittest
from unittest.mock import patch
import biblioteca_exercicios as b
import plano_kiara as p
from nomes_exercicios_pt import nome_pt

DADOS = [
    {'id': '01', 'name': 'cable curl', 'target': 'biceps', 'category': 'upper arms', 'equipment': 'cable'},
    {'id': '02', 'name': 'cable concentration curl', 'target': 'biceps', 'category': 'upper arms', 'equipment': 'cable'},
    {'id': '03', 'name': 'Dumbbell curl', 'target': 'biceps', 'category': 'upper arms', 'equipment': 'dumbbell'},
    {'id': '04', 'name': 'Band curl', 'target': 'biceps', 'category': 'upper arms', 'equipment': 'band'},
    {'id': '05', 'name': 'Bodyweight squat', 'target': 'quads', 'category': 'upper legs', 'equipment': 'body weight'},
    {'id': '06', 'name': 'Bodyweight lunge', 'target': 'quads', 'category': 'upper legs', 'equipment': 'body weight'},
    {'id': '07', 'name': 'Curtsey squat', 'target': 'quads', 'category': 'upper legs', 'equipment': 'body weight'},
    {'id': '08', 'name': 'All fours squat stretch', 'target': 'quads', 'category': 'upper legs', 'equipment': 'body weight'},
    {'id': '09', 'name': 'Leg press', 'target': 'quads', 'category': 'upper legs', 'equipment': 'leverage machine'},
]


def h(*itens):
    return [{'role': 'user', 'content': s} for s in itens]


class PlanoKiaraTest(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(b, 'carregar', return_value=DADOS)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_biceps_sem_halteres_e_nome_pt(self):
        texto, estado = p.tratar(h('Quero treino de bíceps sem halteres'))
        self.assertNotIn('cable curl', texto.lower())
        self.assertIn('Rosca', texto)
        self.assertTrue(all(x['equipment'] != 'dumbbell' for x in estado['exercicios']))

    def test_combinacao_sem_maquinas_e_sem_halteres_nao_inventa(self):
        anterior = h('Quero treino de bíceps sem halteres',
                     'Agora quero um treino de pernas sem máquinas')
        text1, estado1 = p.tratar(anterior)
        texto, estado2 = p.tratar(anterior + h('Combine os dois, respeitando os equipamentos que não tenho'), estado1)
        self.assertIn('Pernas:', texto)
        self.assertIn('bíceps', texto.lower())
        self.assertIn('elástico', texto.lower())
        self.assertNotIn('cable curl', texto.lower())
        self.assertTrue(all(x['equipment'] == 'body weight' for x in estado2['exercicios']))

    def test_substituicao_mantem_quantidade_e_outros(self):
        historia = h('Treino de pernas sem máquinas')
        _, estado = p.tratar(historia)
        antes = estado['exercicios']
        texto, atualizado = p.tratar(historia + h('Substitua um exercício por outro diferente, sem repetir os demais'), estado)
        depois = atualizado['exercicios']
        self.assertEqual(len(antes), len(depois))
        self.assertEqual(len({e['nome_pt'] for e in depois}), len(depois))
        self.assertIn('Substituí', texto)
        self.assertEqual(sum(a['id'] == b['id'] for a,b in zip(antes,depois)),len(antes)-1)
        self.assertNotIn('alongamento', texto.lower())

    def test_sem_plano_nao_finge_substituicao(self):
        texto, estado = p.tratar(h('Substitua um exercício por outro'), {})
        self.assertIn('Ainda não temos uma série válida', texto)
        self.assertFalse(estado.get('exercicios'))

    def test_traducao_curtsey_e_bloqueio_inseguro(self):
        self.assertEqual(nome_pt('curtsey squat'), 'Agachamento com passada cruzada')
        self.assertIsNone(nome_pt('unknown gymnastics exercise'))
        itens = b.selecionar(h('Treino de pernas sem máquinas'))['itens']
        self.assertFalse(any('stretch' in x['name'] for x in itens))
        self.assertTrue(all(x.get('nome_pt') for x in itens))

    def test_resposta_nao_repetir_exercicio_traduzido_de_ids_distintos(self):
        dado_extra = {'id': '10', 'name': 'Biceps cable curl', 'target': 'biceps', 'category': 'upper arms', 'equipment': 'cable'}
        with patch.object(b, 'carregar', return_value=DADOS + [dado_extra]):
            texto, estado = p.tratar(h('Treino de bíceps'))
        nomes = [x['nome_pt'] for x in estado['exercicios']]
        self.assertEqual(len(nomes), len(set(nomes)))

if __name__ == '__main__':
    unittest.main()
