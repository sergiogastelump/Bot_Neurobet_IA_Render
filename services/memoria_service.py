import json
import os
from datetime import datetime

# === RUTAS DE LOS ARCHIVOS DE MEMORIA === #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GLOBAL_FILE = os.path.join(BASE_DIR, "../data/memoria_global.json")
USERS_FILE = os.path.join(BASE_DIR, "../data/memoria_usuarios.json")


# === FUNCIONES AUXILIARES === #
def _leer_json(path):
    """Lee un archivo JSON y devuelve su contenido."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _guardar_json(path, data):
    """Guarda un diccionario en un archivo JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# === MEMORIA GLOBAL === #
def guardar_evento_global(usuario, accion, datos):
    """Guarda un evento en la memoria global."""
    memoria = _leer_json(GLOBAL_FILE)
    evento = {
        "usuario": usuario,
        "accion": accion,
        "datos": datos,
        "timestamp": datetime.utcnow().isoformat()
    }

    memoria.setdefault("eventos", []).append(evento)
    _guardar_json(GLOBAL_FILE, memoria)


# === MEMORIA POR USUARIO === #
def guardar_evento_usuario(user_id, accion, datos):
    """Guarda un evento individual por usuario."""
    memoria = _leer_json(USERS_FILE)
    evento = {
        "accion": accion,
        "datos": datos,
        "timestamp": datetime.utcnow().isoformat()
    }

    if str(user_id) not in memoria:
        memoria[str(user_id)] = []

    memoria[str(user_id)].append(evento)
    _guardar_json(USERS_FILE, memoria)


def obtener_historial_usuario(user_id, limite=5):
    """Devuelve los últimos eventos de un usuario."""
    memoria = _leer_json(USERS_FILE)
    eventos = memoria.get(str(user_id), [])
    return eventos[-limite:] if eventos else []


def obtener_resumen_global(limite=10):
    """Devuelve los últimos eventos globales."""
    memoria = _leer_json(GLOBAL_FILE)
    eventos = memoria.get("eventos", [])
    return eventos[-limite:] if eventos else []


# === LIMPIEZA === #
def limpiar_memoria(tipo="todo"):
    """Permite limpiar la memoria global, individual o completa."""
    if tipo in ("global", "todo") and os.path.exists(GLOBAL_FILE):
        os.remove(GLOBAL_FILE)
    if tipo in ("usuarios", "todo") and os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)
