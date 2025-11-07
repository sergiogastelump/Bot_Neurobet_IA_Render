# ai_model/ia_predictiva.py
"""
Módulo de IA Predictiva para Neurobet IA
----------------------------------------
Objetivo:
- Dar una predicción estructurada ya lista para enviar a Telegram.
- Permitir entrenar/cargar un modelo de ML cuando haya datos reales.
- Guardar memoria (global y por usuario) para autoaprendizaje futuro.

Este módulo está hecho para funcionar incluso si todavía no hay dataset real:
en ese caso usa un "modelo básico" que genera una distribución lógica.
"""

import os
import json
import random
from datetime import datetime
from typing import Dict, Any, Optional

# Rutas por defecto (puedes ajustarlas según tu repo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORIA_GLOBAL_PATH = os.path.join(BASE_DIR, "memoria_global.json")
MEMORIA_USUARIOS_DIR = os.path.join(BASE_DIR, "memoria_usuarios")
DATASET_PATH = os.path.join(BASE_DIR, "historial_partidos.csv")
MODELO_PATH = os.path.join(BASE_DIR, "modelo_neurobet.pkl")

# Crea carpeta de memorias si no existe
os.makedirs(MEMORIA_USUARIOS_DIR, exist_ok=True)


# =============================
# 1. UTILIDADES DE MEMORIA
# =============================
def cargar_memoria_global() -> Dict[str, Any]:
    if not os.path.exists(MEMORIA_GLOBAL_PATH):
        return {
            "total_predicciones": 0,
            "equipos_consultados": {},
            "ultimo_entrenamiento": None
        }
    with open(MEMORIA_GLOBAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_memoria_global(memoria: Dict[str, Any]) -> None:
    with open(MEMORIA_GLOBAL_PATH, "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)


def cargar_memoria_usuario(user_id: str) -> Dict[str, Any]:
    ruta = os.path.join(MEMORIA_USUARIOS_DIR, f"{user_id}.json")
    if not os.path.exists(ruta):
        return {
            "user_id": user_id,
            "consultas": 0,
            "equipos_frecuentes": {}
        }
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_memoria_usuario(user_id: str, data: Dict[str, Any]) -> None:
    ruta = os.path.join(MEMORIA_USUARIOS_DIR, f"{user_id}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =============================
# 2. MODELO BÁSICO (FALLBACK)
# =============================
def _prediccion_basica(equipo_local: str, equipo_visitante: str) -> Dict[str, Any]:
    """
    Genera una predicción lógica aunque no haya modelo real.
    Regresa un dict con el mismo formato que usará el modelo entrenado.
    """
    # Distribución aleatoria pero razonable
    base_local = random.randint(45, 70)  # local suele tener ventaja
    base_visitante = random.randint(10, 35)
    restante = 100 - (base_local + base_visitante)
    empate = max(5, restante)

    return {
        "local": equipo_local,
        "visitante": equipo_visitante,
        "prob_local": round(base_local, 2),
        "prob_empate": round(empate, 2),
        "prob_visitante": round(base_visitante, 2),
        "fuente": "simulado",  # luego será "modelo_entrenado"
    }


# =============================
# 3. PREDICCIÓN PRINCIPAL
# =============================
def predecir_partido(
    equipo_local: str,
    equipo_visitante: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Punto de entrada principal.
    1. Carga memoria.
    2. (en futuro) intenta cargar modelo real.
    3. Devuelve predicción.
    4. Actualiza memoria.
    """

    # 1. Por ahora usamos el modelo básico
    pred = _prediccion_basica(equipo_local, equipo_visitante)

    # 2. Actualizar memoria global
    memoria_global = cargar_memoria_global()
    memoria_global["total_predicciones"] += 1

    # contar equipos
    for eq in (equipo_local, equipo_visitante):
        memoria_global["equipos_consultados"].setdefault(eq, 0)
        memoria_global["equipos_consultados"][eq] += 1

    # marcar fecha de “uso” (sirve después para autoentrenar cada X días)
    memoria_global["ultimo_uso"] = datetime.utcnow().isoformat()
    guardar_memoria_global(memoria_global)

    # 3. Actualizar memoria del usuario (si viene de Telegram)
    if user_id:
        mem_user = cargar_memoria_usuario(str(user_id))
        mem_user["consultas"] += 1
        mem_user["equipos_frecuentes"].setdefault(equipo_local, 0)
        mem_user["equipos_frecuentes"][equipo_local] += 1
        mem_user["equipos_frecuentes"].setdefault(equipo_visitante, 0)
        mem_user["equipos_frecuentes"][equipo_visitante] += 1
        guardar_memoria_usuario(str(user_id), mem_user)

    # 4. Armar salida lista para el bot
    respuesta_texto = (
        f"🔮 Predicción IA (modo {pred['fuente']}):\n"
        f"{pred['local']}: {pred['prob_local']}%\n"
        f"Empate: {pred['prob_empate']}%\n"
        f"{pred['visitante']}: {pred['prob_visitante']}%"
    )

    return {
        "texto": respuesta_texto,
        "local": pred["local"],
        "visitante": pred["visitante"],
        "prob_local": pred["prob_local"],
        "prob_empate": pred["prob_empate"],
        "prob_visitante": pred["prob_visitante"],
        "memoria_total_predicciones": memoria_global["total_predicciones"],
    }


# =============================
# 4. ESPACIO PARA MODELO REAL
# =============================
def entrenar_modelo_desde_csv(csv_path: str = DATASET_PATH) -> None:
    """
    FUTURO: aquí vamos a leer tu dataset real (10 años, ligas, etc.),
    entrenar un modelo de ML y guardarlo en MODELO_PATH.
    Por ahora queda como placeholder.
    """
    # TODO: implementar cuando tengamos datos reales
    pass
