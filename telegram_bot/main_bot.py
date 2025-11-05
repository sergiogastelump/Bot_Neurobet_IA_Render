# telegram_bot/main_bot.py
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Token desde variables de entorno (.env)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8238035123:AAHaX2iFZjNWFMLwm8QUmjYc09qA_y9IDa8")

# Flask App para Render
app = Flask(__name__)
application = None  # referencia global

# --- Comandos del bot --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Bienvenido a Neurobet IA! Usa /predecir para analizar un partido.")

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Formato correcto: /predecir América vs Chivas")
        return
    equipo_local = context.args[0]
    equipo_visitante = context.args[2]
    await update.message.reply_text(f"📊 Analizando: {equipo_local} vs {equipo_visitante}...\n🔮 Predicción: {equipo_local} 65% - Empate 20% - {equipo_visitante} 15%")

# --- Flask Routes --- #
@app.route('/')
def index():
    return "🤖 Neurobet IA Webhook activo", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Procesa las actualizaciones de Telegram."""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put(update)
        return "OK", 200
    return "Método no permitido", 405

# --- Inicializar el bot --- #
def main():
    global application
    webhook_url = "https://bot-neurobet-ia.onrender.com/webhook"

    print("🚀 Iniciando Neurobet IA en modo Webhook (Render) - Puerto 10000")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("predecir", predecir))

    # Flask corre en Render
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=webhook_url,
    )

if __name__ == '__main__':
    main()
