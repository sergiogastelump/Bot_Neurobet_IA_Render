# telegram_bot/main_bot.py
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from services.ia_service import actualizar_predicciones, entrenar_modelo_ia

# Configuración base
TOKEN = os.getenv("TELEGRAM_TOKEN") or "TU_TOKEN_AQUI"  # Sustituir con tu token real si no está en .env
PORT = int(os.environ.get("PORT", "10000"))

app = Flask(__name__)

# --------------------- FUNCIONES DEL BOT ---------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje de bienvenida."""
    await update.message.reply_text(
        "🤖 ¡Bienvenido a *Neurobet IA*!\n\n"
        "Soy tu asistente de predicciones deportivas inteligente.\n\n"
        "Usa:\n"
        "📊 /predecir [equipo1] vs [equipo2]\n"
        "🧠 /entrenar para mejorar la IA\n"
        "ℹ️ /ayuda para más comandos."
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los comandos disponibles."""
    await update.message.reply_text(
        "⚙️ *Comandos disponibles:*\n\n"
        "/start - Iniciar el bot\n"
        "/predecir [equipo1] vs [equipo2] - Obtener predicción IA\n"
        "/entrenar - Entrenar el modelo con nuevos datos\n"
        "/ayuda - Mostrar esta ayuda\n\n"
        "💡 Ejemplo: /predecir América vs Chivas"
    )

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera una predicción IA."""
    try:
        texto = " ".join(context.args)
        if "vs" not in texto.lower():
            await update.message.reply_text("⚠️ Formato incorrecto. Usa: /predecir equipo1 vs equipo2")
            return

        partes = texto.split("vs")
        equipo_local = partes[0].strip()
        equipo_visitante = partes[1].strip()

        await update.message.reply_text(f"🔎 Analizando el partido *{equipo_local} vs {equipo_visitante}*...")
        resultado = actualizar_predicciones(equipo_local, equipo_visitante)
        await update.message.reply_text(f"📊 Resultado IA: {resultado}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error al generar la predicción: {e}")

async def entrenar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entrena el modelo de IA."""
    await update.message.reply_text("🧠 Entrenando el modelo de IA, por favor espera unos segundos...")
    resultado = entrenar_modelo_ia()
    await update.message.reply_text(resultado)

# --------------------- FLASK WEBHOOK ---------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe las actualizaciones del bot desde Telegram."""
    data = request.get_json(force=True)
    if data:
        update = Update.de_json(data, application.bot)
        application.create_task(application.process_update(update))
    return "Webhook activo", 200

@app.route("/", methods=["GET"])
def home():
    return "🤖 Neurobet IA bot en ejecución", 200

# --------------------- INICIALIZACIÓN ---------------------

def main():
    global application

    print("🚀 Iniciando bot en modo Webhook (Render) - Puerto", PORT)

    application = Application.builder().token(TOKEN).build()

    # Comandos del bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("predecir", predecir))
    application.add_handler(CommandHandler("entrenar", entrenar))

    # Configurar webhook (Render)
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'bot-neurobet-ia.onrender.com')}/webhook"
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="",
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()
