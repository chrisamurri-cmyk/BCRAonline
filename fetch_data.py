import os
import json
import urllib.request
from datetime import datetime
from google import genai

# Configuración API BCRA v4.0
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# 20 Variables Clave Seleccionadas para Historial Completo
VARIABLE_IDS = [1, 4, 5, 7, 8, 11, 12, 13, 14, 15, 16, 17, 21, 24, 26, 27, 28, 29, 30, 31]

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error BCRA ({url}): {e}")
        return None

def generar_analisis_ia(datos_principales):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Falta configuración de clave de IA.", "Informe Económico"

    try:
        client = genai.Client(api_key=api_key)
        
        # Búsqueda defensiva del modelo Flash activo
        modelos_vivos = [m.name for m in client.models.list()]
        mejor_modelo = next((m for m in modelos_vivos if "flash" in m.lower()), modelos_vivos[0])
        print(f"Usando modelo IA: {mejor_modelo}")

        # Identificar la fecha de los datos de referencia (Dólar oficial ID 4 o el primero disponible)
        fecha_datos_str = "—"
        for v in datos_principales:
            if v.get('idVariable') == 4:
                fecha_datos_str = v.get('ultFechaInformada')
                break
        if fecha_datos_str == "—" and datos_principales:
            fecha_datos_str = datos_principales[0].get('ultFechaInformada', '—')

        hoy = datetime.now().date()
        try:
            fecha_dt = datetime.strptime(fecha_datos_str, "%Y-%m-%d").date()
            diff = (hoy - fecha_dt).days
            if diff == 0: titulo = "Resumen del día"
            elif diff == 1: titulo = "Resumen de la jornada de ayer"
            else: titulo = f"Resumen de la jornada del {fecha_dt.strftime('%d/%m/%Y')}"
        except Exception:
            titulo = "Resumen de la jornada"

        resumen_datos = "".join([f"- {v.get('descripcion')}: {v.get('ultValorInformado')} ({v.get('unidadExpresion', '')})\n" for v in datos_principales[:10]])

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
    print("--- INICIANDO DESCARGA Y PROCESAMIENTO DE VARIABLES BCRA ---")
    v_data = fetch_json(BASE_URL)
    if not v_data or "results" not in v_data:
        print("Error al obtener el catálogo de variables.")
        return
    
    all_results = v_data.get("results", [])
    print(f"Catálogo completo recibido: {len(all_results)} variables disponibles.")

    # 1. Catálogo liviano con el ÚLTIMO dato conocido de TODAS las variables
    latest_catalog = []
    for item in all_results:
        latest_catalog.append({
            "idVariable": item.get("idVariable"),
            "descripcion": item.get("descripcion", "").strip(),
            "ultValorInformado": item.get("ultValorInformado"),
            "ultFechaInformada": item.get("ultFechaInformada"),
            "unidadExpresion": item.get("unidadExpresion", "").strip(),
            "categoria": item.get("categoria", "").strip()
        })

    # 2. Filtrar las 20 variables principales para la interfaz de tarjetas y gráficos
    filtered_variables = [v for v in all_results if v.get("idVariable") in VARIABLE_IDS]
    
    # 3. Descargar histórico de 365 días para las 20 variables seleccionadas
    history = {}
    for vid in VARIABLE_IDS:
        print(f"Descargando historial para variable ID {vid}...")
        h_data = fetch_json(f"{BASE_URL}/{vid}")
        if h_data and "results" in h_data:
            raw_results = h_data["results"]
            if raw_results and isinstance(raw_results, list) and "detalle" in raw_results[0]:
                detalle = raw_results[0].get("detalle", [])
                history[str(vid)] = sorted(detalle, key=lambda x: x.get("fecha", ""))[-365:]
            else:
                history[str(vid)] = []
        else:
            history[str(vid)] = []

    # 4. Generar Análisis IA
    analisis_txt, titulo_txt = generar_analisis_ia(filtered_variables)

    # 5. Estructurar archivo de salida JSON
    output = {
        "metadata": {
            "last_update": datetime.now().isoformat(),
            "total_catalog_count": len(latest_catalog)
        },
        "ai_analysis": analisis_txt,
        "ai_title": titulo_txt,
        "variables": filtered_variables,
        "history": history,
        "latest_catalog": latest_catalog
    }
    
    os.makedirs("data", exist_ok=True)
    output_file = "data/bcra_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"--- PROCESO FINALIZADO EXITOSAMENTE ---")
    print(f"Generado {output_file} con {len(filtered_variables)} variables con historial y {len(latest_catalog)} en la micro BD.")

if __name__ == "__main__":
    main()
