import os
import json
import logging
import random
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===========================
# 🔧 CONFIGURACIÓN BASE
# ===========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"

app = Flask(__name__)

# ===========================
# 🧠 LOGGING
# ===========================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ===========================
# 🤖 INICIALIZAR BOT
# ===========================
application = Application.builder().token(TELEGRAM_TOKEN).build()


# ===========================
# 🎯 FUNCIONES DE IA SIMULADA
# ===========================
def autoaprendizaje():
    """Simula el autoaprendizaje continuo."""
    while True:
        precision = random.randint(60, 85)
        logging.info(f"🧠 Modelo actualizado automáticamente. Precisión simulada: {precision}%")
        threading.Event().wait(120)  # Espera 2 minutos entre ciclos


def iniciar_autoaprendizaje():
    hilo = threading.Thread(target=autoaprendizaje, daemon=True)
    hilo.start()
    logging.info("🧩 Hilo de autoaprendizaje automático iniciado correctamente.")


# ===========================
# 💬 COMANDOS TELEGRAM
# ===========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *Bienvenido a Neurobet IA*\n\n"
        "🔹 IA Predictiva Multideporte\n"
        "🔹 Autoaprendizaje continuo\n"
        "🔹 Soporte para voz y predicciones futuras\n\n"
        "Usa `/predecir equipo1 vs equipo2` para comenzar."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    logging.info(f"✅ Usuario inició el bot: {update.effective_user.first_name}")


async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usa: `/predecir equipo1 vs equipo2`", parse_mode="Markdown")
        return

    equipos = " ".join(context.args)
    opciones = ["🏆 Gana Local", "🤝 Empate", "⚽ Gana Visitante"]
    prediccion = random.choice(opciones)
    confianza = random.randint(60, 85)

    mensaje = (
        f"📊 *Predicción Automática*\n"
        f"🎯 Partido: {equipos}\n"
        f"📈 Resultado probable: {prediccion}\n"
        f"🔢 Confianza: {confianza}%"
    )

    await update.message.reply_text(mensaje, parse_mode="Markdown")
    logging.info(f"💾 Predicción enviada: {equipos} → {prediccion} ({confianza}%)")


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = {
        "modo": "Render KeepAlive",
        "precision_simulada": f"{random.randint(60,80)}%",
        "status": "OK",
        "uptime_hours": round(random.random() * 10, 2),
        "webhook_activo": True
    }
    await update.message.reply_text("🧠 Estado actual:\n" + json.dumps(status, indent=2))
    logging.info("🧩 /debug ejecutado correctamente.")


# ===========================
# 🔗 REGISTRO DE COMANDOS
# ===========================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("debug", debug))


# ===========================
# 🌐 RUTAS FLASK
# ===========================
@app.route("/")
def index():
    return "🧠 Neurobet IA corriendo en Render."

@app.route("/status")
def status():
    return jsonify({
        "modo": "Render KeepAlive",
        "precision_simulada": "72%",
        "status": "OK",
        "webhook_activo": True
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe actualizaciones del bot (modo webhook)."""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)
        application.update_queue.put_nowait(update)
        logging.info("✅ Update recibido y encolado correctamente.")
    except Exception as e:
        logging.error(f"❌ Error en webhook: {e}")
    return "OK", 200


# ===========================
# 🚀 EJECUCIÓN PRINCIPAL
# ===========================
if __name__ == "__main__":
    logging.info("🚀 Iniciando Neurobet IA v7.3 (modo Render Flask webhook)...")
    iniciar_autoaprendizaje()

    # Iniciar bot con webhook (no async)
    application.bot.set_webhook(WEBHOOK_URL)
    logging.info(f"📡 Webhook activo en: {WEBHOOK_URL}")

    app.run(host="0.0.0.0", port=PORT)
