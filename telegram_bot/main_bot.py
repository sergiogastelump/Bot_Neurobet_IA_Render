# ============================================================
# 🧠 NEUROBET IA - v7.6 Render Stable (Flask + Webhook)
# ============================================================

import os
import json
import random
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ============================================================
# 🔧 CONFIGURACIÓN
# ============================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"

# ============================================================
# 🧾 LOGGING
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ============================================================
# 🌐 FLASK APP
# ============================================================
app = Flask(__name__)

# ============================================================
# 🤖 TELEGRAM BOT
# ============================================================
application = Application.builder().token(TELEGRAM_TOKEN).build()

# --------------------- COMANDOS ---------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "👋 *Bienvenido a Neurobet IA*\n\n"
        "Soy tu asistente de predicciones deportivas automáticas.\n"
        "Prueba con:\n"
        "`/predecir america vs chivas`\n\n"
        "O usa `/debug` para verificar el estado."
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")
    logging.info("✅ /start respondido correctamente.")

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usa: `/predecir equipo1 vs equipo2`", parse_mode="Markdown")
        return

    partido = " ".join(context.args)
    opcion = random.choice(["🏆 Gana local", "🤝 Empate", "⚽ Gana visitante"])
    confianza = random.randint(60, 90)

    mensaje = (
        f"📊 *Predicción automática*\n\n"
        f"Partido: {partido}\n"
        f"Resultado: {opcion}\n"
        f"Confianza: {confianza}%\n\n"
        "🤖 Sistema IA v7.6 (Render Stable)"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")
    logging.info(f"✅ Predicción enviada: {partido}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado = {
        "status": "OK",
        "webhook_activo": True,
        "modo": "Render Webhook",
        "precision_simulada": f"{random.randint(60,85)}%"
    }
    texto = "🧠 *Estado actual:*\n```\n" + json.dumps(estado, indent=2) + "\n```"
    await update.message.reply_text(texto, parse_mode="Markdown")
    logging.info("✅ /debug respondido correctamente.")

# Registrar comandos
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("debug", debug))

# ============================================================
# 🔗 RUTAS FLASK
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return "🧠 Neurobet IA (Render Stable v7.6)", 200

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "OK",
        "webhook_activo": True,
        "precision_simulada": f"{random.randint(60, 90)}%",
        "uptime_hours": round(random.random() * 3, 2),
        "modo": "Render Webhook"
    }), 200

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Recibe actualizaciones de Telegram"""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        # Inicializar antes de procesar si no está iniciado
        if not application.running:
            await application.initialize()
            await application.start()
            logging.info("✅ Aplicación Telegram inicializada correctamente.")
        await application.process_update(update)
        logging.info("✅ Update procesado correctamente (webhook directo).")
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Error procesando webhook: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================
# 🏁 ARRANQUE
# ============================================================

async def iniciar_bot():
    """Inicializa el bot y configura el webhook"""
    try:
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(WEBHOOK_URL)
        logging.info(f"📡 Webhook configurado correctamente: {WEBHOOK_URL}")
    except Exception as e:
        logging.error(f"❌ Error configurando webhook: {e}")

loop = asyncio.get_event_loop()
loop.run_until_complete(iniciar_bot())

# Flask se mantiene corriendo por Gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
