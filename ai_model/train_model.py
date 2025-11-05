# ai_model/train_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# Ruta del modelo entrenado
MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_entrenado.pkl")

def entrenar_modelo(ruta_datos="data/partidos_historicos.csv"):
    """
    Entrena el modelo de predicción con datos históricos.
    Los datos deben incluir columnas como:
    equipo_local, equipo_visitante, goles_local, goles_visitante, corners, tarjetas, resultado.
    """
    if not os.path.exists(ruta_datos):
        print("⚠️ No se encontró el archivo de datos históricos.")
        return

    df = pd.read_csv(ruta_datos)

    # Codificación simple (reemplazaremos luego con embeddings deportivos)
    df["resultado_binario"] = df["resultado"].apply(lambda x: 1 if x == "local" else 0)
    X = df[["goles_local", "goles_visitante", "corners", "tarjetas"]]
    y = df["resultado_binario"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = RandomForestClassifier(n_estimators=200, random_state=42)
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    precision = accuracy_score(y_test, y_pred) * 100

    joblib.dump(modelo, MODEL_PATH)
    print(f"✅ Modelo entrenado y guardado con precisión: {precision:.2f}%")
    return precision
