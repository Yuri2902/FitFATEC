"""Produz cópia local de NOMES em pt-BR para o catálogo ExerciseDB MIT.

Requisitos:
  python importar_exercicios_mit.py  # já executado antes
  GEMINI_API_KEY configurada no mesmo terminal em que este script é executado
  pip install google-genai

Execução:
  python traduzir_exercicios.py
  python traduzir_exercicios.py --conferir

Escreve ia_academia/dados/nomes_exercicios_pt.json (ID -> nome_pt +
original verificado) e ia_academia/dados/revisao_traducoes.csv (revisão humana).
Pode interromper e executar de novo: cada lote bem-sucedido é salvo.
Não envia imagens, GIFs, alunos ou senhas para o modelo.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import configuracao  # permite reutilizar GEMINI_API_KEY de .env
from nomes_exercicios_pt import NOMES, _chave

BASE = Path(__file__).resolve().parent / 'dados'
CATALOGO = BASE / 'exercicios_mit.json'
TRADUCOES = BASE / 'nomes_exercicios_pt.json'
RELATORIO = BASE / 'revisao_traducoes.csv'

# Termos técnicos amplamente usados no Brasil são aceitos; os demais termos
# ingleses devem ser traduzidos em vez de aparecer no resultado.
INGLES_NAO_TRADUZIDO = re.compile(
    r'\b(?:bodyweight|lying|standing|seated|dumbbell|barbell|cable|squat|'
    r'pull[- ]?up|push[- ]?up|curl|lunge|hammer|raise|shoulder|glute|'
    r'forward|reverse|incline|bent[- ]?over|with|machine|hip thrust)\b', re.I)


def carregar_catalogo(path=CATALOGO):
    if not path.exists():
        raise FileNotFoundError('Catálogo não encontrado. Execute primeiro: python importar_exercicios_mit.py')
    dados = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(dados, list):
        raise ValueError('Catálogo inválido: esperado lista JSON')
    return [r for r in dados if isinstance(r, dict) and r.get('id') and r.get('name')]


def carregar_traducoes(path=TRADUCOES):
    if not path.exists():
        return {}
    dados = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(dados, dict):
        raise ValueError('Arquivo de traduções inválido')
    return dados


def validar(nome, original):
    if not isinstance(nome, str):
        return False
    nome = ' '.join(nome.split()).strip(' .')
    if (len(nome) < 4 or len(nome) > 180 or '<' in nome or '>' in nome
            or '[' in nome or ']' in nome or re.search(r'\b(?:unknown|n/a|sem tradução)\b', nome, re.I)):
        return False
    if _chave(nome) == _chave(original):
        # Permitir nomes convencionais consagrados em academias brasileiras.
        return _chave(nome) in {'leg press', 'agachamento goblet', 'step up'}
    if INGLES_NAO_TRADUZIDO.search(nome):
        return False
    return True


def registro_valido(reg, src):
    return (isinstance(reg, dict)
            and _chave(reg.get('nome_original')) == _chave(src['name'])
            and validar(reg.get('nome_pt'), src['name']))


def salvar(traducoes, base=BASE):
    base.mkdir(parents=True, exist_ok=True)
    arquivo = base / 'nomes_exercicios_pt.json'
    temporario = arquivo.with_suffix('.json.tmp')
    temporario.write_text(json.dumps(traducoes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporario.replace(arquivo)
    with (base / 'revisao_traducoes.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['ID', 'Nome original (uso interno)', 'Nome português (exibido)', 'Origem', 'Revisão necessária'])
        for id_, r in sorted(traducoes.items()):
            w.writerow([id_, r['nome_original'], r['nome_pt'], r.get('origem','ia'),
                        'Sim' if r.get('revisar') else 'Não'])


def carregar_sementes(catalogo, traducoes):
    for item in catalogo:
        id_ = str(item['id'])
        if registro_valido(traducoes.get(id_), item):
            continue
        pt = NOMES.get(_chave(item['name']))
        if pt and validar(pt, item['name']):
            traducoes[id_] = {'nome_original': item['name'], 'nome_pt': pt,
                              'origem': 'dicionario_revisado', 'revisar': False}
    return traducoes


def prompt(lote):
    campos = [
        {'id': str(i['id']), 'nome_original': i['name'],
         'musculo_alvo': i.get('target',''), 'equipamento': i.get('equipment',''),
         'categoria': i.get('category','')}
        for i in lote
    ]
    return (
        'Você é tradutor técnico de exercícios de musculação e educação física para o português brasileiro. '
        'Traduza APENAS os nomes de exercícios destes registros, usando a categoria, o músculo e o equipamento '
        'para escolher uma terminologia correta. Não mude o movimento, não acrescente saltos, aparelhos, '
        'cargas ou movimentos que não estejam no original. Evite anglicismos, exceto nomes consagrados no Brasil. '
        'Se for ambíguo, forneça uma descrição literal em português e marque revisar=true. '
        'NUNCA invente correspondências. Responda SOMENTE JSON válido com o formato '
        '{"items":[{"id":"0001","nome_pt":"Rosca...", "revisar":false}]}. '
        'Inclua exatamente um item por ID recebido. NÃO repita o nome em inglês na tradução.\n'
        'ENTRADAS:\n' + json.dumps(campos, ensure_ascii=False)
    )


def extrair_resposta(texto, lote):
    texto = str(texto or '').strip()
    if texto.startswith('```'):
        texto = re.sub(r'^```(?:json)?\s*|\s*```$', '', texto)
    obj = json.loads(texto)
    lista = obj.get('items') if isinstance(obj, dict) else obj
    if not isinstance(lista, list):
        raise ValueError('Resposta do Gemini não trouxe array items')
    previstos = {str(i['id']): i for i in lote}
    traduzidos = {}
    for x in lista:
        if not isinstance(x, dict):
            continue
        id_ = str(x.get('id', ''))
        if id_ not in previstos or id_ in traduzidos:
            continue
        pt = str(x.get('nome_pt') or '').strip()
        if not validar(pt, previstos[id_]['name']):
            continue
        traduzidos[id_] = {
            'nome_original': previstos[id_]['name'], 'nome_pt': ' '.join(pt.split()),
            'origem': 'ia_gerada', 'revisar': bool(x.get('revisar', False))
        }
    return traduzidos


def traduzir_lote(cliente, modelo, lote):
    resposta = cliente.models.generate_content(
        model=modelo,
        contents=prompt(lote),
        config={"response_mime_type":"application/json", "temperature":0.05,
                "max_output_tokens":3500},
    )
    return extrair_resposta(resposta.text, lote)


def executar(catalogo, traducoes, cliente, modelo, tamanho=15, pausa=1.0, base=BASE):
    pendentes = [i for i in catalogo if not registro_valido(traducoes.get(str(i['id'])),i)]
    total = len(catalogo)
    print(f'Catálogo: {total}. Já traduzidos: {total-len(pendentes)}. Restantes: {len(pendentes)}.')
    while pendentes:
        lote = pendentes[:tamanho]
        try:
            novos = traduzir_lote(cliente, modelo, lote)
        except Exception as e:
            print(f'Não foi possível traduzir o próximo lote ({type(e).__name__}).', file=sys.stderr)
            print('As traduções concluídas estão salvas. Execute de novo para continuar.', file=sys.stderr)
            break
        if not novos:
            print('A tradução do lote falhou na validação; nada foi descartado.', file=sys.stderr)
            break
        traducoes.update(novos)
        salvar(traducoes, base)
        # O lote pode retornar parcialmente. Registros problemáticos são
        # tentados individualmente na próxima rodada, sem loop infinito.
        nao_traduzidos = [x for x in lote if str(x['id']) not in novos]
        pendentes = nao_traduzidos + pendentes[tamanho:]
        if len(nao_traduzidos) == len(lote):
            print('Todos os nomes do lote foram rejeitados. Corrija os nomes indicados e tente novamente.')
            break
        print(f'Traduções salvas: {total - len(pendentes)}/{total}.')
        if pausa and pendentes:
            time.sleep(pausa)
    return total - len(pendentes), total


def main():
    parser=argparse.ArgumentParser(description='Gerar nomes em português de todos os exercícios')
    parser.add_argument('--conferir', action='store_true', help='Mostrar andamento, sem chamar API')
    parser.add_argument('--modelo', default=os.getenv('GEMINI_MODEL','gemini-2.5-flash'))
    parser.add_argument('--lote', type=int, default=15)
    parser.add_argument('--pausa', type=float, default=1.0)
    args=parser.parse_args()
    dados=carregar_catalogo()
    traducoes=carregar_traducoes()
    carregar_sementes(dados,traducoes)
    salvar(traducoes)
    faltando=[x for x in dados if not registro_valido(traducoes.get(str(x['id'])),x)]
    print(f'{len(traducoes)} traduções disponíveis; {len(faltando)} exercício(s) ainda pendente(s).')
    if args.conferir:
        print('Relatório de revisão: '+str(RELATORIO))
        return
    if not faltando:
        print('Catálogo integralmente traduzido. Reinicie o Flask. Revise os nomes marcados no CSV.')
        return
    chave=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not chave:
        raise SystemExit('Defina GEMINI_API_KEY neste terminal para traduzir o catálogo restante.')
    try:
        from google import genai
    except ImportError:
        raise SystemExit('Instale google-genai: pip install google-genai')
    cliente=genai.Client(api_key=chave)
    concluido,total=executar(dados,traducoes,cliente,args.modelo,max(1,min(args.lote,25)),args.pausa)
    print(f'Conclusão: {concluido}/{total}. Arquivo: {TRADUCOES}')
    print(f'CSV para revisão humana: {RELATORIO}')
    if concluido!=total:
        print('Faltaram traduções; execute novamente para continuar sem perder o progresso.')
    else:
        print('Todos os nomes têm uma tradução automática ou revisada. Reinicie o Flask.')
        print('ATENÇÃO: traduções automáticas ainda precisam de revisão antes de uso definitivo.')


if __name__=='__main__':
    main()
