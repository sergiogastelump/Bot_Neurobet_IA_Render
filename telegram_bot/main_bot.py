# telegram_bot/main_bot.py
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === CONFIGURACIÓN === #
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8238035123:AAHaX2iFZjNWFMLwm8QUmjYc09qA_y9IDa8")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"

# === INICIALIZACIÓN DE FLASK === #
flask_app = Flask(__name__)

# === APLICACIÓN DE TELEGRAM === #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === COMANDOS === #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido a *Neurobet IA Bot*.\nUsa /predecir para analizar un partido o /ayuda para ver comandos.",
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
    await update.message.reply_text(f"🔮 Predicción IA:\n{local} 62% - Empate 23% - {visitante} 15%")

# === REGISTRAR COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))

# === ENDPOINTS === #
@flask_app.route('/')
def index():
    return "🤖 Neurobet IA Webhook activo", 200

@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    """Recibe actualizaciones desde Telegram."""
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
    except Exception as e:
        print(f"Error procesando webhook: {e}")
    return "OK", 200

# === INICIO DEL SERVIDOR === #
if __name__ == '__main__':
    print("🚀 Iniciando Neurobet IA en modo Webhook (Render) - Puerto", PORT)
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )
    flask_app.run(host="0.0.0.0", port=PORT)
