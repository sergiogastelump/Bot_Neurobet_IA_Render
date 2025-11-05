# telegram_bot/main_bot.py
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

# Crear instancia Flask
app = Flask(__name__)

# Crear aplicación de Telegram
bot_app = Application.builder().token(TOKEN).build()

# --- Comandos del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 ¡Hola! Soy Neurobet IA Bot.\nPuedo darte predicciones y estadísticas deportivas. Usa /predecir [equipo1] vs [equipo2]")

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if "vs" not in texto:
        await update.message.reply_text("⚠️ Usa el formato: /predecir [equipo1] vs [equipo2]")
        return
    equipo1, equipo2 = [x.strip() for x in texto.split("vs")]
    # Simulación simple de predicción (luego se conectará al modelo IA real)
    await update.message.reply_text(f"📊 Predicción simulada:\n{equipo1}: 52%\n{equipo2}: 48%\n(Ganador probable: {equipo1})")

# Registrar comandos
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("predecir", predecir))

# --- Endpoint Webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        bot_app.update_queue.put_nowait(update)
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        return "error", 500
    return "ok", 200

# Endpoint raíz (opcional)
@app.route("/", methods=["GET"])
def index():
    return "🤖 Neurobet IA Bot en ejecución - Webhook activo", 200

# --- Ejecución principal ---
if __name__ == "__main__":
    print(f"🚀 Iniciando Neurobet IA en modo Webhook (Render) - Puerto {PORT}")
    bot_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=f"https://bot-neurobet-ia.onrender.com/webhook"
    )
