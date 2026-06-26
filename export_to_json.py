import os
import json
import requests
import pandas as pd

def descargar_desde_drive(file_id, api_key, output_path):
    print("Iniciando accion_magica: Detectando formato de Hoja de Google Sheets...")
    
    # MÉTODO 1: Endpoint de exportación para Hojas de Cálculo nativas de Google
    url_export = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet&key={api_key}"
    
    response = requests.get(url_export, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("¡Conversión y descarga de Google Sheets completada con éxito!")
        return

    print(f"El método nativo devolvió código {response.status_code}. Intentando método alternativo para archivos XLSX directos...")
    
    # MÉTODO 2: Endpoint clásico por si el archivo es un .xlsx subido a la carpeta
    url_media = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={api_key}"
    response_media = requests.get(url_media, stream=True)
    
    if response_media.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response_media.iter_content(chunk_size=8192):
                f.write(chunk)
        print("¡Descarga de archivo Excel estático completada con éxito!")
    else:
        raise Exception(
            f"Error total en accion_magica (Código {response_media.status_code}).\n"
            "Causas probables:\n"
            "1. El archivo en Google Drive NO está compartido como 'Cualquiera con el enlace puede ver'.\n"
            "2. El GOOGLE_DRIVE_FILE_ID o GOOGLE_API_KEY están mal copiados en los Secrets de GitHub.\n"
            "3. La API de Google Drive no está activa en tu consola de Google Cloud."
        )

def process_excel():
    excel_path = 'ejecucion_total.xlsx'
    json_path = 'datos_ejecucion.json'
    
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_file_id = os.environ.get("GOOGLE_DRIVE_FILE_ID")
    
    if google_api_key and google_file_id:
        descargar_desde_drive(google_file_id, google_api_key, excel_path)
    else:
        print("Corriendo localmente en PC. Se omiten los pasos de accion_magica de GitHub.")
    
    if not os.path.exists(excel_path):
        print(f"Error crítico: No se generó el archivo {excel_path}")
        return

    print(f"Procesando y limpiando datos de {excel_path}...")
    df = pd.read_excel(excel_path)
    
    df.columns = [str(col).strip() for col in df.columns]
    df = df.fillna('')
    
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
            
    records = df.to_dict(orient='records')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False)
        
    print(f"¡Éxito! Se exportaron {len(records)} filas a {json_path}")
    
    if google_api_key and os.path.exists(excel_path):
        os.remove(excel_path)
        print("Archivo temporal excel removido por seguridad por la accion_magica.")

if __name__ == '__main__':
    process_excel()
