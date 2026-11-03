import unittest
from datetime import date

from treinos.catalogo import EXERCICIOS, NIVEIS, buscar_exercicio, filtrar_exercicios
from treinos.contexto_ia import contexto_para_ia
from treinos.gerador import ETAPAS, gerar_plano, sessao_do_dia
from treinos.regras import SESSOES, ErroPerfil, avaliar_nivel, normalizar_perfil

SEGUNDA = date(2026, 11, 9)
TERCA = date(2026, 11, 10)


def itens_do_plano(plano):
    return [item for s in plano["sessoes"] for etapa in ETAPAS for item in s[etapa]]


def sessoes_de_musculacao(plano):
    return [s for s in plano["sessoes"] if s["nome"] != "Recuperação ativa"]


class TestCatalogo(unittest.TestCase):
    def test_codigos_e_nomes_unicos(self):
        codigos = [e["codigo"] for e in EXERCICIOS]
        nomes = [e["nome"] for e in EXERCICIOS]
        self.assertEqual(len(codigos), len(set(codigos)))
        self.assertEqual(len(nomes), len(set(nomes)))

    def test_campos_cabem_na_tabela_exercicio(self):
        for e in EXERCICIOS:
            self.assertLessEqual(len(e["nome"]), 100)
            self.assertLessEqual(len(e["grupo"]), 40)
            self.assertIn(e["nivel"], NIVEIS)

    def test_todo_grupo_das_sessoes_tem_opcao_para_iniciante(self):
        for _, _, grupos in SESSOES.values():
            for grupo in grupos:
                for local in ("academia", "casa"):
                    opcoes = filtrar_exercicios(tipo="forca", grupo=grupo, nivel="iniciante", local=local)
                    self.assertTrue(opcoes, f"sem exercício iniciante de {grupo} para {local}")

    def test_busca_ignora_acento(self):
        nomes = [e["nome"] for e in filtrar_exercicios(busca="flexao")]
        self.assertIn("Flexão de braço", nomes)


class TestPerfil(unittest.TestCase):
    def test_aceita_os_textos_que_o_frontend_ja_usa(self):
        perfil = normalizar_perfil({"objetivo": "ganhar massa muscular", "nivel": "Intermediário", "dias_por_semana": 3})
        self.assertEqual(perfil["objetivo"], "hipertrofia")
        self.assertEqual(perfil["nivel"], "intermediario")
        self.assertEqual(perfil["dias_semana"], ["seg", "qua", "sex"])
        self.assertEqual(perfil["minutos_por_sessao"], 60)
        self.assertEqual(perfil["local"], "academia")

    def test_dias_por_nome_ou_numero(self):
        perfil = normalizar_perfil({"objetivo": "saude", "nivel": "iniciante", "dias_semana": ["Sexta-feira", "terça", 1]})
        self.assertEqual(perfil["dias_semana"], ["seg", "ter", "sex"])

    def test_dados_invalidos(self):
        base = {"objetivo": "saude", "nivel": "iniciante"}
        invalidos = [
            {"objetivo": "voar"},
            {"nivel": "mestre"},
            {"dias_por_semana": 9},
            {"dias_semana": ["feriado"]},
            {"minutos_por_sessao": 5},
            {"local": "praia"},
            {"restricoes": ["cotovelo"]},
        ]
        for extra in invalidos:
            with self.subTest(extra=extra), self.assertRaises(ErroPerfil):
                normalizar_perfil({**base, **extra})


class TestDivisaoSemanal(unittest.TestCase):
    def test_iniciante_tres_dias_faz_corpo_inteiro_alternado(self):
        plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "iniciante", "dias_por_semana": 3})
        self.assertEqual(plano["divisao"], "Corpo inteiro")
        semana = {d["dia"]: d["sessao"] for d in plano["semana"]}
        self.assertEqual((semana["seg"], semana["qua"], semana["sex"]), ("A", "B", "A"))
        self.assertIsNone(semana["ter"])

    def test_intermediario_tres_dias_faz_abc(self):
        plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "intermediario", "dias_por_semana": 3})
        nomes = [s["nome"] for s in plano["sessoes"]]
        self.assertEqual(nomes, ["Peito, ombros e tríceps", "Costas e bíceps", "Pernas e glúteos"])

    def test_quatro_dias_faz_superiores_e_inferiores(self):
        plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "avancado", "dias_por_semana": 4})
        self.assertEqual(plano["divisao"], "Superiores e inferiores")
        self.assertEqual(len(plano["sessoes"]), 4)

    def test_iniciante_tem_no_maximo_quatro_dias_de_musculacao(self):
        plano = gerar_plano({"objetivo": "saude", "nivel": "iniciante", "dias_por_semana": 6})
        dias_musculacao = sum(len(s["dias"]) for s in sessoes_de_musculacao(plano))
        self.assertEqual(dias_musculacao, 4)
        self.assertIn("Recuperação ativa", [s["nome"] for s in plano["sessoes"]])

    def test_sete_dias_deixa_o_domingo_livre(self):
        plano = gerar_plano({"objetivo": "condicionamento", "nivel": "avancado", "dias_por_semana": 7})
        semana = {d["dia"]: d["sessao"] for d in plano["semana"]}
        self.assertIsNone(semana["dom"])
        self.assertEqual(sum(1 for letra in semana.values() if letra), 6)

    def test_dias_escolhidos_sao_respeitados(self):
        plano = gerar_plano({"objetivo": "emagrecimento", "nivel": "intermediario", "dias_semana": ["ter", "qui", "sab"]})
        dias = sorted(d for s in plano["sessoes"] for d in s["dias"])
        self.assertEqual(dias, sorted(["ter", "qui", "sab"]))


class TestConteudoDoTreino(unittest.TestCase):
    PERFIS = [
        {"objetivo": "hipertrofia", "nivel": "iniciante", "dias_por_semana": 3},
        {"objetivo": "emagrecimento", "nivel": "intermediario", "dias_por_semana": 4, "minutos_por_sessao": 45},
        {"objetivo": "condicionamento", "nivel": "avancado", "dias_por_semana": 5, "local": "casa"},
        {"objetivo": "saude", "nivel": "iniciante", "dias_por_semana": 2, "minutos_por_sessao": 90},
    ]

    def test_toda_sessao_tem_aquecimento_principal_e_complementar(self):
        for dados in self.PERFIS:
            plano = gerar_plano(dados)
            for sessao in sessoes_de_musculacao(plano):
                with self.subTest(perfil=dados, sessao=sessao["letra"]):
                    self.assertEqual(buscar_exercicio(sessao["aquecimento"][0]["codigo"])["tipo"], "cardio")
                    self.assertGreaterEqual(len(sessao["principal"]), 3)
                    self.assertEqual(sessao["complementar"][-1]["codigo"], "alongamento_geral")

    def test_nao_repete_exercicio_na_mesma_sessao(self):
        for dados in self.PERFIS:
            for sessao in gerar_plano(dados)["sessoes"]:
                codigos = [i["codigo"] for etapa in ETAPAS for i in sessao[etapa]]
                self.assertEqual(len(codigos), len(set(codigos)))

    def test_iniciante_so_recebe_exercicios_de_iniciante(self):
        plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "iniciante", "dias_por_semana": 4})
        for item in itens_do_plano(plano):
            self.assertEqual(buscar_exercicio(item["codigo"])["nivel"], "iniciante", item["nome"])

    def test_treino_em_casa_so_usa_exercicios_possiveis_em_casa(self):
        plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "intermediario", "dias_por_semana": 3, "local": "casa"})
        for item in itens_do_plano(plano):
            self.assertTrue(buscar_exercicio(item["codigo"])["casa"], item["nome"])

    def test_restricao_tira_exercicios_que_forcam_a_regiao(self):
        plano = gerar_plano({
            "objetivo": "condicionamento", "nivel": "avancado", "dias_por_semana": 3,
            "restricoes": ["joelho", "lombar"],
        })
        for item in itens_do_plano(plano):
            restricoes = buscar_exercicio(item["codigo"])["restricoes"]
            self.assertNotIn("joelho", restricoes, item["nome"])
            self.assertNotIn("lombar", restricoes, item["nome"])
        self.assertTrue(any("joelho" in o for o in plano["observacoes"]))

    def test_cardio_no_final_depende_do_objetivo(self):
        def tem_cardio(plano):
            return any(buscar_exercicio(i["codigo"])["tipo"] == "cardio" for i in plano["sessoes"][0]["complementar"])

        self.assertTrue(tem_cardio(gerar_plano({"objetivo": "emagrecimento", "nivel": "iniciante"})))
        self.assertFalse(tem_cardio(gerar_plano({"objetivo": "hipertrofia", "nivel": "iniciante"})))

    def test_series_e_repeticoes_seguem_objetivo_e_nivel(self):
        plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "avancado", "dias_por_semana": 4})
        self.assertEqual(plano["prescricao"]["series"], 4)
        for item in plano["sessoes"][0]["principal"]:
            self.assertEqual((item["series"], item["repeticoes"], item["intervalo_seg"]), (4, "6-10", 90))

    def test_sessao_cabe_no_tempo_disponivel(self):
        for minutos in (45, 60, 90):
            plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "intermediario", "minutos_por_sessao": minutos})
            for sessao in plano["sessoes"]:
                self.assertLessEqual(sessao["duracao_estimada_min"], minutos + 5, f"{minutos} min")

    def test_mais_tempo_gera_mais_exercicios(self):
        curto = gerar_plano({"objetivo": "hipertrofia", "nivel": "intermediario", "minutos_por_sessao": 45})
        longo = gerar_plano({"objetivo": "hipertrofia", "nivel": "intermediario", "minutos_por_sessao": 90})
        self.assertLess(len(curto["sessoes"][0]["principal"]), len(longo["sessoes"][0]["principal"]))


class TestConsultas(unittest.TestCase):
    def test_sessao_do_dia(self):
        plano = gerar_plano({"objetivo": "hipertrofia", "nivel": "iniciante", "dias_por_semana": 3})
        self.assertEqual(sessao_do_dia(plano, SEGUNDA)["letra"], "A")
        self.assertIsNone(sessao_do_dia(plano, TERCA))

    def test_contexto_para_ia_com_plano(self):
        plano = gerar_plano({"objetivo": "emagrecimento", "nivel": "iniciante", "dias_por_semana": 3})
        texto = contexto_para_ia(plano, plano_salvo=True, hoje=SEGUNDA)
        self.assertIn("Modalidades de aquecimento", texto)
        self.assertIn("Spinning", texto)
        self.assertIn("Plano de treino salvo do aluno", texto)
        self.assertIn("Treino A", texto)
        self.assertIn("Hoje é segunda, dia do treino A.", texto)

    def test_contexto_para_ia_sem_plano(self):
        texto = contexto_para_ia(None)
        self.assertIn("ainda não tem plano", texto)


class TestNivelDeCondicionamento(unittest.TestCase):
    def test_quem_esta_comecando_e_iniciante(self):
        resultado = avaliar_nivel({"meses_treinando": 1, "treinos_por_semana": 5, "flexoes": 30, "aguenta_20min_aerobico": True})
        self.assertEqual(resultado["nivel"], "iniciante")

    def test_intermediario(self):
        resultado = avaliar_nivel({"meses_treinando": 8, "treinos_por_semana": 3, "flexoes": 15, "aguenta_20min_aerobico": "sim"})
        self.assertEqual(resultado["nivel"], "intermediario")

    def test_avancado(self):
        resultado = avaliar_nivel({"meses_treinando": 24, "treinos_por_semana": 5, "flexoes": 30, "aguenta_20min_aerobico": True})
        self.assertEqual(resultado["nivel"], "avancado")
        self.assertEqual(resultado["pontos"], 7)

    def test_muito_tempo_mas_pouca_base_nao_vira_avancado(self):
        resultado = avaliar_nivel({"meses_treinando": 24, "treinos_por_semana": 1, "flexoes": 5, "aguenta_20min_aerobico": "não"})
        self.assertEqual(resultado["nivel"], "iniciante")

    def test_valor_negativo_e_invalido(self):
        with self.assertRaises(ErroPerfil):
            avaliar_nivel({"flexoes": -3})


if __name__ == "__main__":
    unittest.main()
