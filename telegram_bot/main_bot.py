# telegram_bot/main_bot.py

import os
import json
import time
import logging
import threading
import asyncio
from pathlib import Path
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ====== IMPORTAR SERVICIOS ====== #
from services.ia_service import predecir_partido
from services.memoria_service import (
    guardar_evento_global,
    guardar_evento_usuario,
    obtener_historial_usuario,
    obtener_resumen_global,
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
from services.visualizacion_service import generar_grafico_precision

# ====== CONFIGURACIÓN DE LOGS ====== #
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ====== VARIABLES DE ENTORNO ====== #
TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN",
    "8238035123:AAHaX2iFZjNWFMLwm8QUmjYc09qA_y9IDa8"
)
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia.onrender.com/webhook"

# ====== FLASK APP ====== #
app = Flask(__name__)

# ====== APLICACIÓN TELEGRAM ====== #
application = Application.builder().token(TELEGRAM_TOKEN).build()
BOT_EVENT_LOOP: asyncio.AbstractEventLoop | None = None

# =========================================================
# COMANDOS DEL BOT
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Usuario {user.first_name} inició el bot.")
    texto = (
        f"👋 ¡Hola {user.first_name}!\n"
        f"Soy *Neurobet IA*, tu asistente de predicciones deportivas con inteligencia artificial y autoaprendizaje.\n\n"
        f"📘 *Comandos disponibles:*\n"
        f"/predecir América vs Chivas\n"
        f"/historial - Tus predicciones\n"
        f"/global - Actividad global\n"
        f"/aprendizaje - Entrenar IA\n"
        f"/evaluar - Revisar aciertos\n"
        f"/modelo - Estado actual\n"
        f"/dashboard - Panel web\n"
        f"/tipster - Picks diarios\n"
        f"/debug - Diagnóstico del sistema\n"
        f"/ayuda - Ver comandos"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")
    guardar_evento_usuario(user.id, "inicio", {"mensaje": "/start"})
    guardar_evento_global(user.first_name, "inicio", "Comando /start usado")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 *Comandos disponibles:*\n"
        "/start\n"
        "/predecir Equipo1 vs Equipo2\n"
        "/historial\n"
        "/global\n"
        "/aprendizaje\n"
        "/evaluar\n"
        "/modelo\n"
        "/dashboard\n"
        "/tipster\n"
        "/debug",
        parse_mode="Markdown"
    )


async def predecir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    texto = " ".join(context.args)

    if len(context.args) < 3 or "vs" not in texto.lower():
        await update.message.reply_text("❌ Usa el formato: /predecir Equipo1 vs Equipo2")
        return

    equipo_local, equipo_visitante = texto.split("vs", 1)
    equipo_local, equipo_visitante = equipo_local.strip(), equipo_visitante.strip()

    pred = predecir_partido(equipo_local, equipo_visitante)
    msg = (
        f"🔮 *Predicción IA:*\n"
        f"{pred['resultado']}\n"
        f"🎯 Precisión estimada: {pred['probabilidad']}%\n"
        f"🤖 Modo: {pred['modo']}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

    evento = {"consulta": f"{equipo_local} vs {equipo_visitante}", "resultado": pred}
    guardar_evento_usuario(user.id, "predicción", evento)
    guardar_evento_global(user.first_name, "predicción", evento)


async def evaluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = evaluar_predicciones_recientes()
    if not resultado:
        await update.message.reply_text("📭 No hay predicciones recientes para evaluar.")
        return

    msg = (
        "🧠 *Evaluación completada*\n\n"
        f"📊 Partidos revisados: {resultado['evaluados']}\n"
        f"✅ Aciertos: {resultado['aciertos']}\n"
        f"📈 Precisión actual: {resultado['precision']}%"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def modelo_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modelo = obtener_estado_modelo()
    if not modelo:
        await update.message.reply_text("⚙️ El modelo aún no tiene datos registrados.")
        return

    texto = (
        "🤖 *Estado actual del modelo IA:*\n\n"
        f"📊 Sesgo Local: {round(modelo['sesgo_local'], 3)}\n"
        f"📊 Sesgo Visitante: {round(modelo['sesgo_visitante'], 3)}\n"
        f"📈 Confianza: {round(modelo['factor_confianza'], 3)}\n"
    )

    graf = generar_grafico_precision()
    if graf and os.path.exists(graf):
        await update.message.reply_photo(photo=open(graf, "rb"), caption=texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")


async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    hist = obtener_historial_usuario(user.id)
    if not hist:
        await update.message.reply_text("📭 No tienes historial aún. Usa /predecir para comenzar.")
        return

    texto = "📜 *Tus últimas interacciones:*\n\n"
    for item in hist[-10:][::-1]:
        texto += f"• {item['accion']} - {item['timestamp']}\n"
        if "consulta" in item.get("datos", {}):
            texto += f"   Partido: {item['datos']['consulta']}\n"
            texto += f"   Resultado: {item['datos']['resultado']['resultado']}\n\n"
    await update.message.reply_text(texto, parse_mode="Markdown")


async def global_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resumen = obtener_resumen_global()
    if not resumen:
        await update.message.reply_text("🌎 Aún no hay actividad global.")
        return

    texto = "🌍 *Últimas actividades globales:*\n\n"
    for e in resumen[-15:][::-1]:
        texto += f"👤 {e['usuario']} → {e['accion']} ({e['timestamp']})\n"
    await update.message.reply_text(texto, parse_mode="Markdown")


async def aprendizaje_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = evaluar_predicciones()
    if not res:
        await update.message.reply_text("📂 No hay suficientes datos para entrenar aún.")
        return

    msg = (
        "🧠 *Autoaprendizaje manual ejecutado*\n\n"
        f"📊 Total: {res['total_predicciones']}\n"
        f"✅ Aciertos: {res['aciertos_estimados']}\n"
        f"📈 Precisión: {res['precision']}%"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def tipster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📣 *Picks IA del día (demo)*\n"
        "1️⃣ América -1.0 🟢 cuota 1.65\n"
        "2️⃣ Over 8.5 córners 🇲🇽 cuota 1.72\n"
        "3️⃣ MLB: Yankees gana 🟡 cuota 1.60\n\n"
        "📈 Próximamente se integrará registro y estadísticas."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = {
        "modelo": os.path.exists("modelo_entrenado.joblib"),
        "autoaprendizaje": True,
        "webhook": WEBHOOK_URL,
        "event_loop": BOT_EVENT_LOOP.is_running() if BOT_EVENT_LOOP else False
    }
    texto = (
        "🧩 *Diagnóstico del sistema:*\n\n"
        f"📡 Webhook: {status['webhook']}\n"
        f"🧠 Modelo cargado: {'✅' if status['modelo'] else '❌'}\n"
        f"🔁 Autoaprendizaje activo: {'✅' if status['autoaprendizaje'] else '❌'}\n"
        f"⚙️ Event Loop: {'✅ Activo' if status['event_loop'] else '❌ Inactivo'}"
    )
    await update.message.reply_text(texto, parse_mode="Markdown")

# =========================================================
# REGISTRAR COMANDOS
# =========================================================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("evaluar", evaluar))
application.add_handler(CommandHandler("modelo", modelo_estado))
application.add_handler(CommandHandler("historial", historial))
application.add_handler(CommandHandler("global", global_resumen))
application.add_handler(CommandHandler("aprendizaje", aprendizaje_manual))
application.add_handler(CommandHandler("tipster", tipster))
application.add_handler(CommandHandler("debug", debug))

# =========================================================
# ENDPOINTS FLASK
# =========================================================
@app.route("/", methods=["GET"])
def home():
    return "🤖 Neurobet IA Webhook activo y en aprendizaje continuo.", 200


@app.route("/dashboard", methods=["GET"])
def dashboard():
    HISTORIAL_PATH = Path("data/historial_predicciones.json")
    if HISTORIAL_PATH.exists():
        historial = json.loads(HISTORIAL_PATH.read_text(encoding="utf-8"))
    else:
        historial = []

    total = len(historial)
    evaluados = sum(1 for h in historial if h.get("acierto") is not None)
    aciertos = sum(1 for h in historial if h.get("acierto") is True)
    precision = round((aciertos / evaluados) * 100, 2) if evaluados else 0

    ultimas = historial[-10:][::-1]
    html = "<h1>📊 Neurobet IA - Dashboard</h1>"
    html += f"<p>Total: {total} | Evaluadas: {evaluados} | Precisión: {precision}%</p><ul>"
    for item in ultimas:
        partido = item.get("partido", "N/D")
        pred = item.get("prediccion", "N/D")
        res_real = item.get("resultado_real", "pendiente")
        estado = "✅" if item.get("acierto") else ("⌛" if item.get("acierto") is None else "❌")
        html += f"<li>{estado} {partido} → {pred} | real: {res_real}</li>"
    html += "</ul>"
    return html, 200


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        logger.info(f"✅ Update recibido correctamente: {update}")
        application.update_queue.put_nowait(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return "ERROR", 500

# =========================================================
# HILO ESTABLE DE TELEGRAM
# =========================================================
def _start_bot_background():
    """Loop de procesamiento estable que evita bloqueos."""
    def runner():
        global BOT_EVENT_LOOP
        BOT_EVENT_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(BOT_EVENT_LOOP)

        async def main():
            try:
                inicializar_modelo()
                await application.initialize()
                await application.start()

                await application.bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
                logger.info(f"📡 Webhook establecido correctamente: {WEBHOOK_URL}")
                logger.info("🟢 Bot Telegram inicializado correctamente (modo Render).")

                while True:
                    update = await application.update_queue.get()
                    if update:
                        logger.info(f"📩 Procesando update de {update.effective_user.first_name if update.effective_user else 'desconocido'}")
                        await application.process_update(update)
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ Error principal en hilo de bot: {e}")

        BOT_EVENT_LOOP.run_until_complete(main())

    hilo_bot = threading.Thread(target=runner, daemon=True)
    hilo_bot.start()

# =========================================================
# INICIO DEL SISTEMA
# =========================================================
inicializar_modelo()
iniciar_hilo_autoaprendizaje()
iniciar_autoevaluacion_automatica()

time.sleep(1)
_start_bot_background()
