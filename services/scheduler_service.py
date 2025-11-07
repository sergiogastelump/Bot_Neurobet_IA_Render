import threading
import time
import logging
from datetime import datetime, timedelta

from services.autoaprendizaje_service import evaluar_predicciones
from services.memoria_service import guardar_evento_global
from services.visualizacion_service import generar_grafico_precision  # ✅ Nuevo

logger = logging.getLogger(__name__)

# === MODO DE PRUEBA === #
# ⏳ Intervalo corto: 2 minutos
# ⚙️ En producción, cambia a 12 * 3600 (12 horas)
INTERVALO_SEGUNDOS = 120


def ciclo_autoaprendizaje():
    """
    Ciclo automático de autoentrenamiento y generación de gráficos IA (modo prueba)
    """
    while True:
        try:
            logger.info("🧠 [AUTO] Iniciando ciclo automático de autoaprendizaje...")

            resultado = evaluar_predicciones()
            if resultado:
                guardar_evento_global("Sistema", "autoaprendizaje_automatico", resultado)

                # 🧩 Generar gráfico actualizado
                grafico = generar_grafico_precision()
                if grafico:
                    logger.info(f"📊 [AUTO] Gráfico actualizado automáticamente: {grafico}")

                logger.info(f"✅ [AUTO] Ciclo completado: {resultado}")
            else:
                logger.info("⚠️ [AUTO] No hay suficientes datos para entrenar este ciclo.")

        except Exception as e:
            logger.error(f"❌ Error en autoaprendizaje automático: {e}")

        # Esperar el siguiente ciclo
        siguiente = datetime.now() + timedelta(seconds=INTERVALO_SEGUNDOS)
        logger.info(f"⏰ Próximo ciclo automático: {siguiente.strftime('%H:%M:%S')}")
        time.sleep(INTERVALO_SEGUNDOS)


def iniciar_hilo_autoaprendizaje():
    """
    Inicia el hilo del ciclo automático sin bloquear el servidor Flask.
    """
    hilo = threading.Thread(target=ciclo_autoaprendizaje, daemon=True)
    hilo.start()
    logger.info("🧩 Hilo de autoaprendizaje automático (modo prueba) iniciado correctamente.")
