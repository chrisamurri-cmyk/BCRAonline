import os
import json
import urllib.request
from datetime import datetime
from google import genai

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
        return "Falta configuración de clave de IA.", "Informe"

    # 1. Título Dinámico
    fecha_datos_str = "—"
    for v in datos_principales:
        if v.get('idVariable') == 4:
            fecha_datos_str = v.get('ultFechaInformada')
            break
    
    try:
        hoy = datetime.now().date()
        fecha_datos = datetime.strptime(fecha_datos_str, "%Y-%m-%d").date()
        diferencia = (hoy - fecha_datos).days
        if diferencia == 0: titulo = "Resumen del día"
        elif diferencia == 1: titulo = "Resumen de ayer"
        else: titulo = f"Resumen del {fecha_datos.strftime('%d/%m/%Y')}"
    except:
        titulo = "Resumen de mercado"

    # 2. Conexión a Gemini
    try:
        client = genai.Client(api_key=api_key)
        
        resumen_texto = "".join([f"- {v.get('descripcion')}: {v.get('ultValorInformado')}\n" for v in datos_principales])
        
        prompt = f"""
        Actúa como analista financiero. Analiza estos datos del BCRA: {resumen_texto}.
        REGLAS: Un solo párrafo corto. Sin introducciones. Usa formato 1.234,56. 
        Foco en Reservas y Dólar.
        """

        # Intentamos generar el contenido
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        
        if response.text:
            return response.text.strip(), titulo
        else:
            return "Análisis generado vacío.", titulo

    except Exception as e:
        # ESTO ES LO MÁS IMPORTANTE: Ver el error en el log de GitHub
        print(f"--- ERROR CRÍTICO DE GOOGLE ---")
        print(str(e)) 
        print(f"-------------------------------")
        return f"La IA no pudo responder (Error 429/404).", titulo

def main():
    print("--- INICIANDO PROCESO ---")
    v_data = fetch_json(BASE_URL)
    if not v_data: return
    
    filtered = [v for v in v_data.get("results", []) if v.get("idVariable") in VARIABLE_IDS]
    
    history = {}
    for vid in VARIABLE_IDS:
        h_data = fetch_json(f"{BASE_URL}/{vid}")
        if h_data and "results" in h_data:
            detalle = h_data["results"][0].get("detalle", [])
            history[str(vid)] = sorted(detalle, key=lambda x: x.get("fecha", ""))[-365:]

    print("Solicitando análisis a la IA...")
    analisis_texto, titulo_ia = generar_analisis_ia(filtered)

    output = {
        "metadata": {"last_update": datetime.now().isoformat()},
        "ai_analysis": analisis_texto,
        "ai_title": titulo_ia,
        "variables": filtered,
        "history": history
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/bcra_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"--- PROCESO FINALIZADO: {titulo_ia} ---")

if __name__ == "__main__":
    main()
