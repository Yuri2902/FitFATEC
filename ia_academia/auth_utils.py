import re
from werkzeug.security import generate_password_hash, check_password_hash

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def gerar_hash_senha(senha):
    return generate_password_hash(senha)


def verificar_senha(senha, hash_senha):
    return check_password_hash(hash_senha, senha)


def validar_cadastro(nome, email, senha):
    if not nome or not nome.strip():
        return False, "Nome é obrigatório."
    if not email or not EMAIL_REGEX.match(email):
        return False, "E-mail inválido."
    if not senha or len(senha) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres."
    return True, "Dados válidos."
