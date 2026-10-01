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

    # Imprimir URLs en consola
    # print("Carpeta pública:", f"https://drive.google.com/drive/folders/{public_id}")
    # print("Carpeta privada:", f"https://drive.google.com/drive/folders/{private_id}")

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
    numero_control = entry_control.get().strip()
    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return

    drive_service = get_drive_service()

    # Obtener archivo seleccionado en tabla privada
    item_id = tabla_privada.focus()
    if not item_id:
        messagebox.showerror("Error", "Selecciona un archivo en la carpeta privada")
        return

    valores = tabla_privada.item(item_id, "values")
    archivo, extension, estatus, acciones = valores
    file_id = archivos_privados_dict.get(archivo)

    if not file_id:
        messagebox.showerror("Error", "No se encontró el archivo en el diccionario")
        return

    # Confirmar eliminación
    respuesta = messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar '{archivo}' de la carpeta privada?")
    if not respuesta:
        return

    # 🔥 Eliminar archivo
    drive_service.files().delete(fileId=file_id).execute()
    messagebox.showinfo("Éxito", f"Archivo '{archivo}' eliminado de la carpeta privada.")

    # Refrescar tablas
    mostrar_archivos(entry_control, tabla_publica, tabla_privada)

# __________________________________________________________________________________

def copiar_a_privada(entry_control, tabla_publica, tabla_privada):
    numero_control = entry_control.get().strip()
    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return

    drive_service = get_drive_service()
    private_id = find_folder(drive_service, f"{numero_control}_private")

    # Obtener archivo seleccionado en tabla pública
    item_id = tabla_publica.focus()
    if not item_id:
        messagebox.showerror("Error", "Selecciona un archivo en la carpeta pública")
        return

    valores = tabla_publica.item(item_id, "values")
    archivo, extension, estatus, acciones = valores
    file_id = archivos_publicos_dict.get(archivo)

    if not file_id:
        messagebox.showerror("Error", "No se encontró el archivo en el diccionario")
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
    copia = drive_service.files().copy(
        fileId=file_id,
        body={"parents": [private_id]}
    ).execute()

    # Mensaje Exitó
    messagebox.showinfo("Éxito", f"Archivo '{archivo}' copiado a privada como '{copia['name']}'")

    # Opcional: refrescar tabla privada para mostrar el nuevo archivo
    mostrar_archivos(entry_control, tabla_publica, tabla_privada)

# __________________________________________________________________________________

def on_click_row(event, diccionario):
    tabla = event.widget   # el widget que disparó el evento

    item_id = tabla.focus()
    if not item_id:
        return

    valores = tabla.item(item_id, "values")
    archivo, extension, estatus, acciones = valores

    # Aquí deberías tener el ID del archivo de Drive
    # Supongamos que lo guardaste en un diccionario al llenar la tabla:
    file_id = diccionario.get(archivo)

    if file_id:
        # URL de visualización en Google Drive
        url = f"https://drive.google.com/file/d/{file_id}/view"
        webbrowser.open_new_tab(url)  # abre en pestaña nueva
        print("Visualizando archivo:", archivo)
# __________________________________________________________________________________

def mostrar_archivos(entry_control, tabla_publica, tabla_privada):
    global archivos_publicos_dict, archivos_privados_dict

    archivos_publicos_dict = {}
    archivos_privados_dict = {}

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
        messagebox.showerror("Error", "Las carpetas digitales no fueron encontradas. Primero debe generarlas antes de enviar la notificación.")
        return

    # Limpiar tablas antes de llenarlas
    for tabla in (tabla_publica, tabla_privada):
        for row in tabla.get_children():
            tabla.delete(row)
    
    # Listar archivos de carpeta pública
    archivos_publicos = drive_service.files().list(
        q=f"'{public_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute().get("files", [])

    # archivos_publicos_dict = {}
    for archivo in archivos_publicos:
        file_id = archivo["id"]
        nombre = archivo["name"]
        extension = nombre.split(".")[-1] if "." in nombre else ""
        estatus = "Disponible"  # aquí puedes poner lógica real
        acciones = ""           # columna vacía por ahora
        tabla_publica.insert("", "end", values=(nombre, extension, estatus, acciones))
        
        archivos_publicos_dict[nombre] = file_id

    # Listar archivos de carpeta privada
    archivos_privados = drive_service.files().list(
        q=f"'{private_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)"
    ).execute().get("files", [])

    for archivo in archivos_privados:
        file_id = archivo["id"]
        nombre = archivo["name"]
        extension = nombre.split(".")[-1] if "." in nombre else ""
        estatus = "Disponible"
        acciones = ""
        tabla_privada.insert("", "end", values=(nombre, extension, estatus, acciones))

        archivos_privados_dict[nombre] = file_id

# __________________________________________________________________________________

# Interfaz gráfica
# root = tk.Tk()
# root.title("Generar Carpeta Digital")

# tk.Label(root, text="Número de control:").pack(pady=5)
# entry_control = tk.Entry(root, width=30)
# entry_control.pack(pady=5)

# tk.Label(root, text="Correo personal (opcional):").pack(pady=5)
# entry_correo = tk.Entry(root, width=30)
# entry_correo.pack(pady=5)

# # Botón para crear carpetas
# tk.Button(root, text="Generar Carpeta Digital", command=generar_carpetas).pack(pady=20)

# # Botón para notificar de carpetas
# tk.Button(root, text="Notificar Carpeta Digital", command=notificar_carpetas).pack(pady=20)

# root.mainloop()

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
    ventana.geometry("350x300")

    tk.Label(ventana, text="Número de control:").pack(pady=5)
    entry_control = tk.Entry(ventana, width=30)
    entry_control.pack(pady=5)

    tk.Label(ventana, text="Correo personal (opcional):").pack(pady=5)
    entry_correo = tk.Entry(ventana, width=30)
    entry_correo.pack(pady=5)

    tk.Button(
        ventana,
        text="Generar Carpeta Digital",
        command=lambda: generar_carpetas(entry_control, entry_correo)
        # command=generar_carpetas
    ).pack(pady=15)

    tk.Button(
        ventana,
        text="Notificar Carpeta Digital",
        command=lambda: notificar_carpetas(entry_control, entry_correo)
        # command=notificar_carpetas
    ).pack(pady=5)

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
        tk.Label(ventana, text="No se encontró el archivo Especificaciones").pack(pady=5)
        return

    # Obtener ID del archivo Especificaciones
    spreadsheet_id = files[0]["id"]

    # Obtener nombres de hojas
    hojas = get_sheet_names(spreadsheet_id)

    # Crear botones dinámicos
    for hoja in hojas:
        tk.Button(
            ventana,
            text=hoja,
            command=lambda h=hoja: abrir_especificaciones(h, spreadsheet_id)
        ).pack(pady=5)

# __________________________________________________________________________________

def leer_condiciones(nombre_hoja, spreadsheet_id):
    service = get_sheets_service()  # usa tus credenciales
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=nombre_hoja
    ).execute()

    values = result.get("values", [])
    if not values:
        return []

    # Buscar columnas ID y Condicion
    encabezados = values[0]
    try:
        idx_id = encabezados.index("ID")
        idx_cond = encabezados.index("Condicion")
    except ValueError:
        return []

    filas = []
    for row in values[1:]:
        if len(row) > max(idx_id, idx_cond):
            filas.append({"id": row[idx_id], "condicion": row[idx_cond]})
    return filas

# Diccionario global para guardar condiciones seleccionadas
condiciones_dict = {}

def abrir_especificaciones(nombre_hoja, spreadsheet_id):
    ventana = tk.Toplevel(root)
    ventana.title("Observaciones")
    ventana.geometry("500x300")

    # Título
    tk.Label(ventana, text=f"{nombre_hoja}", font=("Arial", 12, "bold")).pack(pady=10)

    # Frame para tabla
    frame_tabla = tk.Frame(ventana)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

    columnas = ("id", "condicion", "estado")

    # Crear tabla
    tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    tabla.pack(fill="both", expand=True)

    # Configurar encabezados
    # for col in columnas:
    #     tabla.heading(col, text=col.capitalize())

    # Fuente usada en la tabla
    # font = tkFont.nametofont("TkDefaultFont")

    # Insertar filas y calcular ancho máximo
    # max_widths = {col: len(col) for col in columnas}  # empieza con el ancho del encabezado

    tabla.heading("id", text="ID")
    tabla.heading("condicion", text="Condición")
    tabla.heading("estado", text="Estado")

    tabla.column("id", width=100)
    tabla.column("condicion", width=250)
    tabla.column("estado", width=150)

    # Leer datos de la hoja Especificaciones
    datos = leer_condiciones(nombre_hoja, spreadsheet_id)

    # Insertar filas validando contra condiciones_dict
    for d in datos:
        estado_inicial = "TRUE" if nombre_hoja in condiciones_dict and d["id"] in condiciones_dict[nombre_hoja] else "FALSE"
        tabla.insert("", "end", values=(d["id"], d["condicion"], estado_inicial))

        # Calcular ancho de cada columna según texto
        # max_widths["id"] = max(max_widths["id"], font.measure(d["id"]))
        # max_widths["condicion"] = max(max_widths["condicion"], font.measure(d["condicion"]))
        # max_widths["estado"] = max(max_widths["estado"], font.measure(estado_inicial))

    # Aplicar ancho calculado y centrar texto
    # for col in columnas:
    #     tabla.column(col, width=max_widths[col] + 20, anchor="center")  # +20 para padding

    # Alternar estado con doble clic
    def toggle_estado(event):
        item_id = tabla.focus()
        if not item_id:
            return
        valores = tabla.item(item_id, "values")
        cond_id, cond_text, estado = valores

        nuevo_estado = "TRUE" if estado == "FALSE" else "FALSE"
        tabla.item(item_id, values=(cond_id, cond_text, nuevo_estado))

        # Actualizar diccionario global
        if nuevo_estado == "TRUE":
            condiciones_dict.setdefault(nombre_hoja, [])
            if cond_id not in condiciones_dict[nombre_hoja]:
                condiciones_dict[nombre_hoja].append(cond_id)
        else:
            if nombre_hoja in condiciones_dict and cond_id in condiciones_dict[nombre_hoja]:
                condiciones_dict[nombre_hoja].remove(cond_id)

        print("Diccionario actualizado:", condiciones_dict)

    tabla.bind("<Double-1>", toggle_estado)


    # Titulo documento (nombre_hoja)

    # Crear una tabla con el id y la condicion de la hoja (columnas)

    # Cada row o fila o condicion puede ser marcado o desmarcado (alomejor un combobox o no recuerdo como se llamaba)

    # En un diccionario meter el nombre del documento y el id de la condicion

    # Si el admin marca una condicion guardar el id pero si desmarca la condicion, eliminar el id
    

    # Aquí defines qué hacer al abrir cada hoja
    print(f"Abrir hoja: {nombre_hoja}")

# =====================================
# VENTANA OBSERVACIONES
# =====================================

def abrir_observaciones():

    ventana = tk.Toplevel(root)
    ventana.title("Observaciones")
    ventana.geometry("1000x500")

    tk.Label(ventana, text="Número de control:").pack(pady=5)

    entry_control = tk.Entry(ventana, width=30)
    entry_control.pack(pady=5)

    frame_tablas = tk.Frame(ventana)
    frame_tablas.pack(fill="both", expand=True, padx=10, pady=10)

    columnas = ("archivo", "acciones")
    columnas = ("archivo", "extension", "estatus", "acciones")

    # Carpeta pública
    frame_publica = tk.LabelFrame(frame_tablas, text="Carpeta Pública")
    frame_publica.pack(side="left", fill="both", expand=True, padx=5)

    tabla_publica = ttk.Treeview(
        frame_publica,
        columns=columnas,
        show="headings"
    )

    # Enlazar evento de clic
    tabla_publica.bind("<Double-1>", lambda event: on_click_row(event, archivos_publicos_dict))

    # Carpeta privada
    frame_privada = tk.LabelFrame(frame_tablas, text="Carpeta Privada")
    frame_privada.pack(side="left", fill="both", expand=True, padx=5)

    tabla_privada = ttk.Treeview(
        frame_privada,
        columns=columnas,
        show="headings"
    )

    # Enlazar evento de clic
    tabla_privada.bind("<Double-1>", lambda event: on_click_row(event, archivos_privados_dict))

    for tabla in (tabla_publica, tabla_privada):

        tabla.heading("archivo", text="Archivo")
        tabla.heading("extension", text="Extensión")
        tabla.heading("estatus", text="Estatus")
        tabla.heading("acciones", text="Acciones")

        tabla.column("archivo", width=150)
        tabla.column("extension", width=80)
        tabla.column("estatus", width=100)
        tabla.column("acciones", width=120)

        tabla.pack(fill="both", expand=True, padx=5, pady=5)

    # Botón para mostrar archivos
    tk.Button(
        ventana,
        text="Mostrar archivos",
        command=lambda: mostrar_archivos(entry_control, tabla_publica, tabla_privada)
    ).pack(pady=15)

    # Botón para copiar archivo seleccionado de pública a privada
    tk.Button(
        ventana,
        text="Copiar a privada",
        command=lambda: copiar_a_privada(entry_control, tabla_publica, tabla_privada)
    ).pack(pady=10)

    # Botón para eliminar archivos de privada 
    tk.Button(
        ventana,
        text="Eliminar de privada",
        command=lambda: eliminar_de_privada(entry_control, tabla_privada, tabla_publica)
    ).pack(pady=10)

    # Crear botones de hojas de Especificaciones
    botones_documentos(ventana)


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
