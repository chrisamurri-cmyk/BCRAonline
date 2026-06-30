import os
import json
import urllib.request
from datetime import datetime
from google import genai # Nueva librería de 2026

# Configuración API BCRA
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
VARIABLE_IDS = [1, 4, 5, 7, 8, 12, 15, 16, 27, 28]

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error BCRA: {e}")
        return None

def generar_analisis_ia(datos_principales):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Falta configuración de clave de IA."

    try:
        # Nueva forma de conectar en 2026
        client = genai.Client(api_key=api_key)
        
        resumen_texto = ""
        for v in datos_principales:
            resumen_texto += f"- {v.get('descripcion')}: {v.get('ultValorInformado')}\n"

        prompt = f"Analiza estos datos económicos de Argentina y haz un informe de 3 párrafos cortos: {resumen_texto}"
        
        # Usamos el modelo más actual de 2026
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error con la nueva API de Google: {str(e)}"

def main():
    print("--- INICIANDO PROCESO ACTUALIZADO 2026 ---")
    
    v_data = fetch_json(BASE_URL)
    if not v_data: return
    
    filtered = [v for v in v_data.get("results", []) if v.get("idVariable") in VARIABLE_IDS]
    
    history = {}
    for vid in VARIABLE_IDS:
        h_data = fetch_json(f"{BASE_URL}/{vid}")
        if h_data and "results" in h_data:
            detalle = h_data["results"][0].get("detalle", [])
            history[str(vid)] = sorted(detalle, key=lambda x: x.get("fecha", ""))[-365:]

    print("Generando análisis con la nueva librería google-genai...")
    analisis = generar_analisis_ia(filtered)

    output = {
        "metadata": {"last_update": datetime.now().isoformat()},
        "ai_analysis": analisis,
        "variables": filtered,
        "history": history
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/bcra_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("--- PROCESO FINALIZADO CON ÉXITO ---")

if __name__ == "__main__":
    main()
