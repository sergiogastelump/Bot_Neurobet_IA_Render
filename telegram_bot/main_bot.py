# telegram_bot/main_bot.py

import os
import json
import logging
import threading
from datetime import datetime, date
from pathlib import Path

from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ====== IMPORTS DE SERVICIOS EXISTENTES ====== #
from services.ia_service import predecir_partido
from services.autoaprendizaje_service import (
    inicializar_modelo,
)
from services.evaluacion_service import (
    iniciar_autoevaluacion_automatica,
)
from services.scheduler_service import iniciar_hilo_autoaprendizaje

# ====== LOGGING ====== #
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ====== CONFIG / RUTAS ====== #
TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    "8238035123:AAHaX2iFZjNWFMLwm8QUmjYc09qA_y9IDa8"  # ← tu token
)
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL",
    "https://bot-neurobet-ia-render.onrender.com/webhook"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PRED_HIST_PATH = DATA_DIR / "historial_predicciones.json"
PICKS_PATH = DATA_DIR / "picks_diarios.json"

# ====== FLASK APP ====== #
app = Flask(__name__)

# ====== TELEGRAM APP (sin loops raros) ====== #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# =========================================================
#  UTILIDADES TIPSTER
# =========================================================

def _cargar_picks():
    if PICKS_PATH.exists():
        try:
            with open(PICKS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _guardar_picks(data: dict):
    PICKS_PATH.parent.mkdir(exist_ok=True, parents=True)
    with open(PICKS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _generar_picks_del_dia():
    """Genera una lista dummy de picks del día (free + premium)."""
    hoy = date.today().isoformat()
    return {
        "fecha": hoy,
        "picks": [
            {
                "tipo": "free",
                "partido": "América vs Chivas",
                "mercado": "Handicap -1 América",
                "odd": 1.65,
                "confianza": 82,
                "analisis": (
                    "América llega con racha goleadora y Chivas flojo de visita. "
                    "En los últimos 5 enfrentamientos América ha dominado."
                ),
            },
            {
                "tipo": "premium",
                "partido": "Dodgers vs Yankees",
                "mercado": "Gana Yankees",
                "odd": 1.70,
                "confianza": 78,
                "analisis": (
                    "Yankees con mejor bullpen para hoy y Dodgers rotación secundaria. "
                    "Valor aceptable por arriba de 1.65."
                ),
            },
            {
                "tipo": "premium",
                "partido": "Barcelona vs Sevilla",
                "mercado": "Más de 2.5 goles",
                "odd": 1.68,
                "confianza": 75,
                "analisis": (
                    "Ambos con promedio alto de tiros y Barcelona concede ocasiones. "
                    "Buen pick para combinadas."
                ),
            },
        ],
    }


def _asegurar_picks_de_hoy():
    """Se asegura de que exista entrada para el día de hoy en el JSON."""
    hoy = date.today().isoformat()
    data = _cargar_picks()
    if data.get("fecha") != hoy:
        data = _generar_picks_del_dia()
        _guardar_picks(data)
        logger.info("🧠 Picks del día generados automáticamente.")
    return data


def _hilo_picks_daemon():
    """Hilo muy ligero que cada hora se asegura de que existan picks del día."""
    while True:
        try:
            _asegurar_picks_de_hoy()
        except Exception as e:
            logger.error(f"❌ Error auto-picks: {e}")
        # 3600 segundos = 1 hora
        import time
        time.sleep(3600)

# =========================================================
#  HANDLERS TELEGRAM
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mensaje = (
        f"👋 ¡Hola {user.first_name}!\n"
        f"Soy *Neurobet IA v8.0*.\n\n"
        f"📘 Comandos:\n"
        f"/predecir Equipo1 vs Equipo2\n"
        f"/picks - Ver picks del día\n"
        f"/picks_free - Picks gratis\n"
        f"/picks_premium - Picks premium\n"
        f"/dashboard - Ver panel web\n"
        f"/debug - Estado del bot\n"
    )
    # Respondemos directo (esto sí está dentro del loop de telegram)
    await update.message.reply_text(mensaje, parse_mode="Markdown")
    logger.info("✅ /start respondido correctamente.")


async def debug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra un pequeño estado del bot."""
    hoy = date.today().isoformat()
    picks = _cargar_picks()
    tiene_picks = picks.get("fecha") == hoy
    texto = (
        "🛠 *Debug Neurobet IA*\n"
        f"📡 Webhook OK\n"
        f"📅 Picks hoy: {'sí' if tiene_picks else 'no'}\n"
        f"🕒 Fecha servidor: {datetime.utcnow().isoformat()}Z\n"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if len(context.args) < 3 or "vs" not in texto.lower():
        await update.message.reply_text("❌ Usa el formato: /predecir Equipo1 vs Equipo2")
        return

    equipo_local, equipo_visitante = texto.split("vs")
    equipo_local = equipo_local.strip()
    equipo_visitante = equipo_visitante.strip()

    pred = predecir_partido(equipo_local, equipo_visitante)

    msg = (
        f"🔮 *Predicción IA:*\n"
        f"{pred['resultado']}\n"
        f"🎯 Precisión estimada: {pred['probabilidad']}%\n"
        f"🤖 Modo: {pred['modo']}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    # Guardamos al historial de predicciones (simple)
    _guardar_prediccion_historial(
        partido=f"{equipo_local} vs {equipo_visitante}",
        pred=pred["resultado"],
    )


def _guardar_prediccion_historial(partido: str, pred: str):
    PRED_HIST_PATH.parent.mkdir(exist_ok=True, parents=True)
    if PRED_HIST_PATH.exists():
        with open(PRED_HIST_PATH, "r", encoding="utf-8") as f:
            historial = json.load(f)
    else:
        historial = []
    historial.append(
        {
            "partido": partido,
            "prediccion": pred,
            "fecha": datetime.utcnow().isoformat() + "Z",
            "acierto": None,
            "resultado_real": None,
        }
    )
    with open(PRED_HIST_PATH, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


async def picks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _asegurar_picks_de_hoy()
    texto = "🎯 *Picks del día*\n\n"
    for p in data["picks"]:
        texto += (
            f"• [{p['tipo'].upper()}] {p['partido']} → {p['mercado']} "
            f"(odd {p['odd']})\n"
            f"  Confianza: {p['confianza']}%\n"
            f"  {p['analisis']}\n\n"
        )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def picks_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _asegurar_picks_de_hoy()
    free = [p for p in data["picks"] if p["tipo"] == "free"]
    if not free:
        await update.message.reply_text("📭 Hoy no hay picks free.")
        return
    texto = "🆓 *Picks FREE de hoy*\n\n"
    for p in free:
        texto += (
            f"• {p['partido']} → {p['mercado']} (odd {p['odd']})\n"
            f"{p['analisis']}\n\n"
        )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def picks_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _asegurar_picks_de_hoy()
    premium = [p for p in data["picks"] if p["tipo"] == "premium"]
    if not premium:
        await update.message.reply_text("📭 Hoy no hay picks premium.")
        return
    texto = "💎 *Picks PREMIUM de hoy*\n\n"
    for p in premium:
        texto += (
            f"• {p['partido']} → {p['mercado']} (odd {p['odd']})\n"
            f"{p['analisis']}\n\n"
        )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Solo confirmamos que recibimos voz. (luego podemos transcribir)."""
    user = update.effective_user
    logger.info(f"🗣 Mensaje de voz recibido de {user.id}")
    await update.message.reply_text(
        "🎙 Recibí tu audio. En la siguiente versión lo transcribimos y lo pasamos por la IA 😉"
    )


# ====== REGISTRO DE HANDLERS ====== #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("debug", debug_cmd))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("picks", picks))
application.add_handler(CommandHandler("picks_free", picks_free))
application.add_handler(CommandHandler("picks_premium", picks_premium))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))

# =========================================================
#  FLASK ROUTES
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "🤖 Neurobet IA v8.0 webhook OK", 200


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if PRED_HIST_PATH.exists():
        with open(PRED_HIST_PATH, "r", encoding="utf-8") as f:
            historial = json.load(f)
    else:
        historial = []

    total = len(historial)
    evaluados = sum(1 for h in historial if h.get("acierto") is not None)
    aciertos = sum(1 for h in historial if h.get("acierto") is True)
    precision = round(aciertos / evaluados * 100, 2) if evaluados else 0

    html = "<h1>📊 Neurobet IA - Dashboard</h1>"
    html += f"<p>Total predicciones: {total}</p>"
    html += f"<p>Evaluadas: {evaluados} | Aciertos: {aciertos} | Precisión: {precision}%</p>"
    html += "<h2>Últimas 10</h2><ul>"
    for item in historial[-10:][::-1]:
        html += f"<li>{item['fecha']} → {item['partido']} → {item['prediccion']}</li>"
    html += "</ul>"
    return html, 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe el update de Telegram y lo procesa directamente."""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)
        logger.info("✅ Update recibido y procesando...")
        # procesamos directo (esto sí está dentro del loop que maneja PTB internamente)
        application.create_task(application.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        return "ERROR", 500


# =========================================================
#  ARRANQUE
# =========================================================

def iniciar_servicios_background():
    """Arranca los servicios que ya tenías: autoaprendizaje, autoevaluación, picks."""
    inicializar_modelo()
    iniciar_hilo_autoaprendizaje()
    iniciar_autoevaluacion_automatica()

    # hilo de picks
    t = threading.Thread(target=_hilo_picks_daemon, daemon=True)
    t.start()
    logger.info("🟣 Hilo de picks diarios iniciado.")


# Render entra por aquí con gunicorn: telegram_bot.main_bot:app
# Pero si lo corres local, entra en este if
if __name__ == "__main__":
    logger.info("🚀 Iniciando Neurobet IA (local/debug)")
    # set webhook por si lo corres local con túnel
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )
    iniciar_servicios_background()
    app.run(host="0.0.0.0", port=PORT)
