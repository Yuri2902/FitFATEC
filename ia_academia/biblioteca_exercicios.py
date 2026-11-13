"""Consulta local de METADADOS MIT de ExerciseDB/hasaneyldrm, sem mídia.

A licença e a origem devem permanecer documentadas em
`documentacao/ATRIBUICOES_EXERCICIOS.md`. Nenhum dado é baixado em tempo de
execução do servidor: o operador importa os metadados uma única vez.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from functools import lru_cache
from nomes_exercicios_pt import nome_pt

DATA_PATH = Path(__file__).resolve().parent / "dados" / "exercicios_mit.json"


def normalizar(texto: str) -> str:
    texto = "".join(c for c in unicodedata.normalize("NFD", str(texto).casefold())
                    if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto)

# Expressões em português para grupos pedidos pelo aluno. Nomes no dataset em inglês.
GRUPOS = {
    "biceps": ("biceps", "bicep"),
    "triceps": ("triceps", "tricep"),
    "pernas": ("pernas", "perna", "quadriceps", "coxa", "coxas"),
    "gluteos": ("gluteos", "gluteo"),
    "panturrilhas": ("panturrilha", "panturrilhas"),
    "peito": ("peito", "peitoral"),
    "costas": ("costas", "dorsal", "dorsais"),
    "ombros": ("ombro", "ombros"),
    "abdomen": ("abdomen", "abdominal", "abdominais", "core"),
}

ALVOS = {
    "biceps": {"biceps", "brachialis"},
    "triceps": {"triceps"},
    "pernas": {"quads", "quadriceps", "hamstrings", "glutes", "calves", "adductors", "abductors"},
    "gluteos": {"glutes"},
    "panturrilhas": {"calves"},
    "peito": {"pectorals", "chest", "pectoralis major"},
    "costas": {"lats", "upper back", "middle back", "traps", "lower back"},
    "ombros": {"delts", "shoulders", "deltoids"},
    "abdomen": {"abs", "abdominals", "obliques"},
}

CATEGORIAS = {
    "pernas": {"upper legs", "lower legs"},
    "peito": {"chest"},
    "costas": {"back"},
    "ombros": {"shoulders"},
    "abdomen": {"waist"},
    "panturrilhas": {"lower legs"},
}

# Equipamentos da fonte estão em inglês. O filtro é conservador:
# sem máquinas também veta cabo/polia e smith.
PROIBICOES = {
    "halter": {"dumbbell"},
    "maquina": {"leverage machine", "smith machine", "cable", "assisted"},
    "barra": {"barbell", "ez barbell", "smith machine"},
    "elastico": {"band", "resistance band"},
    "kettlebell": {"kettlebell"},
}


def _palavra(texto: str, termo: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(termo) + r"(?!\w)", texto) is not None


def grupos_relevantes(historico: list[dict]) -> list[str]:
    """Conserva focos da conversa curta quando aluno diz 'ambos'."""
    usuarios = [normalizar(m.get("content", "")) for m in historico if m.get("role") == "user"]
    if not usuarios:
        return []
    atual = usuarios[-1]
    partes = [atual]
    if re.search(r"\b(?:combin\w*|junt\w*|mistur\w*|ambos|ambas|dois|duas)\b", atual):
        partes += usuarios[-5:-1]
    elif any(p in atual for p in ("trocar", "substituir", "substitua", "no lugar", "alternativa")):
        partes += usuarios[-4:-1]
    encontrados = []
    for trecho in partes:
        for grupo, aliases in GRUPOS.items():
            if grupo not in encontrados and any(_palavra(trecho, alias) for alias in aliases):
                encontrados.append(grupo)
    return encontrados[:3]


def restricoes_equipamento(historico: list[dict]) -> set[str]:
    """Restrições ditas pelo aluno persistem durante a conversa atual.

    É intencionalmente conservador: preferimos não sugerir certo equipamento
    a ignorar uma restrição. Reiniciar a conversa reinicia o contexto.
    """
    proibir = set()
    mensagens = [normalizar(m.get("content", "")) for m in historico if m.get("role") == "user"]
    for texto in mensagens:
        if re.search(r"(?:sem|nao tenho|nao uso|evitar|evite|nao posso usar|indisponive[l])\s+(?:acesso\s+a\s+)?(?:nenhum\s+)?(?:equipamento|equipamentos)", texto):
            proibir.update({"dumbbell", "leverage machine", "smith machine", "cable", "assisted",
                            "barbell", "ez barbell", "band", "resistance band", "kettlebell", "weighted",
                            "stability ball", "medicine ball", "rope", "bosu ball"})
        frases = {
            "halter": r"(?:sem|nao tenho|nao uso|evit\w*|nao posso usar)\s+(?:acesso\s+a\s+)?(?:os?\s+)?halter",
            "maquina": r"(?:sem|nao tenho|nao uso|evit\w*|nao posso usar)\s+(?:acesso\s+a\s+)?(?:as?\s+)?maquin",
            "barra": r"(?:sem|nao tenho|nao uso|evit\w*|nao posso usar)\s+(?:acesso\s+a\s+)?(?:as?\s+)?barra",
            "elastico": r"(?:sem|nao tenho|nao uso|evit\w*|nao posso usar)\s+(?:acesso\s+a\s+)?(?:os?\s+)?elastic",
            "kettlebell": r"(?:sem|nao tenho|nao uso|evit\w*|nao posso usar)\s+(?:acesso\s+a\s+)?(?:os?\s+)?kettlebell",
        }
        for tipo, regex in frases.items():
            if re.search(regex, texto):
                proibir.update(PROIBICOES[tipo])
    return proibir


@lru_cache(maxsize=1)
def carregar() -> list[dict]:
    if not DATA_PATH.is_file():
        return []
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _do_grupo(item: dict, grupo: str) -> bool:
    alvo = normalizar(item.get("target", ""))
    categoria = normalizar(item.get("category", ""))
    if alvo in ALVOS.get(grupo, set()):
        return True
    # Categorias são amplas; só usar quando não confundem bíceps com tríceps.
    return categoria in CATEGORIAS.get(grupo, set())


def _candidatos_grupo(exercicios, grupo: str, proibidos: set[str], excluir: set[str]) -> list[dict]:
    candidatos = []
    for x in exercicios:
        if not _do_grupo(x, grupo):
            continue
        nome = normalizar(x.get("name", ""))
        equip = normalizar(x.get("equipment", ""))
        if equip in proibidos or any(termo in nome for termo in excluir):
            continue
        original = str(x.get("name", "")).strip()
        traducao = nome_pt(original, x.get("id"))
        # Nomes originais ainda não traduzidos precisam ser processados UMA VEZ
        # por traduzir_exercicios.py. Não exibir inglês como resposta ao aluno.
        if not traducao:
            continue
        # Alongamentos não são exercícios de força principal.
        if any(t in nome for t in ("stretch", "mobility", "warm-up", "warm up")):
            continue
        item = dict(x)
        item["nome_pt"] = traducao
        item["nome_original"] = original
        item["traducao_revisada"] = True
        item["nome_exibicao"] = traducao
        candidatos.append(item)
    # Depois de gerar o mapa completo, todo o catálogo fica disponível
    # sem misturar idioma original na apresentação.
    peso = {"body weight": 0, "band": 1, "resistance band": 1,
            "dumbbell": 2, "cable": 3}
    candidatos.sort(key=lambda x: (peso.get(normalizar(x.get("equipment")), 4),
                                    not x["traducao_revisada"], normalizar(x.get("name"))))
    return candidatos


def selecionar(historico: list[dict], limite: int = 18) -> dict:
    grupos = grupos_relevantes(historico)
    proibidos = restricoes_equipamento(historico)
    ultimo = normalizar(next((m.get("content", "") for m in reversed(historico)
                              if m.get("role") == "user"), ""))
    relevante = bool(grupos) or any(p in ultimo for p in (
        "treino", "serie", "exercic", "substitu", "trocar", "troque", "agachamento",
        "leg press", "combinar", "juntar", "alternar", "ambos", "ambas"))
    if not relevante or any(p in ultimo for p in ("agendar aula", "marcar aula")):
        return {"disponivel": bool(carregar()), "grupos": grupos,
                "proibidos": sorted(proibidos), "itens": [], "aplicavel": False}
    # Evitar sugerir o próprio exercício que o aluno explicitamente quer trocar.
    excluir = set()
    if any(t in ultimo for t in ("substitu", "trocar", "troque", "no lugar", "sem leg press")):
        if "leg press" in ultimo:
            excluir.add("leg press")
    todos = carregar()
    if not todos:
        return {"disponivel": False, "grupos": grupos, "proibidos": sorted(proibidos), "itens": []}
    grupos = grupos or ["pernas", "costas", "peito", "biceps", "triceps"]
    por_grupo = {g: _candidatos_grupo(todos, g, proibidos, excluir) for g in grupos}
    # Rodízio por grupo para pedidos combinados; não repetir IDs.
    itens = []
    ids = set()
    limite = max(1, min(30, limite))
    while len(itens) < limite and any(por_grupo.values()):
        houve = False
        for g in grupos:
            if not por_grupo[g] or len(itens) >= limite:
                continue
            x = por_grupo[g].pop(0)
            if x["id"] not in ids:
                ids.add(x["id"])
                itens.append(x)
                houve = True
        if not houve:
            break
    faltantes = [g for g in grupos if not any(_do_grupo(i, g) for i in itens)]
    return {"disponivel": True, "grupos": grupos,
            "proibidos": sorted(proibidos), "itens": itens,
            "faltantes": faltantes, "aplicavel": True}


def resumo_para_ia(resultado: dict) -> str:
    if resultado.get("aplicavel") is False:
        return "Biblioteca ampliada disponível para consultas de treino, não necessária nesta mensagem."
    if not resultado["disponivel"]:
        return ("Biblioteca MIT adicional NÃO importada. Use somente o catálogo local básico. "
                "Se a restrição do aluno não for atendida pelo catálogo, diga isso; "
                "não proponha um equipamento que ele disse não ter.")
    lines = ["OPÇÕES LICENCIADAS (ExerciseDB/hasaneyldrm, metadados MIT; sem imagens):"]
    if resultado["grupos"]:
        lines.append("Grupos solicitados: " + ", ".join(resultado["grupos"]))
    if resultado["proibidos"]:
        lines.append("EQUIPAMENTOS PROIBIDOS pelo aluno: " + ", ".join(resultado["proibidos"]))
    EQUIPAMENTOS_PT = {"body weight": "peso corporal", "band": "elástico",
                       "resistance band": "elástico", "dumbbell": "halteres",
                       "cable": "polia", "barbell": "barra",
                       "leverage machine": "máquina", "smith machine": "máquina Smith"}
    for item in resultado["itens"]:
        # A IA recebe apenas rótulos PT, mas os IDs garantem rastreabilidade
        # no dataset original. Nomes ingleses ficam privados no arquivo local.
        lines.append(f"- [{item['id']}] {item['nome_pt']} | grupo: {item['target']} | "
                     f"equipamento: {EQUIPAMENTOS_PT.get(item['equipment'], item['equipment'])}")
    if resultado.get("faltantes"):
        lines.append("Grupos sem opção traduzida e compatível com os equipamentos informados: " + ", ".join(resultado["faltantes"]))
    if not resultado["itens"]:
        lines.append("Nenhuma opção segura no filtro atual. Pergunte sobre equipamento disponível.")
    return "\n".join(lines)
