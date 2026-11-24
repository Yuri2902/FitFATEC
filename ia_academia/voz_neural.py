"""Voz neural brasileira via Edge TTS com tempos reais de cada palavra.

Serviço de rede não oficial; não requer chave. Usado somente quando o usuário
ativa a reprodução. Não altera a geração de texto pelo Gemini.
"""
from __future__ import annotations

import asyncio
import base64
import os


VOZ_PT_BR = os.getenv('KIARA_VOZ_NEURAL', 'pt-BR-FranciscaNeural')
# Aceitar apenas as duas vozes femininas brasileiras conhecidas do serviço.
VOZES_PERMITIDAS = {'pt-BR-FranciscaNeural', 'pt-BR-ThalitaMultilingualNeural'}
if VOZ_PT_BR not in VOZES_PERMITIDAS:
    VOZ_PT_BR = 'pt-BR-FranciscaNeural'


async def gerar_audio_neural(texto: str) -> dict:
    """Retorna MP3 em base64 e posições das palavras (segundos de reprodução)."""
    import edge_tts

    texto = str(texto or '').strip()
    if not texto or len(texto) > 240:
        raise ValueError('Trecho de fala inválido (até 240 caracteres).')

    comunicacao = edge_tts.Communicate(
        texto, VOZ_PT_BR, rate='+7%', pitch='+0Hz', boundary='WordBoundary',
        connect_timeout=8, receive_timeout=12,
    )
    audio = bytearray()
    marcacoes = []
    async for parte in comunicacao.stream():
        if parte['type'] == 'audio':
            audio.extend(parte['data'])
        elif parte['type'] == 'WordBoundary':
            marcacoes.append({
                'seg': round(parte['offset'] / 10_000_000, 3),
                'palavra': parte.get('text', ''),
            })
    if not audio:
        raise RuntimeError('O serviço de voz não enviou áudio.')
    return {
        'audio_b64': base64.b64encode(audio).decode('ascii'),
        'marcacoes': marcacoes,
        'voz': VOZ_PT_BR,
    }


def gerar_audio_neural_sincrono(texto: str) -> dict:
    # Flask roda esta rota sincronamente; limite total para não bloquear em rede.
    return asyncio.run(asyncio.wait_for(gerar_audio_neural(texto), timeout=15))
