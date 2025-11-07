import os
import json
import logging
import asyncio
import requests
from flask import Flask, request
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === CONFIGURACIÓN GENERAL === #
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"

# === FLASK APP === #
app = Flask(__name__)

# === IMPORTAR SERVICIOS === #
from services.ia_service import predecir_partido
from services.memoria_service import guardar_evento_global, guardar_evento_usuario
from services.autoaprendizaje_service import obtener_estado_modelo, inicializar_modelo
from services.scheduler_service import iniciar_hilo_autoaprendizaje
from services.evaluacion_service import evaluar_predicciones_recientes, iniciar_autoevaluacion_automatica

# === INICIAR BOT === #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === WEBHOOK CHECK === #
def configurar_webhook():
    try:
        info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo").json()
        actual = info.get("result", {}).get("url", "")
        if actual != WEBHOOK_URL:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
                data={"url": WEBHOOK_URL}
            ).json()
            if r.get("ok"):
                logger.info(f"✅ Webhook configurado automáticamente en: {WEBHOOK_URL}")
            else:
                logger.error(f"❌ Error al configurar webhook: {r}")
        else:
            logger.info("🔗 Webhook ya configurado correctamente.")
    except Exception as e:
        logger.error(f"⚠️ No se pudo configurar el webhook: {e}")

# === COMANDOS === #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name}! Soy *Neurobet IA*.\n\n"
        f"📘 Comandos disponibles:\n"
        f"/predecir [Equipo1 vs Equipo2]\n"
        f"/evaluar - Revisar aciertos reales\n"
        f"/modelo - Estado actual del modelo\n"
        f"/dashboard - Ver panel web\n"
        f"/ayuda - Ver comandos",
        parse_mode="Markdown"
    )
    guardar_evento_usuario(user.id, "inicio", {"mensaje": "/start"})
    guardar_evento_global(user.first_name, "inicio", "Inicio del bot")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Comandos:\n"
        "/start\n/predecir [Equipo1 vs Equipo2]\n/evaluar\n/modelo\n/dashboard",
        parse_mode="Markdown"
    )

async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if "vs" not in texto.lower():
        await update.message.reply_text("❌ Usa el formato: /predecir Equipo1 vs Equipo2")
        return
    local, visitante = [e.strip() for e in texto.split("vs")]
    pred = predecir_partido(local, visitante)
    mensaje = (
        f"🔮 *Predicción IA:*\n"
        f"{pred['resultado']}\n"
        f"🎯 Precisión estimada: {pred['probabilidad']}%\n"
        f"🤖 Modo: {pred['modo']}"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def evaluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = evaluar_predicciones_recientes()
    if not resultado:
        await update.message.reply_text("📭 No hay predicciones recientes para evaluar.")
        return
    msg = (
        f"🧠 *Evaluación completada*\n\n"
        f"📊 Revisados: {resultado['evaluados']}\n"
        f"✅ Aciertos: {resultado['aciertos']}\n"
        f"📈 Precisión: {resultado['precision']}%"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def modelo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modelo = obtener_estado_modelo()
    if not modelo:
        await update.message.reply_text("⚙️ El modelo aún no tiene datos registrados.")
        return
    msg = (
        f"🤖 *Estado del modelo:*\n\n"
        f"Sesgo Local: {modelo['sesgo_local']:.3f}\n"
        f"Sesgo Visitante: {modelo['sesgo_visitante']:.3f}\n"
        f"Confianza: {modelo['factor_confianza']:.3f}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# === REGISTRAR HANDLERS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("evaluar", evaluar))
application.add_handler(CommandHandler("modelo", modelo))

# === ENDPOINTS FLASK === #
@app.route("/", methods=["GET"])
def home():
    return "🤖 Neurobet IA activo", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))
        logger.info(f"✅ Update procesado correctamente.")
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return "ERROR", 500
    return "OK", 200

# === ARRANQUE PRINCIPAL === #
if __name__ == "__main__":
    logger.info("🚀 Iniciando Neurobet IA...")

    # Inicialización IA + tareas automáticas
    inicializar_modelo()
    iniciar_hilo_autoaprendizaje()
    iniciar_autoevaluacion_automatica()
    configurar_webhook()

    # 🔹 Inicializar bot sincronamente antes de iniciar Flask
    asyncio.run(application.initialize())
    asyncio.run(application.start())
    logger.info("✅ Bot Telegram inicializado correctamente y listo para recibir webhooks.")

    # 🔹 Iniciar Flask después de que el bot esté listo
    logger.info(f"🌐 Servidor Flask ejecutándose en puerto dinámico {PORT}")
    app.run(host="0.0.0.0", port=PORT)
