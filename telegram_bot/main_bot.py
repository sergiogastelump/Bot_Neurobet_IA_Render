import os
import time
import logging
import threading
import asyncio
from flask import Flask, request, jsonify
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ====== SERVICIOS INTERNOS ====== #
from services.ia_service import predecir_partido
from services.autoaprendizaje_service import inicializar_modelo
from services.scheduler_service import iniciar_hilo_autoaprendizaje
from services.evaluacion_service import iniciar_autoevaluacion_automatica

# ====== LOGS ====== #
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== CONFIGURACIÓN ====== #
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8238035123:AAHaX2iFZjNWFMLwm8QUmjYc09qA_y9IDa8")
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ====== VARIABLES GLOBALES ====== #
BOT_EVENT_LOOP = None
START_TIME = datetime.utcnow()
PRECISION_SIMULADA = 72

# =========================================================
# COMANDOS TELEGRAM
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Usuario {user.first_name} inició el bot.")
    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name}!\n"
        f"Soy *Neurobet IA*, tu asistente de predicciones deportivas.\n\n"
        f"Comandos disponibles:\n"
        f"/predecir América vs Chivas\n"
        f"/debug - Estado actual del sistema",
        parse_mode="Markdown"
    )

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if "vs" not in texto.lower():
        await update.message.reply_text("❌ Usa el formato: /predecir Equipo1 vs Equipo2")
        return
    e1, e2 = texto.split("vs", 1)
    pred = predecir_partido(e1.strip(), e2.strip())
    msg = (
        f"🔮 *Predicción IA:*\n"
        f"{pred['resultado']}\n"
        f"🎯 Precisión: {pred['probabilidad']}%\n"
        f"🤖 Modo: {pred['modo']}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = round((datetime.utcnow() - START_TIME).total_seconds() / 3600, 2)
    msg = (
        f"🧩 *Diagnóstico del sistema:*\n"
        f"📡 Webhook: {WEBHOOK_URL}\n"
        f"⚙️ Event Loop: {'Activo ✅' if BOT_EVENT_LOOP and BOT_EVENT_LOOP.is_running() else 'Inactivo ❌'}\n"
        f"⏱️ Uptime: {uptime} h\n"
        f"📈 Precisión simulada: {PRECISION_SIMULADA}%"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# =========================================================
# REGISTRAR COMANDOS
# =========================================================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("debug", debug))

# =========================================================
# ENDPOINTS FLASK
# =========================================================
@app.route("/", methods=["GET"])
def home():
    return "🤖 Neurobet IA activo y conectado.", 200

@app.route("/status", methods=["GET"])
def status():
    uptime = round((datetime.utcnow() - START_TIME).total_seconds() / 3600, 2)
    status_info = {
        "status": "OK",
        "uptime_hours": uptime,
        "precision_simulada": f"{PRECISION_SIMULADA}%",
        "webhook_activo": True,
        "loop_activo": BOT_EVENT_LOOP.is_running() if BOT_EVENT_LOOP else False,
        "modo": "Render Free KeepAlive"
    }
    return jsonify(status_info), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        logger.info(f"✅ Update recibido correctamente: {update}")
        if BOT_EVENT_LOOP and BOT_EVENT_LOOP.is_running():
            asyncio.run_coroutine_threadsafe(application.process_update(update), BOT_EVENT_LOOP)
        else:
            logger.warning("⚠️ Event loop inactivo, reiniciando hilo del bot...")
            threading.Thread(target=_start_bot_background, daemon=True).start()
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return "ERROR", 500

# =========================================================
# HILO PRINCIPAL
# =========================================================
def _start_bot_background():
    """Inicia el bot en segundo plano y mantiene el loop activo."""
    def runner():
        global BOT_EVENT_LOOP
        BOT_EVENT_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(BOT_EVENT_LOOP)

        async def main():
            try:
                inicializar_modelo()
                await application.initialize()
                await application.start()
                await application.bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
                logger.info(f"📡 Webhook establecido correctamente: {WEBHOOK_URL}")
                await application.bot.send_message(
                    chat_id=5124041224,
                    text="✅ Neurobet IA está en línea y lista para recibir comandos."
                )
                while True:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Error en hilo del bot: {e}")

        BOT_EVENT_LOOP.run_until_complete(main())

    threading.Thread(target=runner, daemon=True).start()

# =========================================================
# INICIO AUTOMÁTICO
# =========================================================
if __name__ == "__main__":
    logger.info("🚀 Iniciando Neurobet IA (modo Render KeepAlive)...")
    inicializar_modelo()
    iniciar_hilo_autoaprendizaje()
    iniciar_autoevaluacion_automatica()
    time.sleep(1)
    _start_bot_background()
    app.run(host="0.0.0.0", port=PORT)
