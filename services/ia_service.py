import random

def predecir_partido(equipo_local: str, equipo_visitante: str) -> dict:
    """
    Predicción temporal (modo simulación)
    En versiones futuras se conectará al modelo IA entrenado.
    """
    # Simulación actual
    goles_local = random.randint(0, 3)
    goles_visitante = random.randint(0, 3)
    prob = random.uniform(55, 90)

    # Resultado estructurado
    return {
        "local": equipo_local,
        "visitante": equipo_visitante,
        "resultado": f"{equipo_local} {goles_local} - {goles_visitante} {equipo_visitante}",
        "probabilidad": round(prob, 2),
        "modo": "simulado"
    }
