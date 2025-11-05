# services/ia_service.py
import os
from ai_model.train_model import entrenar_modelo
from ai_model.predictor import predecir_resultado
from data.db_manager import guardar_prediccion
import random

def actualizar_predicciones(equipo_local, equipo_visitante):
    """
    Función principal de predicción: usa el modelo entrenado o genera predicción simulada.
    """

    # Simular estadísticas básicas por ahora (se reemplazarán por API deportiva)
    goles_local = random.randint(0, 5)
    goles_visitante = random.randint(0, 5)
    corners = random.randint(0, 10)
    tarjetas = random.randint(0, 6)

    print(f"📊 Datos simulados: {equipo_local}({goles_local}) - {equipo_visitante}({goles_visitante})")

    try:
        resultado = predecir_resultado(goles_local, goles_visitante, corners, tarjetas)
    except Exception as e:
        print(f"⚠️ Error al predecir: {e}")
        resultado = f"Error en predicción: {e}"

    # Guardar predicción en la base de datos
    guardar_prediccion(equipo_local, equipo_visitante, resultado)
    return resultado


def entrenar_modelo_ia():
    """
    Entrena el modelo de IA usando datos históricos.
    """
    try:
        precision = entrenar_modelo()
        return f"✅ Modelo IA reentrenado con precisión de {precision:.2f}%"
    except Exception as e:
        print(f"❌ Error al entrenar modelo: {e}")
        return f"❌ Error al entrenar modelo: {e}"
