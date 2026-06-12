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
VARIABLE_IDS = [1, 4, 7, 15, 27, 16]

def get_api_token():
    # Retorna el token si existe en variables de entorno (GitHub Secrets)
    return os.environ.get("BCRA_API_TOKEN", "")

def check_token_expiration():
    # Comprueba si existe una fecha de expiración del token configurada
    exp_date_str = os.environ.get("BCRA_TOKEN_EXPIRATION_DATE", "")
    if not exp_date_str:
        return None, False

    try:
        exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
        days_left = (exp_date - datetime.now()).days
        # Generar alerta si faltan 30 días o menos (o si ya venció)
        alert = days_left <= 30
        return exp_date_str, alert
    except ValueError:
        print(f"Error: El formato de BCRA_TOKEN_EXPIRATION_DATE debe ser YYYY-MM-DD (recibido: {exp_date_str})")
        return None, False

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
    
    # 1. Obtener variables principales (lista general)
    print("Obteniendo variables principales de /monetarias...")
    variables_data = fetch_json(BASE_URL)
    
    if not variables_data or "results" not in variables_data:
        print("Error crítico: No se pudieron obtener las variables principales.")
        return

    results = variables_data.get("results", [])
    # Filtrar solo las variables de interés
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
            
            # En la v4.0 del BCRA, los datos históricos vienen bajo la clave 'detalle' de la primera posición del array de resultados
            if raw_results and isinstance(raw_results, list) and "detalle" in raw_results[0]:
                raw_history = raw_results[0]["detalle"]
                # Ordenar por fecha de forma ascendente (más antigua a más reciente)
                sorted_history = sorted(raw_history, key=lambda x: x.get("fecha", ""))
                # Nos quedamos con los últimos 180 registros para el gráfico
                history_data[str(var_id)] = sorted_history[-180:]
            else:
                history_data[str(var_id)] = []
        else:
            history_data[str(var_id)] = []

    # 3. Verificar expiración de credenciales
    exp_date, token_alert = check_token_expiration()
    
    # 4. Consolidar datos
    output_data = {
        "metadata": {
            "last_update": datetime.now().isoformat(),
            "token_expiration": exp_date,
            "token_alert": token_alert
        },
        "variables": filtered_variables,
        "history": history_data
    }
    
    # Asegurar que la carpeta 'data' exista
    os.makedirs("data", exist_ok=True)
    
    # Guardar en archivo JSON
    output_path = "data/bcra_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Datos descargados con éxito en {output_path}")

if __name__ == "__main__":
    main()

