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
        client = genai.Client(api_key=api_key)
        
        # 1. Identificar la fecha más reciente de los datos (usamos Dólar ID 4 como referencia)
        fecha_datos_str = "—"
        for v in datos_principales:
            if v.get('idVariable') == 4:
                fecha_datos_str = v.get('ultFechaInformada')
                break
        
        # 2. Lógica de Título Dinámico
        hoy = datetime.now().date()
        fecha_datos = datetime.strptime(fecha_datos_str, "%Y-%m-%d").date()
        diferencia = (hoy - fecha_datos).days

        if diferencia == 0:
            titulo_dinamico = "Resumen del día"
        elif diferencia == 1:
            titulo_dinamico = "Resumen de la jornada de ayer"
        else:
            # Para fines de semana o feriados
            titulo_dinamico = f"Resumen de la jornada del {fecha_datos.strftime('%d/%m/%Y')}"

        # 3. Preparar los datos para la IA
        resumen_texto = ""
        for v in datos_principales:
            resumen_texto += f"- {v.get('descripcion')}: {v.get('ultValorInformado')} (Fecha: {v.get('ultFechaInformada')})\n"

        # 4. PROMPT REFINADO
        prompt = f"""
        Actúa como un analista financiero senior. 
        Analiza los datos del BCRA con cierre al {fecha_datos_str}.
        
        REGLAS CRÍTICAS:
        1. Responde ÚNICAMENTE con un solo párrafo de máximo 100 palabras.
        2. CERO introducciones tipo "Aquí tienes el informe". Empieza directo con la información.
        3. Foco principal: Reservas y Tipo de Cambio. Menciona la tendencia de variación (si subió o bajó).
        4. Formato de números: SIEMPRE punto para miles y coma para decimales (ej: 1.502,09).
        5. Tono: Seco, profesional, de terminal financiera.

        DATOS:
        {resumen_texto}
        """
        
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        
        # Devolvemos el texto y el título por separado
        return response.text.strip(), titulo_dinamico

    except Exception as e:
        return f"Error: {str(e)}", "Informe Económico"

# --- NOTA: En tu función main() deberás recibir ambos valores ---
# analisis_texto, titulo_info = generar_analisis_ia(filtered_variables)
# output_data["ai_analysis"] = analisis_texto
# output_data["ai_title"] = titulo_info

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
