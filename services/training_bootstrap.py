import os
import json
import random
import logging
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from joblib import dump

# === LOGGING === #
logger = logging.getLogger(__name__)

# === RUTAS === #
DATA_DIR = Path("data")
MODEL_PATH = DATA_DIR / "modelo_entrenado.joblib"
BOOTSTRAP_LOG = DATA_DIR / "bootstrap_log.json"

DATA_DIR.mkdir(exist_ok=True)

# === FUNCIÓN PRINCIPAL === #
def entrenamiento_autonomo_previo():
    """Entrena el modelo IA automáticamente usando datos simulados y reales."""
    try:
        logger.info("🧠 Iniciando entrenamiento autónomo previo...")

        # 1️⃣ Generar dataset simulado (10,000 partidos ficticios)
        equipos = ["Barcelona", "Real Madrid", "Bayern", "PSG", "Arsenal", "Juventus", "Inter", "Liverpool"]
        data = []

        for _ in range(10000):
            local = random.choice(equipos)
            visitante = random.choice([e for e in equipos if e != local])
            goles_local = random.randint(0, 5)
            goles_visitante = random.randint(0, 5)
            tiros_local = random.randint(1, 15)
            tiros_visitante = random.randint(1, 15)
            posesion_local = random.randint(40, 70)
            posesion_visitante = 100 - posesion_local

            ganador = 1 if goles_local > goles_visitante else (0 if goles_local == goles_visitante else -1)

            data.append({
                "local": local,
                "visitante": visitante,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "tiros_local": tiros_local,
                "tiros_visitante": tiros_visitante,
                "posesion_local": posesion_local,
                "posesion_visitante": posesion_visitante,
                "resultado": ganador
            })

        df = pd.DataFrame(data)
        logger.info(f"📊 Dataset simulado generado: {len(df)} registros")

        # 2️⃣ Preparar variables de entrenamiento
        X = df[["goles_local", "goles_visitante", "tiros_local", "tiros_visitante", "posesion_local", "posesion_visitante"]]
        y = df["resultado"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 3️⃣ Entrenar modelo ML
        modelo = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
        modelo.fit(X_train, y_train)

        # 4️⃣ Evaluar rendimiento
        y_pred = modelo.predict(X_test)
        precision = round(accuracy_score(y_test, y_pred) * 100, 2)
        logger.info(f"✅ Entrenamiento completo. Precisión simulada: {precision}%")

        # 5️⃣ Guardar modelo entrenado
        dump(modelo, MODEL_PATH)
        logger.info(f"💾 Modelo guardado en {MODEL_PATH}")

        # 6️⃣ Guardar log de entrenamiento
        with open(BOOTSTRAP_LOG, "w", encoding="utf-8") as f:
            json.dump({
                "precision": precision,
                "total_partidos": len(df),
                "modelo": "RandomForestClassifier",
                "fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=4, ensure_ascii=False)

        logger.info("🏁 Entrenamiento autónomo previo completado con éxito.")
        return precision

    except Exception as e:
        logger.error(f"❌ Error en entrenamiento autónomo previo: {e}")
        return None
