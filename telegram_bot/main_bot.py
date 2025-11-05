import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from services.ia_service import predecir_partido

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

app = Flask(__name__)
application = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Neurobet IA Bot\nUsa /predecir Equipo1 vs Equipo2")

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or "vs" not in " ".join(context.args):
        await update.message.reply_text("⚠️ Formato: /predecir Equipo1 vs Equipo2")
        return
    texto = " ".join(context.args)
    equipo_local, equipo_visitante = [p.strip() for p in texto.split("vs")]
    pred = predecir_partido(equipo_local, equipo_visitante)
    mejor = max(
        [("🏠 " + pred["equipo_local"], pred["prob_local"]), ("🤝 Empate", pred["prob_empate"]), ("🚌 " + pred["equipo_visitante"], pred["prob_visitante"])],
        key=lambda x: x[1],
    )
    msg = f"📊 Predicción Neurobet IA\n{pred['equipo_local']} vs {pred['equipo_visitante']}\n\n🏠 Local: {pred['prob_local']}%\n🤝 Empate: {pred['prob_empate']}%\n🚌 Visitante: {pred['prob_visitante']}%\n\n✅ Sugerencia: {mejor[0]} ({mejor[1]}%)"
    await update.message.reply_text(msg)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predecir", predecir))

@app.route("/", methods=["GET"])
def home():
    return "Neurobet IA Bot activo ✅", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200

if __name__ == "__main__":
    print(f"🚀 Bot corriendo en puerto {PORT}")
    app.run(host="0.0.0.0", port=PORT)
