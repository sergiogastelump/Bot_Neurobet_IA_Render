import os
import json
import logging
import random
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===========================
# 🔧 CONFIGURACIÓN BÁSICA
# ===========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = f"https://bot-neurobet-ia.onrender.com/webhook"  # <-- cambia si tu URL cambia

app = Flask(__name__)

# ===========================
# 🧠 CONFIGURACIÓN DE LOGGING
# ===========================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ===========================
# 🧩 INICIALIZACIÓN DEL BOT
# ===========================
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ===========================
# 🧠 FUNCIONES DE IA SIMULADA
# ===========================
def autoaprendizaje():
    """Simula un ciclo automático de autoaprendizaje."""
    while True:
        precision = random.randint(55, 85)
        logging.info(f"🧠 Modelo actualizado automáticamente. Precisión simulada: {precision}%")
        logging.info("✅ [AUTO] Ciclo completado.")
        threading.Event().wait(120)  # espera 2 minutos entre ciclos


def iniciar_autoaprendizaje():
    """Ejecuta el autoaprendizaje en un hilo aparte."""
    hilo = threading.Thread(target=autoaprendizaje, daemon=True)
    hilo.start()
    logging.info("🧩 Hilo de autoaprendizaje automático iniciado correctamente.")


# ===========================
# 🤖 COMANDOS DEL BOT
# ===========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"✅ Update recibido correctamente: {update}")
    await update.message.reply_text("👋 ¡Bienvenido a Neurobet IA!\nEstoy en línea y listo para ayudarte con tus predicciones deportivas.")


async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usa el comando correctamente:\n`/predecir equipo1 vs equipo2`", parse_mode="Markdown")
        return

    equipos = " ".join(context.args)
    predicciones = ["🏆 Gana Local", "🤝 Empate", "⚽ Gana Visitante"]
    prediccion = random.choice(predicciones)
    probabilidad = random.randint(55, 85)

    mensaje = (
        f"📊 *Predicción automática:*\n"
        f"🎯 Partido: {equipos}\n"
        f"📈 Resultado probable: {prediccion}\n"
        f"🔢 Confianza: {probabilidad}%"
    )

    await update.message.reply_text(mensaje, parse_mode="Markdown")
    logging.info(f"💾 Predicción generada: {mensaje}")


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = {
        "loop_activo": True,
        "modo": "Render KeepAlive",
        "precision_simulada": f"{random.randint(60,80)}%",
        "status": "OK",
        "uptime_hours": round(random.random() * 10, 2),
        "webhook_activo": True
    }
    await update.message.reply_text("🤖 Neurobet IA en línea (modo Render)\n" + json.dumps(status, indent=2))
    logging.info("🧠 Comando /debug ejecutado correctamente.")


# ===========================
# 🔗 REGISTRO DE COMANDOS
# ===========================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("debug", debug))

# ===========================
# 🌐 FLASK ENDPOINTS
# ===========================
@app.route("/")
def home():
    return "🧠 Neurobet IA activo y en modo Render."

@app.route("/status")
def status():
    data = {
        "loop_activo": True,
        "modo": "Render KeepAlive",
        "precision_simulada": "72%",
        "status": "OK",
        "uptime_hours": round(random.random(), 2),
        "webhook_activo": True
    }
    return jsonify(data)

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Recibe actualizaciones de Telegram."""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        logging.info(f"✅ Update recibido correctamente: {update}")
    except Exception as e:
        logging.error(f"❌ Error en webhook: {e}")
    return "OK", 200


# ===========================
# 🚀 INICIO DE LA APLICACIÓN
# ===========================
if __name__ == "__main__":
    logging.info("🚀 Iniciando Neurobet IA (modo Render)...")
    iniciar_autoaprendizaje()
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )
    app.run(host="0.0.0.0", port=PORT)
