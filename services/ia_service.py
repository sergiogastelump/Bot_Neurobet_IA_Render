import os
import random
import joblib
import pandas as pd

# Intentar cargar modelo si existe
MODEL_PATH = "models/random_forest.pkl"
modelo = None

if os.path.exists(MODEL_PATH):
    try:
        modelo = joblib.load(MODEL_PATH)
        print("✅ Modelo IA cargado correctamente.")
    except Exception as e:
        print(f"⚠️ No se pudo cargar el modelo: {e}")
else:
    print("⚠️ Modelo no encontrado. Modo simulado activo.")

def predecir_partido(equipo_local: str, equipo_visitante: str) -> dict:
    """
    Si hay modelo IA, predice con él.
    Si no, usa modo simulado.
    """

    if modelo is not None:
        # Ejemplo: DataFrame de prueba (simulamos entrada de datos reales)
        datos = pd.DataFrame([{
            "ataque_local": random.uniform(0.4, 0.9),
            "defensa_local": random.uniform(0.4, 0.9),
            "ataque_visitante": random.uniform(0.4, 0.9),
            "defensa_visitante": random.uniform(0.4, 0.9),
        }])

        try:
            pred = modelo.predict(datos)[0]
            proba = modelo.predict_proba(datos).max() * 100
            resultado = f"Predicción IA: {equipo_local} {pred} - {3 - pred} {equipo_visitante}"
            return {
                "local": equipo_local,
                "visitante": equipo_visitante,
                "resultado": resultado,
                "probabilidad": round(proba, 2),
                "modo": "IA Real"
            }
        except Exception as e:
            print(f"⚠️ Error al predecir: {e}")

    # Si no hay modelo, modo simulado
    goles_local = random.randint(0, 3)
    goles_visitante = random.randint(0, 3)
    prob = random.uniform(55, 90)

    return {
        "local": equipo_local,
        "visitante": equipo_visitante,
        "resultado": f"{equipo_local} {goles_local} - {goles_visitante} {equipo_visitante}",
        "probabilidad": round(prob, 2),
        "modo": "Simulado"
    }
