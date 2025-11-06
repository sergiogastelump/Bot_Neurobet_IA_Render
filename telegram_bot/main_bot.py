import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# === CONFIGURACIÓN === #
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"

if not TELEGRAM_TOKEN:
    raise ValueError("❌ No se encontró TELEGRAM_TOKEN en las variables de entorno")

# === INICIALIZACIÓN DE FLASK === #
app = Flask(__name__)

# === APLICACIÓN DE TELEGRAM === #
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
    await update.message.reply_text(f"🔮 Predicción IA:\n{local} 62% - Empate 23% - {visitante} 15%")

# === REGISTRAR COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))

# === ENDPOINTS === #
@app.route('/')
def index():
    return "🤖 Neurobet IA Webhook activo", 200


@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibe actualizaciones desde Telegram de forma segura."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            print("⚠️ Webhook recibido vacío o sin datos JSON válidos.")
            return "No data", 200

        update = Update.de_json(data, application.bot)
        if update:
            application.update_queue.put_nowait(update)
        else:
            print("⚠️ Update inválido recibido.")
    except Exception as e:
        print(f"⚠️ Error procesando webhook: {e}")
        return "Internal Error", 200  # <— devolvemos 200 para que Telegram no marque error
    return "OK", 200


# === MAIN === #
if __name__ == '__main__':
    print(f"🚀 Iniciando Neurobet IA en modo Webhook - Puerto {PORT}")
    app.run(host="0.0.0.0", port=PORT)
