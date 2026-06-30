import os
import json
import urllib.request
from datetime import datetime
import google.generativeai as genai # Nueva librería para la IA

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

def generar_analisis_ia(datos_principales):
    """Esta función le pide a Gemini que analice los números"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "El análisis económico no está disponible hoy (Falta configuración)."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Preparamos una lista de texto con los valores actuales para que la IA los lea
        resumen_texto = ""
        for v in datos_principales:
            resumen_texto += f"- {v.get('descripcion')}: {v.get('ultValorInformado')} ({v.get('ultFechaInformada')})\n"

        prompt = f"""
        Actúa como un analista económico experto de Argentina. 
        Analiza estos datos actuales del Banco Central (BCRA) y escribe un resumen ejecutivo de 3 párrafos muy breves. 
        Usa un tono profesional. Explica qué significan estos movimientos para la economía diaria.
        Datos del día:
        {resumen_texto}
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error de IA: {str(e)}"

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

def main():
    print("Iniciando descarga de datos del BCRA v4.0...")
    
    variables_data = fetch_json(BASE_URL)
    if not variables_data or "results" not in variables_data:
        print("Error crítico: No se pudieron obtener las variables principales.")
        return

    results = variables_data.get("results", [])
    filtered_variables = [v for v in results if v.get("idVariable") in VARIABLE_IDS]
    
    history_data = {}
    for var_id in VARIABLE_IDS:
        print(f"Descargando histórico para variable ID {var_id}...")
        history_url = f"{BASE_URL}/{var_id}"
        var_history = fetch_json(history_url)
        
        if var_history and "results" in var_history:
            raw_results = var_history["results"]
            if raw_results and isinstance(raw_results, list) and "detalle" in raw_results[0]:
                raw_history = raw_results[0]["detalle"]
                sorted_history = sorted(raw_history, key=lambda x: x.get("fecha", ""))
                history_data[str(var_id)] = sorted_history[-365:]

    # --- NUEVA PARTE: ANALISIS CON IA ---
    print("Solicitando análisis a Gemini AI...")
    analisis_ia = generar_analisis_ia(filtered_variables)
    # ------------------------------------

    output_data = {
        "metadata": {
            "last_update": datetime.now().isoformat(),
        },
        "ai_analysis": analisis_ia, # Guardamos el texto de la IA aquí
        "variables": filtered_variables,
        "history": history_data
    }
    
    os.makedirs("data", exist_ok=True)
    output_path = "data/bcra_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Proceso finalizado con éxito.")

if __name__ == "__main__":
    main()
