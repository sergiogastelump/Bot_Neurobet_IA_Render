# telegram_bot/main_bot.py
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import asyncio

# === CARGAR VARIABLES DE ENTORNO === #
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"

# === CONFIGURAR FLASK === #
app = Flask(__name__)

# === INICIALIZAR BOT DE TELEGRAM === #
application = Application.builder().token(TELEGRAM_TOKEN).build()
asyncio.get_event_loop().run_until_complete(application.initialize())

# === COMANDOS DEL BOT === #
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
        await update.message.reply_text("⚠️ Formato correcto: /predecir América vs Chivas")
        return

    local, visitante = context.args[0], context.args[2]
    await update.message.reply_text(
        f"🔮 *Predicción IA:*\n"
        f"{local} 62% - Empate 23% - {visitante} 15%",
        parse_mode="Markdown"
    )

# === REGISTRAR COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))

# === RUTAS FLASK === #
@app.route('/')
def home():
    """Ruta principal"""
    return "🤖 Neurobet IA Webhook activo", 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Recibe actualizaciones de Telegram y las procesa (modo async)."""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
    except Exception as e:
        print(f"⚠️ Error procesando webhook: {e}")
        return "ERROR", 500
    return "OK", 200

# === MAIN === #
if __name__ == "__main__":
    print(f"🚀 Iniciando Neurobet IA en modo Webhook (Render) - Puerto {PORT}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )
