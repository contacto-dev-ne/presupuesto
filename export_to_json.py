import os
import json
import requests
import pandas as pd

def descargar_desde_drive(file_id, api_key, output_path):
    print("Iniciando accion_magica: Descargando archivo desde Google Drive...")
    # Endpoint para descargar archivos binarios de Drive usando un API Key
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={api_key}"
    
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("¡Descarga de Google Drive completada con éxito!")
    else:
        raise Exception(f"Error en la descarga (Código {response.status_code}). Verifica las credenciales asociadas a accion_magica.")

def process_excel():
    excel_path = 'ejecucion_total.xlsx'
    json_path = 'datos_ejecucion.json'
    
    # Capturamos de forma segura las llaves secretas de GitHub
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_file_id = os.environ.get("GOOGLE_DRIVE_FILE_ID")
    
    if google_api_key and google_file_id:
        descargar_desde_drive(google_file_id, google_api_key, excel_path)
    else:
        print("Corriendo localmente en PC. Se omiten los pasos de accion_magica de GitHub.")
    
    if not os.path.exists(excel_path):
        print(f"Error crítico: No se encontró el archivo {excel_path}")
        return

    print(f"Procesando {excel_path}...")
    df = pd.read_excel(excel_path)
    
    # Limpieza de columnas
    df.columns = [str(col).strip() for col in df.columns]
    df = df.fillna('')
    
    # Formatear fechas
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
            
    records = df.to_dict(orient='records')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False)
        
    print(f"¡Éxito! Se exportaron {len(records)} filas a {json_path}")
    
    # Borramos el excel del servidor de GitHub para no dejar rastro por seguridad
    if google_api_key and os.path.exists(excel_path):
        os.remove(excel_path)
        print("Archivo temporal excel removido por seguridad por la accion_magica.")

if __name__ == '__main__':
    process_excel()
