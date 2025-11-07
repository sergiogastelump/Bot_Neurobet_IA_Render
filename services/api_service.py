import os
import logging
import requests

# === CONFIGURACIÓN DE LOGS === #
logger = logging.getLogger(__name__)

# === CLAVE DE API Y URL BASE === #
API_KEY = os.getenv("API_KEY", "329f4fac732d45049158a52092727496")
BASE_URL = "https://api.football-data.org/v4"  # Puedes cambiar a otra API si lo prefieres
HEADERS = {"X-Auth-Token": API_KEY}


# === FUNCIÓN PRINCIPAL === #
def obtener_estadisticas_equipo(nombre_equipo: str):
    """
    Busca estadísticas recientes del equipo mediante la API.
    Retorna promedios de goles, victorias y rendimiento general.
    """
    try:
        logger.info(f"📡 Consultando datos del equipo: {nombre_equipo}")

        # === 1️⃣ Buscar información general del equipo === #
        url_teams = f"{BASE_URL}/teams"
        response = requests.get(url_teams, headers=HEADERS)
        response.raise_for_status()

        data = response.json()
        equipos = data.get("teams", [])

        # Buscar coincidencia por nombre
        equipo_id = None
        for equipo in equipos:
            if nombre_equipo.lower() in equipo["name"].lower():
                equipo_id = equipo["id"]
                break

        if not equipo_id:
            logger.warning(f"⚠️ No se encontró el equipo '{nombre_equipo}' en la API.")
            return None

        # === 2️⃣ Obtener últimos partidos del equipo === #
        url_matches = f"{BASE_URL}/teams/{equipo_id}/matches?status=FINISHED&limit=10"
        response = requests.get(url_matches, headers=HEADERS)
        response.raise_for_status()

        matches = response.json().get("matches", [])
        if not matches:
            logger.warning(f"⚠️ No hay partidos recientes disponibles para {nombre_equipo}.")
            return None

        # === 3️⃣ Procesar estadísticas === #
        goles_favor = 0
        goles_contra = 0
        victorias = 0
        empates = 0
        derrotas = 0

        for match in matches:
            home = match["homeTeam"]["id"]
            away = match["awayTeam"]["id"]
            score = match["score"]["fullTime"]

            # Identificar si jugó como local o visitante
            if home == equipo_id:
                goles_favor += score.get("home", 0)
                goles_contra += score.get("away", 0)
                if match["score"]["winner"] == "HOME_TEAM":
                    victorias += 1
                elif match["score"]["winner"] == "DRAW":
                    empates += 1
                else:
                    derrotas += 1
            else:
                goles_favor += score.get("away", 0)
                goles_contra += score.get("home", 0)
                if match["score"]["winner"] == "AWAY_TEAM":
                    victorias += 1
                elif match["score"]["winner"] == "DRAW":
                    empates += 1
                else:
                    derrotas += 1

        total_partidos = len(matches)
        promedio_goles = round(goles_favor / total_partidos, 2)
        promedio_contra = round(goles_contra / total_partidos, 2)
        win_rate = round((victorias / total_partidos) * 100, 2)

        resultado = {
            "equipo": nombre_equipo,
            "partidos": total_partidos,
            "goles_prom": promedio_goles,
            "goles_contra": promedio_contra,
            "victorias": victorias,
            "empates": empates,
            "derrotas": derrotas,
            "win_rate": win_rate,
        }

        logger.info(f"✅ Datos obtenidos para {nombre_equipo}: {resultado}")
        return resultado

    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Error de conexión con la API: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error procesando estadísticas de {nombre_equipo}: {e}")
        return None
