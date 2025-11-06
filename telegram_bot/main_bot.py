import os
import asyncio
import logging
from threading import Thread
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# === CONFIGURACIÓN GENERAL === #
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"

if not TELEGRAM_TOKEN:
    raise ValueError("❌ No se encontró TELEGRAM_TOKEN en las variables de entorno")

# === LOGGING === #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("neurobet.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# === INICIALIZAR FLASK === #
app = Flask(__name__)

# === INICIALIZAR BOT === #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === COMANDOS DEL BOT === #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("👋 Ejecutando comando /start")
    await update.message.reply_text(
        "👋 Bienvenido a *Neurobet IA Bot*.\n"
        "Usa /predecir para analizar un partido o /ayuda para ver los comandos disponibles.",
        parse_mode="Markdown"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📘 Ejecutando comando /ayuda")
    await update.message.reply_text(
        "📘 *Comandos disponibles:*\n"
        "/start - Inicio\n"
        "/predecir [Equipo1 vs Equipo2]\n"
        "/ayuda - Ver comandos",
        parse_mode="Markdown"
    )

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔮 Ejecutando comando /predecir")
    if len(context.args) < 3:
        await update.message.reply_text("Formato correcto: /predecir América vs Chivas")
        return
    local, visitante = context.args[0], context.args[2]
    await update.message.reply_text(
        f"🔮 Predicción IA:\n{local} 62% - Empate 23% - {visitante} 15%"
    )

# === REGISTRAR COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))

# === FLASK ROUTES === #
@app.route("/")
def home():
    return "🤖 Neurobet IA Webhook activo", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(silent=True)
        if not data:
            logger.warning("⚠️ Webhook recibió cuerpo vacío.")
            return "OK", 200

        update = Update.de_json(data, application.bot)
        if update:
            application.update_queue.put_nowait(update)
            logger.info(f"✅ Update recibido correctamente: {update}")
        else:
            logger.warning("⚠️ Update inválido recibido.")
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        return "OK", 200
    return "OK", 200

# === ARRANQUE BOT Y FLASK EN PARALELO === #
def run_flask():
    logger.info(f"🌐 Iniciando servidor Flask en puerto {PORT}")
    app.run(host="0.0.0.0", port=PORT)

async def run_bot():
    logger.info("🤖 Iniciando bot de Telegram...")
    await application.initialize()
    await application.start()
    logger.info("✅ Bot en ejecución continua (Webhook activo).")
    await asyncio.Event().wait()  # Mantiene el loop vivo

if __name__ == "__main__":
    logger.info("🚀 Iniciando Neurobet IA (Render Deployment)")
    Thread(target=run_flask, daemon=True).start()  # Flask en hilo paralelo
    asyncio.run(run_bot())