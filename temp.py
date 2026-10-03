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
# ________________________________

#________________________________

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

#________________________________

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

#________________________________

# Variables globales
service_drive = None
service_gmail = None
service_sheets = None

dicc_archivos_publicos = {}
dicc_archivos_privados = {}

id_carpeta_publica = None
id_carpeta_privada = None

# ______________________________________________
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

    # Mensaje Exitó
    # messagebox.showinfo("Éxito", f"Archivo '{archivo}' copiado a privada como '{copia['name']}'")

    # Refrescar tabla privada
    reset_tabla(f"{numero_control}_private", tabla_privada, "privada")
    # listar_archivos(entry_control, tabla_publica, tabla_privada)

# ##############################################################################################################

        # Button: preview
    tk.Button(
        frame_reporte, 
        text="Vista Previa",
        command=lambda: generar_reporte(dicc_especificaciones, entry_control, True)
    ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    tk.Button(
        frame_reporte,
        text="Generar Reporte",
        command=lambda: generar_reporte(dicc_especificaciones, entry_control)
    ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")