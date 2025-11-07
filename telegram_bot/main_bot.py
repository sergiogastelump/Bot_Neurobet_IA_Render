import os
import json
import logging
import threading
import asyncio
import requests
from flask import Flask, request
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Importar servicios internos === #
from services.ia_service import predecir_partido
from services.memoria_service import (
    guardar_evento_global,
    guardar_evento_usuario,
)
from services.autoaprendizaje_service import (
    evaluar_predicciones,
    obtener_estado_modelo,
    inicializar_modelo,
)
from services.scheduler_service import iniciar_hilo_autoaprendizaje
from services.evaluacion_service import (
    evaluar_predicciones_recientes,
    iniciar_autoevaluacion_automatica,
)

# === CONFIGURACIÓN DE LOGS === #
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === VARIABLES DE ENTORNO === #
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8238035123:AAHaX2iFZjNWFMLwm8QUmjYc09qA_y9IDa8")
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"

# === FLASK APP === #
app = Flask(__name__)

# === INICIAR BOT === #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === CREAR MODELO SI NO EXISTE === #
inicializar_modelo()

# === FUNCIÓN: VERIFICAR WEBHOOK AUTOMÁTICAMENTE === #
def verificar_y_configurar_webhook():
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
        logger.error(f"⚠️ No se pudo verificar o configurar el webhook automáticamente: {e}")

# === COMANDOS DEL BOT === #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    logger.info(f"Usuario {user.first_name} inició el bot.")
    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name}!\n"
        f"Soy *Neurobet IA*, tu asistente de predicciones deportivas con autoaprendizaje y autoevaluación.\n\n"
        f"📘 *Comandos disponibles:*\n"
        f"/predecir [Equipo1 vs Equipo2]\n"
        f"/evaluar - Comprobar aciertos reales\n"
        f"/modelo - Estado actual del modelo\n"
        f"/dashboard - Ver resumen web\n"
        f"/ayuda - Lista de comandos",
        parse_mode="Markdown"
    )
    guardar_evento_usuario(user.id, "inicio", {"mensaje": "/start"})
    guardar_evento_global(user.first_name, "inicio", "Comando /start usado")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda"""
    await update.message.reply_text(
        "📘 *Comandos disponibles:*\n"
        "/start - Iniciar conversación\n"
        "/predecir [Equipo1 vs Equipo2]\n"
        "/evaluar - Revisar aciertos reales\n"
        "/modelo - Ver estado del modelo\n"
        "/dashboard - Abrir panel web",
        parse_mode="Markdown"
    )


async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /predecir"""
    user = update.effective_user
    texto = " ".join(context.args)

    if len(context.args) < 3 or "vs" not in texto.lower():
        await update.message.reply_text("❌ Usa el formato: /predecir Equipo1 vs Equipo2")
        return

    equipo_local, equipo_visitante = texto.split("vs")
    equipo_local = equipo_local.strip()
    equipo_visitante = equipo_visitante.strip()

    pred = predecir_partido(equipo_local, equipo_visitante)

    mensaje = (
        f"🔮 *Predicción IA:*\n"
        f"{pred['resultado']}\n"
        f"🎯 Precisión estimada: {pred['probabilidad']}%\n\n"
        f"🤖 Modo: {pred['modo']}"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")

    evento = {"consulta": f"{equipo_local} vs {equipo_visitante}", "resultado": pred}
    guardar_evento_usuario(user.id, "predicción", evento)
    guardar_evento_global(user.first_name, "predicción", evento)


async def evaluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /evaluar"""
    resultado = evaluar_predicciones_recientes()
    if not resultado:
        await update.message.reply_text("📭 No hay predicciones recientes para evaluar.")
        return

    mensaje = (
        f"🧠 *Evaluación completada*\n\n"
        f"📊 Partidos revisados: {resultado['evaluados']}\n"
        f"✅ Aciertos: {resultado['aciertos']}\n"
        f"📈 Precisión actual: {resultado['precision']}%"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def modelo_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /modelo"""
    modelo = obtener_estado_modelo()
    if not modelo:
        await update.message.reply_text("⚙️ El modelo aún no tiene datos registrados.")
        return

    texto = (
        "🤖 *Estado actual del modelo IA:*\n\n"
        f"📊 Sesgo Local: {round(modelo['sesgo_local'], 3)}\n"
        f"📊 Sesgo Visitante: {round(modelo['sesgo_visitante'], 3)}\n"
        f"📈 Factor de Confianza: {round(modelo['factor_confianza'], 3)}\n"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


# === REGISTRAR COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("evaluar", evaluar))
application.add_handler(CommandHandler("modelo", modelo_estado))

# === ENDPOINT PRINCIPAL === #
@app.route("/", methods=["GET"])
def home():
    return "🤖 Neurobet IA Webhook activo y evaluando precisión automáticamente", 200


# === ENDPOINT DASHBOARD === #
HISTORIAL_PATH = Path("data/historial_predicciones.json")

@app.route("/dashboard", methods=["GET"])
def dashboard():
    if HISTORIAL_PATH.exists():
        with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
            historial = json.load(f)
    else:
        historial = []

    total = len(historial)
    aciertos = sum(1 for h in historial if h.get("acierto") is True)
    evaluados = sum(1 for h in historial if h.get("acierto") is not None)
    precision = round((aciertos / evaluados) * 100, 2) if evaluados else 0
    ultimas = historial[-10:][::-1]

    html = "<h1>📊 Neurobet IA - Dashboard</h1>"
    html += f"<p>Total de predicciones: <b>{total}</b></p>"
    html += f"<p>Evaluadas: <b>{evaluados}</b> | Aciertos: <b>{aciertos}</b> | Precisión: <b>{precision}%</b></p>"
    html += "<h2>Últimas predicciones</h2><ul>"
    for item in ultimas:
        partido = item.get("partido", "N/D")
        pred = item.get("prediccion", "N/D")
        res_real = item.get("resultado_real", "pendiente")
        acierto = item.get("acierto")
        estado = "✅" if acierto else ("⌛" if acierto is None else "❌")
        html += f"<li>{estado} {partido} → {pred} | real: {res_real}</li>"
    html += "</ul>"
    return html, 200


# === WEBHOOK (CORREGIDO Y FUNCIONAL) === #
@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe actualizaciones desde Telegram y las procesa directamente."""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)
        logger.info(f"✅ Update recibido correctamente: {update}")

        asyncio.run(application.process_update(update))
    except Exception as e:
        logger.error(f"❌ Error al procesar el webhook: {e}")
        return "ERROR", 500

    return "OK", 200


# === INICIO DEL SERVICIO === #
if __name__ == "__main__":
    logger.info("🚀 Iniciando Neurobet IA (Modo Servidor Render)")
    verificar_y_configurar_webhook()
    inicializar_modelo()
    iniciar_hilo_autoaprendizaje()
    iniciar_autoevaluacion_automatica()

    logger.info("🌐 Flask ejecutándose y bot Telegram activo.")
    app.run(host="0.0.0.0", port=PORT)
