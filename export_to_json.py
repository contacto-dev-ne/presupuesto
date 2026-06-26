import os
import json
import requests
import pandas as pd

def obtener_archivos_de_carpeta(folder_id, api_key):
    print("Acción Mágica: Explorando la carpeta de Google Drive para listar los documentos...")
    # Consultamos a la API de Google todos los archivos dentro de la carpeta que no estén en la papelera
    url = f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents+and+trashed=false&key={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        archivos = response.json().get('files', [])
        print(f"¡Se encontraron {len(archivos)} archivos en la carpeta!")
        return archivos
    else:
        raise Exception(f"No se pudo leer la carpeta de Drive (Código {response.status_code}). Verifica los permisos públicos.")

def descargar_hoja(file_id, mime_type, api_key, output_path):
    # Si es una Hoja de Google Nativa, usamos el endpoint de exportación a Excel
    if mime_type == 'application/vnd.google-apps.spreadsheet':
        url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    else:
        # Si es un archivo XLSX clásico subido a la carpeta, lo bajamos directo
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={api_key}"
        
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        print(f"--> Advertencia: No se pudo descargar el archivo ID {file_id} (Código {response.status_code})")

def process_excel():
    json_path = 'datos_ejecucion.json'
    
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_folder_id = os.environ.get("GOOGLE_DRIVE_FILE_ID") # Contiene el ID de la carpeta
    
    if not google_api_key or not google_folder_id:
        print("Entorno local detectado o faltan credenciales. Omitiendo automatización de carpeta.")
        return

    try:
        # 1. Listar todos los archivos dentro de la carpeta pública
        lista_archivos = obtener_archivos_de_carpeta(google_folder_id, google_api_key)
        
        dataframes_proyectos = []
        
        # 2. Descargar y procesar cada archivo uno por uno
        for archivo in lista_archivos:
            f_id = archivo.get('id')
            f_name = archivo.get('name')
            f_mime = archivo.get('mimeType')
            
            # Saltarse subcarpetas si las hay
            if f_mime == 'application/vnd.google-apps.folder':
                continue
                
            print(f"Descargando y procesando de forma segura: {f_name}...")
            temp_excel = f"temp_{f_id}.xlsx"
            
            descargar_hoja(f_id, f_mime, google_api_key, temp_excel)
            
            if os.path.exists(temp_excel):
                try:
                    # Leer archivo temporal con Pandas
                    df_individual = pd.read_excel(temp_excel)
                    
                    # Limpieza estándar de columnas por archivo
                    df_individual.columns = [str(col).strip() for col in df_individual.columns]
                    
                    # Guardamos en nuestra lista para la unificación masiva
                    dataframes_proyectos.append(df_individual)
                except Exception as e:
                    print(f"Error al leer los datos de {f_name}: {e}")
                finally:
                    # Borramos el archivo temporal inmediatamente del servidor por seguridad
                    os.remove(temp_excel)
        
        # 3. UNIFICACIÓN MÁGICA: Juntar todas las hojas en una sola gran base de datos
        if dataframes_proyectos:
            print("Combinando todas las hojas descargadas en un único set de datos unificado...")
            df_total = pd.concat(dataframes_proyectos, ignore_index=True)
            df_total = df_total.fillna('')
            
            # Formatear columnas de fecha si existen
            for col in df_total.columns:
                if pd.api.types.is_datetime64_any_dtype(df_total[col]):
                    df_total[col] = df_total[col].dt.strftime('%Y-%m-%d')
            
            # Convertir a lista de diccionarios para el JSON
            records = df_total.to_dict(orient='records')
            
            # Guardar el JSON final que alimentará a mop.html
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False)
                
            print(f"¡Éxito Total! Se unificaron todos los archivos. Total de filas consolidadas: {len(records)}")
        else:
            print("No se encontraron documentos válidos para procesar en la carpeta.")
            
    except Exception as e:
        print(f"Error crítico en la ejecución de accion_magica: {e}")

if __name__ == '__main__':
    process_excel()
