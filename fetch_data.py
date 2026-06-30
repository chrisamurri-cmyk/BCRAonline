import os
import json
import urllib.request
from datetime import datetime
import google.generativeai as genai

# Configuración API BCRA
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
VARIABLE_IDS = [1, 4, 5, 7, 8, 12, 15, 16, 27, 28]

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error en API BCRA: {e}")
        return None

def generar_analisis_ia(datos_principales):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: No se encontró la variable GEMINI_API_KEY en GitHub Secrets."

    try:
        genai.configure(api_key=api_key)
        
        # 1. Listamos modelos para ver qué ve tu cuenta realmente
        print("Listando modelos disponibles para esta API Key...")
        try:
            for m in genai.list_models():
                print(f"-> Encontrado: {m.name}")
        except Exception as e:
            print(f"Error al listar modelos: {e}")

        # 2. Intentamos el modelo estándar pero capturando el error real
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        resumen_texto = ""
        for v in datos_principales:
            resumen_texto += f"- {v.get('descripcion')}: {v.get('ultValorInformado')}\n"

        prompt = f"Resume estos datos económicos de Argentina en 3 párrafos: {resumen_texto}"
        
        print("Enviando consulta a Gemini...")
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        # Esto nos va a decir exactamente por qué Google nos rebota
        print(f"DETALLE DEL ERROR DE IA: {str(e)}")
        return f"Error detallado: {str(e)}"

def main():
    print("--- INICIANDO ACTUALIZACIÓN ---")
    
    # 1. Descarga de variables principales
    v_data = fetch_json(BASE_URL)
    if not v_data or "results" not in v_data:
        print("Error al obtener variables principales.")
        return
    
    filtered = [v for v in v_data["results"] if v.get("idVariable") in VARIABLE_IDS]
    
    # 2. Descarga de historiales
    history = {}
    for vid in VARIABLE_IDS:
        print(f"Bajando historial ID {vid}...")
        h_data = fetch_json(f"{BASE_URL}/{vid}")
        if h_data and "results" in h_data:
            detalle = h_data["results"][0].get("detalle", [])
            history[str(vid)] = sorted(detalle, key=lambda x: x.get("fecha", ""))[-365:]

    # 3. Análisis de IA
    print("Generando análisis con Gemini...")
    analisis = generar_analisis_ia(filtered)

    # 4. Guardado final
    output = {
        "metadata": {
            "last_update": datetime.now().isoformat()
        },
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
