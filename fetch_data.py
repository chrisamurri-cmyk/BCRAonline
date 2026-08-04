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

    try:
        client = genai.Client(api_key=api_key)
        
        # --- BUSCADOR DE MODELOS (EVITA EL ERROR 404) ---
        modelos_vivos = [m.name for m in client.models.list()]
        mejor_modelo = next((m for m in modelos_vivos if "flash" in m.lower()), modelos_vivos[0])
        print(f"Usando modelo exacto: {mejor_modelo}")

        # --- LÓGICA DE FECHA Y TÍTULO ---
        fecha_datos_str = "—"
        for v in datos_principales:
            if v.get('idVariable') == 4: # Dólar como referencia
                fecha_datos_str = v.get('ultFechaInformada')
                break
        
        hoy = datetime.now().date()
        try:
            fecha_dt = datetime.strptime(fecha_datos_str, "%Y-%m-%d").date()
            diff = (hoy - fecha_dt).days
            if diff == 0: titulo = "Resumen del día"
            elif diff == 1: titulo = "Resumen de la jornada de ayer"
            else: titulo = f"Resumen de la jornada del {fecha_dt.strftime('%d/%m/%Y')}"
        except Exception:
            titulo = "Resumen de la jornada"

        # --- PREPARACIÓN DE DATOS Y PROMPT ---
        resumen_datos = "".join([f"- {v.get('descripcion')}: {v.get('ultValorInformado')}\n" for v in datos_principales])

        prompt = f"""
        Actúa como un analista financiero senior de Argentina. 
        Analiza estos datos del BCRA con cierre al {fecha_datos_str}.
        
        REGLAS ESTRICTAS:
        1. Responde con UN SOLO PÁRRAFO de máximo 80 palabras.
        2. NO incluyas introducciones, saludos ni "Aquí tienes el informe". Empieza directo con los datos.
        3. Foco: Reservas y Tipo de Cambio. Menciona si subieron o bajaron.
        4. Formato de números: SIEMPRE usa punto para miles y coma para decimales (ej: 1.502,09).
        5. Tono: Profesional, seco, tipo terminal de Bloomberg.

        DATOS:
        {resumen_datos}
        """
        
        response = client.models.generate_content(model=mejor_modelo, contents=prompt)
        return response.text.strip(), titulo

    except Exception as e:
        print(f"Error en IA: {e}")
        return "El análisis no pudo ser generado.", "Informe Económico"

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

    analisis_txt, titulo_txt = generar_analisis_ia(filtered)

    output = {
        "metadata": {"last_update": datetime.now().isoformat()},
        "ai_analysis": analisis_txt,
        "ai_title": titulo_txt,
        "variables": filtered,
        "history": history
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/bcra_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"--- FINALIZADO: {titulo_txt} ---")

if __name__ == "__main__":
    main()
