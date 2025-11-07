import os
import json
import matplotlib.pyplot as plt
from datetime import datetime

# === RUTAS === #
LOG_PATH = "data/autoaprendizaje_log.json"
GRAFICO_PATH = "data/precision_evolutiva.png"


def generar_grafico_precision():
    """
    Genera un gráfico de la evolución del aprendizaje de la IA
    a partir del archivo autoaprendizaje_log.json
    """
    if not os.path.exists(LOG_PATH):
        print("⚠️ No existe el archivo de log de aprendizaje.")
        return None

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error al leer el archivo de log: {e}")
        return None

    if not data:
        print("⚠️ No hay datos en el log de aprendizaje.")
        return None

    # Extraer fechas y precisiones
    fechas = [d["fecha"] for d in data]
    precisiones = [d["precision"] for d in data]

    # === Crear gráfico === #
    plt.figure(figsize=(8, 4))
    plt.plot(fechas, precisiones, marker="o", linestyle="-", color="dodgerblue")
    plt.title("Evolución del Aprendizaje - Neurobet IA")
    plt.xlabel("Fecha")
    plt.ylabel("Precisión (%)")
    plt.grid(True)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Crear carpeta data si no existe
    os.makedirs(os.path.dirname(GRAFICO_PATH), exist_ok=True)

    # Guardar imagen
    plt.savefig(GRAFICO_PATH)
    plt.close()

    print(f"✅ Gráfico generado correctamente: {GRAFICO_PATH}")
    return GRAFICO_PATH
