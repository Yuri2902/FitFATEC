"""Dev 3: gravação do plano semanal nas tabelas treinos/treino_exercicios (com conexão falsa)."""
import unittest
from datetime import date

from treinos import plano_semanal

SEGUNDA = date(2026, 11, 16)
QUARTA = date(2026, 11, 18)


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


class TestPreviaComDiasEscolhidos(unittest.TestCase):
    def test_plano_de_terca_e_quinta_respeita_os_dias(self):
        import planejamento
        preview = planejamento.criar_previa(None, ALUNO_DO_BANCO, {
            'dias_por_semana': 2, 'dias_semana': ['ter', 'qui'], 'minutos_por_sessao': 30,
        })
        self.assertEqual([f['dia'] for f in preview['fichas']], ['ter', 'qui'])
        self.assertEqual(preview['dias_escolhidos'], ['ter', 'qui'])

    def test_quantidade_de_dias_incorreta_nao_passa(self):
        import planejamento
        with self.assertRaisesRegex(ValueError, 'Selecione exatamente'):
            planejamento.criar_previa(None, ALUNO_DO_BANCO, {
                'dias_por_semana': 3, 'dias_semana': ['ter', 'qui'], 'minutos_por_sessao': 30,
            })

    def test_dias_duplicados_nao_passam(self):
        import planejamento
        with self.assertRaisesRegex(ValueError, 'Selecione exatamente'):
            planejamento.criar_previa(None, ALUNO_DO_BANCO, {
                'dias_por_semana': 2, 'dias_semana': ['ter', 'ter'], 'minutos_por_sessao': 30,
            })


if __name__ == "__main__":
    unittest.main()
