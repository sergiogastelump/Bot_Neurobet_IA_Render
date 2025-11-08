# telegram_bot/main_bot.py

import os
import json
import logging
import random
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ============ CONFIG ============

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"  # <-- luego lo cambias si el dominio cambia

# ============ LOGS ==============
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ============ FLASK APP =========
app = Flask(__name__)

# ============ TELEGRAM APP ======
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ============ COMANDOS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *Bienvenido a Neurobet IA*\n"
        "Usa `/predecir equipo1 vs equipo2` para probar.\n"
        "Comando de prueba: `/debug`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    logging.info("✅ /start respondido")

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usa: `/predecir america vs chivas`", parse_mode="Markdown")
        return

    partido = " ".join(context.args)
    opcion = random.choice(["🏆 Gana local", "🤝 Empate", "⚽ Gana visita"])
    confianza = random.randint(60, 85)

    txt = (
        f"📊 *Predicción automática*\n"
        f"Partido: {partido}\n"
        f"Resultado: {opcion}\n"
        f"Confianza: {confianza}%"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")
    logging.info(f"✅ Predicción enviada: {partido}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado = {
        "status": "OK",
        "webhook": True,
        "simulado": True
    }
    await update.message.reply_text("🧠 Estado:\n" + json.dumps(estado, indent=2))
    logging.info("✅ /debug respondido")

# registrar comandos
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("debug", debug))

# ============ RUTAS FLASK =======

@app.route("/", methods=["GET"])
def home():
    return "🧠 Neurobet IA en Render", 200

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "OK",
        "webhook_activo": True
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Telegram nos manda los updates aquí"""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        # encolamos el update para que lo procese la app de telegram
        application.update_queue.put_nowait(update)
        logging.info("✅ Update recibido y encolado")
    except Exception as e:
        logging.error(f"❌ Error en webhook: {e}")
    return "OK", 200

# ============ MAIN LOCAL =========
if __name__ == "__main__":
    # esto solo corre si lo lanzas local con: python -m telegram_bot.main_bot
    logging.info("🚀 Iniciando local...")
    # iniciamos webhook en telegram
    if TELEGRAM_TOKEN:
        try:
            application.bot.set_webhook(WEBHOOK_URL)
            logging.info(f"📡 Webhook configurado en {WEBHOOK_URL}")
        except Exception as e:
            logging.error(f"❌ No se pudo poner el webhook: {e}")

    # iniciamos flask
    app.run(host="0.0.0.0", port=PORT)
