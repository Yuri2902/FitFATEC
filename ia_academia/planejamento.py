"""Prévia e gravação de planos semanais; agrupamento não vinculado à agenda.

A IA conversa, mas a proposta de exercícios vem do gerador com regras do perfil.
Só a confirmação explícita cria registros no banco. O payload é assinado e tem validade curta.
"""
import hashlib
import hmac
import json
import time
from datetime import date

from treinos import plano_semanal
from treinos.gerador import ETAPAS
from treinos.regras import DIAS_SEMANA, normalizar_dia


def assinar(preview, aluno_id, chave):
    payload = json.dumps({'aluno': aluno_id, 'preview': preview}, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':')).encode('utf8')
    return hmac.new(chave.encode() if isinstance(chave, str) else chave, payload, hashlib.sha256).hexdigest()


def validar(preview, assinatura, aluno_id, chave):
    try:
        if not hmac.compare_digest(assinar(preview, aluno_id, chave), assinatura):
            return False
        return 0 <= time.time() - int(preview['emitido_em']) <= 3600
    except (KeyError, ValueError, TypeError):
        return False


def criar_previa(conn, aluno, opcoes):
    if not isinstance(opcoes, dict):
        raise ValueError('Configurações inválidas.')
    try:
        dias = int(opcoes.get('dias_por_semana') or aluno.get('treinos_semana') or 3)
        minutos = int(opcoes.get('minutos_por_sessao') or aluno.get('minutos_por_sessao') or 45)
    except (ValueError, TypeError):
        raise ValueError('Informe dias e duração válidos.')
    if dias not in range(1, 8) or minutos not in (20, 30, 45, 60, 75, 90):
        raise ValueError('Escolha de 1 a 7 dias e duração de 20 a 90 minutos.')
    # Uma lista de dias escolhidos sempre prevalece sobre os dias-padrão da frequência.
    dias_escolhidos = opcoes.get('dias_semana')
    if dias_escolhidos is not None:
        if not isinstance(dias_escolhidos, list):
            raise ValueError('Selecione os dias da semana na lista.')
        try:
            selecionados = {normalizar_dia(dia) for dia in dias_escolhidos}
        except (ValueError, TypeError) as exc:
            raise ValueError('Há um dia da semana inválido.') from exc
        if len(selecionados) != dias or len(dias_escolhidos) != dias:
            raise ValueError(f'Selecione exatamente {dias} dia(s) diferentes no calendário semanal.')
        dias_escolhidos = [dia for dia in DIAS_SEMANA if dia in selecionados]
    plano_alvo_id = opcoes.get('plano_id_edicao')
    if plano_alvo_id is not None:
        try: plano_alvo_id=int(plano_alvo_id)
        except (ValueError,TypeError):raise ValueError('Plano de edição inválido.')
        cur=conn.cursor()
        try:
            cur.execute('SELECT id FROM plano_treino WHERE id=%s AND aluno_id=%s',
                        (plano_alvo_id,aluno['id_aluno']))
            if not cur.fetchone():raise ValueError('Plano não encontrado na sua conta.')
        finally:cur.close()
    perfil = {'dias_por_semana': dias, 'minutos_por_sessao': minutos}
    if dias_escolhidos is not None:
        perfil['dias_semana'] = dias_escolhidos
    for nome in ('objetivo','nivel','local','restricoes'):
        if opcoes.get(nome):
            perfil[nome] = opcoes[nome]
    plano = plano_semanal.gerar_para_aluno(aluno, perfil)
    sessoes = {s['letra']: s for s in plano['sessoes']}
    fichas = []
    for item_dia in plano['semana']:
        if not item_dia['sessao']:
            continue
        sessao = sessoes[item_dia['sessao']]
        exercicios = []
        for etapa in ETAPAS:
            for item in sessao[etapa]:
                exercicios.append({
                    'nome_exercicio': item['nome'], 'grupo_muscular': item['grupo'],
                    'exercicio_id': item['codigo'], 'series': item['series'],
                    'repeticoes': item['repeticoes'], 'descanso_segundos': item['intervalo_seg'],
                    'etapa': etapa
                })
        fichas.append({'dia': item_dia['dia'], 'titulo': f'Treino {sessao["letra"]} — {sessao["nome"]}',
                       'minutos_estimados': sessao['duracao_estimada_min'], 'exercicios': exercicios,
                       'origem_preservada': None})
    preservar = opcoes.get('preservar_ids') or []
    if not isinstance(preservar, list) or len(preservar) > 7:
        raise ValueError('Seleção de treinos preservados inválida.')
    if preservar:
        ids = []
        try:
            ids = list(dict.fromkeys(int(v) for v in preservar))
        except (ValueError, TypeError):
            raise ValueError('Seleção de treinos preservados inválida.')
        if len(ids) > len(fichas):
            raise ValueError('Há mais treinos preservados que dias no novo plano.')
        cursor = conn.cursor(dictionary=True)
        try:
            usados = set()
            for treino_id in ids:
                cursor.execute('SELECT id,titulo,dia_semana,plano_id FROM treinos WHERE id=%s AND aluno_id=%s AND ativo=1',
                               (treino_id, aluno['id_aluno']))
                treino = cursor.fetchone()
                if not treino:
                    raise ValueError('Um dos treinos que deseja preservar não existe.')
                cursor.execute('''SELECT nome_exercicio,grupo_muscular,exercicio_id,series,repeticoes,
                                  descanso_segundos,etapa FROM treino_exercicios WHERE treino_id=%s ORDER BY ordem''',
                               (treino_id,))
                itens = cursor.fetchall()
                if not itens:
                    raise ValueError('Não é possível preservar uma ficha sem exercícios.')
                idx = next((i for i,f in enumerate(fichas) if i not in usados
                            and plano_semanal.DIAS_BANCO[f['dia']]==treino.get('dia_semana')),
                           next(i for i in range(len(fichas)) if i not in usados))
                usados.add(idx)
                fichas[idx].update({'titulo': treino['titulo'], 'exercicios': itens,
                                    'origem_preservada': treino_id, 'minutos_estimados': None})
        finally:
            cursor.close()
    return {'titulo': str(opcoes.get('titulo') or f'Plano semanal — {plano["divisao"]}')[:100],
            'objetivo': str(perfil.get('objetivo') or aluno.get('objetivo') or 'saude')[:30],
            'dias_por_semana': dias, 'dias_escolhidos': [f['dia'] for f in fichas],
            'minutos_por_sessao': minutos, 'divisao': plano['divisao'], 'observacoes': plano['observacoes'],
            'fichas': fichas, 'plano_id_edicao': plano_alvo_id, 'emitido_em': int(time.time())}


def salvar_previa(conn, aluno_id, preview):
    # Plano novo ou revisão aprovada. Agendamentos existentes não são apagados.
    cursor = conn.cursor()
    try:
        plano_id = preview.get('plano_id_edicao')
        ids_reaproveitados = set()
        if plano_id:
            cursor.execute('SELECT id FROM plano_treino WHERE id=%s AND aluno_id=%s FOR UPDATE',
                           (plano_id, aluno_id))
            if not cursor.fetchone():
                raise ValueError('Plano não encontrado.')
            cursor.execute('UPDATE plano_treino SET titulo=%s,objetivo=%s,dias_semana=%s,minutos_sessao=%s WHERE id=%s',
                           (preview['titulo'], preview['objetivo'], preview['dias_por_semana'],
                            preview['minutos_por_sessao'], plano_id))
            cursor.execute('SELECT id FROM treinos WHERE plano_id=%s AND aluno_id=%s AND ativo=1 FOR UPDATE',
                           (plano_id, aluno_id))
            antigos = {r[0] for r in cursor.fetchall()}
        else:
            antigos = set()
            cursor.execute('INSERT INTO plano_treino (aluno_id,titulo,objetivo,dias_semana,minutos_sessao) VALUES (%s,%s,%s,%s,%s)',
                           (aluno_id, preview['titulo'], preview['objetivo'],
                            preview['dias_por_semana'], preview['minutos_por_sessao']))
            plano_id = cursor.lastrowid
        ids = []
        for ficha in preview['fichas']:
            anterior = ficha.get('origem_preservada')
            if anterior and anterior in antigos:
                cursor.execute('UPDATE treinos SET dia_semana=%s WHERE id=%s AND aluno_id=%s',
                               (plano_semanal.DIAS_BANCO[ficha['dia']], anterior, aluno_id))
                ids.append(anterior)
                ids_reaproveitados.add(anterior)
                continue
            cursor.execute('INSERT INTO treinos (aluno_id,plano_id,titulo,subtitulo,dia_semana,origem,observacoes) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                           (aluno_id, plano_id, ficha['titulo'][:100],
                            f'{len(ficha["exercicios"])} exercícios', plano_semanal.DIAS_BANCO[ficha['dia']],
                            'kiara', 'Cópia preservada da ficha anterior.' if anterior else 'Gerado pela Kiara.'))
            treino_id = cursor.lastrowid
            ids.append(treino_id)
            for ordem, ex in enumerate(ficha['exercicios'], 1):
                cursor.execute('INSERT INTO treino_exercicios (treino_id,exercicio_id,nome_exercicio,grupo_muscular,series,repeticoes,descanso_segundos,ordem,etapa) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (treino_id, ex.get('exercicio_id'), ex['nome_exercicio'], ex.get('grupo_muscular'),
                                ex['series'], ex['repeticoes'], ex['descanso_segundos'], ordem, ex.get('etapa')))
        for antigo in antigos - ids_reaproveitados:
            cursor.execute('SELECT (SELECT COUNT(*) FROM agendamento WHERE treino_id=%s) + (SELECT COUNT(*) FROM treino_recorrencia WHERE treino_id=%s)',
                           (antigo, antigo))
            if cursor.fetchone()[0]:
                # Não invalidar compromissos: ficha antiga vira individual.
                cursor.execute('UPDATE treinos SET plano_id=NULL WHERE id=%s', (antigo,))
            else:
                # Preserva dados históricos, sem exibir a ficha descartada na biblioteca.
                cursor.execute('UPDATE treinos SET ativo=0 WHERE id=%s', (antigo,))
        conn.commit()
        return plano_id, ids
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
