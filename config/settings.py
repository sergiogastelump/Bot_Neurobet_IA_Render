import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = "https://v3.football.api-sports.io"

if not API_KEY:
    raise ValueError("No se encontró API_KEY (revisa .env o variables en Render)")
if not TELEGRAM_TOKEN:
    raise ValueError("No se encontró TELEGRAM_TOKEN (revisa .env o variables en Render)")
