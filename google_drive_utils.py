import os
import io
import json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Inicializa el servicio de Google Drive

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'], scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def obtener_fecha_modificacion_drive(carpeta_id, nombre_archivo):
    """Obtiene la fecha de última modificación del archivo en Google Drive."""
    service = get_drive_service()
    query = f"'{carpeta_id}' in parents and name = '{nombre_archivo}' and trashed = false"
    results = service.files().list(
        q=query,
        orderBy='modifiedTime desc',
        pageSize=1,
        fields="files(id, name, modifiedTime)"
    ).execute()
    
    files = results.get('files', [])
    if not files:
        raise Exception("No se encontró el archivo en Google Drive.")
    
    return files[0]['modifiedTime']

def cargar_control_versiones():
    """Carga el archivo de control de versiones."""
    control_path = 'control_versiones.json'
    if os.path.exists(control_path):
        with open(control_path, 'r') as f:
            return json.load(f)
    return {
        "ultima_modificacion": None,
        "archivo_local": None
    }

def guardar_control_versiones(control):
    """Guarda el archivo de control de versiones."""
    with open('control_versiones.json', 'w') as f:
        json.dump(control, f)

# Descarga el archivo Excel más reciente con el nombre dado de la carpeta indicada

def descargar_excel_drive(carpeta_id, nombre_archivo, destino_local):
    """Descarga el archivo Excel solo si hay una versión más nueva en Drive."""
    try:
        # Obtener fecha de modificación en Drive
        fecha_drive = obtener_fecha_modificacion_drive(carpeta_id, nombre_archivo)
        
        # Cargar control de versiones
        control = cargar_control_versiones()
        
        # Verificar si necesitamos descargar
        if (control["ultima_modificacion"] is None or 
            control["archivo_local"] is None or 
            fecha_drive > control["ultima_modificacion"]):
            
            print("Descargando nueva versión del archivo...")
            service = get_drive_service()
            query = f"'{carpeta_id}' in parents and name = '{nombre_archivo}' and trashed = false"
            results = service.files().list(q=query, orderBy='modifiedTime desc', pageSize=1, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if not files:
                raise Exception("No se encontró el archivo en Google Drive.")
            
            file_id = files[0]['id']
            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(destino_local, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.close()
            
            # Actualizar control de versiones
            control["ultima_modificacion"] = fecha_drive
            control["archivo_local"] = destino_local
            guardar_control_versiones(control)
            
            print(f"Archivo descargado: {destino_local}")
        else:
            print("Usando versión local del archivo (sin cambios en Drive)")
            
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        raise 