import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Literal

# Carpeta donde se guardan las apuestas
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Tipos
ResultadoTipo = Literal["ganada", "perdida", "push", "pendiente"]


def _get_user_file(user_id: int) -> Path:
    """Devuelve la ruta del archivo de apuestas del usuario."""
    return DATA_DIR / f"apuestas_usuario_{user_id}.json"


def _load_user_bets(user_id: int) -> List[dict]:
    """Carga las apuestas del usuario, si no existe regresa lista vacía."""
    fpath = _get_user_file(user_id)
    if fpath.exists():
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_user_bets(user_id: int, apuestas: List[dict]) -> None:
    """Guarda la lista de apuestas del usuario."""
    fpath = _get_user_file(user_id)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(apuestas, f, indent=2, ensure_ascii=False)


# ==========================
#  CONVERSIONES DE ODDS
# ==========================

def americano_a_decimal(odd_americano: float) -> float:
    """
    Convierte cuota americana (-120, +150) a decimal (1.83, 2.50).
    Fórmulas:
      - si es negativo: 1 + (100 / |odd|)
      - si es positivo: 1 + (odd / 100)
    """
    odd = float(odd_americano)
    if odd < 0:
        return round(1 + (100 / abs(odd)), 4)
    else:
        return round(1 + (odd / 100), 4)


def decimal_a_americano(odd_decimal: float) -> int:
    """
    Convierte cuota decimal a formato americano.
      - si decimal >= 2.0 → positivo
      - si decimal < 2.0 → negativo
    """
    dec = float(odd_decimal)
    if dec >= 2.0:
        return int((dec - 1) * 100)
    else:
        return int(-100 / (dec - 1))


# ==========================
#  CONFIGURACIÓN DE USUARIO
# ==========================

def configurar_usuario_apuestas(
    user_id: int,
    casa: str = "Generica",
    moneda: str = "MXN",
    formato_odds: str = "decimal",
    bank_inicial: float = 0.0,
) -> dict:
    """
    Guarda una entrada de configuración inicial del usuario.
    En realidad lo almacenamos como una apuesta especial de tipo 'config'
    para no crear otro archivo.
    """
    apuestas = _load_user_bets(user_id)

    # buscar si ya hay config
    existe_conf = next((a for a in apuestas if a.get("tipo") == "config"), None)
    config = {
        "tipo": "config",
        "casa_apuestas": casa,
        "moneda": moneda,
        "formato_odds": formato_odds,  # 'decimal' o 'americano'
        "bank_actual": bank_inicial,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if existe_conf:
        # actualizar
        for i, ap in enumerate(apuestas):
            if ap.get("tipo") == "config":
                apuestas[i] = config
    else:
        apuestas.insert(0, config)

    _save_user_bets(user_id, apuestas)
    return config


def obtener_config_usuario(user_id: int) -> dict:
    """Devuelve la config guardada del usuario, o una por defecto."""
    apuestas = _load_user_bets(user_id)
    conf = next((a for a in apuestas if a.get("tipo") == "config"), None)
    if conf:
        return conf
    # si no existe, devolvemos una por defecto
    return {
        "tipo": "config",
        "casa_apuestas": "Generica",
        "moneda": "MXN",
        "formato_odds": "decimal",
        "bank_actual": 0.0,
    }


# ==========================
#  REGISTRO DE APUESTAS
# ==========================

def registrar_apuesta(
    user_id: int,
    partido: str,
    tipo_apuesta: str,
    odd_input: str,
    monto: float,
    resultado: ResultadoTipo = "pendiente",
    es_parley: bool = False,
    selecciones: Optional[List[dict]] = None,
) -> dict:
    """
    Registra una apuesta del usuario.
    - odd_input: puede venir como "1.8" o "-120"
    - convierte internamente a decimal para cálculos
    """
    apuestas = _load_user_bets(user_id)
    config = obtener_config_usuario(user_id)
    bank_actual = float(config.get("bank_actual", 0.0))

    # convertir odd según lo que ingresó
    odd_input = str(odd_input).strip()
    if odd_input.startswith("+") or odd_input.startswith("-"):
        # es formato americano
        odd_decimal = americano_a_decimal(float(odd_input))
        odd_guardado = odd_input  # guardamos el original del usuario
        formato = "americano"
    else:
        # asumimos decimal
        odd_decimal = float(odd_input)
        odd_guardado = odd_input
        formato = "decimal"

    # calcular bank final según resultado
    bank_final = bank_actual  # por defecto si pendiente
    ganancia = 0.0

    if resultado == "ganada":
        ganancia = round(monto * (odd_decimal - 1), 2)
        bank_final = bank_actual + ganancia
    elif resultado == "perdida":
        ganancia = -monto
        bank_final = bank_actual - monto
    elif resultado == "push":
        ganancia = 0.0
        bank_final = bank_actual  # se regresa el dinero
    else:
        # pendiente
        ganancia = 0.0
        bank_final = bank_actual

    apuesta = {
        "tipo": "parley" if es_parley else "simple",
        "partido": partido,
        "tipo_apuesta": tipo_apuesta,
        "odd_usuario": odd_guardado,      # lo que escribió el usuario
        "odd_decimal": odd_decimal,       # lo que usamos para cálculos
        "formato_odd": formato,
        "moneda": config.get("moneda", "MXN"),
        "bank_inicial": bank_actual,
        "apuesta": monto,
        "bank_final": bank_final,
        "resultado": resultado,
        "ganancia": ganancia,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # si es parley, guardamos también las selecciones
    if es_parley and selecciones:
        apuesta["selecciones"] = selecciones

    # guardamos la apuesta
    apuestas.append(apuesta)

    # actualizamos config (bank actual)
    for i, ap in enumerate(apuestas):
        if ap.get("tipo") == "config":
            apuestas[i]["bank_actual"] = bank_final
            break

    _save_user_bets(user_id, apuestas)
    return apuesta


# ==========================
#  ACTUALIZAR RESULTADO
# ==========================

def actualizar_resultado_apuesta(
    user_id: int,
    index: int,
    nuevo_resultado: ResultadoTipo
) -> dict:
    """
    Permite actualizar una apuesta pendiente a ganada/perdida/push y recalcular el bank.
    index: índice dentro de la lista de apuestas (el front puede pasar el index)
    """
    apuestas = _load_user_bets(user_id)
    if index < 0 or index >= len(apuestas):
        raise IndexError("Índice de apuesta inválido.")

    apuesta = apuestas[index]
    if apuesta.get("tipo") == "config":
        raise ValueError("No se puede actualizar la configuración como si fuera apuesta.")

    # obtener config
    config = obtener_config_usuario(user_id)
    bank_actual = float(config.get("bank_actual", 0.0))

    odd_decimal = float(apuesta["odd_decimal"])
    monto = float(apuesta["apuesta"])

    if nuevo_resultado == "ganada":
        ganancia = round(monto * (odd_decimal - 1), 2)
        bank_final = bank_actual + ganancia
    elif nuevo_resultado == "perdida":
        ganancia = -monto
        bank_final = bank_actual - monto
    elif nuevo_resultado == "push":
        ganancia = 0.0
        bank_final = bank_actual
    else:
        ganancia = 0.0
        bank_final = bank_actual

    # actualizar apuesta
    apuesta["resultado"] = nuevo_resultado
    apuesta["ganancia"] = ganancia
    apuesta["bank_final"] = bank_final

    # actualizar config
    for i, ap in enumerate(apuestas):
        if ap.get("tipo") == "config":
            apuestas[i]["bank_actual"] = bank_final
            break

    # guardar
    _save_user_bets(user_id, apuestas)
    return apuesta


# ==========================
#  RESÚMENES
# ==========================

def obtener_resumen_mensual(user_id: int, year: int, month: int) -> dict:
    """
    Devuelve resumen del mes: total apostado, ganancia, aciertos, fallos, pushes.
    """
    apuestas = _load_user_bets(user_id)
    apuestas_mes = []
    for ap in apuestas:
        if ap.get("tipo") == "config":
            continue
        ts = ap.get("timestamp")
        if not ts:
            continue
        fecha = datetime.fromisoformat(ts)
        if fecha.year == year and fecha.month == month:
            apuestas_mes.append(ap)

    total_apostado = sum(float(a["apuesta"]) for a in apuestas_mes)
    ganadas = [a for a in apuestas_mes if a["resultado"] == "ganada"]
    perdidas = [a for a in apuestas_mes if a["resultado"] == "perdida"]
    pushes = [a for a in apuestas_mes if a["resultado"] == "push"]

    ganancia_neta = sum(float(a.get("ganancia", 0.0)) for a in apuestas_mes)
    total = len(apuestas_mes)
    acierto = round((len(ganadas) / total) * 100, 2) if total else 0.0

    return {
        "total_apuestas": total,
        "total_apostado": round(total_apostado, 2),
        "ganancia_neta": round(ganancia_neta, 2),
        "ganadas": len(ganadas),
        "perdidas": len(perdidas),
        "pushes": len(pushes),
        "porcentaje_acierto": acierto,
        "moneda": obtener_config_usuario(user_id).get("moneda", "MXN"),
    }


def obtener_ultimas_apuestas(user_id: int, limit: int = 10) -> List[dict]:
    """
    Devuelve las últimas N apuestas (sin contar la config).
    """
    apuestas = _load_user_bets(user_id)
    apuestas_sin_config = [a for a in apuestas if a.get("tipo") != "config"]
    return apuestas_sin_config[-limit:][::-1]
