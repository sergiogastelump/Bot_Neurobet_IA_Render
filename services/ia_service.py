import random

def predecir_partido(equipo_local: str, equipo_visitante: str) -> dict:
    return {
        "equipo_local": equipo_local,
        "equipo_visitante": equipo_visitante,
        "prob_local": round(random.uniform(35, 70), 2),
        "prob_empate": round(random.uniform(5, 25), 2),
        "prob_visitante": round(random.uniform(20, 60), 2),
    }
