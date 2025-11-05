import requests
from config.settings import API_KEY, BASE_URL

def obtener_datos(endpoint: str, params: dict | None = None):
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[API] Error al obtener {endpoint}: {e}")
        return None
