"""Colunas novas usadas pelo plano semanal e pelas personalidades da Kiara (Dev 3).

O bd_fitfatec.sql já cria essas colunas em instalações novas. Quem já tem o banco
criado não deve rodar o script de novo (o LEIA-ME avisa isso), então o servidor
chama garantir_colunas() ao iniciar, do mesmo jeito que já faz com a tabela do chat.
Só adiciona o que estiver faltando; nunca apaga nem altera dados existentes.
"""

COLUNAS_NOVAS = [
    # (tabela, coluna, definição)
    ("aluno", "personalidade", "VARCHAR(20) NOT NULL DEFAULT 'padrao'"),
    ("treino_exercicios", "etapa", "VARCHAR(20) NULL"),
]


def colunas_faltando(cursor):
    faltando = []
    for tabela, coluna, definicao in COLUNAS_NOVAS:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (tabela, coluna),
        )
        if cursor.fetchone()[0] == 0:
            faltando.append((tabela, coluna, definicao))
    return faltando


def garantir_colunas(abrir_conexao):
    """Recebe a função de conexão do servidor e cria as colunas que faltarem."""
    conn = abrir_conexao()
    try:
        cursor = conn.cursor()
        try:
            for tabela, coluna, definicao in colunas_faltando(cursor):
                # Nomes vêm da lista fixa acima, nunca do usuário.
                cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
            conn.commit()
        finally:
            cursor.close()
    finally:
        conn.close()
