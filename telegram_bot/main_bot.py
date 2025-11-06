import os
import asyncio
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

if not TELEGRAM_TOKEN:
    raise ValueError("❌ No se encontró TELEGRAM_TOKEN en las variables de entorno")

# === CONFIGURAR LOGGING === #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("neurobet.log"),  # Guarda registros
        logging.StreamHandler()                # Muestra logs en consola Render
    ]
)
logger = logging.getLogger(__name__)

# === INICIALIZAR FLASK === #
app = Flask(__name__)

# === INICIALIZAR BOT DE TELEGRAM === #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === COMANDOS === #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido a *Neurobet IA Bot*.\n"
        "Usa /predecir para analizar un partido o /ayuda para ver los comandos disponibles.",
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

# === REGISTRAR COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))

# === ENDPOINT PRINCIPAL === #
@app.route("/")
def home():
    return "🤖 Neurobet IA Webhook activo", 200

# === ENDPOINT WEBHOOK === #
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Endpoint que recibe las actualizaciones de Telegram.
    Se maneja cualquier error para evitar 500 Internal Server Error.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            logger.warning("⚠️ Webhook recibió un cuerpo vacío o inválido.")
            return "OK", 200

        update = Update.de_json(data, application.bot)
        if update:
            application.update_queue.put_nowait(update)
            logger.info(f"✅ Update recibido correctamente: {update}")
        else:
            logger.warning("⚠️ Update inválido recibido.")
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        # AUNQUE OCURRA ERROR, devolvemos 200 para que Telegram no marque fallo
        return "OK", 200

    return "OK", 200


# === BLOQUE FINAL: INICIALIZAR Y ARRANCAR EL BOT === #
if __name__ == "__main__":
    logger.info(f"🚀 Iniciando Neurobet IA Webhook en puerto {PORT}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.initialize())

    # Ejecutar el bot en segundo plano (procesa mensajes entrantes)
    loop.create_task(application.start())

    # Iniciar el servidor Flask
    app.run(host="0.0.0.0", port=PORT)
