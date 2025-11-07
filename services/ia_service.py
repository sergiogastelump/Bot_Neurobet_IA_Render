import os
import logging
import numpy as np
import random
from joblib import load

# === Importaciones internas === #
from services.api_service import obtener_estadisticas_equipo  # Datos reales
from services.evaluacion_service import registrar_prediccion  # Registro automático para evaluación

# === CONFIGURACIÓN DE LOGS === #
logger = logging.getLogger(__name__)

# === RUTA DEL MODELO ENTRENADO === #
MODEL_PATH = "data/modelo_entrenado.joblib"


# === CARGAR MODELO === #
def cargar_modelo():
    """
    Carga el modelo IA entrenado desde disco, si existe.
    Si no está disponible, usa modo simulado.
    """
    if os.path.exists(MODEL_PATH):
        try:
            modelo = load(MODEL_PATH)
            logger.info("✅ Modelo IA cargado correctamente desde disco.")
            return modelo, "modo_real"
        except Exception as e:
            logger.error(f"❌ Error al cargar el modelo entrenado: {e}")
            return None, "modo_simulado"
    else:
        logger.warning("⚠️ Modelo no encontrado. Modo simulado activo.")
        return None, "modo_simulado"


# === FUNCIÓN PRINCIPAL DE PREDICCIÓN === #
def predecir_partido(equipo_local: str, equipo_visitante: str):
    """
    Genera una predicción IA entre dos equipos,
    usando datos reales si están disponibles.
    """
    modelo, modo = cargar_modelo()

    # === 1️⃣ Obtener estadísticas reales desde la API === #
    stats_local = obtener_estadisticas_equipo(equipo_local)
    stats_visitante = obtener_estadisticas_equipo(equipo_visitante)

    if stats_local and stats_visitante:
        logger.info("📈 Datos reales obtenidos correctamente. Usando predicción avanzada.")
        goles_local = stats_local["goles_prom"]
        goles_visitante = stats_visitante["goles_prom"]
        tiros_local = random.randint(6, 14)
        tiros_visitante = random.randint(4, 12)
        posesion_local = 50 + (stats_local["win_rate"] - stats_visitante["win_rate"]) / 4
        posesion_visitante = 100 - posesion_local
    else:
        logger.warning("⚠️ Datos reales no disponibles, generando simulación.")
        goles_local = np.random.poisson(1.5)
        goles_visitante = np.random.poisson(1.2)
        tiros_local = np.random.randint(5, 15)
        tiros_visitante = np.random.randint(3, 12)
        posesion_local = np.random.randint(45, 65)
        posesion_visitante = 100 - posesion_local

    # === 2️⃣ Predicción con el modelo entrenado (modo real) === #
    if modelo and modo == "modo_real":
        try:
            X_pred = np.array([[goles_local, goles_visitante, tiros_local, tiros_visitante,
                                posesion_local, posesion_visitante]])
            pred = modelo.predict(X_pred)[0]
            proba = modelo.predict_proba(X_pred)[0] if hasattr(modelo, "predict_proba") else [0.33, 0.33, 0.33]

            # Interpretación de resultado
            if pred == 1:
                resultado = f"🏆 {equipo_local} gana"
                probabilidad = round(max(proba) * 100, 2)
            elif pred == -1:
                resultado = f"⚽ {equipo_visitante} gana"
                probabilidad = round(max(proba) * 100, 2)
            else:
                resultado = "🤝 Empate"
                probabilidad = round(proba[1] * 100 if len(proba) > 1 else 33.3, 2)

            # Registrar la predicción para futura evaluación
            registrar_prediccion(equipo_local, equipo_visitante, resultado, probabilidad)

            return {
                "resultado": resultado,
                "probabilidad": probabilidad,
                "modo": "Datos Reales + Modelo Entrenado",
            }

        except Exception as e:
            logger.error(f"❌ Error al generar predicción con el modelo: {e}")
            resultado = random.choice([
                f"🏆 {equipo_local} gana",
                f"⚽ {equipo_visitante} gana",
                "🤝 Empate"
            ])
            probabilidad = random.randint(40, 70)
            registrar_prediccion(equipo_local, equipo_visitante, resultado, probabilidad)
            return {
                "resultado": resultado,
                "probabilidad": probabilidad,
                "modo": "Fallback - Simulación de emergencia",
            }

    # === 3️⃣ Modo simulado (sin modelo entrenado) === #
    else:
        outcomes = [
            (f"🏆 {equipo_local} gana", 60),
            ("🤝 Empate", 25),
            (f"⚽ {equipo_visitante} gana", 15)
        ]
        resultado, prob = random.choice(outcomes)

        # Registrar predicción simulada
        registrar_prediccion(equipo_local, equipo_visitante, resultado, prob)

        return {
            "resultado": resultado,
            "probabilidad": prob,
            "modo": "Simulado (sin modelo)",
        }
