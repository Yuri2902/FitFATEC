import unittest

from personalidades import (
    PADRAO,
    PERSONALIDADES,
    instrucoes_personalidade,
    listar_personalidades,
    obter_personalidade,
    personalidade_valida,
)


class TestPersonalidades(unittest.TestCase):
    def test_todas_tem_os_campos_usados_pelo_prompt_e_pela_tela(self):
        for codigo, p in PERSONALIDADES.items():
            for campo in ("nome", "descricao", "tom", "estilo", "expressoes", "exemplo", "saudacao"):
                self.assertIn(campo, p, f"{codigo} sem {campo}")
            self.assertLessEqual(len(codigo), 20)

    def test_padrao_existe(self):
        self.assertTrue(personalidade_valida(PADRAO))

    def test_codigo_invalido_cai_no_padrao(self):
        self.assertIs(obter_personalidade("pirata"), PERSONALIDADES[PADRAO])
        self.assertIs(obter_personalidade(None), PERSONALIDADES[PADRAO])
        self.assertFalse(personalidade_valida("pirata"))

    def test_instrucoes_levam_estilo_girias_e_regras_fixas(self):
        texto = instrucoes_personalidade("maromba")
        self.assertIn("Maromba", texto)
        self.assertIn("tá pago", texto)
        self.assertIn("REGRAS QUE VALEM EM QUALQUER ESTILO", texto)

    def test_formal_nao_recebe_lista_de_girias(self):
        texto = instrucoes_personalidade("formal")
        self.assertNotIn("Expressões que combinam", texto)
        self.assertIn("REGRAS QUE VALEM EM QUALQUER ESTILO", texto)

    def test_lista_para_a_tela(self):
        lista = listar_personalidades()
        self.assertEqual([p["id"] for p in lista], list(PERSONALIDADES))
        self.assertNotIn("estilo", lista[0])


if __name__ == "__main__":
    unittest.main()
