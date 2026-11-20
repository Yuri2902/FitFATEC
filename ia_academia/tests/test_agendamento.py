"""Calendário pessoal vinculado ao treino salvo; banco simulado, sem MySQL real."""
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import servidor
from servidor import app

AMANHA = (date.today() + timedelta(days=1)).isoformat()


class TestCalendario(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess['usuario'] = {'id_aluno': 17, 'nome': 'Ana'}

    def agendar(self, **extra):
        payload = {'treino_id': 3, 'data_treino': AMANHA}
        payload.update(extra)
        return self.client.post('/api/agendamentos', json=payload)

    def test_login_obrigatorio(self):
        self.assertEqual(app.test_client().post('/api/agendamentos', json={}).status_code, 401)

    def test_treino_obrigatorio(self):
        self.assertEqual(self.agendar(treino_id='x').status_code, 400)

    def test_data_passada(self):
        self.assertEqual(self.agendar(data_treino='2020-01-01').status_code, 400)

    def test_horario_invalido(self):
        self.assertEqual(self.agendar(horario='26:99').status_code, 400)

    @patch.object(servidor, 'get_db_connection')
    def test_treino_precisa_pertencer_ao_aluno(self, db):
        db.return_value.cursor.return_value.fetchone.return_value = None
        r = self.agendar()
        self.assertEqual(r.status_code, 404)
        query, params = db.return_value.cursor.return_value.execute.call_args.args
        self.assertIn('aluno_id = %s', query)
        self.assertEqual(params, (3, 17))

    @patch.object(servidor, 'get_db_connection')
    def test_agendar_treino_salvo(self, db):
        cursor = db.return_value.cursor.return_value
        cursor.fetchone.return_value = (3,)
        cursor.lastrowid = 19
        r = self.agendar()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()['id_agendamento'], 19)
        consultas = [ch.args[0] for ch in cursor.execute.call_args_list]
        self.assertTrue(any('INSERT INTO agendamento' in sql for sql in consultas))
        self.assertTrue(all('DELETE FROM treinos' not in sql for sql in consultas))
        db.return_value.commit.assert_called_once()

    @patch.object(servidor, 'get_db_connection')
    def test_excluir_agendamento_preserva_treino(self, db):
        db.return_value.cursor.return_value.rowcount = 1
        r = self.client.delete('/api/agendamentos/8')
        self.assertEqual(r.status_code, 200)
        query, params = db.return_value.cursor.return_value.execute.call_args.args
        self.assertIn('DELETE FROM agendamento', query)
        self.assertEqual(params, (8, 17))
        self.assertNotIn('DELETE FROM treinos', query)

    @patch.object(servidor, 'get_db_connection')
    def test_listagem_so_do_dono(self, db):
        cursor = db.return_value.cursor.return_value
        # A rota faz três SELECTs distintos: agendamentos, recorrências e exceções.
        # Cada consulta precisa receber linhas do formato esperado por ela.
        cursor.fetchall.side_effect = [
            [{'id_agendamento': 8, 'data_treino': date.fromisoformat(AMANHA),
              'horario': None, 'treino_titulo': 'Matador de peito', 'status': 'planejado'}],
            [],  # Nenhuma recorrência cadastrada
            [],  # Nenhuma exceção de recorrência
        ]

        r = self.client.get('/api/agendamentos')
        self.assertEqual(r.status_code, 200)
        corpo = r.get_json()
        self.assertEqual(len(corpo['agendamentos']), 1)
        self.assertEqual(corpo['proximos_agendamentos'][0]['treino_titulo'], 'Matador de peito')

        # Verifica o escopo do aluno em TODAS as consultas, não só na última.
        consultas = cursor.execute.call_args_list
        self.assertEqual(len(consultas), 3)

        sql_agendamentos, params_agendamentos = consultas[0].args
        self.assertIn('FROM agendamento a', sql_agendamentos)
        self.assertIn('JOIN treinos t', sql_agendamentos)
        self.assertIn('WHERE a.id_aluno = %s', sql_agendamentos)
        self.assertEqual(params_agendamentos, (17,))

        sql_recorrencias, params_recorrencias = consultas[1].args
        self.assertIn('FROM treino_recorrencia r', sql_recorrencias)
        self.assertIn('r.aluno_id=%s', sql_recorrencias)
        self.assertEqual(params_recorrencias, (17,))

        sql_excecoes, params_excecoes = consultas[2].args
        self.assertIn('FROM treino_recorrencia_excecao e', sql_excecoes)
        self.assertIn('r.aluno_id=%s', sql_excecoes)
        self.assertEqual(len(params_excecoes), 3)  # aluno + início/fim da janela
        self.assertEqual(params_excecoes[0], 17)


if __name__ == '__main__':
    unittest.main()
