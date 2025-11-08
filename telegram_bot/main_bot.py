import os
import json
import time
import threading
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# --- CONFIGURACIÓN BASE ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"

# --- FLASK APP ---
app = Flask(__name__)

# Variables de estado
estado = {
    "status": "OK",
    "loop_activo": False,
    "webhook_activo": False,
    "precision_simulada": "72%",
    "modo": "Render KeepAlive",
    "uptime_hours": 0.0,
    "inicio": datetime.utcnow(),
}

# --- MODELO SIMULADO (placeholder de IA real) ---
class ModeloIA:
    def __init__(self):
        self.precision = 72

    def autoentrenar(self):
        self.precision = max(50, min(95, self.precision + (2 - int(time.time()) % 4)))
        logging.info(f"🧠 Modelo actualizado automáticamente. Precisión simulada: {self.precision}%")

modelo = ModeloIA()


# --- CICLO AUTOMÁTICO DE APRENDIZAJE ---
def ciclo_autoaprendizaje():
    while True:
        try:
            modelo.autoentrenar()
            logging.info("✅ [AUTO] Ciclo completado.")
            time.sleep(120)
        except Exception as e:
            logging.error(f"❌ Error en autoaprendizaje: {e}")
            time.sleep(60)

threading.Thread(target=ciclo_autoaprendizaje, daemon=True).start()


# --- BOT DE TELEGRAM ---
application = Application.builder().token(TELEGRAM_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Neurobet IA en línea.\nEscribe /predecir [equipo1] vs [equipo2] para comenzar.")


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧩 Diagnóstico: Neurobet IA está activa y conectada a Telegram ✅")


async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Formato correcto: /predecir equipo1 vs equipo2")
        return

    equipos = " ".join(context.args).split("vs")
    equipo1, equipo2 = equipos[0].strip(), equipos[1].strip()
    prob_local = modelo.precision + 5
    prob_visita = 100 - prob_local

    msg = f"📊 *Predicción simulada:*\n\n🏟️ {equipo1} vs {equipo2}\n\n🔹 {equipo1}: {prob_local}%\n🔹 {equipo2}: {prob_visita}%"
    await update.message.reply_text(msg, parse_mode="Markdown")


# Agregar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("debug", debug))
application.add_handler(CommandHandler("predecir", predecir))


# --- AUTO RECUPERACIÓN Y SUPERVISIÓN ---
async def verificar_estado():
    while True:
        try:
            if not estado["loop_activo"]:
                logging.warning("⚠️ Loop inactivo detectado. Reiniciando bot...")
                threading.Thread(target=iniciar_bot_en_segundo_plano, daemon=True).start()
            await asyncio.sleep(60)
        except Exception as e:
            logging.error(f"Error en verificador de loop: {e}")
            await asyncio.sleep(60)


def iniciar_bot_en_segundo_plano():
    try:
        asyncio.run(application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            url_path="webhook",
            webhook_url=WEBHOOK_URL,
        ))
    except Exception as e:
        logging.error(f"❌ Error al iniciar bot en segundo plano: {e}")


threading.Thread(target=lambda: asyncio.run(verificar_estado()), daemon=True).start()


# --- ENDPOINTS FLASK ---
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "OK",
        "message": "Neurobet IA en ejecución.",
        "webhook": estado["webhook_activo"],
    })


@app.route("/status", methods=["GET"])
def status():
    uptime = (datetime.utcnow() - estado["inicio"]).total_seconds() / 3600
    estado["uptime_hours"] = round(uptime, 2)
    return jsonify(estado)


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        estado["loop_activo"] = True
        estado["webhook_activo"] = True
        logging.info(f"✅ Update recibido correctamente: {update}")
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Error en webhook: {e}")
        estado["loop_activo"] = False
        return "ERROR", 500


# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    logging.info("🚀 Iniciando Neurobet IA (modo Render KeepAlive)...")
    threading.Thread(target=iniciar_bot_en_segundo_plano, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
