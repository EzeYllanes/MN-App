import os
import io
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

# Descarga el archivo Excel más reciente con el nombre dado de la carpeta indicada

def descargar_excel_drive(carpeta_id, nombre_archivo, destino_local):
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
    print(f"Archivo descargado: {destino_local}") 