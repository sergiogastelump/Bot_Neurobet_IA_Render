import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_neurobet.db")

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS partidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deporte TEXT,
            liga TEXT,
            equipo_local TEXT,
            equipo_visitante TEXT,
            fecha TEXT,
            prob_local REAL,
            prob_empate REAL,
            prob_visitante REAL
        )
        '''
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_db()
    print("BD creada en:", DB_PATH)
