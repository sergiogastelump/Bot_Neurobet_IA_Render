# data/db_manager.py
import sqlite3
import os

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "bot_predicciones.db")

def crear_tablas():
    """Crea las tablas principales si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deporte TEXT,
        liga TEXT,
        equipo_local TEXT,
        equipo_visitante TEXT,
        fecha TEXT,
        prob_local REAL,
        prob_empate REAL,
        prob_visitante REAL,
        resultado_predicho TEXT,
        prediccion_fecha TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predicciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipo_local TEXT,
        equipo_visitante TEXT,
        resultado_predicho TEXT,
        fecha_prediccion TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

def guardar_prediccion(equipo_local, equipo_visitante, resultado):
    """Guarda la predicción generada por la IA."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predicciones (equipo_local, equipo_visitante, resultado_predicho)
        VALUES (?, ?, ?)
    """, (equipo_local, equipo_visitante, resultado))
    conn.commit()
    conn.close()
    print(f"✅ Predicción guardada: {equipo_local} vs {equipo_visitante} → {resultado}")

def obtener_partidos(limit=10):
    """Devuelve los últimos partidos registrados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT equipo_local, equipo_visitante, fecha FROM partidos ORDER BY id DESC LIMIT ?", (limit,))
    datos = cursor.fetchall()
    conn.close()
    return datos

# Crear las tablas al importar
crear_tablas()
