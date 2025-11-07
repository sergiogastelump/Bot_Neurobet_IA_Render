import os
import json
import logging
import requests
from datetime import datetime, timedelta
from threading import Thread, Event
import time

logger = logging.getLogger(__name__)

# === CONFIGURACIÓN API === #
API_KEY = os.getenv("API_KEY", "329f4fac732d45049158a52092727496")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

# === RUTA DE HISTORIAL === #
HISTORIAL_PATH = "data/historial_predicciones.json"


# === UTILIDADES === #
def cargar_historial():
    if not os.path.exists(HISTORIAL_PATH):
        return []
    try:
        with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Error cargando historial: {e}")
        return []


def guardar_historial(data):
    try:
        with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ Error guardando historial: {e}")


# === REGISTRAR NUEVA PREDICCIÓN === #
def registrar_prediccion(equipo_local, equipo_visitante, prediccion, probabilidad):
    historial = cargar_historial()
    registro = {
        "partido": f"{equipo_local} vs {equipo_visitante}",
        "prediccion": prediccion,
        "probabilidad": probabilidad,
        "fecha": datetime.utcnow().isoformat(),
        "resultado_real": None,
        "acierto": None
    }
    historial.append(registro)
    guardar_historial(historial)
    logger.info(f"💾 Predicción registrada: {registro}")


# === CONSULTAR RESULTADO REAL DESDE LA API === #
def obtener_resultado_real(equipo_local, equipo_visitante):
    try:
        url = f"{BASE_URL}/matches?status=FINISHED&limit=50"
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        data = res.json().get("matches", [])

        for partido in data:
            home = partido["homeTeam"]["name"].lower()
            away = partido["awayTeam"]["name"].lower()
            if equipo_local.lower() in home and equipo_visitante.lower() in away:
                score = partido["score"]["fullTime"]
                return {
                    "local": score.get("home", 0),
                    "visitante": score.get("away", 0)
                }

        return None
    except Exception as e:
        logger.error(f"❌ Error al obtener resultado real: {e}")
        return None


# === EVALUAR PREDICCIONES RECIENTES === #
def evaluar_predicciones_recientes():
    historial = cargar_historial()
    if not historial:
        logger.warning("⚠️ No hay predicciones registradas para evaluar.")
        return None

    aciertos = 0
    total = 0

    for item in historial:
        if item["resultado_real"] is None:
            nombres = item["partido"].split("vs")
            equipo_local = nombres[0].strip()
            equipo_visitante = nombres[1].strip()
            resultado_real = obtener_resultado_real(equipo_local, equipo_visitante)

            if resultado_real:
                total += 1
                if resultado_real["local"] > resultado_real["visitante"]:
                    ganador_real = f"{equipo_local} gana"
                elif resultado_real["local"] < resultado_real["visitante"]:
                    ganador_real = f"{equipo_visitante} gana"
                else:
                    ganador_real = "Empate"

                item["resultado_real"] = ganador_real
                item["acierto"] = ganador_real in item["prediccion"]

                if item["acierto"]:
                    aciertos += 1
                    logger.info(f"✅ ACIERTO: {item['partido']} ({item['prediccion']})")
                else:
                    logger.info(f"❌ FALLÓ: {item['partido']} → Real: {ganador_real}")

    if total > 0:
        precision = round((aciertos / total) * 100, 2)
    else:
        precision = 0.0

    guardar_historial(historial)
    logger.info(f"📊 Evaluación completada: {total} partidos, {aciertos} aciertos, {precision}% precisión")

    return {"evaluados": total, "aciertos": aciertos, "precision": precision}


# === AUTOEVALUACIÓN AUTOMÁTICA (cada 24 h) === #
def iniciar_autoevaluacion_automatica():
    """
    Lanza un hilo que ejecuta la evaluación automáticamente cada 24 horas.
    """
    def ciclo_evaluacion():
        while True:
            logger.info("🧠 [AUTO] Iniciando ciclo automático de evaluación de precisión...")
            resultado = evaluar_predicciones_recientes()
            if resultado:
                logger.info(f"📈 [AUTO] Precisión actual: {resultado['precision']}%")
            else:
                logger.info("⚠️ [AUTO] Sin datos para evaluar.")
            logger.info("⏰ Próxima evaluación automática en 24h.")
            time.sleep(24 * 60 * 60)  # Espera 24 horas

    Thread(target=ciclo_evaluacion, daemon=True).start()
    logger.info("🧩 Autoevaluación automática iniciada correctamente.")
