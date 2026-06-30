import os
import json
import urllib.request
from datetime import datetime
import google.generativeai as genai

# Configuración API BCRA v4.0
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# IDs de variables a procesar
VARIABLE_IDS = [1, 4, 5, 7, 8, 12, 15, 16, 27, 28]

def get_api_token():
    return os.environ.get("BCRA_API_TOKEN", "")

def fetch_json(url):
    token = get_api_token()
    req_headers = HEADERS.copy()
    if token:
        req_headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error cargando {url}: {e}")
        return None

def generar_analisis_ia(datos_principales):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Falta la clave GEMINI_API_KEY en los secretos de GitHub."

    try:
        gen
