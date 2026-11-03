import math
from datetime import date

from .agenda import FUNCIONAMENTO
from .catalogo import EXERCICIOS, NIVEIS, buscar_exercicio
from .regras import (
    CARDIO_FINAL,
    DIAS_SEMANA,
    MAX_DIAS_INICIANTE,
    MAX_EXERCICIOS,
    MIN_EXERCICIOS,
    NOMES_DIAS,
    SEGUNDOS_ISOMETRIA,
    SESSOES,
    montar_divisao,
    normalizar_perfil,
    prescricao,
)

ETAPAS = ("aquecimento", "principal", "complementar")

SEGUNDOS_POR_SERIE = 40
MINUTOS_TROCA_EXERCICIO = 1
MINUTOS_CARDIO_AQUECIMENTO = 5
MINUTOS_CARDIO_MINIMO = 10
MINUTOS_ALONGAMENTO = 5
INTERVALO_CORE = 30

FOCO_MOBILIDADE = {
    "geral": ("ombros", "quadril"),
    "superior": ("ombros", "coluna"),
    "inferior": ("quadril", "tornozelo"),
}

AVISO_ESPECIFICO = "Antes, faça uma série leve de aquecimento com metade da carga ou metade das repetições."


def _filtrar(perfil, tipo, grupo=None, nivel_max=None, mesmo_nivel_primeiro=True):
    limite = NIVEIS.index(nivel_max or perfil["nivel"])
    restricoes = set(perfil["restricoes"])
    lista = [
        e for e in EXERCICIOS
        if e["tipo"] == tipo
        and (grupo is None or e["grupo"] == grupo)
        and NIVEIS.index(e["nivel"]) <= limite
        and (perfil["local"] == "academia" or e["casa"])
        and not restricoes.intersection(e["restricoes"])
    ]
    if mesmo_nivel_primeiro:
        lista.sort(key=lambda e: limite - NIVEIS.index(e["nivel"]))
    return lista


def _girar(lista, variacao):
    if not lista:
        return lista
    k = variacao % len(lista)
    return lista[k:] + lista[:k]


def _item(exercicio, series, repeticoes, intervalo, observacao=""):
    return {
        "codigo": exercicio["codigo"],
        "nome": exercicio["nome"],
        "grupo": exercicio["grupo"],
        "series": series,
        "repeticoes": repeticoes,
        "intervalo_seg": intervalo,
        "observacao": observacao,
    }


def duracao_item(item):
    """Minutos aproximados para fazer o item inteiro, contando o descanso."""
    exercicio = buscar_exercicio(item["codigo"])
    medida = exercicio["medida"] if exercicio else "repeticoes"
    if medida == "minutos":
        return item["series"] * int(item["repeticoes"].split()[0])
    esforco = int(item["repeticoes"].split()[0]) if medida == "segundos" else SEGUNDOS_POR_SERIE
    return item["series"] * (esforco + item["intervalo_seg"]) / 60


def _minutos(itens):
    return sum(duracao_item(i) for i in itens)


def _mobilidade(perfil, foco, variacao):
    itens = []
    for regiao in FOCO_MOBILIDADE[foco]:
        opcoes = _girar(_filtrar(perfil, "mobilidade", grupo=regiao), variacao)
        if opcoes:
            itens.append(_item(opcoes[0], 1, "10", 0))
    return itens


def _aquecimento(perfil, foco, variacao):
    itens = []
    cardio = _girar(_filtrar(perfil, "cardio", nivel_max="iniciante", mesmo_nivel_primeiro=False), variacao)
    if cardio:
        itens.append(_item(cardio[0], 1, f"{MINUTOS_CARDIO_AQUECIMENTO} min", 0, "Ritmo leve, só para aquecer."))
    return itens + _mobilidade(perfil, foco, variacao)


def _principal(grupos, quantidade, perfil, variacao, pres):
    itens, usados = [], set()
    for grupo in grupos:
        if len(itens) == quantidade:
            break
        opcoes = [e for e in _girar(_filtrar(perfil, "forca", grupo), variacao) if e["codigo"] not in usados]
        if not opcoes:
            continue
        usados.add(opcoes[0]["codigo"])
        itens.append(_item(opcoes[0], pres["series"], pres["repeticoes"], pres["intervalo_seg"]))
    if itens:
        itens[0]["observacao"] = AVISO_ESPECIFICO
    return itens


def _complementar(perfil, variacao, pres, evitar=()):
    nivel = perfil["nivel"]
    itens = []
    quantidade_core = 1 if nivel == "iniciante" else 2
    for exercicio in _girar(_filtrar(perfil, "core"), variacao)[:quantidade_core]:
        if exercicio["medida"] == "segundos":
            volume = f"{SEGUNDOS_ISOMETRIA[nivel]} s"
        else:
            volume = "12" if nivel == "iniciante" else "15"
        itens.append(_item(exercicio, pres["series"], volume, INTERVALO_CORE))

    cardio = CARDIO_FINAL.get(perfil["objetivo"], {}).get(nivel)
    opcoes = _girar(_filtrar(perfil, "cardio", mesmo_nivel_primeiro=False), variacao)
    opcoes = [e for e in opcoes if e["codigo"] not in evitar] or opcoes
    if cardio and opcoes:
        minutos, como_fazer = cardio
        itens.append(_item(opcoes[0], 1, f"{minutos} min", 0, como_fazer))

    itens.append(_item(buscar_exercicio("alongamento_geral"), 1, f"{MINUTOS_ALONGAMENTO} min", 0))
    return itens


def _encurtar_cardio(complementar, excesso):
    for item in complementar:
        if excesso <= 0:
            break
        if buscar_exercicio(item["codigo"])["tipo"] != "cardio":
            continue
        atual = int(item["repeticoes"].split()[0])
        novo = max(MINUTOS_CARDIO_MINIMO, atual - math.ceil(excesso))
        item["repeticoes"] = f"{novo} min"
        excesso -= atual - novo


def _duracao_sessao(aquecimento, principal, complementar):
    total = _minutos(aquecimento) + _minutos(principal) + _minutos(complementar)
    return total + len(principal) * MINUTOS_TROCA_EXERCICIO


def _sessao_recuperacao(perfil, letra):
    cardio = _filtrar(perfil, "cardio", nivel_max="iniciante", mesmo_nivel_primeiro=False)
    minutos = max(15, min(30, perfil["minutos_por_sessao"] - 15))
    principal = []
    if cardio:
        principal.append(_item(cardio[0], 1, f"{minutos} min", 0, "Ritmo leve e confortável, sem cansar."))
    aquecimento = _mobilidade(perfil, "geral", 0)
    complementar = [_item(buscar_exercicio("alongamento_geral"), 1, "10 min", 0)]
    return {
        "letra": letra,
        "nome": "Recuperação ativa",
        "dias": [],
        "duracao_estimada_min": round(_minutos(aquecimento) + _minutos(principal) + _minutos(complementar)),
        "aquecimento": aquecimento,
        "principal": principal,
        "complementar": complementar,
    }


def _sessao(tipo, variacao, perfil, letra):
    if tipo == "recuperacao":
        return _sessao_recuperacao(perfil, letra)

    nome, foco, grupos = SESSOES[tipo]
    pres = prescricao(perfil["objetivo"], perfil["nivel"])
    aquecimento = _aquecimento(perfil, foco, variacao)
    complementar = _complementar(perfil, variacao, pres, evitar={i["codigo"] for i in aquecimento})

    livre = perfil["minutos_por_sessao"] - _minutos(aquecimento) - _minutos(complementar)
    por_exercicio = pres["series"] * (SEGUNDOS_POR_SERIE + pres["intervalo_seg"]) / 60 + MINUTOS_TROCA_EXERCICIO
    quantidade = max(MIN_EXERCICIOS, min(int(livre // por_exercicio), MAX_EXERCICIOS[perfil["nivel"]]))
    principal = _principal(grupos, quantidade, perfil, variacao, pres)

    excesso = _duracao_sessao(aquecimento, principal, complementar) - perfil["minutos_por_sessao"]
    if excesso > 0:
        _encurtar_cardio(complementar, excesso)

    return {
        "letra": letra,
        "nome": nome,
        "dias": [],
        "duracao_estimada_min": round(_duracao_sessao(aquecimento, principal, complementar)),
        "aquecimento": aquecimento,
        "principal": principal,
        "complementar": complementar,
    }


def montar_semana(sessoes):
    letra_do_dia = {dia: s["letra"] for s in sessoes for dia in s["dias"]}
    return [{"dia": dia, "sessao": letra_do_dia.get(dia)} for dia in DIAS_SEMANA]


def gerar_plano(dados):
    perfil = normalizar_perfil(dados)
    observacoes = []

    dias = list(perfil["dias_semana"])
    if len(dias) == 7:
        dias.remove("dom")
        observacoes.append("O domingo ficou livre: o corpo precisa de pelo menos um dia de descanso por semana.")
    perfil["dias_semana"] = dias

    nome_divisao, sequencia = montar_divisao(len(dias), perfil["nivel"])
    por_chave = {}
    for dia, (tipo, variacao) in zip(dias, sequencia):
        if (tipo, variacao) not in por_chave:
            letra = chr(ord("A") + len(por_chave))
            por_chave[(tipo, variacao)] = _sessao(tipo, variacao, perfil, letra)
        por_chave[(tipo, variacao)]["dias"].append(dia)
    sessoes = list(por_chave.values())

    if any(tipo == "recuperacao" for tipo, _ in sequencia):
        observacoes.append(
            f"Para iniciantes, o plano tem no máximo {MAX_DIAS_INICIANTE} dias de musculação. "
            "Os outros dias viraram recuperação ativa, com cardio leve e alongamento."
        )
    if perfil["restricoes"]:
        observacoes.append(
            f"Você informou restrição em: {', '.join(perfil['restricoes'])}. Os exercícios que forçam "
            "essas regiões ficaram de fora. Antes de incluí-los, converse com um profissional de saúde."
        )
    fechados = [NOMES_DIAS[d] for d in dias if DIAS_SEMANA.index(d) not in FUNCIONAMENTO]
    if perfil["local"] == "academia" and fechados:
        observacoes.append(
            f"A academia não abre no {', '.join(fechados)}. Nesse dia, faça o treino em casa ou escolha outro dia."
        )
    maior = max(s["duracao_estimada_min"] for s in sessoes)
    if maior > perfil["minutos_por_sessao"] + 5:
        observacoes.append(
            f"Mesmo no formato mais curto, o treino leva cerca de {maior} minutos. "
            "Se o tempo estiver apertado, tire uma série de cada exercício."
        )
    if perfil["nivel"] == "iniciante":
        observacoes.append("Nas primeiras semanas, priorize aprender a execução com carga leve.")
    observacoes.append(
        "Este plano é uma sugestão automática e não substitui a orientação de um profissional de educação física."
    )

    return {
        "perfil": perfil,
        "divisao": nome_divisao,
        "prescricao": prescricao(perfil["objetivo"], perfil["nivel"]),
        "sessoes": sessoes,
        "semana": montar_semana(sessoes),
        "observacoes": observacoes,
    }


def sessao_do_dia(plano, dia=None):
    codigo = DIAS_SEMANA[(dia or date.today()).weekday()]
    for sessao in plano["sessoes"]:
        if codigo in sessao["dias"]:
            return sessao
    return None
