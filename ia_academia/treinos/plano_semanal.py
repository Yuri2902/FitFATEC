"""Liga o gerador de planos às tabelas da equipe (Dev 3).

O gerador.py monta o plano em memória. Este módulo:
- monta o perfil de entrada a partir do aluno no banco (objetivo, nível e
  treinos_semana do perfil) somado às opções escolhidas na tela Meus treinos;
- grava cada dia de treino como uma linha em `treinos` e os exercícios em
  `treino_exercicios`, guardando a etapa (aquecimento, principal ou complementar);
- traduz a data para o nome do dia usado no banco ("Segunda-feira"...), que é o
  que o painel usa para achar o "Treino de hoje";
- resume os treinos salvos em texto para a Kiara usar nas respostas.

Como reconhecer um plano gerado aqui: origem = 'kiara' e semana_inicio preenchida.
Quando o aluno gera um plano novo, só esse plano anterior é desativado; treinos
salvos do chat (semana_inicio vazio) e treinos manuais continuam na lista.
"""
from datetime import date, timedelta

from .gerador import ETAPAS, gerar_plano
from .regras import DIAS_SEMANA, ErroPerfil, normalizar_nivel, normalizar_objetivo

# Nome do dia como a equipe grava na coluna treinos.dia_semana.
DIAS_BANCO = {
    "seg": "Segunda-feira",
    "ter": "Terça-feira",
    "qua": "Quarta-feira",
    "qui": "Quinta-feira",
    "sex": "Sexta-feira",
    "sab": "Sábado",
    "dom": "Domingo",
}


def dia_do_banco(dia):
    """date -> "Segunda-feira", no mesmo texto gravado em treinos.dia_semana."""
    return DIAS_BANCO[DIAS_SEMANA[dia.weekday()]]


def _do_perfil(valor, normalizar, padrao):
    # Valores do perfil salvos com outro texto não podem travar a geração:
    # se não reconhecer, usa um padrão seguro em vez de devolver erro.
    try:
        return normalizar(valor)
    except ErroPerfil:
        return padrao


def montar_perfil(aluno, opcoes=None):
    """Junta o perfil salvo do aluno com as opções enviadas pela tela.

    As opções da tela (dias, tempo, local, restrições) são validadas pelo gerador;
    objetivo e nível vêm do perfil e caem no padrão se estiverem em branco.
    """
    opcoes = opcoes or {}
    perfil = {
        "objetivo": opcoes.get("objetivo") or _do_perfil(aluno.get("objetivo"), normalizar_objetivo, "saude"),
        "nivel": opcoes.get("nivel") or _do_perfil(aluno.get("nivel"), normalizar_nivel, "iniciante"),
        "minutos_por_sessao": opcoes.get("minutos_por_sessao"),
        "local": opcoes.get("local"),
        "restricoes": opcoes.get("restricoes") or [],
    }
    if opcoes.get("dias_semana"):
        perfil["dias_semana"] = opcoes["dias_semana"]
    else:
        perfil["dias_por_semana"] = opcoes.get("dias_por_semana") or aluno.get("treinos_semana") or 3
    return perfil


def gerar_para_aluno(aluno, opcoes=None):
    return gerar_plano(montar_perfil(aluno, opcoes))


def _formatar_item(item):
    if item["series"] == 1 and item["repeticoes"].endswith("min"):
        return f"{item['nome']} {item['repeticoes']}"
    return f"{item['nome']} {item['series']} x {item['repeticoes']}"


def _observacoes_da_sessao(plano, sessao):
    """Texto da aba Observações: prescrição, aquecimento, complementar e avisos."""
    pres = plano["prescricao"]
    linhas = [
        f"Plano semanal gerado pela Kiara ({plano['divisao']}).",
        f"Treino principal: {pres['series']} séries de {pres['repeticoes']} repetições, "
        f"descanso de {pres['intervalo_seg']} s. {pres['carga']}",
        "Aquecimento: " + "; ".join(_formatar_item(i) for i in sessao["aquecimento"]),
        "Complementar: " + "; ".join(_formatar_item(i) for i in sessao["complementar"]),
    ]
    linhas += [f"- {obs}" for obs in plano["observacoes"]]
    return "\n".join(linhas)


def salvar_plano(conn, id_aluno, plano, hoje=None):
    """Grava o plano: uma linha em `treinos` por dia de treino. Retorna os ids criados.

    Faz tudo numa transação: se algo falhar no meio, nada fica gravado pela metade.
    """
    hoje = hoje or date.today()
    segunda_da_semana = hoje - timedelta(days=hoje.weekday())
    por_letra = {s["letra"]: s for s in plano["sessoes"]}
    cursor = conn.cursor()
    try:
        # Desativa só o plano semanal anterior (origem kiara + semana_inicio preenchida).
        cursor.execute(
            "UPDATE treinos SET ativo = 0 "
            "WHERE aluno_id = %s AND origem = 'kiara' AND semana_inicio IS NOT NULL AND ativo = 1",
            (id_aluno,),
        )
        ids = []
        for dia in plano["semana"]:
            if not dia["sessao"]:
                continue
            sessao = por_letra[dia["sessao"]]
            quantidade = sum(len(sessao[etapa]) for etapa in ETAPAS)
            cursor.execute(
                "INSERT INTO treinos (aluno_id, titulo, subtitulo, dia_semana, origem, semana_inicio, observacoes) "
                "VALUES (%s, %s, %s, %s, 'kiara', %s, %s)",
                (
                    id_aluno,
                    f"Treino {sessao['letra']}",
                    f"{sessao['nome']} • {quantidade} exercícios • ~{sessao['duracao_estimada_min']} min",
                    DIAS_BANCO[dia["dia"]],
                    segunda_da_semana,
                    _observacoes_da_sessao(plano, sessao),
                ),
            )
            treino_id = cursor.lastrowid
            ordem = 1
            # A ordem segue as etapas: aquecimento, depois principal, depois complementar.
            for etapa in ETAPAS:
                for item in sessao[etapa]:
                    cursor.execute(
                        "INSERT INTO treino_exercicios (treino_id, exercicio_id, nome_exercicio, grupo_muscular, "
                        "series, repeticoes, descanso_segundos, ordem, etapa) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (treino_id, item["codigo"], item["nome"], item["grupo"], item["series"],
                         item["repeticoes"], item["intervalo_seg"], ordem, etapa),
                    )
                    ordem += 1
            ids.append(treino_id)
        conn.commit()
        return ids
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def resumo_para_kiara(conn, id_aluno, hoje=None, limite=10):
    """Texto com os treinos ativos do aluno e o treino de hoje.

    Serve para duas coisas: entra no prompt do Gemini e, no modo offline, é a própria
    resposta para "qual é o meu treino de hoje?". Por isso já sai num formato legível.
    Devolve string vazia se o aluno não tiver treino salvo.
    """
    hoje = hoje or date.today()
    nome_hoje = dia_do_banco(hoje)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, titulo, subtitulo, dia_semana FROM treinos "
            "WHERE aluno_id = %s AND ativo = 1 ORDER BY (semana_inicio IS NULL), id LIMIT %s",
            (id_aluno, limite),
        )
        treinos = cursor.fetchall()
        if not treinos:
            return ""
        # Sem ":" nas linhas da semana, para o botão "Salvar este treino" não ler o dia como exercício.
        linhas = ["Seus treinos salvos:"]
        linhas += [f"- {t['dia_semana']}, {t['titulo']} ({t['subtitulo'] or 'sem descrição'})" for t in treinos]

        de_hoje = next((t for t in treinos if t["dia_semana"] == nome_hoje), None)
        if de_hoje is None:
            linhas.append(f"\nHoje é {nome_hoje.lower()} e não há treino salvo para hoje, então é dia de descanso.")
        else:
            cursor.execute(
                "SELECT nome_exercicio, series, repeticoes, descanso_segundos FROM treino_exercicios "
                "WHERE treino_id = %s ORDER BY ordem",
                (de_hoje["id"],),
            )
            linhas.append(f"\nHoje é {nome_hoje.lower()} e o seu treino é o {de_hoje['titulo']}:")
            for e in cursor.fetchall():
                descanso = f" (descanso {e['descanso_segundos']}s)" if e["descanso_segundos"] else ""
                linhas.append(f"- {e['nome_exercicio']}: {e['series']}x {e['repeticoes']}{descanso}")
        return "\n".join(linhas)
    finally:
        cursor.close()
