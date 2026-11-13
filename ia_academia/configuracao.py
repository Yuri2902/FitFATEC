"""Configuração compartilhada: lê .env na raiz, sem sobrescrever variáveis do terminal."""
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]


def carregar_ambiente():
    try:
        from dotenv import load_dotenv
    except ImportError:
        # Os testes de lógica podem rodar sem a dependência opcional de configuração.
        return False
    return load_dotenv(RAIZ_PROJETO / ".env", override=False)


carregar_ambiente()
