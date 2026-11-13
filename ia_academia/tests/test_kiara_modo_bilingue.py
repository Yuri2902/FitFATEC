"""Regressões: nomes exibidos apenas em português e indicação real do modo."""
import unittest
from unittest.mock import MagicMock, patch
import assistente
import biblioteca_exercicios as b
import plano_kiara as p

ALUNO = {"idade": 25, "objetivo": "ganhar massa muscular", "nivel": "iniciante",
         "frequencia_semanal": 3, "meses_matricula": 3, "faltas_ultimo_mes": 2}
DADOS = [
    {"id": "1", "name": "Cable curl", "target": "biceps", "category": "upper arms", "equipment": "cable"},
    {"id": "2", "name": "Cable concentration curl", "target": "biceps", "category": "upper arms", "equipment": "cable"},
    {"id": "3", "name": "Reverse grip high cable biceps movement", "target": "biceps", "category": "upper arms", "equipment": "cable"},
    {"id": "4", "name": "Dumbbell curl", "target": "biceps", "category": "upper arms", "equipment": "dumbbell"},
    {"id": "5", "name": "Bodyweight squat", "target": "quads", "category": "upper legs", "equipment": "body weight"},
    {"id": "6", "name": "Walking lunge", "target": "quads", "category": "upper legs", "equipment": "body weight"},
    {"id": "7", "name": "Bodyweight custom quadriceps press", "target": "quads", "category": "upper legs", "equipment": "body weight"},
]

def h(*itens):
    return [{'role': 'user', 'content': x} for x in itens]

class Bilingue(unittest.TestCase):
    def setUp(self):
        pch = patch.object(b, 'carregar', return_value=DADOS)
        pch.start()
        self.addCleanup(pch.stop)

    def test_apenas_nome_portugues(self):
        texto, estado = p.tratar(h('Quero treino de bíceps sem halteres'))
        self.assertIn('Rosca direta na polia', texto)
        self.assertNotIn('Cable curl', texto)
        self.assertTrue(all(x['equipment'] != 'dumbbell' for x in estado['exercicios']))

    def test_sem_traducao_nao_exibe_ingles(self):
        lista = b._candidatos_grupo(DADOS, 'biceps', {'dumbbell'}, set())
        self.assertNotIn('3', [x['id'] for x in lista])
        self.assertTrue(all('[' not in x['nome_exibicao'] for x in lista))

    def test_substituicao_recorrendo_a_traducao_por_id(self):
        from nomes_exercicios_pt import nome_pt
        def resolver(original, id_exercicio=None):
            if str(id_exercicio) == '3':
                return 'Rosca inversa na polia alta'
            return nome_pt(original,id_exercicio)
        historia = h('Quero treino de bíceps sem halteres')
        _, estado = p.tratar(historia)
        with patch.object(b, 'nome_pt', side_effect=resolver):
            texto, atualizado = p.tratar(historia + h('Substitua um exercício por outro sem repetir'), estado)
        self.assertIn('Rosca inversa na polia alta', texto)
        self.assertNotIn('Reverse grip high', texto)
        self.assertEqual(len(estado['exercicios']), len(atualizado['exercicios']))
        self.assertEqual(len({x['id'] for x in atualizado['exercicios']}), 2)

    def test_ia_ativa_quando_geracao_gemini_sucede(self):
        resposta = MagicMock(text='Preparei uma sugestão para você!')
        cliente = MagicMock()
        cliente.models.generate_content.return_value = resposta
        with patch.object(assistente, 'client', cliente), patch.object(assistente, '_types', MagicMock()):
            texto, modo, estado = assistente.responder_com_plano(ALUNO, h('Quero treino de bíceps sem halteres'))
        self.assertEqual(modo, 'gemini')
        self.assertIn('Preparei uma sugestão', texto)
        self.assertEqual(texto, 'Preparei uma sugestão para você!')
        # A resposta da IA é integral, e não uma ficha rígida anexada ao texto.
        self.assertEqual(cliente.models.generate_content.call_count, 1)

    def test_offline_se_gemini_ausente(self):
        with patch.object(assistente, 'client', None):
            texto, modo, _ = assistente.responder_com_plano(ALUNO, h('Quero treino de bíceps sem halteres'))
        self.assertEqual(modo, 'offline')
        self.assertIn('Rosca direta na polia', texto)
        self.assertNotIn('Cable curl', texto)

    def test_offline_se_ia_falha(self):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = RuntimeError('falha simulada')
        with patch.object(assistente, 'client', cliente), patch.object(assistente, '_types', MagicMock()):
            texto, modo, estado = assistente.responder_com_plano(ALUNO, h('Quero treino de bíceps sem halteres'))
        self.assertEqual(modo, 'offline')
        self.assertTrue(estado['exercicios'])

    def test_combinar_equipamentos_sob_restricao(self):
        historia = h('Quero treino de bíceps sem halteres', 'Quero treino de pernas sem máquinas')
        _, plano = p.tratar(historia)
        resposta, novo = p.tratar(historia + h('Combine ambos sem os equipamentos que não tenho'), plano)
        self.assertIn('Pernas:', resposta)
        self.assertTrue(all(x['equipment'] not in {'dumbbell','cable'} for x in novo['exercicios']))
        self.assertIn('bíceps', resposta.lower()) # falta grupo e pergunta por equipamento

if __name__ == '__main__':
    unittest.main()
