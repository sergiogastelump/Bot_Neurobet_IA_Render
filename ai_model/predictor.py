# ai_model/predictor.py
import joblib
import os
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_entrenado.pkl")

def predecir_resultado(goles_local, goles_visitante, corners, tarjetas):
    """
    Realiza una predicción basada en las estadísticas del partido.
    """
    if not os.path.exists(MODEL_PATH):
        return "⚠️ Modelo no entrenado aún. Usa /entrenar para crear el modelo."

    modelo = joblib.load(MODEL_PATH)
    datos = np.array([[goles_local, goles_visitante, corners, tarjetas]])
    prediccion = modelo.predict(datos)[0]
    probas = modelo.predict_proba(datos)[0]

    if prediccion == 1:
        return f"🏠 Victoria local ({probas[1]*100:.1f}%)"
    else:
        return f"🚩 Victoria visitante ({probas[0]*100:.1f}%)"
