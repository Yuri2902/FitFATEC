"""Configuração inicial guiada da Kiara.

As escolhas ficam na sessão até o aluno revisar e confirmar. O backend
valida os valores e grava tudo de uma vez; a IA não escreve no banco.
"""
from datetime import date, datetime
import re
import unicodedata

from treinos.regras import normalizar_nivel, normalizar_objetivo, prescricao
import personalidades

ETAPAS = ('experiencia', 'objetivo', 'frequencia', 'duracao', 'personalidade')
ESCOLHAS = {
    'experiencia': [
        ('Estou começando', 'Iniciante'),
        ('Estou voltando a treinar', 'Iniciante'),
        ('Treino de vez em quando', 'Iniciante'),
        ('Treino regularmente', 'Intermediário'),
        ('Tenho bastante experiência', 'Avançado'),
    ],
    'objetivo': [
        ('Ganhar massa muscular', 'Ganhar massa muscular'),
        ('Emagrecer', 'Emagrecimento'),
        ('Melhorar condicionamento', 'Condicionamento físico'),
        ('Saúde e bem-estar', 'Saúde e bem-estar'),
    ],
    'frequencia': [(f'{n} {"dia" if n == 1 else "dias"} por semana', n) for n in range(1, 8)],
    'duracao': [('Até 30 minutos', 30), ('45 minutos', 45), ('60 minutos', 60), ('Prefiro decidir a cada treino', None)],
    'personalidade': [(item['nome'], codigo) for codigo, item in personalidades.PERSONALIDADES.items()],
}
CAMPOS = {
    'experiencia': 'nivel', 'objetivo': 'objetivo', 'frequencia': 'treinos_semana',
    'duracao': 'minutos_por_sessao', 'personalidade': 'personalidade',
}
PERGUNTAS = {
    'experiencia': 'Antes de montar seu treino, qual opção descreve melhor sua experiência? Você também pode responder com suas palavras.',
    'objetivo': 'Qual é seu principal objetivo atualmente?',
    'frequencia': 'Quantos dias por semana você pretende treinar?',
    'duracao': 'Quanto tempo você costuma ter para cada treino? Isso ajuda a montar fichas que caibam na sua rotina.',
    'personalidade': 'Escolha o jeito que prefere que eu converse com você. Isso muda meu tom, não a segurança ou os exercícios.',
    'nascimento': 'O modo Sem filtro (+18) exige sua data de nascimento. Digite DD/MM/AAAA ou AAAA-MM-DD para verificar a idade. Se preferir, volte e escolha outra personalidade.',
}


def _norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s or '').lower())
                   if not unicodedata.combining(c)).strip()


def precisa_configurar(aluno):
    return not aluno.get('nivel') or not aluno.get('objetivo') or not aluno.get('treinos_semana')


def criar_estado(aluno):
    dados = {k: aluno.get(k) for k in ('nivel', 'objetivo', 'treinos_semana', 'minutos_por_sessao', 'personalidade', 'data_nascimento')}
    if isinstance(dados.get('data_nascimento'), (date, datetime)):
        dados['data_nascimento'] = dados['data_nascimento'].isoformat()[:10]
    # Campos já preenchidos no perfil não são perguntas obrigatórias novamente,
    # mas a personalidade pode sempre ser revisada no primeiro acesso.
    pendentes = [e for e in ETAPAS[:3] if not dados.get(CAMPOS[e])]
    pendentes += ['duracao', 'personalidade']
    return {'etapa': pendentes[0] if pendentes else 'confirmacao',
            'pendentes': pendentes, 'dados': dados, 'editando': False}


def pergunta(estado):
    return resumo(estado['dados']) if estado['etapa'] == 'confirmacao' else PERGUNTAS[estado['etapa']]


def opcoes(estado, idade=None):
    etapa = estado['etapa']
    if etapa == 'confirmacao':
        return [{'rotulo': r, 'valor': r} for r in (
            'Confirmar e salvar', 'Alterar experiência', 'Alterar objetivo',
            'Alterar frequência', 'Alterar duração', 'Alterar personalidade', 'Pular por agora')]
    if etapa == 'nascimento':
        return [{'rotulo': 'Escolher outra personalidade', 'valor': 'Escolher outra personalidade'}]
    return [{'rotulo': nome, 'valor': nome} for nome, _ in ESCOLHAS.get(etapa, [])] + [
        {'rotulo': 'Pular por agora', 'valor': 'Pular por agora'}]


def _experiencia(texto):
    if any(s in texto for s in ('ocasional', 'vez em quando', 'as vezes', 'irregular', 'pouco', 'comec', 'iniciante', 'nunca', 'voltando', 'retom', 'voltei', 'parad')):
        return 'Iniciante'
    if 'avancad' in texto or 'bastante experiencia' in texto:
        return 'Avançado'
    if 'regularmente' in texto or 'intermediari' in texto or 'ha 1 ano' in texto or 'ha um ano' in texto:
        return 'Intermediário'
    return None


def _objetivo(texto):
    for palavra, campo in [('massa','Ganhar massa muscular'), ('musculo','Ganhar massa muscular'), ('hipertrof','Ganhar massa muscular'),
                          ('emagrec','Emagrecimento'), ('perder peso','Emagrecimento'), ('condicionamento','Condicionamento físico'),
                          ('resistencia','Condicionamento físico'), ('saude','Saúde e bem-estar'), ('bem-estar','Saúde e bem-estar')]:
        if palavra in texto: return campo
    return None


def _frequencia(texto):
    match = re.search(r'\b([1-7])\b', texto)
    if match: return int(match.group(1))
    for palavra, n in (('um',1), ('uma',1), ('dois',2), ('duas',2), ('tres',3), ('quatro',4), ('cinco',5), ('seis',6), ('sete',7)):
        if re.search(r'\b'+palavra+r'\b', texto): return n
    return None


def _duracao(texto):
    if any(s in texto for s in ('decidir', 'cada treino', 'variavel', 'sem preferencia')):
        return None, True
    if 'curto' in texto or 'rapid' in texto: return 30, True
    if 'medio' in texto or 'moderado' in texto: return 45, True
    match = re.search(r'\b(30|45|60)\b', texto)
    return (int(match.group(1)), True) if match else (None, False)


def _nascimento(texto):
    valor = texto.strip()
    try:
        if re.fullmatch(r'\d{2}/\d{2}/\d{4}', valor):
            return datetime.strptime(valor, '%d/%m/%Y').date()
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', valor):
            return date.fromisoformat(valor)
    except ValueError:
        pass
    return None


def resumo(dados):
    nivel = dados.get('nivel')
    objetivo = dados.get('objetivo')
    freq = dados.get('treinos_semana')
    tempo = dados.get('minutos_por_sessao')
    persona = personalidades.PERSONALIDADES.get(dados.get('personalidade') or 'padrao', personalidades.PERSONALIDADES['padrao'])['nome']
    parametros = prescricao(normalizar_objetivo(objetivo), normalizar_nivel(nivel))
    duracao = f'{tempo} min' if tempo else 'Definida a cada treino'
    return (f'Vamos conferir seu perfil antes de salvar:\n'
            f'• Nível inicial sugerido: {nivel}\n'
            f'• Objetivo: {objetivo}\n'
            f'• Frequência: {freq} dia(s) por semana\n'
            f'• Duração: {duracao}\n'
            f'• Personalidade: {persona}\n\n'
            f'Como referência, o gerador considera {parametros["series"]} séries, '
            f'{parametros["repeticoes"]} repetições e {parametros["intervalo_seg"]}s de descanso '
            'para exercícios principais. É uma sugestão inicial, não uma avaliação física. '
            'Confirma ou quer alterar alguma opção?')


def _proxima(estado):
    pendentes = estado['pendentes']
    etapa = estado['etapa']
    if etapa in pendentes:
        pendentes.remove(etapa)
    estado['etapa'] = pendentes[0] if pendentes else 'confirmacao'
    estado['editando'] = False
    return pergunta(estado)


def responder(estado, mensagem, idade=None):
    """Retorna resposta, ação e estado; só a ação confirmar autoriza persistência."""
    texto = _norm(mensagem)
    if texto in ('pular', 'pular por agora', 'depois', 'prefiro depois'):
        return 'Tudo bem, você pode configurar seu perfil depois.', 'pular', estado
    etapa = estado['etapa']
    dados = estado['dados']
    if etapa == 'confirmacao':
        if texto in ('confirmar', 'confirmar e salvar', 'sim', 'pode salvar', 'salvar', 'confirmo'):
            return 'Configuração confirmada.', 'confirmar', estado
        for campo, destino in (('experiencia','experiencia'), ('objetivo','objetivo'),
                               ('frequencia','frequencia'), ('duracao','duracao'), ('personalidade','personalidade')):
            if texto == f'alterar {campo}':
                estado['etapa'] = destino
                estado['editando'] = True
                return pergunta(estado), 'continuar', estado
        return 'Você pode confirmar ou clicar em uma opção para alterar.', 'continuar', estado
    if etapa == 'nascimento':
        if texto in ('escolher outra personalidade', 'voltar'):
            estado['etapa'] = 'personalidade'
            return pergunta(estado), 'continuar', estado
        nascimento = _nascimento(mensagem)
        if not nascimento:
            return 'Não consegui validar a data. Use DD/MM/AAAA ou escolha outra personalidade.', 'continuar', estado
        idade_informada = personalidades.calcular_idade(nascimento)
        if idade_informada is None or idade_informada > 120:
            return 'Essa data não parece válida. Confira e tente novamente.', 'continuar', estado
        if idade_informada < 18:
            dados['personalidade'] = 'padrao'
            estado['etapa'] = 'personalidade'
            return 'Esse modo é exclusivo para maiores de 18 anos. Escolha outra personalidade.', 'continuar', estado
        dados['data_nascimento'] = nascimento.isoformat()
        dados['personalidade'] = 'ofensiva'
        estado['etapa'] = 'personalidade'
        return _proxima(estado), 'continuar', estado

    valor = None
    encontrado = False
    for rotulo, v in ESCOLHAS[etapa]:
        if texto == _norm(rotulo):
            valor, encontrado = v, True
            break
    if not encontrado:
        if etapa == 'experiencia': valor = _experiencia(texto)
        elif etapa == 'objetivo': valor = _objetivo(texto)
        elif etapa == 'frequencia': valor = _frequencia(texto)
        elif etapa == 'duracao': valor, encontrado = _duracao(texto)
        elif etapa == 'personalidade':
            for codigo, item in personalidades.PERSONALIDADES.items():
                if texto in (_norm(codigo), _norm(item['nome'])):
                    valor = codigo
                    break
    if valor is None and not encontrado:
        # Cumprimentos, dúvidas e respostas vagas não viram mensagens de erro repetitivas.
        if any(s in texto for s in ('ola', 'oi', 'tudo bem', 'bom dia', 'boa tarde', 'boa noite')):
            return 'Oi! Tudo bem por aqui 😊 ' + pergunta(estado), 'continuar', estado
        return 'Você pode selecionar uma das opções abaixo ou responder com suas palavras. ' + pergunta(estado), 'continuar', estado
    if etapa == 'personalidade' and valor == 'ofensiva':
        if idade is None and not dados.get('data_nascimento'):
            estado['etapa'] = 'nascimento'
            return pergunta(estado), 'continuar', estado
        idade_valida = personalidades.calcular_idade(dados.get('data_nascimento')) if dados.get('data_nascimento') else idade
        if idade_valida is None or idade_valida < 18:
            return 'Sem filtro é apenas para maiores de 18 anos. Escolha outra personalidade.', 'continuar', estado
    dados[CAMPOS[etapa]] = valor
    # Uma edição solicitada na tela final retorna ao resumo sem reabrir etapas concluídas.
    if estado.get('editando'):
        estado['etapa'] = 'confirmacao'
        estado['editando'] = False
        return resumo(dados), 'continuar', estado
    return _proxima(estado), 'continuar', estado
