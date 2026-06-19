import os
import json
import urllib.request
from datetime import datetime

# Configuración API BCRA v4.0
BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# IDs de variables a procesar (v4.0):
# 1: Reservas internacionales
# 4: Tipo de cambio minorista (promedio vendedor)
# 7: Tasa de interés BADLAR de bancos privados
# 15: Base monetaria
# 27: Inflación mensual
# 16: Circulación monetaria
# 8: Tasa de interés TM20 de bancos privados
# 12: Tasa de interés de depósitos a 30 días
VARIABLE_IDS = [1, 4, 7, 15, 27, 16, 8, 12]

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error cargando {url}: {e}")
        return None

def main():
    print("Iniciando descarga de datos del BCRA v4.0...")
    
    # 1. Obtener variables principales (lista general)
    print("Obteniendo variables principales de /monetarias...")
    variables_data = fetch_json(BASE_URL)
    
    if not variables_data or "results" not in variables_data:
        print("Error crítico: No se pudieron obtener las variables principales.")
        return

    results = variables_data.get("results", [])
    filtered_variables = [v for v in results if v.get("idVariable") in VARIABLE_IDS]
    
    # 2. Obtener historial para cada variable
    print("Obteniendo historial de variables...")
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
            else:
                history_data[str(var_id)] = []
        else:
            history_data[str(var_id)] = []

    # 3. Consolidar datos
    output_data = {
        "metadata": {
            "last_update": datetime.now().isoformat()
        },
        "variables": filtered_variables,
        "history": history_data
    }
    
    os.makedirs("data", exist_ok=True)
    
    output_path = "data/bcra_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Datos descargados con éxito en {output_path}")
    print(f"Variables procesadas: {[v.get('idVariable') for v in filtered_variables]}")

if __name__ == "__main__":
    main()
