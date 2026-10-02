import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont

from google.oauth2.credentials import Credentials # ✅ necesario para manejar credenciales
from google_auth_oauthlib.flow import InstalledAppFlow # ✅ necesario para iniciar sesión en Google
from google.auth.transport.requests import Request # ✅ refrescar token
from googleapiclient.discovery import build # ✅ conectar con Google Drive

import base64
from email.mime.text import MIMEText

import os
import webbrowser

# Alcance: acceso completo a Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive', 
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets'
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

def get_sheets_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("sheets", "v4", credentials=creds)

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

# def get_or_create_folder(service, folder_name):
#     """Devuelve el ID de la carpeta, creándola si no existe"""
#     folder_id = find_folder(service, folder_name)
#     if folder_id:
#         print(f"✔ La carpeta '{folder_name}' ya existe con ID: {folder_id}")
#         return folder_id
#     else:
#         folder_id = create_folder(service, folder_name)
#         print(f"➕ Se creó la carpeta '{folder_name}' con ID: {folder_id}")
#         return folder_id

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

def generar_carpetas(entry_control, entry_correo):
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

# __________________________________________________________________________________

def notificar_carpetas(entry_control, entry_correo):
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

def eliminar_de_privada(entry_control, tabla_privada, tabla_publica):
    
    # Validar numero de control
    numero_control = entry_control.get().strip()
    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return

    # Obtener archivo seleccionado en tabla privada
    item_id = tabla_privada.focus()
    if not item_id:
        messagebox.showerror("Error", "Selecciona un archivo en la carpeta privada")
        return

    valores = tabla_privada.item(item_id, "values")
    archivo, size = valores
    # archivo, extension, estatus, acciones = valores

    # Busca el ID de Drive usando el nombre en el diccionario
    file_id = archivos_privados_dict.get(archivo)
    if not file_id:
        messagebox.showerror("Error", "No se encontró el archivo en el diccionario")
        return

    # Confirmar eliminación
    respuesta = messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar '{archivo}' de la carpeta privada?")
    if not respuesta:
        return

    # Coneccion con Drive
    drive_service = get_drive_service()

    # 🔥 Eliminar archivo
    drive_service.files().delete(fileId=file_id).execute()
    # messagebox.showinfo("Éxito", f"Archivo '{archivo}' eliminado de la carpeta privada.")

    # Refrescar tablas
    listar_archivos(entry_control, tabla_publica, tabla_privada)

# __________________________________________________________________________________

def copiar_a_privada(entry_control, tabla_publica, tabla_privada):

    # Validar numero de control
    numero_control = entry_control.get().strip()
    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return

    # drive_service = get_drive_service()
    # private_id = find_folder(drive_service, f"{numero_control}_private")

    # Obtener archivo seleccionado en tabla pública
    item_id = tabla_publica.focus()
    if not item_id:
        messagebox.showerror("Error", "Selecciona un archivo en la carpeta pública")
        return

    valores = tabla_publica.item(item_id, "values")
    archivo, size = valores

    # Busca el ID de Drive usando el nombre en el diccionario
    file_id = archivos_publicos_dict.get(archivo)
    if not file_id:
        messagebox.showerror("Error", "No se encontró el archivo en el diccionario")
        return

    # Coneccion con Drive
    drive_service = get_drive_service()

    # Obtener id de la carpeta privada
    private_id = find_folder(drive_service, f"{numero_control}_private")

    # Validar si existe la carpeta privada
    if not private_id:
        messagebox.showerror("Error", "No se encontró la carpeta privada")
        return

    # 🔎 Validar si ya existe en privada
    query = f"name='{archivo}' and '{private_id}' in parents and trashed=false"
    resultados = drive_service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute().get("files", [])

    if resultados:
        messagebox.showwarning("Aviso", f"El archivo '{archivo}' ya existe en la carpeta privada.")
        return

    # ➕ Copiar archivo a privada
    drive_service.files().copy(
        fileId=file_id,
        body={"parents": [private_id]}
    ).execute()

    # Mensaje Exitó
    # messagebox.showinfo("Éxito", f"Archivo '{archivo}' copiado a privada como '{copia['name']}'")

    # Opcional: refrescar tabla privada para mostrar el nuevo archivo
    listar_archivos(entry_control, tabla_publica, tabla_privada)

# __________________________________________________________________________________

def on_double_click_row(event, diccionario):
    tabla = event.widget # Tabla que disparó el evento

    item_id = tabla.focus() # ID interno de la fila seleccionada (ej. "I003")
    if not item_id:
        return

    valores = tabla.item(item_id, "values") # Obtiene valores de la fila (ej. ("documento.pdf", "1.2 MB"))
    archivo, size = valores # Nombre y tamaño del archivo

    # Busca el ID de Drive usando el nombre en el diccionario
    file_id = diccionario.get(archivo)

    if file_id:
        # Construye URL de visualización en Drive
        url = f"https://drive.google.com/file/d/{file_id}/view"
        webbrowser.open_new_tab(url) # Abre archivo en pestaña nueva
        print("Visualizando archivo:", archivo)
# __________________________________________________________________________________

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    elif size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.2f} KB"
    else:
        return f"{size_bytes/(1024**2):.2f} MB"

# __________________________________________________________________________________

def listar_archivos(entry_control, tabla_publica, tabla_privada):
    global control
    global archivos_publicos_dict, archivos_privados_dict

    archivos_publicos_dict = {}
    archivos_privados_dict = {}

    # Limpiar tablas antes de llenarlas
    for tabla in (tabla_publica, tabla_privada):
        for row in tabla.get_children():
            tabla.delete(row)

    numero_control = entry_control.get().strip()

    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return

    # Coneccion con drive
    drive_service = get_drive_service()

    # Buscar carpetas del estudiante
    public_id = find_folder(drive_service, f"{numero_control}_public")
    private_id = find_folder(drive_service, f"{numero_control}_private")

    if not public_id or not private_id:
        # No existen -> mostrar mensaje
        messagebox.showerror("Error", "Las carpetas digitales no fueron encontradas.")
        return

    # Listar archivos de carpeta pública
    archivos_publicos = drive_service.files().list(
        q=f"'{public_id}' in parents and trashed=false",
        fields="files(id, name, mimeType, size)"
    ).execute().get("files", [])

    # Listar archivos de carpeta privada
    archivos_privados = drive_service.files().list(
        q=f"'{private_id}' in parents and trashed=false",
        fields="files(id, name, mimeType, size)"
    ).execute().get("files", [])

    for archivo in archivos_publicos:
        file_id = archivo["id"]
        nombre = archivo["name"]
        size = format_size(int(archivo.get("size", 0)))

        tabla_publica.insert("", "end", values=(nombre, size))
        archivos_publicos_dict[nombre] = file_id # nombre_archivo: id_archivo

    for archivo in archivos_privados:
        file_id = archivo["id"]
        nombre = archivo["name"]
        size = format_size(int(archivo.get("size", 0)))

        tabla_privada.insert("", "end", values=(nombre, size))
        archivos_privados_dict[nombre] = file_id # nombre_archivo: id_archivo

# __________________________________________________________________________________

root = tk.Tk()
root.title("Gestión de Expedientes")
root.geometry("350x250")

# =====================================
# VENTANA CARPETA DIGITAL
# =====================================

def abrir_carpeta_digital():
    ventana = tk.Toplevel(root)
    ventana.title("Carpeta Digital")
    ventana.geometry("350x200")

    # ==========================================
    # FRAME: Control and Email
    # ==========================================

    # frame
    frame_control = tk.Frame(ventana)
    frame_control.pack(pady=5)

    tk.Label(frame_control, text="Número de control:").grid(row=0, column=0, padx=5, pady=5)
    entry_control = tk.Entry(frame_control, width=30)
    entry_control.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_control, text="Correo personal (opcional):").grid(row=1, column=0, padx=5, pady=5)
    entry_correo = tk.Entry(frame_control, width=30)
    entry_correo.grid(row=1, column=1, padx=5, pady=5)

    # ==========================================
    # FRAME: Buttons Acciones
    # ==========================================

    # frame
    frame_buttons = tk.Frame(ventana)
    frame_buttons.pack(pady=5)

    # Generar Carpeta Digital
    tk.Button(
        frame_buttons,
        text="Generar Carpeta Digital",
        command=lambda: generar_carpetas(entry_control, entry_correo)
    ).grid(row=0, column=0, padx=5, pady=5)

    # Notificar Carpeta Digital
    tk.Button(
        frame_buttons,
        text="Notificar Carpeta Digital",
        command=lambda: notificar_carpetas(entry_control, entry_correo)
    ).grid(row=0, column=1, padx=5, pady=5)

# __________________________________________________________________________________

def get_sheet_names(spreadsheet_id):
    """Devuelve lista de nombres de hojas de un spreadsheet"""
    sheets_service = get_sheets_service()
    metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return [sheet["properties"]["title"] for sheet in metadata["sheets"]]

# __________________________________________________________________________________

def botones_documentos(ventana):
    drive_service = get_drive_service()

    # Buscar archivo Especificaciones
    query = "name='Especificaciones' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        tk.Label(ventana, text="No se encontró la hoja de calculo Especificaciones").pack(pady=5)
        return

    # Obtener ID del archivo Especificaciones
    spreadsheet_id = files[0]["id"]

    # Obtener nombres de hojas
    hojas = get_sheet_names(spreadsheet_id)

    # Frame: contenedor especificaciones
    frame_documentos = tk.LabelFrame(ventana, text="Especificaciones")
    frame_documentos.pack(fill="x", expand=True, padx=5)

    # Frame: contenedor botones
    frame_botones = tk.Frame(frame_documentos)
    frame_botones.pack(anchor="center", pady=5)

    # Botones documentos
    for columna, hoja in enumerate(hojas):
        tk.Button(
            frame_botones,
            text=hoja,
            command=lambda h=hoja: abrir_especificaciones(h, spreadsheet_id)
        ).grid(row=0, column=columna, padx=5, pady=5)

# __________________________________________________________________________________

def leer_condiciones(nombre_hoja, spreadsheet_id):

    # Conectar con Sheets
    service = get_sheets_service()

    # Obtener rows del documento
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=nombre_hoja
    ).execute()

    # Validar filas (ID, Condicion, Especificacion, Activo)
    values = result.get("values", [])
    if not values:
        return []

    # Encabezados
    encabezados = values[0]

    # Índices de las columnas que nos interesan
    try:
        indice_id = encabezados.index("ID")
        indice_condicion = encabezados.index("Condicion")
    except ValueError:
        return []

    # filas finales (id, condicion)
    filas = []

    # Recorrer filas de datos
    for row in values[1:]:
        filas.append({
            "id": row[indice_id],
            "condicion": row[indice_condicion]
        })

    return filas

    # ______________

    # Buscar columnas ID y Condicion
    # encabezados = values[0]
    # try:
    #     idx_id = encabezados.index("ID")
    #     idx_cond = encabezados.index("Condicion")
    # except ValueError:
    #     return []

    # filas = []
    # for row in values[1:]:
    #     if len(row) > max(idx_id, idx_cond):
    #         filas.append({"id": row[idx_id], "condicion": row[idx_cond]})
    # return filas

# Diccionario global para guardar condiciones seleccionadas
condiciones_dict = {}

def abrir_especificaciones(nombre_hoja, spreadsheet_id):
    ventana = tk.Toplevel(root)
    ventana.title("Especificaciones")
    ventana.geometry("500x300")

    # Título
    tk.Label(ventana, text=f"{nombre_hoja}", font=("Arial", 12, "bold")).pack(pady=10)

    # frame: contenedor tabla
    frame_tabla = tk.LabelFrame(ventana, text="18680128")
    frame_tabla.pack(fill="both", expand=True, padx=5)

    # columnas
    columnas = ("id", "condicion", "notificar")

    # tabla
    tabla = ttk.Treeview(
        frame_tabla, 
        columns=columnas, 
        show="headings")
    tabla.pack(fill="both", expand=True)

    tabla.heading("id", text="ID")
    tabla.heading("condicion", text="Condición")
    tabla.heading("notificar", text="Notificar")

    tabla.column("id", width=100)
    tabla.column("condicion", width=250)
    tabla.column("notificar", width=150)

    # Leer datos del documento (id, condicion)
    datos = leer_condiciones(nombre_hoja, spreadsheet_id)

    # Insertar filas (validando contra condiciones_dict)
    for d in datos:
        tabla.insert("", "end", values=(d["id"], d["condicion"], "FALSE"))

    # for d in datos:
    #     estado_inicial = "TRUE" if nombre_hoja in condiciones_dict and d["id"] in condiciones_dict[nombre_hoja] else "FALSE"
    #     tabla.insert("", "end", values=(d["id"], d["condicion"], estado_inicial))

    # Alternar estado con doble clic
    # def toggle_estado(event):
    #     item_id = tabla.focus()
    #     if not item_id:
    #         return
    #     valores = tabla.item(item_id, "values")
    #     cond_id, cond_text, estado = valores

    #     nuevo_estado = "TRUE" if estado == "FALSE" else "FALSE"
    #     tabla.item(item_id, values=(cond_id, cond_text, nuevo_estado))

    #     # Actualizar diccionario global
    #     if nuevo_estado == "TRUE":
    #         condiciones_dict.setdefault(nombre_hoja, [])
    #         if cond_id not in condiciones_dict[nombre_hoja]:
    #             condiciones_dict[nombre_hoja].append(cond_id)
    #     else:
    #         if nombre_hoja in condiciones_dict and cond_id in condiciones_dict[nombre_hoja]:
    #             condiciones_dict[nombre_hoja].remove(cond_id)

    #     print("Diccionario actualizado:", condiciones_dict)

    # Event
    # tabla.bind("<Double-1>", toggle_estado)

    # Aquí defines qué hacer al abrir cada hoja
    print(f"Abrir hoja: {nombre_hoja}")

# =====================================
# VENTANA OBSERVACIONES
# =====================================

def abrir_observaciones():
    ventana = tk.Toplevel(root)
    ventana.title("Observaciones")
    ventana.geometry("1000x500")

    # ==========================================
    # FRAME: Número de control
    # ==========================================

    # Frame
    frame_control = tk.Frame(ventana)
    frame_control.pack(pady=5)

    # Label
    tk.Label(frame_control, text="Número de control:").grid(row=0, column=0, padx=5, pady=5)

    # Entry
    entry_control = tk.Entry(frame_control, width=15)
    entry_control.grid(row=0, column=1, padx=5, pady=5)

    # ==========================================
    # FRAME: Especificaciones
    # ==========================================

    # Crear botones de hojas de Especificaciones
    botones_documentos(ventana)

    # ==========================================
    # FRAME: Tablas pública y privada
    # ==========================================

    # Frame
    frame_tablas = tk.Frame(ventana)
    frame_tablas.pack(fill="both", expand=True, padx=10, pady=10)

    #Columns
    columnas = ("archivo", "size")

    # FRAME: Tabla pública
    frame_publica = tk.LabelFrame(frame_tablas, text="Carpeta Pública")
    frame_publica.pack(side="left", fill="both", expand=True, padx=5)

    # Tabla
    tabla_publica = ttk.Treeview(
        frame_publica,
        columns=columnas,
        show="headings"
    )

    # FRAME: Tabla privada
    frame_privada = tk.LabelFrame(frame_tablas, text="Carpeta Privada")
    frame_privada.pack(side="left", fill="both", expand=True, padx=5)

    # Tabla
    tabla_privada = ttk.Treeview(
        frame_privada,
        columns=columnas,
        show="headings"
    )

    # ==========================================
    # CONSTRUCCIÓN: Tablas pública y privada
    # ==========================================

    for tabla in (tabla_publica, tabla_privada):

        tabla.heading("archivo", text="Archivo")
        tabla.heading("size", text="Tamaño")

        tabla.column("archivo", width=250)
        tabla.column("size", width=50)

        tabla.pack(fill="both", expand=True, padx=5, pady=5)

    # ==========================================
    # FRAME: Buttons Acciones
    # ==========================================

    # Frame
    frame_acciones = tk.Frame(ventana)
    frame_acciones.pack(pady=5)

    # Button - copiar archivo a privada
    tk.Button(
        frame_acciones,
        text="Copiar a privada",
        command=lambda: copiar_a_privada(entry_control, tabla_publica, tabla_privada)
    ).grid(row=0, column=0, padx=5, pady=5)

    # Button - eliminar archivos de privada 
    tk.Button(
        frame_acciones,
        text="Eliminar de privada",
        command=lambda: eliminar_de_privada(entry_control, tabla_privada, tabla_publica)
    ).grid(row=0, column=1, padx=5, pady=5)

    # ==========================================
    # EVENTS
    # ==========================================

    # Entry control
    entry_control.bind(
        "<Return>",
        lambda event: listar_archivos(
            entry_control,
            tabla_publica,
            tabla_privada
        )
    )

    # Tabla pública
    tabla_publica.bind("<Double-1>", lambda event: on_double_click_row(event, archivos_publicos_dict))

    # Tabla privada
    tabla_privada.bind("<Double-1>", lambda event: on_double_click_row(event, archivos_privados_dict))


# =====================================
# VENTANA PRINCIPAL / MENÚ
# =====================================

tk.Label(
    root,
    text="Gestión de Expedientes",
    font=("Arial", 14, "bold")
).pack(pady=20)

tk.Button(
    root,
    text="Carpeta Digital",
    width=25,
    command=abrir_carpeta_digital
).pack(pady=10)

tk.Button(
    root,
    text="Observaciones",
    width=25,
    command=abrir_observaciones
).pack(pady=10)


root.mainloop()












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
