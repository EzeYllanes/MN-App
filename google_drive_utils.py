import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Inicializa el servicio de Google Drive

def get_drive_service():
    creds = None
    if os.path.exists('token_drive.pickle'):
        with open('token_drive.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_drive.pickle', 'wb') as token:
            pickle.dump(creds, token)
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