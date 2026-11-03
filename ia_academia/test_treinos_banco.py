import os
import unittest
from datetime import date, datetime, time, timedelta

from treinos import repositorio
from treinos.gerador import gerar_plano


@unittest.skipUnless(os.environ.get("TESTAR_BANCO") == "1", "defina TESTAR_BANCO=1 para testar com o MySQL de verdade")
class TestTreinosBanco(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mysql.connector

        cls.conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            database=os.environ.get("DB_NAME", "fitfatec"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
        )
        cursor = cls.conn.cursor()
        email = f"teste.treinos.{datetime.now():%Y%m%d%H%M%S%f}@fitfatec.local"
        cursor.execute("INSERT INTO aluno (nome, email) VALUES (%s, %s)", ("Aluno de teste dos treinos", email))
        cls.conn.commit()
        cls.id_aluno = cursor.lastrowid
        cursor.close()

    @classmethod
    def tearDownClass(cls):
        cursor = cls.conn.cursor()
        for tabela in ("agendamento", "plano_treino", "aluno"):
            cursor.execute(f"DELETE FROM {tabela} WHERE id_aluno = %s", (cls.id_aluno,))
        cls.conn.commit()
        cursor.close()
        cls.conn.close()

    def test_salvar_e_ler_plano_devolve_o_mesmo_conteudo(self):
        plano = gerar_plano({
            "objetivo": "emagrecimento", "nivel": "iniciante", "dias_por_semana": 6, "restricoes": ["joelho"],
        })
        id_plano = repositorio.salvar_plano(self.conn, self.id_aluno, plano)
        salvo = repositorio.buscar_plano_ativo(self.conn, self.id_aluno)
        self.assertEqual(salvo["id_plano"], id_plano)
        for campo in ("perfil", "divisao", "prescricao", "sessoes", "semana", "observacoes"):
            self.assertEqual(salvo[campo], plano[campo], campo)

    def test_plano_novo_desativa_o_anterior(self):
        repositorio.salvar_plano(self.conn, self.id_aluno, gerar_plano({"objetivo": "saude", "nivel": "iniciante"}))
        segundo = repositorio.salvar_plano(
            self.conn, self.id_aluno,
            gerar_plano({"objetivo": "hipertrofia", "nivel": "avancado", "dias_por_semana": 5}),
        )
        self.assertEqual(repositorio.buscar_plano_ativo(self.conn, self.id_aluno)["id_plano"], segundo)
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM plano_treino WHERE id_aluno = %s AND ativo = TRUE", (self.id_aluno,))
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.close()

    def test_agendar_contar_e_cancelar(self):
        inicio = datetime.combine(date.today() + timedelta(days=3), time(19, 0))
        id_agendamento = repositorio.criar_agendamento(self.conn, self.id_aluno, "funcional", inicio)
        self.assertEqual(repositorio.ocupacao_do_dia(self.conn, "funcional", inicio.date()), {inicio: 1})

        do_dia = repositorio.listar_agendamentos(self.conn, self.id_aluno, datetime.combine(inicio.date(), time.min))
        self.assertEqual([a["id_agendamento"] for a in do_dia], [id_agendamento])
        self.assertIsNone(repositorio.buscar_agendamento(self.conn, id_agendamento, self.id_aluno + 100000))

        repositorio.cancelar_agendamento(self.conn, id_agendamento)
        self.assertEqual(repositorio.buscar_agendamento(self.conn, id_agendamento, self.id_aluno)["status"], "cancelado")
        self.assertEqual(repositorio.ocupacao_do_dia(self.conn, "funcional", inicio.date()), {})


if __name__ == "__main__":
    unittest.main()
