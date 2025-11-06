import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import logging

# === CONFIGURACIÓN GENERAL === #
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"

if not TELEGRAM_TOKEN:
    raise ValueError("❌ No se encontró TELEGRAM_TOKEN en las variables de entorno")

# === LOGGING (GUARDAR EVENTOS EN LOG) === #
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("neurobet.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# === FLASK APP === #
app = Flask(__name__)

# === TELEGRAM BOT === #
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

# === RUTAS FLASK === #
@app.route("/")
def home():
    return "🤖 Neurobet IA Webhook activo", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe actualizaciones de Telegram sin causar error 500."""
    try:
        data = request.get_json(silent=True)
        if not data:
            logger.warning("⚠️ Webhook recibió un cuerpo vacío.")
            return "OK", 200

        update = Update.de_json(data, application.bot)
        if update:
            application.update_queue.put_nowait(update)
            logger.info(f"✅ Update recibido: {update}")
        else:
            logger.warning("⚠️ Update inválido.")
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        return "OK", 200  # devolvemos 200 para que Telegram no marque error

    return "OK", 200


# === MAIN === #
if __name__ == "__main__":
    logger.info(f"🚀 Iniciando Neurobet IA Webhook en puerto {PORT}")
    app.run(host="0.0.0.0", port=PORT)
