import os
import numpy as np
import pandas as pd

np.random.seed(42)
n = 1000

df = pd.DataFrame({
    "idade": np.random.randint(16, 65, n),
    "frequencia_semanal": np.random.randint(0, 7, n),
    "meses_matricula": np.random.randint(1, 36, n),
    "faltas_ultimo_mes": np.random.randint(0, 20, n),
})

# Pontuação de risco: mais faltas e menos frequência = mais risco
risco = (
    0.08 * df["faltas_ultimo_mes"]
    - 0.25 * df["frequencia_semanal"]
    - 0.01 * df["meses_matricula"]
    + np.random.normal(0, 0.3, n)
)
df["desistiu"] = (risco > risco.median()).astype(int)

os.makedirs("dados", exist_ok=True)
df.to_csv("dados/alunos.csv", index=False)
print("Arquivo dados/alunos.csv criado com", n, "alunos.")
print(df.head())
