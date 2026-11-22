"""Testes isolados do adaptador de voz local da Kiara."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import numpy as np

import voz_kiara


class FakeKokoro:
    def __init__(self, model_path, voices_path):
        self.model_path = model_path
        self.voices_path = voices_path

    def create(self, texto, voice, speed, lang):
        assert voice == "pf_dora"
        assert lang == "pt-br"
        assert speed == 0.96
        assert texto == "Olá, Kiara!"
        return np.zeros(2400, dtype=np.float32), 24000


class TestVozKiara(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        pasta = Path(self.temp.name)
        self.modelo = pasta / "modelo.onnx"
        self.vozes = pasta / "vozes.bin"
        self.modelo.write_bytes(b"modelo de teste")
        self.vozes.write_bytes(b"vozes de teste")
        voz_kiara._motor_voz = None

    def tearDown(self):
        voz_kiara._motor_voz = None
        self.temp.cleanup()

    def test_gera_wav_com_voz_brasileira_local(self):
        modulo = ModuleType("kokoro_onnx")
        modulo.Kokoro = FakeKokoro
        with patch.object(voz_kiara, "ARQUIVO_MODELO", self.modelo), \
                patch.object(voz_kiara, "ARQUIVO_VOZES", self.vozes), \
                patch.dict(sys.modules, {"kokoro_onnx": modulo}):
            wav = voz_kiara.gerar_audio_wav("Olá, Kiara!")

        self.assertEqual(wav.read(4), b"RIFF")
        wav.seek(8)
        self.assertEqual(wav.read(4), b"WAVE")

    def test_recusa_texto_vazio(self):
        with self.assertRaises(ValueError):
            voz_kiara.gerar_audio_wav("   ")

    def test_recusa_texto_acima_do_limite(self):
        with self.assertRaises(ValueError):
            voz_kiara.gerar_audio_wav("a" * 12001)

    def test_avisa_quando_modelos_nao_estao_instalados(self):
        with patch.object(voz_kiara, "ARQUIVO_MODELO", Path(self.temp.name) / "ausente.onnx"), \
                patch.object(voz_kiara, "ARQUIVO_VOZES", Path(self.temp.name) / "ausente.bin"):
            with self.assertRaises(FileNotFoundError):
                voz_kiara.gerar_audio_wav("Olá, Kiara!")


if __name__ == "__main__":
    unittest.main()
