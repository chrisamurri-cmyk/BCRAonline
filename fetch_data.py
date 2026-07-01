import os
import json
import urllib.request
from datetime import datetime
from google import genai # Librería de 2026

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

    try:
        # Usamos la librería moderna de 2026
        client = genai.Client(api_key=api_key)
        
        # Identificar fecha de los datos
        fecha_datos_str = "—"
        for v in datos_principales:
            if v.get('idVariable') == 4:
                fecha_datos_str = v.get('ultFechaInformada')
                break
        
        # Lógica de Título Dinámico
        hoy = datetime.now().date()
        fecha_datos = datetime.strptime(fecha_datos_str, "%Y-%m-%d").date()
        diferencia = (hoy - fecha_datos).days
        if diferencia == 0: titulo_dinamico = "Resumen del día"
        elif diferencia == 1: titulo_dinamico = "Resumen de ayer"
        else: titulo_dinamico = f"Resumen del {fecha_datos.strftime('%d/%m/%Y')}"

        # Preparar datos
        resumen_texto = "".join([f"- {v.get('descripcion')}: {v.get('ultValorInformado')}\n" for v in datos_principales])

        prompt = f"""
        Actúa como un analista financiero senior. Analiza los datos del BCRA al {fecha_datos_str}.
        REGLAS: Un solo párrafo, máximo 100 palabras, sin introducciones. 
        Usa formato 1.234,56 para números. Foco en Reservas y Dólar.
        DATOS: {resumen_texto}
        """
        
        # CAMBIO CLAVE: Quitamos el prefijo 'models/' que está causando el 404
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        
        return response.text.strip(), titulo_dinamico

    except Exception as e:
        # Si falla el 1.5, intentamos con el 1.0 por las dudas
        try:
            response = client.models.generate_content(model='gemini-1.0-pro', contents=prompt)
            return response.text.strip(), titulo_dinamico
        except:
            return f"Análisis no disponible en este momento.", "Informe"
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

    # CORRECCIÓN AQUÍ: Atrapamos los dos valores que devuelve la función
    print("Generando análisis con IA...")
    analisis_texto, titulo_ia = generar_analisis_ia(filtered)

    output = {
        "metadata": {"last_update": datetime.now().isoformat()},
        "ai_analysis": analisis_texto, # El párrafo
        "ai_title": titulo_ia,        # El título dinámico (Hoy, Ayer, etc)
        "variables": filtered,
        "history": history
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/bcra_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"--- PROCESO FINALIZADO: {titulo_ia} ---")

if __name__ == "__main__":
    main()
