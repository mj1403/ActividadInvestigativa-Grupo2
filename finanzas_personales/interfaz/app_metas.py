import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from interfaz.reportes import ventana_reportes

from modulos import metas

ESTADOS_TXT = {"en_progreso": "En progreso", "cumplida": "Cumplida", "cancelada": "Cancelada"}
PLAZOS_TXT = {"corto": "Corto plazo", "largo": "Largo plazo"}

# ---------- Paleta ----------
COLOR_AZUL = "#1976d2"
COLOR_AZUL_OSCURO = "#1565c0"
COLOR_VERDE = "#2e7d32"
COLOR_ROJO = "#c62828"
COLOR_NARANJA = "#ef6c00"
COLOR_MORADO = "#6a1b9a"
FONDO = "#f4f6fb"
BLANCO = "#ffffff"
BORDE = "#e3e8ef"
TEXTO = "#1f2937"
GRIS = "#6b7280"


def _a_numero(texto):
    """Convierte '500000', '500,000', '1.500.000' o '1500,50' en float."""
    t = texto.strip().replace(" ", "")
    if "," in t and "." in t:
        # El último separador es el decimal; el otro es de miles.
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        if t.count(",") > 1 or len(t.split(",")[-1]) == 3:
            t = t.replace(",", "")      # 500,000 -> miles
        else:
            t = t.replace(",", ".")     # 1500,50 -> decimal
    elif t.count(".") > 1:
        t = t.replace(".", "")          # 1.500.000 -> miles
    try:
        return float(t)
    except ValueError:
        raise ValueError("El monto debe ser un número.")


def _dinero(valor):
    return f"{valor:,.2f}"


def _aplicar_estilo(ventana):
    estilo = ttk.Style(ventana)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")

    # Contenedores y etiquetas
    estilo.configure("Fondo.TFrame", background=FONDO)
    estilo.configure("Card.TFrame", background=BLANCO)
    estilo.configure("Card.TLabel", background=BLANCO, foreground=GRIS, font=("Helvetica", 12))
    estilo.configure("CardNegrita.TLabel", background=BLANCO, foreground=TEXTO, font=("Helvetica", 12, "bold"))
    estilo.configure("CardTitulo.TLabel", background=BLANCO, foreground=TEXTO, font=("Helvetica", 17, "bold"))

    # Campos
    estilo.configure("TEntry", padding=6, fieldbackground=BLANCO, bordercolor=BORDE)
    estilo.configure("TCombobox", padding=6, fieldbackground=BLANCO, bordercolor=BORDE, arrowsize=14)

    # Pestañas
    estilo.configure("TNotebook", background=FONDO, borderwidth=0, tabmargins=(0, 4, 0, 0))
    estilo.configure(
        "TNotebook.Tab", padding=(26, 10), font=("Helvetica", 13, "bold"),
        background="#e3e8ef", foreground="#555555", borderwidth=0,
    )
    estilo.map(
        "TNotebook.Tab",
        background=[("selected", COLOR_AZUL), ("active", "#cfe0f5")],
        foreground=[("selected", "white"), ("active", COLOR_AZUL)],
    )

    # Botones
    estilo.configure("Accent.TButton", background=COLOR_AZUL, foreground="white",
                     font=("Helvetica", 12, "bold"), padding=(16, 8), borderwidth=0)
    estilo.map("Accent.TButton", background=[("active", COLOR_AZUL_OSCURO), ("pressed", "#0d47a1")],
               foreground=[("active", "white")])

    estilo.configure("Header.TButton", background="white", foreground=COLOR_AZUL,
                     font=("Helvetica", 12, "bold"), padding=(16, 8), borderwidth=0)
    estilo.map("Header.TButton", background=[("active", "#e8f1fb")], foreground=[("active", COLOR_AZUL_OSCURO)])

    estilo.configure("Suave.TButton", background="#e8f1fb", foreground=COLOR_AZUL,
                     font=("Helvetica", 12, "bold"), padding=(14, 8), borderwidth=0)
    estilo.map("Suave.TButton", background=[("active", "#cfe0f5")], foreground=[("active", COLOR_AZUL_OSCURO)])

    estilo.configure("Peligro.TButton", background="#fdecea", foreground=COLOR_ROJO,
                     font=("Helvetica", 12, "bold"), padding=(14, 8), borderwidth=0)
    estilo.map("Peligro.TButton", background=[("active", "#f9c9c5")], foreground=[("active", COLOR_ROJO)])

    # Tablas
    estilo.configure("Treeview", rowheight=32, font=("Helvetica", 12), background=BLANCO,
                     fieldbackground=BLANCO, borderwidth=0, foreground=TEXTO)
    estilo.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="#eef2f8",
                     foreground=TEXTO, padding=(8, 10), borderwidth=0)
    estilo.map("Treeview", background=[("selected", "#cfe0f5")], foreground=[("selected", "#000000")])
    estilo.map("Treeview.Heading", background=[("active", "#e3e8ef")])

    # Barras de progreso
    for nombre, color in (("Verde", COLOR_VERDE), ("Azul", COLOR_AZUL)):
        estilo.configure(f"{nombre}.Horizontal.TProgressbar", background=color,
                         troughcolor="#e3e8ef", borderwidth=0, thickness=16)


def _cabecera_dialogo(ventana, texto, color=COLOR_AZUL):
    barra = tk.Frame(ventana, bg=color)
    barra.pack(fill="x")
    tk.Label(barra, text=texto, bg=color, fg="white", font=("Helvetica", 16, "bold"),
             anchor="w").pack(fill="x", padx=20, pady=14)


class DialogoMeta(tk.Toplevel):
    """Ventana para crear o editar una meta. Deja el resultado en self.resultado."""

    def __init__(self, padre, meta=None):
        super().__init__(padre)
        self.title("Editar meta" if meta else "Nueva meta")
        self.configure(bg=BLANCO)
        self.resizable(False, False)
        self.transient(padre)
        self.resultado = None

        self.v_nombre = tk.StringVar(value=meta["nombre"] if meta else "")
        self.v_monto = tk.StringVar(value=f"{meta['monto_objetivo']:.2f}" if meta else "")
        self.v_fecha = tk.StringVar(
            value=meta["fecha_limite"] if meta else date.today().isoformat()
        )
        self.v_plazo = tk.StringVar(value=meta["plazo"] if meta else "corto")

        _cabecera_dialogo(self, "Editar meta" if meta else "Nueva meta")

        marco = ttk.Frame(self, padding=20, style="Card.TFrame")
        marco.pack(fill="both")
        filas = (
            ("Nombre de la meta", ttk.Entry(marco, textvariable=self.v_nombre, width=34)),
            ("Monto objetivo (₡)", ttk.Entry(marco, textvariable=self.v_monto, width=34)),
            ("Fecha límite (AAAA-MM-DD)", ttk.Entry(marco, textvariable=self.v_fecha, width=34)),
            (
                "Plazo",
                ttk.Combobox(
                    marco, textvariable=self.v_plazo, values=metas.PLAZOS,
                    state="readonly", width=31,
                ),
            ),
        )
        for i, (texto, campo) in enumerate(filas):
            ttk.Label(marco, text=texto, style="Card.TLabel").grid(row=i * 2, column=0, sticky="w", pady=(8, 0))
            campo.grid(row=i * 2 + 1, column=0, sticky="we")
        filas[0][1].focus_set()

        botones = ttk.Frame(marco, style="Card.TFrame")
        botones.grid(row=8, column=0, sticky="e", pady=(18, 0))
        ttk.Button(botones, text="Guardar", style="Accent.TButton",
                   command=self._guardar).pack(side="right")
        ttk.Button(botones, text="Cancelar", style="Suave.TButton",
                   command=self.destroy).pack(side="right", padx=8)

        self.bind("<Return>", lambda e: self._guardar())
        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_visibility()
        self.grab_set()

    def _guardar(self):
        try:
            self.resultado = {
                "nombre": self.v_nombre.get(),
                "monto": _a_numero(self.v_monto.get()),
                "fecha": self.v_fecha.get().strip(),
                "plazo": self.v_plazo.get(),
            }
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error), parent=self)
            return
        self.destroy()


class DialogoAporte(tk.Toplevel):
    """Ventana para registrar un aporte. Deja el resultado en self.resultado."""

    def __init__(self, padre, nombre_meta):
        super().__init__(padre)
        self.title("Registrar aporte")
        self.configure(bg=BLANCO)
        self.resizable(False, False)
        self.transient(padre)
        self.resultado = None

        self.v_monto = tk.StringVar()
        self.v_fecha = tk.StringVar(value=date.today().isoformat())

        _cabecera_dialogo(self, "Registrar aporte", COLOR_VERDE)

        marco = ttk.Frame(self, padding=20, style="Card.TFrame")
        marco.pack(fill="both")
        ttk.Label(marco, text=f"Meta: {nombre_meta}", style="CardNegrita.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(marco, text="Monto del aporte (₡)", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=(12, 0))
        entrada = ttk.Entry(marco, textvariable=self.v_monto, width=30)
        entrada.grid(row=2, column=0, sticky="we")
        ttk.Label(marco, text="Fecha (AAAA-MM-DD)", style="Card.TLabel").grid(
            row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(marco, textvariable=self.v_fecha, width=30).grid(row=4, column=0, sticky="we")
        entrada.focus_set()

        botones = ttk.Frame(marco, style="Card.TFrame")
        botones.grid(row=5, column=0, sticky="e", pady=(18, 0))
        ttk.Button(botones, text="Registrar", style="Accent.TButton",
                   command=self._guardar).pack(side="right")
        ttk.Button(botones, text="Cancelar", style="Suave.TButton",
                   command=self.destroy).pack(side="right", padx=8)

        self.bind("<Return>", lambda e: self._guardar())
        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_visibility()
        self.grab_set()

    def _guardar(self):
        try:
            self.resultado = {
                "monto": _a_numero(self.v_monto.get()),
                "fecha": self.v_fecha.get().strip() or None,
            }
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error), parent=self)
            return
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finanzas personales · Metas financieras")
        self.geometry("1120x760")
        self.minsize(980, 660)
        self.configure(bg=FONDO)

        _aplicar_estilo(self)
        self._crear_encabezado()
        self._crear_resumen()

        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        self.pestana_metas = ttk.Frame(self.cuaderno, style="Fondo.TFrame", padding=(0, 12, 0, 0))
        self.pestana_grafico = ttk.Frame(self.cuaderno, style="Fondo.TFrame", padding=(0, 12, 0, 0))
        self.cuaderno.add(self.pestana_metas, text="  Metas  ")
        self.cuaderno.add(self.pestana_grafico, text="  Gráfico de progreso  ")
        self.cuaderno.bind("<<NotebookTabChanged>>", lambda e: self._dibujar_grafico())

        self._crear_pestana_metas()
        self._crear_pestana_grafico()
        self.refrescar()

    # ---------- construcción de la ventana ----------

    def _crear_encabezado(self):
        barra = tk.Frame(self, bg=COLOR_AZUL)
        barra.pack(fill="x")

        textos = tk.Frame(barra, bg=COLOR_AZUL)
        textos.pack(side="left", padx=24, pady=16)
        tk.Label(textos, text="Metas financieras", bg=COLOR_AZUL, fg="white",
                 font=("Helvetica", 22, "bold"), anchor="w").pack(anchor="w")
        tk.Label(textos, text="Define objetivos, registra aportes y mira tu progreso",
                 bg=COLOR_AZUL, fg="#cfe0f5", font=("Helvetica", 13), anchor="w").pack(anchor="w")

        ttk.Button(barra, text="+ Nueva meta", style="Header.TButton",
                   command=self.nueva_meta).pack(side="right", padx=24)

    def _crear_resumen(self):
        barra = ttk.Frame(self, style="Fondo.TFrame")
        barra.pack(fill="x", padx=16, pady=(16, 8))
        self.tarjetas = {}
        for i, (clave, texto, color) in enumerate((
            ("total", "Metas registradas", COLOR_AZUL),
            ("en_progreso", "En progreso", COLOR_NARANJA),
            ("cumplidas", "Cumplidas", COLOR_VERDE),
            ("porcentaje_promedio", "Avance promedio", COLOR_MORADO),
        )):
            caja = tk.Frame(barra, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
            caja.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            barra.columnconfigure(i, weight=1, uniform="tarjeta")
            tk.Frame(caja, bg=color, width=6).pack(side="left", fill="y")
            interior = tk.Frame(caja, bg=BLANCO)
            interior.pack(side="left", fill="both", expand=True, padx=14, pady=12)
            tk.Label(interior, text=texto, bg=BLANCO, fg=GRIS,
                     font=("Helvetica", 12), anchor="w").pack(fill="x")
            valor = tk.Label(interior, text="0", bg=BLANCO, fg=color,
                             font=("Helvetica", 22, "bold"), anchor="w")
            valor.pack(fill="x", pady=(2, 0))
            self.tarjetas[clave] = valor

    def _crear_pestana_metas(self):
        raiz = self.pestana_metas

        # Filtros y botones (tarjeta blanca)
        superior = tk.Frame(raiz, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        superior.pack(fill="x")
        fila = ttk.Frame(superior, style="Card.TFrame")
        fila.pack(fill="x", padx=12, pady=10)

        ttk.Label(fila, text="Plazo", style="Card.TLabel").pack(side="left")
        self.f_plazo = tk.StringVar(value="Todos")
        combo_plazo = ttk.Combobox(fila, textvariable=self.f_plazo, state="readonly",
                                   values=["Todos", "corto", "largo"], width=9)
        combo_plazo.pack(side="left", padx=(6, 16))
        ttk.Label(fila, text="Estado", style="Card.TLabel").pack(side="left")
        self.f_estado = tk.StringVar(value="Todos")
        combo_estado = ttk.Combobox(fila, textvariable=self.f_estado, state="readonly",
                                    values=["Todos", *metas.ESTADOS], width=12)
        combo_estado.pack(side="left", padx=6)
        for combo in (combo_plazo, combo_estado):
            combo.bind("<<ComboboxSelected>>", lambda e: self.refrescar())

        ttk.Button(fila, text="Eliminar", style="Peligro.TButton",
                   command=self.eliminar_meta).pack(side="right")
        self.btn_cancelar = ttk.Button(fila, text="Cancelar meta", style="Suave.TButton",
                                       command=self.alternar_cancelada)
        self.btn_cancelar.pack(side="right", padx=8)
        ttk.Button(fila, text="Editar", style="Suave.TButton",
                   command=self.editar_meta).pack(side="right")
        ttk.Button(fila, text="Enviar por correo", style="Accent.TButton",
                   command=self.abrir_reportes).pack(side="right", padx=8)

        # Tabla de metas
        contenedor = tk.Frame(raiz, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        contenedor.pack(fill="x", pady=12)

        columnas = ("nombre", "plazo", "estado", "acumulado", "objetivo", "porcentaje", "fecha", "dias")
        encabezados = ("Meta", "Plazo", "Estado", "Acumulado", "Objetivo", "Avance", "Fecha límite", "Días")
        anchos = (220, 110, 110, 120, 120, 90, 110, 70)
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings",
                                  selectmode="browse", height=5)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col == "nombre" else "center")
        self.tabla.tag_configure("par", background=BLANCO)
        self.tabla.tag_configure("impar", background="#f7f9fc")
        self.tabla.tag_configure("cumplida", foreground=COLOR_VERDE)
        self.tabla.tag_configure("cancelada", foreground="#9e9e9e")
        self.tabla.tag_configure("vencida", foreground=COLOR_ROJO)
        self.tabla.pack(fill="x")
        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._mostrar_detalle())
        self.tabla.bind("<Double-1>", lambda e: self.editar_meta())

        self.lbl_vacio = tk.Label(self.tabla, text="No hay metas todavía.\n"
                                  "Usa «+ Nueva meta» para crear la primera.",
                                  bg=BLANCO, fg=GRIS, font=("Helvetica", 13), justify="center")

        # Detalle de la meta seleccionada (tarjeta blanca)
        detalle = tk.Frame(raiz, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        detalle.pack(fill="both", expand=True)
        cuerpo = ttk.Frame(detalle, style="Card.TFrame", padding=16)
        cuerpo.pack(fill="both", expand=True)

        self.lbl_titulo = ttk.Label(cuerpo, text="Selecciona una meta de la tabla",
                                    style="CardTitulo.TLabel")
        self.lbl_titulo.pack(anchor="w")
        self.lbl_info = ttk.Label(cuerpo, text="", style="Card.TLabel", wraplength=1000)
        self.lbl_info.pack(anchor="w", pady=(2, 8))
        self.barra = ttk.Progressbar(cuerpo, maximum=100, length=400,
                                     style="Azul.Horizontal.TProgressbar")
        self.barra.pack(fill="x")
        self.lbl_porcentaje = ttk.Label(cuerpo, text="", style="CardNegrita.TLabel")
        self.lbl_porcentaje.pack(anchor="e")

        cabecera = ttk.Frame(cuerpo, style="Card.TFrame")
        cabecera.pack(fill="x", pady=(8, 6))
        ttk.Label(cabecera, text="Aportes registrados", style="CardNegrita.TLabel").pack(side="left")
        self.btn_eliminar_aporte = ttk.Button(cabecera, text="Eliminar aporte", style="Peligro.TButton",
                                              command=self.eliminar_aporte)
        self.btn_eliminar_aporte.pack(side="right")
        self.btn_aporte = ttk.Button(cabecera, text="+ Registrar aporte", style="Accent.TButton",
                                     command=self.registrar_aporte)
        self.btn_aporte.pack(side="right", padx=8)

        marco_aportes = tk.Frame(cuerpo, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        marco_aportes.pack(fill="both", expand=True)
        self.tabla_aportes = ttk.Treeview(marco_aportes, columns=("fecha", "monto"),
                                          show="headings", height=4)
        self.tabla_aportes.heading("fecha", text="Fecha")
        self.tabla_aportes.heading("monto", text="Monto")
        self.tabla_aportes.column("fecha", width=140, anchor="center")
        self.tabla_aportes.column("monto", width=160, anchor="e")
        self.tabla_aportes.tag_configure("par", background=BLANCO)
        self.tabla_aportes.tag_configure("impar", background="#f7f9fc")
        scroll = ttk.Scrollbar(marco_aportes, orient="vertical", command=self.tabla_aportes.yview)
        self.tabla_aportes.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tabla_aportes.pack(side="left", fill="both", expand=True)

        self.lbl_sin_aportes = tk.Label(self.tabla_aportes, text="", bg=BLANCO, fg=GRIS,
                                        font=("Helvetica", 12))

    def _crear_pestana_grafico(self):
        tarjeta = tk.Frame(self.pestana_grafico, bg=BLANCO, highlightthickness=1,
                           highlightbackground=BORDE)
        tarjeta.pack(fill="both", expand=True)
        self.figura = Figure(figsize=(8, 4.5), dpi=100, facecolor=BLANCO)
        self.lienzo = FigureCanvasTkAgg(self.figura, master=tarjeta)
        self.lienzo.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ---------- datos en pantalla ----------

    def _filtros(self):
        plazo = self.f_plazo.get()
        estado = self.f_estado.get()
        return (None if plazo == "Todos" else plazo, None if estado == "Todos" else estado)

    def _texto_aportes(self, texto):
        if texto:
            self.lbl_sin_aportes.config(text=texto)
            self.lbl_sin_aportes.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.lbl_sin_aportes.place_forget()

    def refrescar(self):
        """Recarga tarjetas, tabla, detalle y gráfico desde la base de datos."""
        seleccion = self.tabla.selection()
        id_seleccionado = seleccion[0] if seleccion else None

        resumen = metas.resumen_cumplimiento()
        self.tarjetas["total"].config(text=str(resumen["total"]))
        self.tarjetas["en_progreso"].config(text=str(resumen["en_progreso"]))
        self.tarjetas["cumplidas"].config(text=str(resumen["cumplidas"]))
        self.tarjetas["porcentaje_promedio"].config(text=f"{resumen['porcentaje_promedio']:.1f}%")

        self.tabla.delete(*self.tabla.get_children())
        plazo, estado = self._filtros()
        lista = metas.listar_metas(plazo, estado)
        for i, m in enumerate(lista):
            activa = m["estado"] == "en_progreso"
            etiquetas = ["par" if i % 2 == 0 else "impar"]
            if m["estado"] in ("cumplida", "cancelada"):
                etiquetas.append(m["estado"])
            elif activa and m["dias_restantes"] < 0:
                etiquetas.append("vencida")
            self.tabla.insert("", "end", iid=str(m["id_meta"]), tags=etiquetas, values=(
                m["nombre"],
                PLAZOS_TXT[m["plazo"]],
                ESTADOS_TXT[m["estado"]],
                _dinero(m["monto_acumulado"]),
                _dinero(m["monto_objetivo"]),
                f"{m['porcentaje']:.1f}%",
                m["fecha_limite"],
                m["dias_restantes"] if activa else "—",
            ))
        if lista:
            self.lbl_vacio.place_forget()
        else:
            self.lbl_vacio.place(relx=0.5, rely=0.5, anchor="center")

        if id_seleccionado and self.tabla.exists(id_seleccionado):
            self.tabla.selection_set(id_seleccionado)
        self._mostrar_detalle()
        self._dibujar_grafico()

    def _meta_seleccionada(self, avisar=True):
        seleccion = self.tabla.selection()
        if not seleccion:
            if avisar:
                messagebox.showinfo("Selecciona una meta", "Primero selecciona una meta de la tabla.")
            return None
        return metas.obtener_meta(int(seleccion[0]))

    def _mostrar_detalle(self):
        meta = self._meta_seleccionada(avisar=False)
        self.tabla_aportes.delete(*self.tabla_aportes.get_children())
        if meta is None:
            self.lbl_titulo.config(text="Selecciona una meta de la tabla")
            self.lbl_info.config(text="")
            self.lbl_porcentaje.config(text="")
            self.barra["value"] = 0
            self.btn_cancelar.config(text="Cancelar meta")
            self._texto_aportes("Selecciona una meta para ver sus aportes.")
            return

        self.lbl_titulo.config(text=meta["nombre"])
        if meta["estado"] == "en_progreso":
            if meta["dias_restantes"] >= 0:
                plazo_txt = f"{meta['dias_restantes']} días restantes"
            else:
                plazo_txt = f"vencida hace {-meta['dias_restantes']} días"
        else:
            plazo_txt = ESTADOS_TXT[meta["estado"]]
        self.lbl_info.config(text=(
            f"{PLAZOS_TXT[meta['plazo']]}  ·  Límite {meta['fecha_limite']} ({plazo_txt})  ·  "
            f"Acumulado {_dinero(meta['monto_acumulado'])} de {_dinero(meta['monto_objetivo'])}  ·  "
            f"Falta {_dinero(meta['restante'])}"
        ))
        self.barra.config(style="Verde.Horizontal.TProgressbar"
                          if meta["estado"] == "cumplida" else "Azul.Horizontal.TProgressbar")
        self.barra["value"] = meta["porcentaje"]
        self.lbl_porcentaje.config(text=f"{meta['porcentaje']:.1f}%")
        self.btn_cancelar.config(
            text="Reactivar meta" if meta["estado"] == "cancelada" else "Cancelar meta")

        aportes = metas.listar_aportes(meta["id_meta"])
        for i, a in enumerate(aportes):
            self.tabla_aportes.insert("", "end", iid=str(a["id_aporte"]),
                                      tags=("par" if i % 2 == 0 else "impar",),
                                      values=(a["fecha"], _dinero(a["monto"])))
        self._texto_aportes(None if aportes else "Aún no hay aportes para esta meta.")

    def _dibujar_grafico(self):
        self.figura.clear()
        ax = self.figura.add_subplot(111)
        lista = [m for m in metas.listar_metas() if m["estado"] != "cancelada"]
        if not lista:
            ax.axis("off")
            ax.text(0.5, 0.5, "Aún no hay metas para graficar", ha="center", va="center",
                    fontsize=13, color=GRIS)
        else:
            nombres = [m["nombre"] for m in lista]
            porcentajes = [m["porcentaje"] for m in lista]
            colores = [COLOR_VERDE if m["estado"] == "cumplida" else COLOR_AZUL for m in lista]
            ax.barh(nombres, [100] * len(lista), color="#eef2f8", height=0.55)   # fondo de la barra
            barras = ax.barh(nombres, porcentajes, color=colores, height=0.55)
            ax.set_xlim(0, 112)
            ax.invert_yaxis()
            for lado in ("top", "right", "bottom", "left"):
                ax.spines[lado].set_visible(False)
            ax.set_xticks([])
            ax.tick_params(axis="y", length=0, labelsize=12)
            for barra, p in zip(barras, porcentajes):
                ax.text(101, barra.get_y() + barra.get_height() / 2,
                        f"{p:.1f}%", va="center", fontsize=11, fontweight="bold", color=TEXTO)
            ax.set_title("Progreso de metas financieras", fontsize=14, fontweight="bold",
                         color=TEXTO, loc="left")
        self.figura.tight_layout()
        self.lienzo.draw()

    # ---------- acciones ----------

    def _ejecutar(self, accion):
        """Corre una acción y muestra los errores de validación en una ventana."""
        try:
            accion()
        except ValueError as error:
            messagebox.showerror("No se pudo completar", str(error))
            return False
        return True

    def nueva_meta(self):
        dialogo = DialogoMeta(self)
        self.wait_window(dialogo)
        if not dialogo.resultado:
            return
        r = dialogo.resultado
        if self._ejecutar(lambda: metas.crear_meta(r["nombre"], r["monto"], r["fecha"], r["plazo"])):
            self.refrescar()

    def editar_meta(self):
        meta = self._meta_seleccionada()
        if meta is None:
            return
        dialogo = DialogoMeta(self, meta)
        self.wait_window(dialogo)
        if not dialogo.resultado:
            return
        r = dialogo.resultado
        if self._ejecutar(lambda: metas.editar_meta(
                meta["id_meta"], r["nombre"], r["monto"], r["fecha"], r["plazo"])):
            self.refrescar()

    def eliminar_meta(self):
        meta = self._meta_seleccionada()
        if meta is None:
            return
        if messagebox.askyesno("Eliminar meta",
                               f"¿Eliminar la meta «{meta['nombre']}» y todos sus aportes?\n"
                               "Esta acción no se puede deshacer."):
            metas.eliminar_meta(meta["id_meta"])
            self.refrescar()

    def alternar_cancelada(self):
        meta = self._meta_seleccionada()
        if meta is None:
            return
        if meta["estado"] == "cancelada":
            metas.reactivar_meta(meta["id_meta"])
        else:
            metas.cancelar_meta(meta["id_meta"])
        self.refrescar()

    def registrar_aporte(self):
        meta = self._meta_seleccionada()
        if meta is None:
            return
        dialogo = DialogoAporte(self, meta["nombre"])
        self.wait_window(dialogo)
        if not dialogo.resultado:
            return
        r = dialogo.resultado
        if self._ejecutar(lambda: metas.registrar_aporte(meta["id_meta"], r["monto"], r["fecha"])):
            self.refrescar()
            actualizada = metas.obtener_meta(meta["id_meta"])
            if actualizada["estado"] == "cumplida" and meta["estado"] != "cumplida":
                messagebox.showinfo("¡Meta cumplida!",
                                    f"Alcanzaste la meta «{meta['nombre']}». ¡Felicidades!")

    def eliminar_aporte(self):
        seleccion = self.tabla_aportes.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un aporte", "Selecciona un aporte de la lista.")
            return
        if messagebox.askyesno("Eliminar aporte", "¿Eliminar el aporte seleccionado?"):
            metas.eliminar_aporte(int(seleccion[0]))
            self.refrescar()

    def abrir_reportes(self):
        ventana = ventana_reportes(self)
        ventana.focus_set()

def iniciar():
    App().mainloop()