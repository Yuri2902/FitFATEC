"""Protege a estrutura canônica contra regressão de tabelas e papéis legados."""
from pathlib import Path
import re
import unittest

SQL = (Path(__file__).resolve().parents[2] / "bdd" / "bd_fitfatec.sql").read_text(encoding="utf-8")

class EsquemaEnxuto(unittest.TestCase):
    def test_colunas_de_desistencia_e_papel_ausentes(self):
        bloco = SQL.split("CREATE TABLE IF NOT EXISTS aluno", 1)[1].split(");", 1)[0]
        for coluna in ("desistiu", "data_desistencia", "data_matricula", "papel"):
            self.assertIsNone(re.search(rf"\b{coluna}\b", bloco))

    def test_tabelas_legadas_ausentes(self):
        for tabela in ("frequencia", "exercicio"):
            self.assertNotIn(f"CREATE TABLE IF NOT EXISTS {tabela} (", SQL)
        self.assertNotIn("id_exercicio INT", SQL)

    def test_relacoes_de_treino_preservadas(self):
        for tabela in ("aluno", "plano_treino", "treinos", "treino_exercicios",
                       "treino_execucoes", "agendamento", "treino_recorrencia",
                       "treino_recorrencia_excecao", "chat_mensagens"):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {tabela} (", SQL)
        self.assertIn("exercicio_id VARCHAR(100)", SQL)
        self.assertIn("ativo TINYINT(1) NOT NULL DEFAULT 1", SQL)

if __name__ == "__main__":
    unittest.main()
