import os
import json
import logging
from datetime import datetime
from joblib import dump

logger = logging.getLogger(__name__)

MODEL_STATE_PATH = "data/modelo_ia.json"
MODEL_TRAINED_PATH = "data/modelo_entrenado.joblib"


def inicializar_modelo():
    """Crea un modelo base si no existe"""
    if not os.path.exists(MODEL_STATE_PATH):
        estado_inicial = {
            "sesgo_local": 0.0,
            "sesgo_visitante": 0.0,
            "factor_confianza": 1.0,
            "historial_precision": []
        }
        os.makedirs("data", exist_ok=True)
        with open(MODEL_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(estado_inicial, f, indent=2)
        logger.info("🧩 Modelo base inicializado correctamente (modo simulado).")


def evaluar_predicciones():
    """Evalúa precisión simulada hasta tener datos reales"""
    inicializar_modelo()
    try:
        with open(MODEL_STATE_PATH, "r", encoding="utf-8") as f:
            modelo = json.load(f)

        precision_simulada = round(50 + os.urandom(1)[0] % 30, 2)  # 50–80%
        modelo["historial_precision"].append({
            "fecha": datetime.utcnow().isoformat(),
            "precision": precision_simulada
        })
        modelo["factor_confianza"] = round(precision_simulada / 100, 3)

        with open(MODEL_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(modelo, f, indent=2)

        dump(modelo, MODEL_TRAINED_PATH)  # genera joblib simulado
        logger.info(f"🧠 Modelo actualizado automáticamente. Precisión simulada: {precision_simulada}%")
        return {"precision": precision_simulada}

    except Exception as e:
        logger.error(f"❌ Error evaluando modelo: {e}")
        return None


def obtener_estado_modelo():
    """Devuelve el estado actual del modelo IA"""
    if not os.path.exists(MODEL_STATE_PATH):
        return None
    with open(MODEL_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
