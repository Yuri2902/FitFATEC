"""Dicionário de nomes em português do FitFATEC.

NOMES fornece traduções revisadas; nomes_exercicios_pt.json é produzido pelo
tradutor inicial. O idioma original permanece associado ao ID para conferência,
mas nunca aparece no texto exibido ao aluno.
"""
import unicodedata
import json
from functools import lru_cache
from pathlib import Path


def _chave(s):
    s = unicodedata.normalize('NFKD', str(s or '').strip().lower())
    return ' '.join(''.join(c for c in s if not unicodedata.combining(c)).split())

# Traduções/descritivos curtos, não copiados do openGym.
NOMES = {
    'cable curl': 'Rosca direta na polia',
    'biceps leg concentration curl': 'Rosca concentrada de bíceps com resistência da perna',
    'bodyweight side lying biceps curl': 'Rosca de bíceps deitado de lado com peso corporal',
    'biceps cable curl': 'Rosca direta na polia',
    'cable concentration curl': 'Rosca concentrada na polia',
    'cable hammer curl with rope': 'Rosca martelo na polia com corda',
    'cable hammer curl': 'Rosca martelo na polia',
    'cable preacher curl': 'Rosca Scott na polia',
    'band curl': 'Rosca de bíceps com elástico',
    'curl with band': 'Rosca de bíceps com elástico',
    'band biceps curl': 'Rosca de bíceps com elástico',
    'band hammer curl': 'Rosca martelo com elástico',
    'resistance band biceps curl': 'Rosca de bíceps com elástico',
    'dumbbell curl': 'Rosca direta com halteres',
    'dumbbell biceps curl': 'Rosca direta com halteres',
    'dumbbell hammer curl': 'Rosca martelo com halteres',
    'barbell curl': 'Rosca direta com barra',
    'barbell biceps curl': 'Rosca direta com barra',
    'ez barbell curl': 'Rosca direta com barra W',
    'bodyweight squat': 'Agachamento livre',
    'squat': 'Agachamento',
    'air squat': 'Agachamento livre',
    'bodyweight lunge': 'Afundo com peso corporal',
    'lunge': 'Afundo',
    'forward lunge': 'Afundo à frente',
    'reverse lunge': 'Afundo reverso',
    'walking lunge': 'Afundo caminhando',
    'curtsey squat': 'Agachamento com passada cruzada',
    'curtsy squat': 'Agachamento com passada cruzada',
    'bodyweight standing calf raise': 'Elevação de panturrilhas em pé',
    'standing calf raise': 'Elevação de panturrilhas em pé',
    'single leg calf raise': 'Elevação unilateral de panturrilha',
    'glute bridge': 'Ponte de glúteos',
    'bodyweight glute bridge': 'Ponte de glúteos',
    'hip thrust': 'Elevação de quadril',
    'wall sit': 'Agachamento isométrico na parede',
    'step up': 'Subida no degrau',
    'step-up': 'Subida no degrau',
    'leg press': 'Leg press',
    'barbell squat': 'Agachamento com barra',
    'goblet squat': 'Agachamento goblet',
    'dumbbell squat': 'Agachamento com halteres',
    'leg extension': 'Extensão de joelhos na máquina',
    'seated leg curl': 'Flexão de joelhos sentado na máquina',
    'plank': 'Prancha',
    'forearm plank': 'Prancha sobre os antebraços',
    'side plank': 'Prancha lateral',
    'crunch': 'Abdominal curto',
    'abdominal crunch': 'Abdominal curto',
    'bicycle crunch': 'Abdominal bicicleta',
    'push-up': 'Flexão de braços',
    'push up': 'Flexão de braços',
    'knee push-up': 'Flexão de braços com joelhos apoiados',
    'bench press': 'Supino reto',
    'barbell bench press': 'Supino reto com barra',
    'dumbbell bench press': 'Supino reto com halteres',
    'incline dumbbell press': 'Supino inclinado com halteres',
    'pull-up': 'Barra fixa com pegada pronada',
    'chin-up': 'Barra fixa com pegada supinada',
    'lat pulldown': 'Puxada alta na polia',
    'seated cable row': 'Remada sentada na polia',
    'barbell row': 'Remada curvada com barra',
    'dumbbell row': 'Remada com halteres',
    'dumbbell shoulder press': 'Desenvolvimento com halteres',
    'lateral raise': 'Elevação lateral',
    'dumbbell lateral raise': 'Elevação lateral com halteres',
    'cable triceps pushdown': 'Extensão de tríceps na polia',
    'triceps pushdown': 'Extensão de tríceps na polia',
    'triceps dip': 'Mergulho para tríceps',
}


ARQUIVO_TRADUCOES = Path(__file__).resolve().parent / "dados" / "nomes_exercicios_pt.json"


@lru_cache(maxsize=1)
def traducoes_por_id():
    """Mapa local persistido; a geração nunca ocorre em uma consulta do aluno."""
    if not ARQUIVO_TRADUCOES.exists():
        return {}
    try:
        bruto = json.loads(ARQUIVO_TRADUCOES.read_text(encoding="utf-8"))
        return bruto if isinstance(bruto, dict) else {}
    except (ValueError, OSError):
        return {}


def nome_pt(nome_ingles, id_exercicio=None):
    """Obtém português por ID + original verificado, ou do dicionário revisado.

    None significa que a tradução ainda não foi produzida. Jamais retornar
    nome em inglês sob o rótulo de nome português.
    """
    original = str(nome_ingles or "").strip()
    if id_exercicio is not None:
        registro = traducoes_por_id().get(str(id_exercicio))
        if (isinstance(registro, dict)
                and _chave(registro.get("nome_original")) == _chave(original)
                and isinstance(registro.get("nome_pt"), str)
                and registro["nome_pt"].strip()):
            return registro["nome_pt"].strip()
    return NOMES.get(_chave(original))
