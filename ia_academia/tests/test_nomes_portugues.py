"""Testes locais de traduções; não usam Google nem rede."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import nomes_exercicios_pt as np
import biblioteca_exercicios as biblioteca
import plano_kiara
from traduzir_exercicios import extrair_resposta, carregar_sementes, salvar, validar, executar

DADOS = [
    {'id': '0001', 'name': 'Cable curl', 'category': 'upper arms', 'target': 'biceps', 'equipment': 'cable'},
    {'id': '0002', 'name': 'Bodyweight squat', 'category': 'upper legs', 'target': 'quads', 'equipment': 'body weight'},
    {'id': '0003', 'name': 'Bodyweight side lying biceps curl', 'category': 'upper arms', 'target': 'biceps', 'equipment': 'body weight'},
    {'id': '0004', 'name': 'Custom kneeling arm lift', 'category': 'upper arms', 'target': 'biceps', 'equipment': 'body weight'},
]

class Portugues(unittest.TestCase):
    def tearDown(self):
        np.traducoes_por_id.cache_clear()

    def test_sementes_mantem_id_original(self):
        d = carregar_sementes(DADOS, {})
        self.assertEqual(d['0001']['nome_pt'], 'Rosca direta na polia')
        self.assertEqual(d['0001']['nome_original'], 'Cable curl')

    def test_resposta_ia_e_parse_pt(self):
        texto=json.dumps({'items':[{'id':'0004', 'nome_pt':'Elevação de braço ajoelhado', 'revisar':True}]})
        parsed=extrair_resposta(texto,[DADOS[3]])
        self.assertEqual(parsed['0004']['nome_pt'], 'Elevação de braço ajoelhado')
        self.assertTrue(parsed['0004']['revisar'])
        self.assertNotIn('Custom kneeling',parsed['0004']['nome_pt'])

    def test_rejeita_nome_em_ingles(self):
        texto=json.dumps({'items':[{'id':'0004', 'nome_pt':'custom kneeling arm lift', 'revisar':False}]})
        self.assertEqual(extrair_resposta(texto,[DADOS[3]]),{})

    def test_preserva_id_originais_e_exibe_so_pt(self):
        with tempfile.TemporaryDirectory() as d:
            caminho=Path(d)
            trad={'0004':{'nome_original':'Custom kneeling arm lift', 'nome_pt':'Elevação de braço ajoelhado', 'origem':'ia_gerada','revisar':True}}
            salvar(trad,caminho)
            with patch.object(np,'ARQUIVO_TRADUCOES', caminho/'nomes_exercicios_pt.json'):
                np.traducoes_por_id.cache_clear()
                with patch.object(biblioteca,'carregar',return_value=DADOS):
                    hist=[{'role':'user','content':'Quero treino de bíceps sem halteres'}]
                    texto,estado=plano_kiara.tratar(hist)
                    self.assertIn('Rosca de bíceps deitado de lado com peso corporal',texto)
                    self.assertNotIn('bodyweight side lying',texto.lower())
                    self.assertNotIn('Cable curl',texto)
                    self.assertTrue(all('(' not in x['nome_exibicao'] for x in estado['exercicios']))
            np.traducoes_por_id.cache_clear()

    def test_id_origem_diferente_nao_reutiliza_traducao(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'nomes_exercicios_pt.json'
            path.write_text(json.dumps({'0004':{'nome_original':'Different exercise','nome_pt':'Nome errado'}}))
            with patch.object(np,'ARQUIVO_TRADUCOES',path):
                np.traducoes_por_id.cache_clear()
                self.assertIsNone(np.nome_pt('Custom kneeling arm lift','0004'))

    def test_traduz_nome_ingles_em_resposta_livre(self):
        import assistente
        with patch.object(biblioteca, 'carregar', return_value=DADOS):
            texto=assistente._portugues_na_resposta('Experimente Bodyweight squat no treino.')
        self.assertIn('Agachamento livre',texto)
        self.assertNotIn('Bodyweight squat',texto)

    def test_execucao_retomavel_usa_lotes_e_salva_csv(self):
        with tempfile.TemporaryDirectory() as d:
            raiz=Path(d)
            orig=DADOS[3]
            m=MagicMock()
            m.models.generate_content.return_value.text=json.dumps({'items':[
                {'id':orig['id'],'nome_pt':'Elevação de braço ajoelhado','revisar':True}]})
            traducoes=carregar_sementes(DADOS,{})
            feitos,total=executar(DADOS,traducoes,m,'mock-gemini',tamanho=10,pausa=0,base=raiz)
            self.assertEqual(feitos,total)
            self.assertEqual(m.models.generate_content.call_count,1)
            armazenado=json.loads((raiz/'nomes_exercicios_pt.json').read_text())
            self.assertEqual(armazenado['0004']['nome_original'],'Custom kneeling arm lift')
            self.assertTrue((raiz/'revisao_traducoes.csv').exists())

if __name__ == '__main__':
    unittest.main()
