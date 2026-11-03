import os

from .catalogo import EXERCICIOS

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bdd", "catalogo_exercicios.sql")


def _texto(valor):
    return "'" + str(valor).replace("\\", "\\\\").replace("'", "''") + "'"


def gerar_sql():
    valores = ",\n".join(
        f"    ({_texto(e['nome'])}, {_texto(e['grupo'])}, {_texto(e['nivel'])})" for e in EXERCICIOS
    )
    return (
        "-- Catálogo de exercícios do FitFATEC. Gerado por: python -m treinos.gerar_sql_catalogo\n"
        "-- Pode rodar mais de uma vez: o que já existe só é atualizado.\n"
        "USE fitfatec;\n"
        "SET NAMES utf8mb4;\n\n"
        "INSERT INTO exercicio (nome, grupo_muscular, nivel) VALUES\n"
        f"{valores}\n"
        "ON DUPLICATE KEY UPDATE grupo_muscular = VALUES(grupo_muscular), nivel = VALUES(nivel);\n"
    )


if __name__ == "__main__":
    caminho = os.path.normpath(ARQUIVO)
    with open(caminho, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(gerar_sql())
    print("Gerado:", caminho)
