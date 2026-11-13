from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

df = pd.read_csv(BASE_DIR / "dados" / "alunos.csv")

colunas = ["idade", "frequencia_semanal", "meses_matricula", "faltas_ultimo_mes"]
X = df[colunas]
y = df["desistiu"]

X_treino, X_teste, y_treino, y_teste = train_test_split(
    X, y, test_size=0.2, random_state=42
)

modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_treino, y_treino)

previsoes = modelo.predict(X_teste)
print("Acurácia:", round(modelo.score(X_teste, y_teste), 3))
print(classification_report(y_teste, previsoes))

for nome, importancia in zip(colunas, modelo.feature_importances_):
    print(f"{nome}: {importancia:.2f}")

joblib.dump(modelo, BASE_DIR / "modelo_evasao.pkl")
print("Modelo salvo em modelo_evasao.pkl")
