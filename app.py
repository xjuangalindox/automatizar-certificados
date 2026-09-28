import tkinter as tk
from tkinter import messagebox

from google.oauth2.credentials import Credentials # ✅ necesario para manejar credenciales
from google_auth_oauthlib.flow import InstalledAppFlow # ✅ necesario para iniciar sesión en Google
from google.auth.transport.requests import Request # ✅ refrescar token
from googleapiclient.discovery import build # ✅ conectar con Google Drive

import base64
from email.mime.text import MIMEText

import os

# Alcance: acceso completo a Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive', 
    'https://www.googleapis.com/auth/gmail.send'
]

# __________________________________________________________________________________

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def get_gmail_service():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('gmail', 'v1', credentials=creds)

# __________________________________________________________________________________

def send_email(service, to, subject, body_text):
    message = MIMEText(body_text)
    message['to'] = to
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}

    service.users().messages().send(userId='me', body=body).execute()

# __________________________________________________________________________________

def find_folder(service, folder_name):
    """Busca carpeta por nombre y devuelve su ID si existe"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    if folders:
        return folders[0]['id']  # devuelve el primero encontrado
    return None

# __________________________________________________________________________________

def create_folder(service, folder_name):
    """Crea carpeta en Drive y devuelve su ID"""
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

# __________________________________________________________________________________

def get_or_create_folder(service, folder_name):
    """Devuelve el ID de la carpeta, creándola si no existe"""
    folder_id = find_folder(service, folder_name)
    if folder_id:
        print(f"✔ La carpeta '{folder_name}' ya existe con ID: {folder_id}")
        return folder_id
    else:
        folder_id = create_folder(service, folder_name)
        print(f"➕ Se creó la carpeta '{folder_name}' con ID: {folder_id}")
        return folder_id

# __________________________________________________________________________________

def add_permission(service, folder_id, email):
    """Agrega permiso de escritura a un correo"""
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }
    try:
        service.permissions().create(
            fileId=folder_id, 
            body=permission, 
            sendNotificationEmail=True # True para que Google envíe aviso
        ).execute()
        print(f"✔ Permiso otorgado a {email}")

    except Exception as e:
        print(f"⚠ No se pudo dar permiso a {email}: {e}")

# __________________________________________________________________________________

def generar_carpetas():
    numero_control = entry_control.get().strip()
    correo_personal = entry_correo.get().strip()

    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return

    correo_institucional = f"{numero_control}@cuautla.tecnm.mx"

    # Coneccion con drive
    drive_service = get_drive_service()

    # Buscar carpetas del estudiante
    public_id = find_folder(drive_service, f"{numero_control}_public")
    private_id = find_folder(drive_service, f"{numero_control}_private")

    if public_id and private_id:
        # Ya existen → mostrar mensaje
        messagebox.showinfo("Aviso", f"Las carpetas ya fueron creadas anteriormente.\n"
                                     f"Pública ID: {public_id}\nPrivada ID: {private_id}")
        return

    # Generar carpetas
    public_id = create_folder(drive_service, f"{numero_control}_public")
    private_id = create_folder(drive_service, f"{numero_control}_private")

    # Establecer permisos y notificar
    add_permission(drive_service, public_id, correo_institucional)
    if correo_personal:
        add_permission(drive_service, public_id, correo_personal)
    
    # Mensaje exitoso
    messagebox.showinfo("Éxito", f"Carpetas creadas:\nPública ID: {public_id}\nPrivada ID: {private_id}")

    # Notificar
    notificar_carpetas()

    # Imprimir URLs en consola
    # print("Carpeta pública:", f"https://drive.google.com/drive/folders/{public_id}")
    # print("Carpeta privada:", f"https://drive.google.com/drive/folders/{private_id}")

# __________________________________________________________________________________

def notificar_carpetas():
    numero_control = entry_control.get().strip()
    correo_personal = entry_correo.get().strip()

    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return

    correo_institucional = f"{numero_control}@cuautla.tecnm.mx"

    # Coneccion con drive y gmail
    drive_service = get_drive_service()
    gmail_service = get_gmail_service()

    # Buscar carpetas del estudiante
    public_id = find_folder(drive_service, f"{numero_control}_public")
    private_id = find_folder(drive_service, f"{numero_control}_private")

    if not public_id or not private_id:
        # No existen -> mostrar mensaje
        messagebox.showerror("Error", "Las carpetas digitales no fueron encontradas. Primero debe generarlas antes de enviar la notificación.")
        return

    # Enlace carpeta publica
    public_url = f"https://drive.google.com/drive/folders/{public_id}"

    # Enviar correo personalizado con requisitos
    body = f"""Estimado estudiante,

    El Departamento de Servicios Escolares le informa que su carpeta digital ha sido creada correctamente. 
    Podrá acceder a ella desde el siguiente enlace:

    Carpeta digital: {public_url}

    A continuación se comparte el enlace con los pasos que deberá seguir para tramitar su certificado de licenciatura:

    Requisitos Certificado:
    https://sites.google.com/cuautla.tecnm.mx/serviciosescolares/certificado

    IMPORTANTE:
    Primero debe subir sus documentos a la carpeta digital para el trámite de certificado. 
    El personal de Servicios Escolares revisará sus documentos y, en caso de observaciones, se le notificará para que realice las correcciones necesarias. 
    Una vez que su certificado sea entregado, recibirá otra notificación para traer los documentos físicos y continuar con el trámite de titulación.

    Atentamente,
    Departamento de Servicios Escolares
    """

    # Notificar
    send_email(gmail_service, correo_institucional, "Notificación de Carpeta Digital - Departamento de Servicios Escolares", body)
    if correo_personal:
        send_email(gmail_service, correo_personal, "Notificación de Carpeta Digital - Departamento de Servicios Escolares", body)

    messagebox.showinfo("Éxito", "Se envió la notificación de carpeta digital y requisitos.")

# __________________________________________________________________________________

# Interfaz gráfica
root = tk.Tk()
root.title("Generar Carpeta Digital")

tk.Label(root, text="Número de control:").pack(pady=5)
entry_control = tk.Entry(root, width=30)
entry_control.pack(pady=5)

tk.Label(root, text="Correo personal (opcional):").pack(pady=5)
entry_correo = tk.Entry(root, width=30)
entry_correo.pack(pady=5)

# Botón para crear carpetas
tk.Button(root, text="Generar Carpeta Digital", command=generar_carpetas).pack(pady=20)

# Botón para notificar de carpetas
tk.Button(root, text="Notificar Carpeta Digital", command=notificar_carpetas).pack(pady=20)

root.mainloop()

# __________________________________________________________________________________














# def find_folder(service, folder_name):
#     query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
#     results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
#     files = results.get('files', [])
#     return files[0]['id'] if files else None

# def create_folder(service, folder_name):
#     folder_metadata = {
#         'name': folder_name,
#         'mimeType': 'application/vnd.google-apps.folder'
#     }
#     folder = service.files().create(body=folder_metadata, fields='id').execute()
#     return folder['id']

# Mapeo de tipos de archivo
# FOLDER_MAPPING = {
#     'application/pdf': 'PDFs',
#     'application/vnd.google-apps.document': 'Documentos_Google',
#     'application/vnd.google-apps.spreadsheet': 'Hojas_de_Calculo',
#     'application/vnd.google-apps.presentation': 'Presentaciones',
#     'image/jpeg': 'Imagenes',
#     'image/png': 'Imagenes',
#     'video/mp4': 'Videos',
#     'video/quicktime': 'Videos',
#     'application/zip': 'Archivos_Comprimidos',
# }
