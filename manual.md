# _______________________________________________________________________
# CONFIGURAR GOOGLE DRIVE
# _______________________________________________________________________

# Ingresar a Google Cloud Console
https://console.cloud.google.com/

# Paso 1: Crear un proyecto nuevo
 - nombre del proyecto: automatizar-archivos
 - ubicacion: sin organizacion

# Paso 2: Habilitar Google Drive API
Selecionar proyecto
Ingresar a la seccion "APIs y servicios/Biblioteca"
Buscar Google Drive API en el buscador y habilitarla

# NOTA: Pantalla de consentimiento
"Configurar pantalla de consentimiento" y "comenzar"

    Informacion de la app:
        - nombre de la aplicacion: automatizar archivos
        - correo de asistencia al usuario: xjuangalindox@gmail.com

    Publico:
        - usuarios externos

    Informacion de contacto:
        xjuangalindox@gmail.com

    Finalizar: 
        aceptar

# Paso 3: Configurar OAuth 2.0
Ingresar a la seccion APIs y servicios/Credenciales

Crear credencial "ID de cliente de OAuth"
    - tipo: "App de escritorio"
    - nombre: automatizar-archivos

Descargar archivo JSON (llave de acceso) y cambiar nombre:
    - credentials.json

# _______________________________________________________________________
# CONFIGURAR CONECCION DRIVE-PYTHON
# _______________________________________________________________________

from google.oauth2.credentials import Credentials # ✅ necesario para manejar credenciales
from google_auth_oauthlib.flow import InstalledAppFlow # ✅ necesario para iniciar sesión en Google
from google.auth.transport.requests import Request # ✅ refrescar token
from googleapiclient.discovery import build # ✅ conectar con Google Drive
import os

# Alcance: acceso completo a Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

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

# _______________________________________________________________________
# ERROR DE AUTENTICACION
# _______________________________________________________________________

# Configurar usuarios con acceso al proyecto
Ingresar a https://console.cloud.google.com/
Ingresar a la seccion APIs y servicios/Credenciales
Selecionar proyecto
Ingresar a la seccion "Pantalla de consentimiento de OAth"
Ingresar a la seccion "Publico"
Agregar usuarios de prueba (usuarios que tendran acceso al drive)

NOTA: despues de ejecutar la app, los usuarios de prueba se deben autenticar y confiar en el proyecto
MENSAJE EXISTOSO: The authentication flow has completed. You may close this window.

# _______________________________________________________________________
# CONFIGURAR PYTHON
# _______________________________________________________________________

# crear y activar entorno virtual (bash)
python -m venv venv
venv/Scripts/activate

# instalar librerias (bash)
./venv/Scripts/python.exe -m pip install google-auth-httplib2 google-auth-oauthlib google-api-python-client

# ejecutar script (bash)
python app.py

# _______________________________________________________________________
# CONFIGURAR VISUAL STUDIO CODE
# _______________________________________________________________________

# extensiones VSC
    - python