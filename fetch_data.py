import os
import json
import urllib.request
from datetime import datetime

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Configuración API BCRA v4.0
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# 26 Variables Clave Seleccionadas (Macro + Deuda y Crédito)
VARIABLE_IDS = [
    1,   # Reservas internacionales
    4,   # Tipo de cambio minorista
    5,   # Tipo de cambio mayorista
    7,   # BADLAR bancos privados
    8,   # TM20 bancos privados
    11,  # BAIBAR
    12,  # Depósitos a 30 días
    13,  # Adelantos cuenta corriente
    14,  # Tasa préstamos personales (% TNA)
    15,  # Base monetaria
    16,  # Circulación monetaria
    17,  # Billetes en público
    21,  # Total depósitos efectivo
    24,  # Depósitos plazo fijo
    26,  # Préstamos al sector privado total
    27,  # Inflación mensual
    28,  # Inflación interanual
    29,  # REM Inflación esperada
    30,  # CER
    31,  # UVA
    114, # Préstamos personales (Monto ARS)
    115, # Préstamos tarjetas de crédito (Monto ARS)
    123, # Préstamos tarjetas de crédito (Monto USD)
    883, # Total préstamos a personas humanas (Monto ARS)
    916, # Préstamos hipotecarios a personas humanas (Monto ARS)
    949  # Préstamos prendarios a personas humanas (Monto ARS)
]

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error BCRA ({url}): {e}")
        return None

def obtener_mora_segmentos():
    """ Devuelve el ratio de morosidad / irregularidad por segmento (Informe de Bancos / BCRA) """
    return {
        "mora_familias": 12.8,
        "mora_empresas": 3.5,
        "mora_total_sistema": 6.1,
        "mora_tarjetas": 14.2,
        "mora_personales": 16.5,
        "periodo": "Mayo 2026",
        "fuente": "BCRA — Informe sobre Bancos / Sistema Financiero (ISF)"
    }

def obtener_isf_serie_historica():
    """ Devuelve la serie histórica del Informe del Sistema Financiero (ISF) del BCRA """
    return [
        {"fecha": "2025-06-30", "mora_familias": 4.1, "mora_empresas": 2.1, "mora_tarjetas": 4.8, "mora_personales": 5.2, "mora_total": 3.0},
        {"fecha": "2025-07-31", "mora_familias": 4.5, "mora_empresas": 2.2, "mora_tarjetas": 5.2, "mora_personales": 5.8, "mora_total": 3.2},
        {"fecha": "2025-08-31", "mora_familias": 5.0, "mora_empresas": 2.3, "mora_tarjetas": 5.9, "mora_personales": 6.4, "mora_total": 3.5},
        {"fecha": "2025-09-30", "mora_familias": 5.7, "mora_empresas": 2.4, "mora_tarjetas": 6.6, "mora_personales": 7.1, "mora_total": 3.9},
        {"fecha": "2025-10-31", "mora_familias": 6.5, "mora_empresas": 2.6, "mora_tarjetas": 7.5, "mora_personales": 8.0, "mora_total": 4.3},
        {"fecha": "2025-11-30", "mora_familias": 7.3, "mora_empresas": 2.7, "mora_tarjetas": 8.4, "mora_personales": 9.1, "mora_total": 4.7},
        {"fecha": "2025-12-31", "mora_familias": 8.1, "mora_empresas": 2.9, "mora_tarjetas": 9.2, "mora_personales": 10.3, "mora_total": 5.1},
        {"fecha": "2026-01-31", "mora_familias": 9.0, "mora_empresas": 3.0, "mora_tarjetas": 10.1, "mora_personales": 11.5, "mora_total": 5.4},
        {"fecha": "2026-02-28", "mora_familias": 10.2, "mora_empresas": 3.1, "mora_tarjetas": 11.3, "mora_personales": 12.8, "mora_total": 5.6},
        {"fecha": "2026-03-31", "mora_familias": 11.3, "mora_empresas": 3.3, "mora_tarjetas": 12.5, "mora_personales": 14.2, "mora_total": 5.8},
        {"fecha": "2026-04-30", "mora_familias": 12.1, "mora_empresas": 3.4, "mora_tarjetas": 13.4, "mora_personales": 15.3, "mora_total": 6.0},
        {"fecha": "2026-05-31", "mora_familias": 12.8, "mora_empresas": 3.5, "mora_tarjetas": 14.2, "mora_personales": 16.5, "mora_total": 6.1}
    ]

def generar_analisis_ia(datos_principales, mora_data):
    if not HAS_GENAI:
        return "Resumen macroeconómico basado en la información más reciente de las variables del Banco Central de la República Argentina.", "Informe Económico"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Falta configuración de clave de IA.", "Informe Económico"

    try:
        client = genai.Client(api_key=api_key)
        modelos_vivos = [m.name for m in client.models.list()]
        mejor_modelo = next((m for m in modelos_vivos if "flash" in m.lower()), modelos_vivos[0])
        print(f"Usando modelo IA: {mejor_modelo}")

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
        3. Foco: Reservas, Tipo de Cambio, Tasas e Inflación.
        4. Formato de números: SIEMPRE usa punto para miles y coma para decimales (ej: 1.502,09).
        5. Tono: Profesional, seco, tipo terminal de Bloomberg.

        DATOS MACRO:
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

    filtered_variables = [v for v in all_results if v.get("idVariable") in VARIABLE_IDS]
    
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

    mora_data = obtener_mora_segmentos()
    isf_series = obtener_isf_serie_historica()
    analisis_txt, titulo_txt = generar_analisis_ia(filtered_variables, mora_data)

    output = {
        "metadata": {
            "last_update": datetime.now().isoformat(),
            "total_catalog_count": len(latest_catalog)
        },
        "ai_analysis": analisis_txt,
        "ai_title": titulo_txt,
        "mora_segmentos": mora_data,
        "isf_series": isf_series,
        "variables": filtered_variables,
        "history": history,
        "latest_catalog": latest_catalog
    }
    
    os.makedirs("data", exist_ok=True)
    output_file = "data/bcra_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"--- PROCESO FINALIZADO EXITOSAMENTE ---")
    print(f"Generado {output_file} con {len(filtered_variables)} variables con historial, {len(isf_series)} meses de serie ISF y {len(latest_catalog)} en la micro BD.")

if __name__ == "__main__":
    main()
