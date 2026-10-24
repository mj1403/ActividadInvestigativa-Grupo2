import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from interfaz.reportes import ventana_reportes

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from modulos import metas

ESTADOS_TXT = {"en_progreso": "En progreso", "cumplida": "Cumplida", "cancelada": "Cancelada"}
PLAZOS_TXT = {"corto": "Corto plazo", "largo": "Largo plazo"}
COLOR_AZUL = "#1976d2"
COLOR_VERDE = "#2e7d32"


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


class DialogoMeta(tk.Toplevel):
    """Ventana para crear o editar una meta. Deja el resultado en self.resultado."""

    def __init__(self, padre, meta=None):
        super().__init__(padre)
        self.title("Editar meta" if meta else "Nueva meta")
        self.resizable(False, False)
        self.transient(padre)
        self.resultado = None

        self.v_nombre = tk.StringVar(value=meta["nombre"] if meta else "")
        self.v_monto = tk.StringVar(value=f"{meta['monto_objetivo']:.2f}" if meta else "")
        self.v_fecha = tk.StringVar(
            value=meta["fecha_limite"] if meta else date.today().isoformat()
        )
        self.v_plazo = tk.StringVar(value=meta["plazo"] if meta else "corto")

        marco = ttk.Frame(self, padding=18)
        marco.grid()
        filas = (
            ("Nombre de la meta", ttk.Entry(marco, textvariable=self.v_nombre, width=34)),
            ("Monto objetivo", ttk.Entry(marco, textvariable=self.v_monto, width=34)),
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
            ttk.Label(marco, text=texto).grid(row=i * 2, column=0, sticky="w", pady=(6, 0))
            campo.grid(row=i * 2 + 1, column=0, sticky="we")
        filas[0][1].focus_set()

        botones = ttk.Frame(marco)
        botones.grid(row=8, column=0, sticky="e", pady=(16, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar", style="Accent.TButton",
                   command=self._guardar).pack(side="right", padx=8)

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
        self.resizable(False, False)
        self.transient(padre)
        self.resultado = None

        self.v_monto = tk.StringVar()
        self.v_fecha = tk.StringVar(value=date.today().isoformat())

        marco = ttk.Frame(self, padding=18)
        marco.grid()
        ttk.Label(marco, text=f"Meta: {nombre_meta}",
                  font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(marco, text="Monto del aporte").grid(row=1, column=0, sticky="w", pady=(10, 0))
        entrada = ttk.Entry(marco, textvariable=self.v_monto, width=30)
        entrada.grid(row=2, column=0, sticky="we")
        ttk.Label(marco, text="Fecha (AAAA-MM-DD)").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(marco, textvariable=self.v_fecha, width=30).grid(row=4, column=0, sticky="we")
        entrada.focus_set()

        botones = ttk.Frame(marco)
        botones.grid(row=5, column=0, sticky="e", pady=(16, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Registrar", style="Accent.TButton",
                   command=self._guardar).pack(side="right", padx=8)

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
        self.geometry("1120x720")
        self.minsize(980, 640)

        self._estilos()
        self._crear_resumen()

        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.pestana_metas = ttk.Frame(self.cuaderno, padding=10)
        self.pestana_grafico = ttk.Frame(self.cuaderno, padding=10)
        self.cuaderno.add(self.pestana_metas, text="  Metas  ")
        self.cuaderno.add(self.pestana_grafico, text="  Gráfico de progreso  ")
        self.cuaderno.bind("<<NotebookTabChanged>>", lambda e: self._dibujar_grafico())

        self._crear_pestana_metas()
        self._crear_pestana_grafico()
        self.refrescar()

    # ---------- construcción de la ventana ----------

    def _estilos(self):
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        estilo.configure("Accent.TButton", font=("Segoe UI", 10, "bold"),
                         background=COLOR_AZUL, foreground="white")
        estilo.map("Accent.TButton", background=[("active", "#1565c0")])
        estilo.configure("Tarjeta.TFrame", background="white", relief="solid", borderwidth=1)
        estilo.configure("TarjetaValor.TLabel", background="white",
                         font=("Segoe UI", 20, "bold"), foreground=COLOR_AZUL)
        estilo.configure("TarjetaTexto.TLabel", background="white",
                         font=("Segoe UI", 9), foreground="#555555")
        estilo.configure("Verde.Horizontal.TProgressbar", background=COLOR_VERDE)
        estilo.configure("Azul.Horizontal.TProgressbar", background=COLOR_AZUL)

    def _crear_resumen(self):
        barra = ttk.Frame(self, padding=(12, 12, 12, 8))
        barra.pack(fill="x")
        self.tarjetas = {}
        for i, (clave, texto) in enumerate((
            ("total", "Metas registradas"),
            ("en_progreso", "En progreso"),
            ("cumplidas", "Cumplidas"),
            ("porcentaje_promedio", "Avance promedio"),
        )):
            tarjeta = ttk.Frame(barra, style="Tarjeta.TFrame", padding=(16, 10))
            tarjeta.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            barra.columnconfigure(i, weight=1)
            valor = ttk.Label(tarjeta, text="0", style="TarjetaValor.TLabel")
            valor.pack(anchor="w")
            ttk.Label(tarjeta, text=texto, style="TarjetaTexto.TLabel").pack(anchor="w")
            self.tarjetas[clave] = valor

    def _crear_pestana_metas(self):
        raiz = self.pestana_metas

        # Filtros y botones
        superior = ttk.Frame(raiz)
        superior.pack(fill="x")
        ttk.Label(superior, text="Plazo:").pack(side="left")
        self.f_plazo = tk.StringVar(value="Todos")
        combo_plazo = ttk.Combobox(superior, textvariable=self.f_plazo, state="readonly",
                                   values=["Todos", "corto", "largo"], width=9)
        combo_plazo.pack(side="left", padx=(4, 12))
        ttk.Label(superior, text="Estado:").pack(side="left")
        self.f_estado = tk.StringVar(value="Todos")
        combo_estado = ttk.Combobox(superior, textvariable=self.f_estado, state="readonly",
                                    values=["Todos", *metas.ESTADOS], width=12)
        combo_estado.pack(side="left", padx=4)
        for combo in (combo_plazo, combo_estado):
            combo.bind("<<ComboboxSelected>>", lambda e: self.refrescar())

        ttk.Button(superior, text="Eliminar", command=self.eliminar_meta).pack(side="right")
        self.btn_cancelar = ttk.Button(superior, text="Cancelar meta", command=self.alternar_cancelada)
        self.btn_cancelar.pack(side="right", padx=6)
        ttk.Button(superior, text="Editar", command=self.editar_meta).pack(side="right")
        ttk.Button(superior, text="+ Nueva meta", style="Accent.TButton",
                   command=self.nueva_meta).pack(side="right", padx=6)

        ttk.Button(superior, text="Enviar por correo", command=self.abrir_reportes).pack(side="right", padx=6)

        # Tabla de metas
        columnas = ("nombre", "plazo", "estado", "acumulado", "objetivo", "porcentaje", "fecha", "dias")
        encabezados = ("Meta", "Plazo", "Estado", "Acumulado", "Objetivo", "Avance", "Fecha límite", "Días")
        anchos = (220, 100, 100, 110, 110, 80, 100, 70)
        self.tabla = ttk.Treeview(raiz, columns=columnas, show="headings",
                                  selectmode="browse", height=5)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="w" if col == "nombre" else "center")
        self.tabla.tag_configure("cumplida", foreground=COLOR_VERDE)
        self.tabla.tag_configure("cancelada", foreground="#9e9e9e")
        self.tabla.tag_configure("vencida", foreground="#c62828")
        self.tabla.pack(fill="x", pady=10)
        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._mostrar_detalle())
        self.tabla.bind("<Double-1>", lambda e: self.editar_meta())

        # Detalle de la meta seleccionada
        detalle = ttk.LabelFrame(raiz, text=" Detalle de la meta seleccionada ", padding=12)
        detalle.pack(fill="both", expand=True)

        self.lbl_titulo = ttk.Label(detalle, text="Selecciona una meta de la tabla",
                                    font=("Segoe UI", 13, "bold"))
        self.lbl_titulo.pack(anchor="w")
        self.lbl_info = ttk.Label(detalle, text="", foreground="#555555")
        self.lbl_info.pack(anchor="w", pady=(2, 6))
        self.barra = ttk.Progressbar(detalle, maximum=100, length=400,
                                     style="Azul.Horizontal.TProgressbar")
        self.barra.pack(fill="x")
        self.lbl_porcentaje = ttk.Label(detalle, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_porcentaje.pack(anchor="e")

        cabecera = ttk.Frame(detalle)
        cabecera.pack(fill="x", pady=(6, 4))
        ttk.Label(cabecera, text="Aportes registrados",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.btn_eliminar_aporte = ttk.Button(cabecera, text="Eliminar aporte",
                                              command=self.eliminar_aporte)
        self.btn_eliminar_aporte.pack(side="right")
        self.btn_aporte = ttk.Button(cabecera, text="+ Registrar aporte", style="Accent.TButton",
                                     command=self.registrar_aporte)
        self.btn_aporte.pack(side="right", padx=6)

        self.tabla_aportes = ttk.Treeview(detalle, columns=("fecha", "monto"),
                                          show="headings", height=5)
        self.tabla_aportes.heading("fecha", text="Fecha")
        self.tabla_aportes.heading("monto", text="Monto")
        self.tabla_aportes.column("fecha", width=140, anchor="center")
        self.tabla_aportes.column("monto", width=160, anchor="e")
        self.tabla_aportes.pack(fill="both", expand=True)

    def _crear_pestana_grafico(self):
        self.figura = Figure(figsize=(8, 4.5), dpi=100)
        self.lienzo = FigureCanvasTkAgg(self.figura, master=self.pestana_grafico)
        self.lienzo.get_tk_widget().pack(fill="both", expand=True)

    # ---------- datos en pantalla ----------

    def _filtros(self):
        plazo = self.f_plazo.get()
        estado = self.f_estado.get()
        return (None if plazo == "Todos" else plazo, None if estado == "Todos" else estado)

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
        for m in metas.listar_metas(plazo, estado):
            activa = m["estado"] == "en_progreso"
            etiquetas = []
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

        for a in metas.listar_aportes(meta["id_meta"]):
            self.tabla_aportes.insert("", "end", iid=str(a["id_aporte"]),
                                      values=(a["fecha"], _dinero(a["monto"])))

    def _dibujar_grafico(self):
        self.figura.clear()
        ax = self.figura.add_subplot(111)
        lista = [m for m in metas.listar_metas() if m["estado"] != "cancelada"]
        if not lista:
            ax.axis("off")
            ax.text(0.5, 0.5, "Aún no hay metas para graficar", ha="center", va="center",
                    fontsize=13, color="#777777")
        else:
            nombres = [m["nombre"] for m in lista]
            porcentajes = [m["porcentaje"] for m in lista]
            colores = [COLOR_VERDE if m["estado"] == "cumplida" else COLOR_AZUL for m in lista]
            barras = ax.barh(nombres, porcentajes, color=colores)
            ax.set_xlim(0, 100)
            ax.set_xlabel("Progreso (%)")
            ax.set_title("Progreso de metas financieras")
            ax.invert_yaxis()
            for barra, p in zip(barras, porcentajes):
                ax.text(p + 1, barra.get_y() + barra.get_height() / 2,
                        f"{p:.1f}%", va="center")
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