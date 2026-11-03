from datetime import date

from .agenda import resumo_agenda
from .catalogo import modalidades_aquecimento
from .gerador import sessao_do_dia
from .regras import DIAS_SEMANA, NOMES_DIAS, NOMES_NIVEIS, NOMES_OBJETIVOS


def _formatar_item(item):
    if item["series"] == 1 and item["repeticoes"].endswith("min"):
        texto = f"{item['nome']} {item['repeticoes']}"
    else:
        texto = f"{item['nome']} {item['series']} x {item['repeticoes']}"
    if item.get("observacao"):
        texto += f" ({item['observacao']})"
    return texto


def _formatar_etapa(itens):
    return "; ".join(_formatar_item(i) for i in itens) or "nenhum"


def resumo_plano(plano, hoje=None):
    perfil = plano["perfil"]
    pres = plano["prescricao"]
    quantidade = len(perfil["dias_semana"])
    dias_texto = "1 dia por semana" if quantidade == 1 else f"{quantidade} dias por semana"

    linhas = [
        f"Objetivo: {NOMES_OBJETIVOS[perfil['objetivo']]}; nível: {NOMES_NIVEIS[perfil['nivel']]}; "
        f"{dias_texto}; cerca de {perfil['minutos_por_sessao']} min por sessão; local: {perfil['local']}."
    ]
    if perfil["restricoes"]:
        linhas.append(f"Restrições informadas pelo aluno: {', '.join(perfil['restricoes'])}.")

    semana = ", ".join(f"{NOMES_DIAS[d['dia']]} treino {d['sessao']}" for d in plano["semana"] if d["sessao"])
    linhas.append(f"Divisão: {plano['divisao']}. Semana: {semana}. Os outros dias são de descanso.")
    linhas.append(
        f"Treino principal: {pres['series']} séries de {pres['repeticoes']} repetições, "
        f"descanso de {pres['intervalo_seg']} s. {pres['carga']}"
    )

    for sessao in plano["sessoes"]:
        linhas.append(f"Treino {sessao['letra']} ({sessao['nome']}, cerca de {sessao['duracao_estimada_min']} min):")
        linhas.append(f"  Aquecimento: {_formatar_etapa(sessao['aquecimento'])}")
        linhas.append(f"  Principal: {_formatar_etapa(sessao['principal'])}")
        linhas.append(f"  Complementar: {_formatar_etapa(sessao['complementar'])}")

    hoje = hoje or date.today()
    sessao = sessao_do_dia(plano, hoje)
    nome_dia = NOMES_DIAS[DIAS_SEMANA[hoje.weekday()]]
    if sessao:
        linhas.append(f"Hoje é {nome_dia}, dia do treino {sessao['letra']}.")
    else:
        linhas.append(f"Hoje é {nome_dia}, dia de descanso.")

    for observacao in plano["observacoes"]:
        linhas.append(f"Observação: {observacao}")
    return "\n".join(linhas)


def contexto_para_ia(plano=None, plano_salvo=False, hoje=None):
    partes = [
        "INFORMAÇÕES DE TREINO DA ACADEMIA (use como base para falar de treinos, aquecimento e agenda):",
        "",
        "Modalidades de aquecimento:",
    ]
    for modalidade in modalidades_aquecimento():
        linha = f"- {modalidade['nome']} ({modalidade['duracao']}): {modalidade['descricao']}"
        if modalidade["exemplos"]:
            linha += " Exemplos: " + ", ".join(e["nome"] for e in modalidade["exemplos"]) + "."
        partes.append(linha)

    partes += ["", "Agenda da academia:", resumo_agenda(), ""]

    if plano is None:
        partes.append(
            "O aluno ainda não tem plano de treino. Se ele pedir um treino, pergunte objetivo, nível "
            "e quantos dias por semana pode treinar, e sugira gerar o plano pelo app."
        )
    else:
        if plano_salvo:
            partes.append("Plano de treino salvo do aluno:")
        else:
            partes.append("Plano sugerido pelo sistema com base nos dados do aluno (ainda não foi salvo):")
        partes.append(resumo_plano(plano, hoje))

    partes += [
        "",
        "Ao falar de exercícios, séries, horários e regras, use só as informações acima. Não invente horários "
        "de aula e não diga que uma reserva foi feita: quem confirma o agendamento é a agenda do app.",
    ]
    return "\n".join(partes)
