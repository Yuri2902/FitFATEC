"""Síntese de voz local da Kiara usando Kokoro ONNX e a voz brasileira pf_dora."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from threading import Lock

RAIZ_BACKEND = Path(__file__).resolve().parent
PASTA_MODELO = RAIZ_BACKEND / "modelos" / "kiara_voz"
ARQUIVO_MODELO = PASTA_MODELO / "kokoro-v1.0.int8.onnx"
ARQUIVO_VOZES = PASTA_MODELO / "voices-v1.0.bin"

_lock_voz = Lock()
_motor_voz = None


def _carregar_motor():
    """Carrega o modelo apenas na primeira solicitação e mantém em memória."""
    global _motor_voz
    if _motor_voz is not None:
        return _motor_voz

    if not ARQUIVO_MODELO.is_file() or not ARQUIVO_VOZES.is_file():
        raise FileNotFoundError(
            "Arquivos do Kokoro ausentes. Execute configurar.ps1 para baixá-los."
        )

    try:
        from kokoro_onnx import Kokoro
    except ImportError as erro:
        raise RuntimeError(
            "Dependências da voz local ausentes. Execute configurar.ps1."
        ) from erro

    _motor_voz = Kokoro(str(ARQUIVO_MODELO), str(ARQUIVO_VOZES))
    return _motor_voz


def preparar_motor_voz() -> None:
    """Pré-carrega o Kokoro ao ativar o botão de voz, sem sintetizar fala."""
    with _lock_voz:
        _carregar_motor()


def gerar_audio_wav(texto: str) -> BytesIO:
    """Gera WAV PCM localmente; não faz chamadas a serviços externos."""
    texto = str(texto or "").strip()
    if not texto:
        raise ValueError("O texto para sintetizar está vazio.")
    if len(texto) > 12000:
        raise ValueError("O texto é muito longo para a síntese de voz.")

    # A inicialização e a inferência ficam serializadas para evitar duas cargas
    # simultâneas do modelo e contenção desnecessária de memória/CPU.
    with _lock_voz:
        motor = _carregar_motor()
        audio, taxa_amostragem = motor.create(
            texto,
            voice="pf_dora",
            speed=1.10,
            lang="pt-br",
        )

        try:
            import soundfile as sf
        except ImportError as erro:
            raise RuntimeError(
                "A biblioteca soundfile não está instalada. Execute configurar.ps1."
            ) from erro

        arquivo = BytesIO()
        sf.write(arquivo, audio, taxa_amostragem, format="WAV", subtype="PCM_16")
        arquivo.seek(0)
        return arquivo
