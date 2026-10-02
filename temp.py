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
