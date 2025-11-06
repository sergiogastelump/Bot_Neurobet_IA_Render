# ===========================================
#  NEUROBET IA - BOT TELEGRAM (Render versión)
# ===========================================

import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# === CONFIGURACIÓN GENERAL === #
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"

# === LOGGING === #
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === FLASK APP === #
app = Flask(__name__)

# === TELEGRAM APP === #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === COMANDOS DEL BOT === #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bienvenido a *Neurobet IA Bot*.\n"
        "Usa /predecir para analizar un partido o /ayuda para ver comandos.",
        parse_mode="Markdown"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 *Comandos disponibles:*\n"
        "/start - Inicio\n"
        "/predecir [Equipo1 vs Equipo2]\n"
        "/ayuda - Ver comandos",
        parse_mode="Markdown"
    )

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Formato correcto: /predecir América vs Chivas")
        return

    local, visitante = context.args[0], context.args[2]
    await update.message.reply_text(
        f"🔮 Predicción IA:\n{local} 62% - Empate 23% - {visitante} 15%"
    )

# === REGISTRO DE COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))

# === RUTAS FLASK === #
@app.route("/")
def home():
    return "✅ Servidor Flask activo y webhook operativo.", 200

# === 🔧 BLOQUE WEBHOOK CORREGIDO === #
@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe actualizaciones desde Telegram y las procesa correctamente."""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)

        # Ejecutar la actualización de forma asíncrona sin bloquear Flask
        application.create_task(application.process_update(update))

        app.logger.info(f"✅ Update recibido correctamente: {update}")
    except Exception as e:
        app.logger.error(f"❌ Error procesando webhook: {e}")
    return "OK", 200

# === INICIO DEL SERVIDOR === #
if __name__ == "__main__":
    logger.info("🚀 Iniciando Neurobet IA (Render Deployment)")
    logger.info(f"🌐 Iniciando servidor Flask en puerto {PORT}")
    logger.info("🤖 Iniciando bot de Telegram...")

    # Ejecutar Flask y Telegram webhook en el mismo proceso
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )

    logger.info("✅ Bot en ejecución continua (Webhook activo).")
    app.run(host="0.0.0.0", port=PORT)
