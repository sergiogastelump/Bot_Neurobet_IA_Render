# telegram_bot/main_bot.py
import os
from flask import Flask, request
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === CONFIGURACIÓN === #
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8238035123:AAHaX2iFZjNWFMLwm8QUmjYc09qA_y9IDa8")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"

# === FLASK APP === #
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "🤖 Neurobet IA Webhook activo", 200

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    """Recibe actualizaciones desde Telegram."""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK", 200


# === COMANDOS DEL BOT === #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bienvenido a Neurobet IA.\nUsa /predecir para analizar un partido o /ayuda para ver opciones.")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 Comandos disponibles:\n/start - Inicio\n/predecir [equipo1 vs equipo2]\n/ayuda - Ver comandos")

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Formato correcto: /predecir América vs Chivas")
        return
    local = context.args[0]
    visitante = context.args[2]
    await update.message.reply_text(
        f"🔮 Predicción IA:\n{local} 62% - Empate 23% - {visitante} 15%"
    )


# === APLICACIÓN TELEGRAM === #
application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))


# === EJECUCIÓN DEL BOT === #
def run_flask():
    """Ejecuta Flask en un hilo separado."""
    flask_app.run(host="0.0.0.0", port=PORT)

def run_telegram():
    """Ejecuta el bot con polling (respaldo del webhook)."""
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == '__main__':
    print("🚀 Iniciando Neurobet IA en modo híbrido (Webhook + Polling)")
    Thread(target=run_flask).start()
    Thread(target=run_telegram).start()
