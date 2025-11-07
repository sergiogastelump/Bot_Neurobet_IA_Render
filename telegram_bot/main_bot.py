import os
import json
import logging
from flask import Flask, request
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === Importar servicios internos === #
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
from services.visualizacion_service import generar_grafico_precision
from services.evaluacion_service import (
    evaluar_predicciones_recientes,
    iniciar_autoevaluacion_automatica,
)

# 🆕 Apuestas
from services.apuestas_service import (
    configurar_usuario_apuestas,
    registrar_apuesta,
    obtener_ultimas_apuestas,
)

# === CONFIGURACIÓN DE LOGS === #
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === VARIABLES DE ENTORNO === #
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = "https://bot-neurobet-ia-render.onrender.com/webhook"

if not TELEGRAM_TOKEN:
    raise ValueError("❌ No se encontró TELEGRAM_TOKEN en el entorno.")

# === FLASK APP === #
app = Flask(__name__)

# === INICIAR BOT === #
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === CREAR MODELO SI NO EXISTE === #
inicializar_modelo()

# =========================================================
#                     COMANDOS DEL BOT
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    logger.info(f"Usuario {user.first_name} inició el bot.")
    await update.message.reply_text(
        f"👋 ¡Hola {user.first_name}!\n"
        f"Soy *Neurobet IA*, tu asistente de predicciones deportivas con autoaprendizaje, autoevaluación y ahora registro de apuestas.\n\n"
        f"📘 *Comandos disponibles:*\n"
        f"/predecir [Equipo1 vs Equipo2]\n"
        f"/historial - Tus predicciones\n"
        f"/global - Actividad global\n"
        f"/aprendizaje - Entrenamiento IA\n"
        f"/evaluar - Comprobar aciertos reales\n"
        f"/modelo - Estado actual del modelo\n"
        f"/dashboard - Ver resumen web\n"
        f"/configapuestas - Configurar moneda, formato y bank\n"
        f"/apostar - Registrar una apuesta\n"
        f"/misapuestas - Ver tus últimas apuestas\n"
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
        "/historial - Ver tus últimas predicciones (si lo habilitamos)\n"
        "/global - Actividad global\n"
        "/aprendizaje - Forzar entrenamiento IA\n"
        "/evaluar - Revisar aciertos reales\n"
        "/modelo - Ver estado del modelo\n"
        "/dashboard - Abrir panel web\n"
        "/configapuestas [formato] [moneda] [bank] - Configurar registro de apuestas\n"
        "/apostar ... - Registrar apuesta\n"
        "/misapuestas - Ver tus apuestas recientes",
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


# =========================================================
#             NUEVOS COMANDOS DE APUESTAS
# =========================================================

async def config_apuestas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite configurar formato de odds, moneda y bank inicial"""
    user = update.effective_user

    if len(context.args) < 3:
        await update.message.reply_text(
            "⚙️ Usa el formato:\n"
            "/configapuestas [decimal|americano] [MXN|USD|EUR] [bank_inicial]\n\n"
            "Ejemplo:\n"
            "/configapuestas decimal MXN 10000"
        )
        return

    formato = context.args[0].lower()
    moneda = context.args[1].upper()
    try:
        bank_inicial = float(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ El bank inicial debe ser un número.")
        return

    conf = configurar_usuario_apuestas(
        user.id,
        casa="Personal",
        moneda=moneda,
        formato_odds=formato,
        bank_inicial=bank_inicial,
    )

    await update.message.reply_text(
        f"✅ Configuración guardada:\n\n"
        f"Formato de odds: {conf['formato_odds']}\n"
        f"Moneda: {conf['moneda']}\n"
        f"Bank actual: {conf['bank_actual']}",
        parse_mode="Markdown"
    )


async def apostar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite registrar una apuesta manual"""
    user = update.effective_user

    if len(context.args) < 4:
        await update.message.reply_text(
            "📋 Usa el formato:\n"
            "/apostar Partido | Selección | Odd | Monto\n\n"
            "Ejemplo:\n"
            "/apostar América_vs_Chivas | Gana América | -120 | 500"
        )
        return

    try:
        datos = " ".join(context.args).split("|")
        partido = datos[0].strip()
        seleccion = datos[1].strip()
        odd = datos[2].strip()
        monto = float(datos[3].strip())

        apuesta = registrar_apuesta(
            user.id,
            partido=partido,
            tipo_apuesta=seleccion,
            odd_input=odd,
            monto=monto,
            resultado="pendiente"
        )

        await update.message.reply_text(
            f"🧾 *Apuesta registrada:*\n\n"
            f"🏟 Partido: {apuesta['partido']}\n"
            f"🎯 Selección: {apuesta['tipo_apuesta']}\n"
            f"💰 Odd: {apuesta['odd_usuario']} ({apuesta['formato_odd']})\n"
            f"📊 Monto: {apuesta['apuesta']} {apuesta['moneda']}\n"
            f"🏦 Bank actual: {apuesta['bank_final']} {apuesta['moneda']}\n"
            f"Estado: *{apuesta['resultado']}*",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error al registrar la apuesta: {e}")


async def mis_apuestas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las últimas apuestas registradas"""
    user = update.effective_user
    apuestas = obtener_ultimas_apuestas(user.id)

    if not apuestas:
        await update.message.reply_text("📭 No tienes apuestas registradas aún.")
        return

    texto = "📊 *Tus últimas apuestas:*\n\n"
    for ap in apuestas:
        estado = ap["resultado"]
        if estado == "ganada":
            icono = "🟢"
        elif estado == "perdida":
            icono = "🔴"
        elif estado == "push":
            icono = "🔵"
        else:
            icono = "⚪"

        texto += (
            f"{icono} {ap['partido']}\n"
            f"   • Selección: {ap['tipo_apuesta']}\n"
            f"   • Odd: {ap['odd_usuario']}\n"
            f"   • Apuesta: {ap['apuesta']} {ap['moneda']}\n"
            f"   • Bank final: {ap['bank_final']} {ap['moneda']}\n"
            f"   • Estado: {ap['resultado']}\n\n"
        )

    await update.message.reply_text(texto, parse_mode="Markdown")


# === REGISTRAR COMANDOS === #
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ayuda", ayuda))
application.add_handler(CommandHandler("predecir", predecir))
application.add_handler(CommandHandler("evaluar", evaluar))
application.add_handler(CommandHandler("modelo", modelo_estado))

# nuevos
application.add_handler(CommandHandler("configapuestas", config_apuestas))
application.add_handler(CommandHandler("apostar", apostar))
application.add_handler(CommandHandler("misapuestas", mis_apuestas))

# =========================================================
#               ENDPOINTS FLASK / WEB
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "🤖 Neurobet IA Webhook activo y evaluando precisión automáticamente", 200


# === ENDPOINT DASHBOARD SENCILLO === #
HISTORIAL_PATH = Path("data/historial_predicciones.json")

@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Muestra resumen IA y últimas predicciones"""
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


# === WEBHOOK === #
@app.route("/webhook", methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, application.bot)
    logger.info(f"✅ Update recibido correctamente: {update}")
    application.update_queue.put_nowait(update)
    return "OK", 200


# === INICIO DEL SERVICIO === #
if __name__ == "__main__":
    logger.info("🚀 Iniciando Neurobet IA (Modo Servidor Render)")
    inicializar_modelo()
    iniciar_hilo_autoaprendizaje()
    iniciar_autoevaluacion_automatica()
    app.run(host="0.0.0.0", port=PORT)
