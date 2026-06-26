import os
import json
import requests
import pandas as pd

def descargar_desde_drive(file_id, api_key, output_path):
    print("Iniciando accion_magica: Intentando descarga directa mediante enlace web de Google Sheets...")
    
    # MÉTODO MAESTRO: Enlace de exportación directa de navegador (Bypassea las restricciones de la API Key)
    url_directa = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    
    response = requests.get(url_directa, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("¡Conversión y descarga directa completada con éxito!")
        return

    print(f"El método directo falló con código {response.status_code}. Probando método API tradicional...")
    
    # MÉTODO RESPALDO: API Drive tradicional
    url_export = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet&key={api_key}"
    response_api = requests.get(url_export, stream=True)
    
    if response_api.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response_api.iter_content(chunk_size=8192):
                f.write(chunk)
        print("¡Descarga por API completada con éxito!")
    else:
        raise Exception(
            f"Error crítico en accion_magica (Código {response_api.status_code}).\n"
            "Verifica que el GOOGLE_DRIVE_FILE_ID en los Secrets de GitHub sea el correcto."
        )

def process_excel():
    excel_path = 'ejecucion_total.xlsx'
    json_path = 'datos_ejecucion.json'
    
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_file_id = os.environ.get("GOOGLE_DRIVE_FILE_ID")
    
    if google_file_id:
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
    
    if google_file_id and os.path.exists(excel_path):
        os.remove(excel_path)
        print("Archivo temporal excel removido por seguridad por la accion_magica.")

if __name__ == '__main__':
    process_excel()
