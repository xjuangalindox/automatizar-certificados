import tkinter as tk
from tkinter import ttk, messagebox
# import tkinter.font as tkFont

from google.oauth2.credentials import Credentials # ✅ necesario para manejar credenciales
from google_auth_oauthlib.flow import InstalledAppFlow # ✅ necesario para iniciar sesión en Google
from google.auth.transport.requests import Request # ✅ refrescar token
from googleapiclient.discovery import build # ✅ conectar con Google Drive

import base64
from email.mime.text import MIMEText

import os
import webbrowser

from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
# from fpdf import FPDF

# Variables globales
service_drive = None
service_gmail = None
service_sheets = None

dicc_archivos_publicos = {}
dicc_archivos_privados = {}
dicc_especificaciones = {}

id_carpeta_publica = None
id_carpeta_privada = None

def init_google_services():
    global service_drive, service_gmail, service_sheets

    # Alcance: acceso completo a Drive
    SCOPES = [
        'https://www.googleapis.com/auth/drive', 
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/spreadsheets'
    ]

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

    # Crear servicios una sola vez
    service_drive = build('drive', 'v3', credentials=creds)
    service_gmail = build('gmail', 'v1', credentials=creds)
    service_sheets = build('sheets', 'v4', credentials=creds)
# __________________________________________________________________________________

def send_email(to, subject, body_text):
    message = MIMEText(body_text)
    message['to'] = to
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}

    service_gmail.users().messages().send(userId='me', body=body).execute()
# __________________________________________________________________________________

def find_folder(folder_name):
    """Busca carpeta por nombre y devuelve su ID si existe"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service_drive.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    if folders:
        return folders[0]['id']  # devuelve el primero encontrado
    return None
# __________________________________________________________________________________

def create_folder(folder_name):
    """Crea carpeta en Drive y devuelve su ID"""
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service_drive.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']
# __________________________________________________________________________________

def add_permission(folder_id, email):
    """Agrega permiso de escritura a un correo"""
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }
    try:
        service_drive.permissions().create(
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
    # drive_service = get_drive_service()

    # Buscar carpetas del estudiante
    public_id = find_folder(f"{numero_control}_public")
    private_id = find_folder(f"{numero_control}_private")

    if public_id and private_id:
        # Ya existen → mostrar mensaje
        messagebox.showinfo("Aviso", f"Las carpetas ya fueron creadas anteriormente.\n"
                                     f"Pública ID: {public_id}\nPrivada ID: {private_id}")
        return

    # Generar carpetas
    public_id = create_folder(f"{numero_control}_public")
    private_id = create_folder(f"{numero_control}_private")

    # Establecer permisos y notificar
    add_permission(public_id, correo_institucional)
    if correo_personal:
        add_permission(public_id, correo_personal)
    
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
    # drive_service = get_drive_service()
    # gmail_service = get_gmail_service()

    # Buscar carpetas del estudiante
    public_id = find_folder(f"{numero_control}_public")
    private_id = find_folder(f"{numero_control}_private")

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
    send_email(correo_institucional, "Notificación de Carpeta Digital - Departamento de Servicios Escolares", body)
    if correo_personal:
        send_email(correo_personal, "Notificación de Carpeta Digital - Departamento de Servicios Escolares", body)

    messagebox.showinfo("Éxito", "Se envió la notificación de carpeta digital y requisitos.")
# __________________________________________________________________________________

def eliminar_de_privada(entry_control, tabla_privada):

    # Validar numero de control
    numero_control = validate_control(entry_control)
    if not numero_control:
        return

    # Obtener archivo seleccionado en tabla privada
    item_id = tabla_privada.focus()
    if not item_id:
        messagebox.showerror("Error", "Selecciona un archivo en la carpeta privada.")
        return

    valores = tabla_privada.item(item_id, "values")
    archivo, size = valores

    # Busca el ID de Drive usando el nombre en el diccionario
    file_id = dicc_archivos_privados.get(archivo)
    if not file_id:
        messagebox.showerror("Error", "No se encontró el archivo en el diccionario.")
        return

    # Confirmar eliminación
    respuesta = messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar '{archivo}' de la carpeta privada?")
    if not respuesta:
        return

    # 🔥 Eliminar archivo y refrescar tabla
    service_drive.files().delete(fileId=file_id).execute()

    # Refrescar tabla privada
    reset_tabla(f"{numero_control}_private", tabla_privada, "privada")
# __________________________________________________________________________________

def copiar_a_privada(entry_control, tabla_publica, tabla_privada):

    # Validar numero de control
    numero_control = validate_control(entry_control)
    if not numero_control:
        return

    # Obtener archivo seleccionado en tabla pública
    item_id = tabla_publica.focus()
    if not item_id:
        messagebox.showerror("Error", "Selecciona un archivo en la carpeta pública.")
        return

    valores = tabla_publica.item(item_id, "values")
    archivo, size = valores

    # Busca el ID de Drive usando el nombre en el diccionario
    file_id = dicc_archivos_publicos.get(archivo)
    if not file_id:
        messagebox.showerror("Error", "No se encontró el archivo en el diccionario.")
        return

    # Validar si carpeta privada existe
    if not id_carpeta_privada:
        messagebox.showerror("Error", "La carpeta privada no fue encontrada.")
        return

    # 🔎 Validar si el archivo ya existe en privada
    query = f"name='{archivo}' and '{id_carpeta_privada}' in parents and trashed=false"
    resultados = service_drive.files().list(
        q=query,
        fields="files(id, name)"
    ).execute().get("files", [])

    if resultados:
        messagebox.showwarning("Aviso", f"El archivo '{archivo}' ya existe en la carpeta privada.")
        return

    # ➕ Copiar archivo publico a privada
    service_drive.files().copy(
        fileId=file_id,
        body={"parents": [id_carpeta_privada]}
    ).execute()

    # Refrescar tabla privada
    reset_tabla(f"{numero_control}_private", tabla_privada, "privada")
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

def reset_tabla(nombre_carpeta, tabla, tipo="publica"):
    global dicc_archivos_publicos, dicc_archivos_privados
    global id_carpeta_publica, id_carpeta_privada

    # Limpiar tabla
    for row in tabla.get_children():
        tabla.delete(row)

    # Buscar carpeta_id
    id_carpeta = find_folder(nombre_carpeta) # 18680128_public o 18680128_privada

    # Validar carpeta_id
    if not id_carpeta:
        messagebox.showerror("Error", f"La carpeta digital {tipo} no fue encontrada.")
        return

    # Guardar ID en global según tipo
    if tipo == "publica":
        id_carpeta_publica = id_carpeta
        dicc_archivos_publicos = {}
    else:
        id_carpeta_privada = id_carpeta
        dicc_archivos_privados = {}

    # Buscar archivos de la carpeta
    archivos = service_drive.files().list(
        q=f"'{id_carpeta}' in parents and trashed=false",
        fields="files(id, name, mimeType, size)"
    ).execute().get("files", [])

    # Insertar archivos a la tabla y llenar diccionario
    for archivo in archivos:
        file_id = archivo["id"] # id archivo
        nombre = archivo["name"] # nombre archivo
        size = format_size(int(archivo.get("size", 0))) # tamaño archivo

        tabla.insert("", "end", values=(nombre, size))

        if tipo == "publica":
            dicc_archivos_publicos[nombre] = file_id
        else:
            dicc_archivos_privados[nombre] = file_id

    print(f"📦 Diccionario Archivos Publicos Lleno: {dicc_archivos_publicos}")
    print(f"📦 Diccionario Archivos Privados Lleno: {dicc_archivos_privados}")
# __________________________________________________________________________________

def listar_archivos(entry_control, tabla_publica, tabla_privada):
    global dicc_especificaciones
    dicc_especificaciones = {}
    print(f"🗑️ Diccionario Especificaciones reiniciado: {dicc_especificaciones}")

    # Validar numero de control
    numero_control = validate_control(entry_control)
    if not numero_control:
        return

    reset_tabla(f"{numero_control}_public", tabla_publica, "publica")
    reset_tabla(f"{numero_control}_private", tabla_privada, "privada")
# __________________________________________________________________________________

def validate_control(entry_control):
    numero_control = entry_control.get().strip()

    if not numero_control:
        messagebox.showerror("Error", "Debes ingresar el número de control")
        return       

    return numero_control 
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
    frame_control.pack(fill="x", expand=True, padx=10, pady=10)

    # numero de control
    tk.Label(frame_control, text="Número de control *").grid(row=0, column=0, padx=5, pady=5)
    entry_control = tk.Entry(frame_control, width=30)
    entry_control.grid(row=0, column=1, padx=5, pady=5)

    # correo personal (opcional)
    tk.Label(frame_control, text="Correo personal").grid(row=1, column=0, padx=5, pady=5)
    entry_correo = tk.Entry(frame_control, width=30)
    entry_correo.grid(row=1, column=1, padx=5, pady=5)

    # ==========================================
    # FRAME: Buttons Acciones
    # ==========================================

    # frame
    frame_buttons = tk.Frame(ventana)
    frame_buttons.pack(anchor="center", padx=10, pady=10)

    # Generar Carpeta Digital
    tk.Button(
        frame_buttons,
        text="Generar Carpeta Digital",
        command=lambda: generar_carpetas(entry_control, entry_correo)
    ).grid(row=0, column=0, padx=5, pady=5)

    # Notificar Carpeta Digital
    tk.Button(
        frame_buttons,
        text="Notificar Al Estudiante",
        command=lambda: notificar_carpetas(entry_control, entry_correo)
    ).grid(row=0, column=1, padx=5, pady=5)

# __________________________________________________________________________________

def get_sheet_names(spreadsheet_id):
    """Devuelve lista de nombres de hojas de un spreadsheet"""
    metadata = service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return [sheet["properties"]["title"] for sheet in metadata["sheets"]]

# __________________________________________________________________________________

def botones_documentos(ventana, entry_control):

    # Frame: contenedor especificaciones
    frame_documentos = tk.LabelFrame(ventana, text="Especificaciones")
    frame_documentos.pack(fill="x", expand=True, padx=10, pady=10)

    # Buscar archivo Especificaciones
    query = "name='Especificaciones' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    results = service_drive.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    # Mostrar mensaje (si no existen especificaciones)
    if not files:
        tk.Label(frame_documentos, text="No se encontró la hoja de calculo Especificaciones").pack(pady=5, padx=5)
        return

    # Obtener ID del archivo Especificaciones
    spreadsheet_id = files[0]["id"]

    # Obtener nombres de hojas
    hojas = get_sheet_names(spreadsheet_id)

    # Frame: contenedor botones
    frame_botones = tk.Frame(frame_documentos)
    frame_botones.pack(anchor="center", pady=5)

    # Botones documentos
    for columna, hoja in enumerate(hojas):
        tk.Button(
            frame_botones,
            text=hoja,
            command=lambda h=hoja: abrir_especificaciones(entry_control, h, spreadsheet_id)
        ).grid(row=0, column=columna, padx=5, pady=5)

# __________________________________________________________________________________

def leer_condiciones(nombre_hoja, spreadsheet_id):

    # Obtener rows del documento
    result = service_sheets.spreadsheets().values().get(
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
        indice_activo = encabezados.index("Activo")

    except ValueError:
        return []

    # filas finales (id, condicion)
    filas = []

    # Recorrer filas de datos
    for row in values[1:]:

        # Solo incluir si Activo == "TRUE"
        if row[indice_activo].strip().upper() == "TRUE":
            filas.append({
                "id": row[indice_id],
                "condicion": row[indice_condicion]
            })

    return filas
# __________________________________________________________________________________

def abrir_especificaciones(entry_control, nombre_hoja, spreadsheet_id):
    # Validar numero de control
    numero_control = validate_control(entry_control)
    if not numero_control:
        return

    # Validate carpetas
    # public_id = find_folder(f"{numero_control}_public")
    # private_id = find_folder(f"{numero_control}_private")

    # if not public_id or not private_id:
    #     messagebox.showerror("Error", "Las carpetas digitales no fueron encontradas.")
    #     return

    ventana = tk.Toplevel(root)
    ventana.title("Especificaciones")
    ventana.geometry("500x400")

    # Título
    tk.Label(ventana, text=f"{nombre_hoja}", font=("Arial", 12, "bold")).pack(pady=10)

    # frame: contenedor tabla
    frame_tabla = tk.LabelFrame(ventana, text = numero_control)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

    # columnas
    columnas = ("id", "condicion", "notificar")

    # tabla
    tabla = ttk.Treeview(
        frame_tabla, 
        columns=columnas, 
        show="headings")
    tabla.pack(fill="both", expand=True, padx=5, pady=5)

    tabla.heading("id", text="ID")
    tabla.heading("condicion", text="Condición")
    tabla.heading("notificar", text="Notificar")

    tabla.column("id", width=100, anchor="center")
    tabla.column("condicion", width=250, anchor="center")
    tabla.column("notificar", width=150, anchor="center")

    # Leer datos del documento (id, condicion)
    datos = leer_condiciones(nombre_hoja, spreadsheet_id)

    # Insertar filas (validando contra condiciones_dict)
    # for d in datos:
    #     tabla.insert("", "end", values=(d["id"], d["condicion"], "FALSE"))

    # Configurar estilos de fila
    tabla.tag_configure("activo", background="lightcoral")
    tabla.tag_configure("inactivo", background="lightgreen")
    # tabla.tag_configure("inactivo", background="lightcoral")

    # Insertar filas con color según estado
    for d in datos:
        estado_inicial = "TRUE" if nombre_hoja in dicc_especificaciones and d["id"] in dicc_especificaciones[nombre_hoja] else "FALSE"
        tag = "activo" if estado_inicial == "TRUE" else "inactivo"
        tabla.insert("", "end", values=(d["id"], d["condicion"], estado_inicial), tags=(tag,))

    # Alternar estado con doble clic
    # Alternar estado con doble clic
    def toggle_estado(event):
        item_id = tabla.focus()
        if not item_id:
            return
        cond_id, cond_text, estado = tabla.item(item_id, "values")

        nuevo_estado = "TRUE" if estado == "FALSE" else "FALSE"
        nuevo_tag = "activo" if nuevo_estado == "TRUE" else "inactivo"

        # Actualizar valores y color
        tabla.item(item_id, values=(cond_id, cond_text, nuevo_estado), tags=(nuevo_tag,))

        # Actualizar diccionario global
        if nuevo_estado == "TRUE":
            dicc_especificaciones.setdefault(nombre_hoja, [])
            if cond_id not in dicc_especificaciones[nombre_hoja]:
                dicc_especificaciones[nombre_hoja].append(cond_id)
        else:
            if nombre_hoja in dicc_especificaciones and cond_id in dicc_especificaciones[nombre_hoja]:
                dicc_especificaciones[nombre_hoja].remove(cond_id)

        print("Diccionario actualizado:", dicc_especificaciones)

        # Quitar selección azul
        tabla.selection_remove(item_id)
        
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
    #         dicc_especificaciones.setdefault(nombre_hoja, [])
    #         if cond_id not in dicc_especificaciones[nombre_hoja]:
    #             dicc_especificaciones[nombre_hoja].append(cond_id)
    #     else:
    #         if nombre_hoja in dicc_especificaciones and cond_id in dicc_especificaciones[nombre_hoja]:
    #             dicc_especificaciones[nombre_hoja].remove(cond_id)

    #     print("Diccionario actualizado:", dicc_especificaciones)

    # Event
    tabla.bind("<Double-1>", toggle_estado)

    # Aquí defines qué hacer al abrir cada hoja
    print(f"Abrir hoja: {nombre_hoja}")

def generar_reporte(diccionario, nombre_archivo="reporte.pdf", vista_previa=False):
    c = canvas.Canvas(nombre_archivo, pagesize=LETTER)
    width, height = LETTER

    # Encabezado
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 50, "Observaciones de documentos enviados")
    c.drawString(50, height - 70, f"Fecha de revisión: {fecha_actual}")

    y = height - 100

    for hoja, ids in diccionario.items():
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, hoja)
        y -= 20

        if not ids:
            c.setFont("Helvetica", 12)
            c.drawString(70, y, "Documento Correcto ✅")
            y -= 20
        else:
            c.setFont("Helvetica", 12)
            for i, cond_id in enumerate(ids, start=1):
                # Aquí deberías mapear cond_id → mensaje completo desde tu tabla de condiciones
                mensaje = dicc_especificaciones.get(cond_id, "Observación no encontrada")
                c.drawString(70, y, f"{i}. {mensaje}")
                y -= 20

    # Mensaje final
    c.setFont("Helvetica", 12)
    c.drawString(50, y - 20, "Favor de corregir los documentos con observaciones y reemplazarlos por los existentes.")
    c.drawString(50, y - 40, "Mantener los documentos correctos en la carpeta digital.")

    # Guardar archivo
    c.save()

    # Abrir vista previa si corresponde
    if vista_previa:
        os.startfile(nombre_archivo)  # en Windows abre el PDF con el visor predeterminado

    

# def generar_reporte(diccionario, nombre_archivo="reporte.pdf", vista_previa=False):
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)

#     # Encabezado
#     fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#     pdf.multi_cell(0, 10, f"Observaciones de documentos enviados\nFecha de revisión: {fecha_actual}\n")

#     # Recorrer todas las hojas (documentos)
#     for hoja, ids in diccionario.items():
#         pdf.set_font("Arial", "B", 12)
#         pdf.cell(0, 10, hoja, ln=True)

#         if not ids:  # sin observaciones
#             pdf.set_font("Arial", size=12)
#             pdf.cell(0, 10, "Documento Correcto [OK]", ln=True)
#         else:
#             pdf.set_font("Arial", size=12)
#             for i, cond_id in enumerate(ids, start=1):
#                 # Aquí deberías mapear cond_id → mensaje completo desde tu tabla de condiciones
#                 mensaje = dicc_especificaciones.get(cond_id, "Observación no encontrada")
#                 pdf.multi_cell(0, 10, f"{i}. {mensaje}")

#         pdf.ln(5)

#     # Mensaje final
#     pdf.multi_cell(0, 10, "Favor de corregir los documentos con observaciones y reemplazarlos por los existentes. Mantener los documentos correctos en la carpeta digital.")

#     # Guardar archivo
#     pdf.output(nombre_archivo)

#     # Abrir vista previa si corresponde
#     if vista_previa:
#         os.startfile(nombre_archivo)  # en Windows abre el PDF con el visor predeterminado
# __________________________________________________________________________________
# =====================================
# VENTANA OBSERVACIONES
# =====================================

def abrir_observaciones():
    ventana = tk.Toplevel(root)
    ventana.title("Observaciones")
    ventana.geometry("1000x500")

    # ==========================================
    # FRAME: Encabezado (Estudiante y Reporte)
    # ==========================================    
    frame_encabezado = tk.Frame(ventana)
    frame_encabezado.pack(fill="x", expand=True, padx=10, pady=10)

    # ==========================================
    # FRAMELABEL: Estudiante
    # ==========================================
    frame_control = tk.LabelFrame(frame_encabezado, text="Estudiante")
    frame_control.pack(side="left", fill="x", anchor="center", expand=True, padx=5, pady=5)

    # Label
    tk.Label(frame_control, text="Número de control:").grid(row=0, column=0, padx=5, pady=5)

    # Entry
    entry_control = tk.Entry(frame_control, width=15)
    entry_control.grid(row=0, column=1, padx=5, pady=5)

    # ==========================================
    # FRAMELABEL: Reporte
    # ==========================================
    frame_reporte = tk.LabelFrame(frame_encabezado, text="Reporte")
    frame_reporte.pack(side="right", fill="x", anchor="center", expand=True, padx=5, pady=5)

    # Button: preview
    tk.Button(
        frame_reporte, 
        text="Vista Previa",
        command=lambda: generar_reporte(dicc_especificaciones, "preview.pdf", True)
    ).grid(row=0, column=0, padx=5, pady=5)

    tk.Button(
        frame_reporte,
        text="Generar Reporte",
        command=lambda: generar_reporte(dicc_especificaciones, "reporte_final.pdf")
    ).grid(row=0, column=1, padx=5, pady=5)

    # ==========================================
    # FRAME: Reporte
    # ==========================================

    # ==========================================
    # FRAME: Especificaciones
    # ==========================================

    # Crear botones de hojas de Especificaciones
    botones_documentos(ventana, entry_control)

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
    frame_privada.pack(side="right", fill="both", expand=True, padx=5)

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

        tabla.column("archivo", width=250, anchor="center")
        tabla.column("size", width=50, anchor="center")

        tabla.pack(fill="both", expand=True, padx=5, pady=5)

    # ==========================================
    # FRAME: Buttons Acciones - Publica
    # ==========================================

    # Frame: buttons publico
    frame_buttons_publica = tk.Frame(frame_publica)
    frame_buttons_publica.pack(pady=5)

    # Button - copiar archivo a privada
    tk.Button(
        frame_buttons_publica,
        text="Copiar a privada",
        command=lambda: copiar_a_privada(entry_control, tabla_publica, tabla_privada)
    ).grid(row=0, column=0, padx=5, pady=5)

    # ==========================================
    # FRAME: Buttons Acciones - Privada
    # ==========================================

    # Frame: buttons privada
    frame_buttons_privada = tk.Frame(frame_privada)
    frame_buttons_privada.pack(pady=5)

    # Button - eliminar archivos de privada 
    tk.Button(
        frame_buttons_privada,
        text="Eliminar de privada",
        command=lambda: eliminar_de_privada(entry_control, tabla_privada)
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
    tabla_publica.bind("<Double-1>", lambda event: on_double_click_row(event, dicc_archivos_publicos))

    # Tabla privada
    tabla_privada.bind("<Double-1>", lambda event: on_double_click_row(event, dicc_archivos_privados))


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

# Iniciar Google Services 
init_google_services()

root.mainloop()