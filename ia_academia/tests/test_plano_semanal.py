"""Dev 3: gravação do plano semanal nas tabelas treinos/treino_exercicios (com conexão falsa)."""
import unittest
from datetime import date

from treinos import plano_semanal

SEGUNDA = date(2026, 11, 16)
QUARTA = date(2026, 11, 18)


class CursorFalso:
    """Guarda os comandos SQL em vez de executar, e simula o id gerado."""

    def __init__(self):
        self.comandos = []
        self.lastrowid = 0

    def execute(self, sql, parametros=None):
        self.comandos.append((sql, parametros))
        if sql.startswith("INSERT"):
            self.lastrowid += 1

    def close(self):
        pass


class ConexaoFalsa:
    def __init__(self):
        self.cursor_falso = CursorFalso()
        self.confirmada = False
        self.desfeita = False

    def cursor(self, dictionary=False):
        return self.cursor_falso

    def commit(self):
        self.confirmada = True

    def rollback(self):
        self.desfeita = True


ALUNO_DO_BANCO = {"id_aluno": 3, "objetivo": "Ganhar massa muscular", "nivel": "Intermediário", "treinos_semana": 3}


class TestPerfil(unittest.TestCase):
    def test_usa_objetivo_nivel_e_frequencia_do_perfil(self):
        plano = plano_semanal.gerar_para_aluno(ALUNO_DO_BANCO)
        self.assertEqual(plano["perfil"]["objetivo"], "hipertrofia")
        self.assertEqual(plano["perfil"]["nivel"], "intermediario")
        self.assertEqual(plano["perfil"]["dias_semana"], ["seg", "qua", "sex"])

    def test_opcoes_da_tela_mudam_o_plano(self):
        plano = plano_semanal.gerar_para_aluno(ALUNO_DO_BANCO, {
            "dias_semana": ["ter", "qui"], "local": "casa", "minutos_por_sessao": 45, "restricoes": ["joelho"],
        })
        self.assertEqual(plano["perfil"]["dias_semana"], ["ter", "qui"])
        self.assertEqual(plano["perfil"]["local"], "casa")
        self.assertEqual(plano["perfil"]["restricoes"], ["joelho"])

    def test_perfil_com_texto_estranho_nao_trava(self):
        plano = plano_semanal.gerar_para_aluno({"objetivo": "ficar monstro", "nivel": None, "treinos_semana": None})
        self.assertEqual(plano["perfil"]["objetivo"], "saude")
        self.assertEqual(plano["perfil"]["nivel"], "iniciante")


class TestNomeDoDia(unittest.TestCase):
    def test_nome_em_portugues_igual_ao_banco(self):
        self.assertEqual(plano_semanal.dia_do_banco(SEGUNDA), "Segunda-feira")
        self.assertEqual(plano_semanal.dia_do_banco(QUARTA), "Quarta-feira")
        self.assertEqual(plano_semanal.dia_do_banco(date(2026, 11, 22)), "Domingo")


class TestSalvarPlano(unittest.TestCase):
    def setUp(self):
        self.plano = plano_semanal.gerar_para_aluno(ALUNO_DO_BANCO)
        self.conn = ConexaoFalsa()
        self.ids = plano_semanal.salvar_plano(self.conn, 3, self.plano, hoje=QUARTA)
        self.comandos = self.conn.cursor_falso.comandos

    def test_desativa_so_o_plano_semanal_anterior(self):
        sql, parametros = self.comandos[0]
        self.assertTrue(sql.startswith("UPDATE treinos SET ativo = 0"))
        self.assertIn("semana_inicio IS NOT NULL", sql)
        self.assertEqual(parametros, (3,))

    def test_uma_linha_por_dia_de_treino(self):
        treinos = [p for sql, p in self.comandos if sql.startswith("INSERT INTO treinos ")]
        self.assertEqual([p[3] for p in treinos], ["Segunda-feira", "Quarta-feira", "Sexta-feira"])
        self.assertEqual(len(self.ids), 3)
        # semana_inicio é a segunda-feira da semana em que o plano foi gerado
        self.assertTrue(all(p[4] == SEGUNDA for p in treinos))

    def test_exercicios_saem_na_ordem_das_etapas(self):
        primeiro_treino = self.ids[0]
        itens = [p for sql, p in self.comandos
                 if sql.startswith("INSERT INTO treino_exercicios") and p[0] == primeiro_treino]
        etapas = [p[8] for p in itens]
        self.assertEqual(etapas[0], "aquecimento")
        self.assertEqual(etapas[-1], "complementar")
        self.assertEqual(etapas, sorted(etapas, key=["aquecimento", "principal", "complementar"].index))
        self.assertEqual([p[7] for p in itens], list(range(1, len(itens) + 1)))

    def test_confirma_a_transacao(self):
        self.assertTrue(self.conn.confirmada)
        self.assertFalse(self.conn.desfeita)


class TestResumoParaKiara(unittest.TestCase):
    TREINOS = [{"id": 1, "titulo": "Treino A", "subtitulo": "Corpo inteiro", "dia_semana": "Segunda-feira"}]

    def conexao(self, *resultados):
        from unittest.mock import MagicMock
        conn = MagicMock()
        conn.cursor.return_value.fetchall.side_effect = list(resultados)
        return conn

    def test_mostra_os_exercicios_do_treino_de_hoje(self):
        conn = self.conexao(self.TREINOS, [
            {"nome_exercicio": "Leg press 45", "series": 3, "repeticoes": "10-12", "descanso_segundos": 60}])
        texto = plano_semanal.resumo_para_kiara(conn, 3, hoje=SEGUNDA)
        self.assertIn("- Segunda-feira, Treino A (Corpo inteiro)", texto)
        self.assertIn("o seu treino é o Treino A", texto)
        self.assertIn("- Leg press 45: 3x 10-12 (descanso 60s)", texto)

    def test_dia_sem_treino_e_descanso(self):
        texto = plano_semanal.resumo_para_kiara(self.conexao(self.TREINOS), 3, hoje=QUARTA)
        self.assertIn("dia de descanso", texto)

    def test_sem_treinos_salvos(self):
        self.assertEqual(plano_semanal.resumo_para_kiara(self.conexao([]), 3, hoje=SEGUNDA), "")


if __name__ == "__main__":
    unittest.main()
