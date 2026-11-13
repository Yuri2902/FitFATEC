"""Plano de treino temporário e validável para o chat da Kiara.

A IA conversa; o catálogo local seleciona movimentos e mantém IDs sem
inventar exercícios. Estado por sessão Flask (não salvo no MySQL).
"""
from __future__ import annotations

import re
import biblioteca_exercicios as b

GRUPO_PT = {
    'biceps': 'Bíceps', 'triceps': 'Tríceps', 'pernas': 'Pernas',
    'gluteos': 'Glúteos', 'panturrilhas': 'Panturrilhas', 'peito': 'Peito',
    'costas': 'Costas', 'ombros': 'Ombros', 'abdomen': 'Abdômen',
}
EQ_PT = {'dumbbell': 'halteres', 'cable': 'polia', 'band': 'elástico',
         'barbell': 'barra', 'body weight': 'peso corporal',
         'resistance band': 'elástico', 'leverage machine': 'máquina',
         'smith machine': 'máquina Smith', 'ez barbell': 'barra W'}


def _ultima_usuario(historico):
    for m in reversed(historico):
        if m.get('role') == 'user':
            return b.normalizar(m.get('content', ''))
    return ''


def _intencao(historico):
    msg = _ultima_usuario(historico)
    if any(p in msg for p in ('substitu', 'trocar', 'troque', 'retire', 'remova', 'no lugar')):
        return 'trocar'
    if any(p in msg for p in ('combine', 'combinar', 'junte', 'juntar', 'misture', 'ambos', 'ambas', 'dois treinos')):
        return 'combinar'
    if any(p in msg for p in ('treino', 'serie', 'exercicios', 'exercicio')) and b.grupos_relevantes(historico):
        return 'gerar'
    return None


def _formato(item):
    nome = item['nome_pt']
    return f"- {nome}: {item['series']}x {item['repeticoes']} (descanso {item['descanso_s']}s)"


def _mostrar(plano, faltantes=None, introducao=None):
    faltantes = faltantes or []
    saida = [introducao or 'Aqui está a sugestão de exercícios da Kiara:', '']
    if plano:
        vistos = []
        for x in plano:
            if x['grupo'] not in vistos:
                vistos.append(x['grupo'])
        for g in vistos:
            saida.append(GRUPO_PT.get(g, g.title()) + ':')
            saida.extend(_formato(x) for x in plano if x['grupo'] == g)
            saida.append('')
    for g in faltantes:
        saida.append(f"Ainda não encontrei exercícios compatíveis para {GRUPO_PT.get(g, g).lower()} com esses equipamentos.")
    if faltantes:
        saida.append('Você dispõe de elástico, barra fixa ou algum equipamento adicional? Posso adaptar somente com o que você tiver.')
    else:
        saida.append('Os exercícios são sugestões do catálogo; peça orientação de um profissional de educação física para individualizar a execução e o volume.')
    return '\n'.join(saida).strip()


def _item(item, grupo):
    return {
        'id': str(item['id']), 'grupo': grupo,
        'nome_pt': item['nome_pt'], 'nome_original': item.get('nome_original', item.get('name', '')),
        'nome_exibicao': item['nome_pt'],
        'equipment': item['equipment'],
        'series': 2, 'repeticoes': '10–12', 'descanso_s': 60,
    }


def _permitido(item, proibidos):
    return item.get('equipment', '') not in proibidos


def _proibidos_ativos(historico):
    proibidos = b.restricoes_equipamento(historico)
    # Quando halteres e máquinas foram vetados, não pressupor que o aluno
    # tenha acessórios avulsos (elásticos ou barras) sem confirmação explícita.
    if {'dumbbell', 'cable'}.issubset(proibidos):
        ultimas = ' '.join(b.normalizar(m.get('content', '')) for m in historico
                          if m.get('role') == 'user')
        if not re.search(r'(?<!nao )(?:tenho|possuo|posso usar) (?:um |uma |o |a )?(?:elastico|faixa)', ultimas):
            proibidos.update({'band', 'resistance band'})
        if not re.search(r'(?<!nao )(?:tenho|possuo|posso usar) (?:uma |a )?barra', ultimas):
            proibidos.update({'barbell', 'ez barbell'})
    return proibidos


def _selecionar_grupos(historico, grupos, existentes=None, quantidade=2):
    proibidos = _proibidos_ativos(historico)
    usados = {x['id'] for x in (existentes or [])}
    nomes_usados = {b.normalizar(x['nome_pt']) for x in (existentes or [])}
    originais_usados = {b.normalizar(x.get('nome_original', '')) for x in (existentes or [])}
    todos = b.carregar()
    plano = []
    faltantes = []
    for g in grupos:
        candidatos = b._candidatos_grupo(todos, g, proibidos, set())
        escolhidos = []
        for e in candidatos:
            if (str(e['id']) in usados or b.normalizar(e['nome_pt']) in nomes_usados
                    or b.normalizar(e.get('nome_original', e.get('name', ''))) in originais_usados):
                continue
            # Movimento que precisa de acessórios embutidos no nome não deve
            # passar por 'peso corporal' como se não exigisse equipamento.
            original = b.normalizar(e.get('name', ''))
            if e.get('equipment') == 'body weight' and any(t in original for t in
                ('chin-up', 'pull-up', 'hanging', 'dip on', 'parallel bar')):
                continue
            usados.add(str(e['id']))
            nomes_usados.add(b.normalizar(e['nome_pt']))
            originais_usados.add(b.normalizar(e.get('nome_original', e.get('name', ''))))
            escolhidos.append(_item(e, g))
            if len(escolhidos) >= quantidade:
                break
        plano.extend(escolhidos)
        if not escolhidos:
            faltantes.append(g)
    return plano, faltantes


def _alterar(historico, anterior):
    ultimo = _ultima_usuario(historico)
    plano = [dict(x) for x in (anterior or [])]
    if not plano:
        return ('Ainda não temos uma série válida montada nesta conversa. Peça primeiro um treino e depois diga qual exercício quer substituir.', anterior)
    # Identifica o exercício mencionado usando exclusivamente o plano salvo,
    # não deduz que o primeiro exercício foi citado sem evidência.
    indices = [i for i, x in enumerate(plano)
               if b.normalizar(x['nome_pt']) in ultimo or
               (x.get('nome_original') and b.normalizar(x['nome_original']) in ultimo)]
    if len(indices) > 1:
        return ('Você mencionou mais de um exercício. Qual deles devo substituir?', anterior)
    indice = indices[0] if indices else 0  # pedido genérico: escolhe um exercício alterável
    ordem = [indice] if indices else list(range(len(plano)))
    proibidos = _proibidos_ativos(historico)
    todos = b.carregar()
    ids = {x['id'] for x in plano}
    nomes = {b.normalizar(x['nome_pt']) for x in plano}
    originais = {b.normalizar(x.get('nome_original', '')) for x in plano}
    for i in ordem:
        atual = plano[i]
        candidatos = b._candidatos_grupo(todos, atual['grupo'], proibidos, set())
        for candidato in candidatos:
            if str(candidato['id']) in ids:
                continue
            if (b.normalizar(candidato['nome_pt']) in nomes or
                    b.normalizar(candidato.get('nome_original', candidato.get('name', ''))) in originais):
                continue
            novo = _item(candidato, atual['grupo'])
            plano[i] = novo
            introducao = (f"Substituí {atual['nome_pt']} "
                          f"por {novo['nome_pt']}, "
                          'mantendo todos os outros exercícios:')
            return _mostrar(plano, introducao=introducao), plano
    return ('Não encontrei uma alternativa diferente e compatível no catálogo disponível. '
            'Mantive a série anterior sem alterações. Você tem elástico, barra ou outro equipamento disponível?', anterior)


def tratar(historico, estado=None):
    """(texto, estado) ou None quando a mensagem é conversa comum.

    O catálogo precisa ter sido importado antes de interceptar pedidos de série.
    """
    intencao = _intencao(historico)
    if not intencao or not b.carregar():
        return None
    anteriores = (estado or {}).get('exercicios', [])
    if intencao == 'trocar':
        texto, plano = _alterar(historico, anteriores)
        return texto, {'exercicios': plano}

    grupos = b.grupos_relevantes(historico)
    if intencao == 'combinar':
        grupos_estado = list(dict.fromkeys(x.get('grupo') for x in anteriores))
        grupos = list(dict.fromkeys(grupos_estado + grupos))
    if not grupos:
        return ('Quais grupos musculares você quer treinar?', estado or {'exercicios': []})

    proibidos = _proibidos_ativos(historico)
    preservados = []
    if intencao == 'combinar':
        preservados = [dict(x) for x in anteriores if _permitido(x, proibidos)]
    grupos_pendentes = [g for g in grupos if not any(x.get('grupo') == g for x in preservados)]
    novos, faltantes = _selecionar_grupos(historico, grupos_pendentes, preservados)
    plano = preservados + novos
    # Nenhum movimento com ID repetido, e nenhum movimento além das restrições.
    ids = set()
    nomes = set()
    originais = set()
    plano_ok = []
    for x in plano:
        n = b.normalizar(x['nome_pt'])
        orig = b.normalizar(x.get('nome_original', ''))
        if (x['id'] not in ids and n not in nomes and orig not in originais
                and _permitido(x, proibidos)):
            ids.add(x['id'])
            nomes.add(n)
            originais.add(orig)
            plano_ok.append(x)
    if intencao == 'combinar':
        intro = ('Reuni os exercícios compatíveis, mas ainda há grupos pendentes.' if faltantes
                 else 'Combinei os grupos respeitando suas restrições de equipamentos.')
    else:
        intro = 'Separei uma sugestão de exercícios conforme seu pedido.'
    texto = _mostrar(plano_ok, faltantes, intro)
    return texto, {'exercicios': plano_ok}
