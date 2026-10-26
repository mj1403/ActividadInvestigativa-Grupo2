import sys
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, ttk

# Permite correr este archivo con el botón de play de VS Code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from modulos import transacciones

# ---------- Paleta ----------
COLOR_AZUL = "#1976d2"
COLOR_AZUL_OSCURO = "#1565c0"
COLOR_VERDE = "#2e7d32"
COLOR_ROJO = "#c62828"
FONDO = "#f4f6fb"
BLANCO = "#ffffff"
BORDE = "#e3e8ef"
TEXTO = "#1f2937"
GRIS = "#6b7280"
PALETA_GASTOS = ["#1976d2", "#26a69a", "#ffa726", "#ab47bc", "#ef5350", "#66bb6a", "#8d6e63", "#78909c"]

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _a_numero(texto):
    """Convierte '500000', '500,000', '1.500.000' o '1500,50' en float."""
    t = texto.strip().replace(" ", "").replace("₡", "")
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        if t.count(",") > 1 or len(t.split(",")[-1]) == 3:
            t = t.replace(",", "")
        else:
            t = t.replace(",", ".")
    elif t.count(".") > 1:
        t = t.replace(".", "")
    return float(t)


def _formato(monto):
    return f"₡{monto:,.2f}"


def _aplicar_estilo():
    estilo = ttk.Style()
    estilo.theme_use("clam")

    # Contenedores
    estilo.configure("Fondo.TFrame", background=FONDO)
    estilo.configure("Card.TFrame", background=BLANCO)
    estilo.configure("Card.TLabel", background=BLANCO, foreground=GRIS, font=("Helvetica", 12))
    estilo.configure("Card.TRadiobutton", background=BLANCO, foreground=TEXTO, font=("Helvetica", 12))
    estilo.map("Card.TRadiobutton", background=[("active", BLANCO)])

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
    estilo.configure(
        "Acento.TButton", background=COLOR_AZUL, foreground="white",
        font=("Helvetica", 12, "bold"), padding=(16, 8), borderwidth=0,
    )
    estilo.map("Acento.TButton", background=[("active", COLOR_AZUL_OSCURO), ("pressed", "#0d47a1")],
               foreground=[("active", "white")])

    estilo.configure(
        "Header.TButton", background="white", foreground=COLOR_AZUL,
        font=("Helvetica", 12, "bold"), padding=(16, 8), borderwidth=0,
    )
    estilo.map("Header.TButton", background=[("active", "#e8f1fb")], foreground=[("active", COLOR_AZUL_OSCURO)])

    estilo.configure(
        "Peligro.TButton", background="#fdecea", foreground=COLOR_ROJO,
        font=("Helvetica", 12, "bold"), padding=(14, 8), borderwidth=0,
    )
    estilo.map("Peligro.TButton", background=[("active", "#f9c9c5")], foreground=[("active", COLOR_ROJO)])

    estilo.configure(
        "Suave.TButton", background="#e8f1fb", foreground=COLOR_AZUL,
        font=("Helvetica", 12, "bold"), padding=(14, 8), borderwidth=0,
    )
    estilo.map("Suave.TButton", background=[("active", "#cfe0f5")], foreground=[("active", COLOR_AZUL_OSCURO)])

    # Tabla
    estilo.configure("Treeview", rowheight=32, font=("Helvetica", 12), background=BLANCO,
                     fieldbackground=BLANCO, borderwidth=0, foreground=TEXTO)
    estilo.configure("Treeview.Heading", font=("Helvetica", 12, "bold"), background="#eef2f8",
                     foreground=TEXTO, padding=(8, 10), borderwidth=0)
    estilo.map("Treeview", background=[("selected", "#cfe0f5")], foreground=[("selected", "#000000")])
    estilo.map("Treeview.Heading", background=[("active", "#e3e8ef")])


class DialogoTransaccion(tk.Toplevel):
    """Ventana para registrar un ingreso o un egreso."""

    def __init__(self, master, al_guardar):
        super().__init__(master)
        self.title("Nueva transacción")
        self.configure(bg=BLANCO)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.al_guardar = al_guardar
        self.categorias = {}

        self.var_tipo = tk.StringVar(value="egreso")
        self.var_categoria = tk.StringVar()
        self.var_monto = tk.StringVar()
        self.var_fecha = tk.StringVar(value=date.today().isoformat())
        self.var_desc = tk.StringVar()

        # Cabecera que cambia de color según el tipo
        self.cabecera = tk.Frame(self, bg=COLOR_ROJO)
        self.cabecera.pack(fill="x")
        self.lbl_titulo = tk.Label(self.cabecera, text="", bg=COLOR_ROJO, fg="white",
                                   font=("Helvetica", 16, "bold"), anchor="w")
        self.lbl_titulo.pack(fill="x", padx=20, pady=14)

        marco = ttk.Frame(self, padding=20, style="Card.TFrame")
        marco.pack()

        ttk.Label(marco, text="Tipo", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        fila = ttk.Frame(marco, style="Card.TFrame")
        fila.grid(row=0, column=1, sticky="w")
        for texto, valor in (("Ingreso", "ingreso"), ("Egreso", "egreso")):
            ttk.Radiobutton(
                fila, text=texto, value=valor, variable=self.var_tipo, style="Card.TRadiobutton",
                command=self._cargar_categorias,
            ).pack(side="left", padx=(0, 16))

        ttk.Label(marco, text="Categoría", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.combo = ttk.Combobox(marco, textvariable=self.var_categoria, state="readonly", width=28)
        self.combo.grid(row=1, column=1, pady=6)

        ttk.Label(marco, text="Monto (₡)", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(marco, textvariable=self.var_monto, width=31).grid(row=2, column=1, pady=6)

        ttk.Label(marco, text="Fecha (AAAA-MM-DD)", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(marco, textvariable=self.var_fecha, width=31).grid(row=3, column=1, pady=6)

        ttk.Label(marco, text="Descripción", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(marco, textvariable=self.var_desc, width=31).grid(row=4, column=1, pady=6)

        botones = ttk.Frame(marco, style="Card.TFrame")
        botones.grid(row=5, column=0, columnspan=2, pady=(16, 0), sticky="e")
        ttk.Button(botones, text="Guardar", style="Acento.TButton", command=self._guardar).pack(side="right")
        ttk.Button(botones, text="Cancelar", style="Suave.TButton", command=self.destroy).pack(side="right", padx=(0, 8))

        self._cargar_categorias()
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def _cargar_categorias(self):
        tipo = self.var_tipo.get()
        filas = transacciones.listar_categorias(tipo)
        self.categorias = {f["nombre"]: f["id_categoria"] for f in filas}
        nombres = list(self.categorias)
        self.combo["values"] = nombres
        self.var_categoria.set(nombres[0] if nombres else "")

        color = COLOR_VERDE if tipo == "ingreso" else COLOR_ROJO
        self.cabecera.configure(bg=color)
        self.lbl_titulo.configure(bg=color, text="Nuevo ingreso" if tipo == "ingreso" else "Nuevo egreso")

    def _guardar(self):
        nombre = self.var_categoria.get()
        if nombre not in self.categorias:
            messagebox.showwarning("Falta la categoría", "Selecciona una categoría.", parent=self)
            return
        try:
            monto = _a_numero(self.var_monto.get())
        except ValueError:
            messagebox.showwarning("Monto inválido", "Escribe un monto numérico, por ejemplo 15000.", parent=self)
            return
        try:
            fecha = datetime.strptime(self.var_fecha.get().strip(), "%Y-%m-%d").date().isoformat()
        except ValueError:
            messagebox.showwarning("Fecha inválida", "Usa el formato AAAA-MM-DD, por ejemplo 2026-10-25.", parent=self)
            return
        try:
            transacciones.registrar_transaccion(
                self.categorias[nombre], monto,
                self.var_desc.get().strip() or None, fecha,
            )
        except ValueError as error:
            messagebox.showwarning("No se pudo guardar", str(error), parent=self)
            return
        self.al_guardar()
        self.destroy()


class VentanaTransacciones(ttk.Frame):
    """Pantalla de ingresos y egresos (vista diaria y mensual)."""

    def __init__(self, master):
        _aplicar_estilo()
        super().__init__(master, style="Fondo.TFrame")
        self.pack(fill="both", expand=True)

        hoy = date.today()
        self.var_modo = tk.StringVar(value="mes")
        self.var_mes = tk.StringVar(value=MESES[hoy.month - 1])
        self.var_anio = tk.StringVar(value=str(hoy.year))
        self.var_dia = tk.StringVar(value=hoy.isoformat())
        self.var_tipo = tk.StringVar(value="Todos")

        self._crear_encabezado()
        self._crear_tarjetas()
        self._crear_pestanas()
        self._actualizar_modo()

    # ---------- construcción de la interfaz ----------
    def _crear_encabezado(self):
        barra = tk.Frame(self, bg=COLOR_AZUL)
        barra.pack(fill="x")

        textos = tk.Frame(barra, bg=COLOR_AZUL)
        textos.pack(side="left", padx=24, pady=16)
        tk.Label(textos, text="Ingresos y egresos", bg=COLOR_AZUL, fg="white",
                 font=("Helvetica", 22, "bold"), anchor="w").pack(anchor="w")
        self.lbl_periodo = tk.Label(textos, text="", bg=COLOR_AZUL, fg="#cfe0f5",
                                    font=("Helvetica", 13), anchor="w")
        self.lbl_periodo.pack(anchor="w")

        ttk.Button(barra, text="+ Nueva transacción", style="Header.TButton",
                   command=self._nueva).pack(side="right", padx=24)

    def _crear_tarjetas(self):
        marco = ttk.Frame(self, style="Fondo.TFrame")
        marco.pack(fill="x", padx=16, pady=(16, 8))
        self.tarjetas = {}
        colores = {"ingresos": COLOR_VERDE, "egresos": COLOR_ROJO, "balance": COLOR_AZUL, "total": "#6a1b9a"}
        for clave in ("ingresos", "egresos", "balance", "total"):
            caja = tk.Frame(marco, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
            caja.pack(side="left", fill="both", expand=True, padx=6)
            tk.Frame(caja, bg=colores[clave], width=6).pack(side="left", fill="y")
            contenido = tk.Frame(caja, bg=BLANCO)
            contenido.pack(side="left", fill="both", expand=True, padx=14, pady=12)
            titulo = tk.Label(contenido, text="", bg=BLANCO, fg=GRIS, font=("Helvetica", 12), anchor="w")
            titulo.pack(fill="x")
            valor = tk.Label(contenido, text="₡0.00", bg=BLANCO, fg=colores[clave],
                             font=("Helvetica", 22, "bold"), anchor="w")
            valor.pack(fill="x", pady=(2, 0))
            self.tarjetas[clave] = (valor, titulo)

    def _crear_pestanas(self):
        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        tab_lista = ttk.Frame(self.pestanas, style="Fondo.TFrame")
        tab_grafico = ttk.Frame(self.pestanas, style="Fondo.TFrame")
        self.pestanas.add(tab_lista, text="  Transacciones  ")
        self.pestanas.add(tab_grafico, text="  Resumen gráfico  ")

        # ----- Barra de filtros (tarjeta blanca) -----
        filtros = tk.Frame(tab_lista, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        filtros.pack(fill="x", pady=(12, 8))
        interior = ttk.Frame(filtros, style="Card.TFrame")
        interior.pack(fill="x", padx=12, pady=10)

        ttk.Radiobutton(interior, text="Mensual", value="mes", variable=self.var_modo,
                        style="Card.TRadiobutton", command=self._actualizar_modo).pack(side="left")
        ttk.Radiobutton(interior, text="Diario", value="dia", variable=self.var_modo,
                        style="Card.TRadiobutton", command=self._actualizar_modo).pack(side="left", padx=(8, 14))

        self.combo_mes = ttk.Combobox(interior, textvariable=self.var_mes, values=MESES,
                                      state="readonly", width=11)
        self.combo_mes.pack(side="left")
        self.combo_mes.bind("<<ComboboxSelected>>", self.refrescar)

        self.entry_anio = ttk.Entry(interior, textvariable=self.var_anio, width=6)
        self.entry_anio.pack(side="left", padx=(8, 14))
        self.entry_anio.bind("<Return>", self.refrescar)

        self.entry_dia = ttk.Entry(interior, textvariable=self.var_dia, width=11)
        self.entry_dia.pack(side="left", padx=(0, 14))
        self.entry_dia.bind("<Return>", self.refrescar)

        ttk.Label(interior, text="Tipo", style="Card.TLabel").pack(side="left")
        combo_tipo = ttk.Combobox(interior, textvariable=self.var_tipo,
                                  values=["Todos", "ingreso", "egreso"], state="readonly", width=9)
        combo_tipo.pack(side="left", padx=(6, 10))
        combo_tipo.bind("<<ComboboxSelected>>", self.refrescar)

        ttk.Button(interior, text="Aplicar", style="Suave.TButton", command=self.refrescar).pack(side="left")
        ttk.Button(interior, text="Eliminar", style="Peligro.TButton", command=self._eliminar).pack(side="right")

        # ----- Tabla (tarjeta blanca con scroll) -----
        contenedor = tk.Frame(tab_lista, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        contenedor.pack(fill="both", expand=True)

        columnas = ("fecha", "categoria", "tipo", "monto", "descripcion")
        self.tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        encabezados = {
            "fecha": ("Fecha", 110), "categoria": ("Categoría", 170), "tipo": ("Tipo", 90),
            "monto": ("Monto", 150), "descripcion": ("Descripción", 380),
        }
        for col, (texto, ancho) in encabezados.items():
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="e" if col == "monto" else "w")
        self.tabla.tag_configure("par", background=BLANCO)
        self.tabla.tag_configure("impar", background="#f7f9fc")
        self.tabla.tag_configure("ingreso", foreground=COLOR_VERDE)
        self.tabla.tag_configure("egreso", foreground=COLOR_ROJO)

        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tabla.pack(side="left", fill="both", expand=True)

        self.lbl_vacio = tk.Label(self.tabla, text="No hay transacciones en este periodo.\n"
                                  "Usa «+ Nueva transacción» para agregar una.",
                                  bg=BLANCO, fg=GRIS, font=("Helvetica", 13), justify="center")

        # ----- Gráficos -----
        tarjeta_grafico = tk.Frame(tab_grafico, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        tarjeta_grafico.pack(fill="both", expand=True, pady=12)
        self.figura = Figure(figsize=(8, 4), dpi=100, facecolor=BLANCO)
        self.lienzo = FigureCanvasTkAgg(self.figura, master=tarjeta_grafico)
        self.lienzo.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ---------- lógica ----------
    def _actualizar_modo(self):
        mensual = self.var_modo.get() == "mes"
        self.combo_mes.configure(state="readonly" if mensual else "disabled")
        self.entry_anio.configure(state="normal" if mensual else "disabled")
        self.entry_dia.configure(state="disabled" if mensual else "normal")
        self.refrescar()

    def _leer_periodo(self):
        if self.var_modo.get() == "dia":
            return "dia", datetime.strptime(self.var_dia.get().strip(), "%Y-%m-%d").date()
        mes = MESES.index(self.var_mes.get()) + 1
        return "mes", date(int(self.var_anio.get()), mes, 1)

    def refrescar(self, *_):
        try:
            modo, ref = self._leer_periodo()
        except ValueError:
            messagebox.showwarning("Periodo inválido", "Revisa el año o la fecha (AAAA-MM-DD).")
            return

        if modo == "dia":
            filas = transacciones.listar_por_dia(ref.isoformat())
            ing, egr, bal = transacciones.resumen_diario(ref.isoformat())
            periodo = "del día"
            self.lbl_periodo.configure(text=f"Vista diaria · {ref:%d/%m/%Y}")
        else:
            filas = transacciones.listar_por_mes(ref.year, ref.month)
            ing, egr, bal = transacciones.resumen_mensual(ref.year, ref.month)
            periodo = "del mes"
            self.lbl_periodo.configure(text=f"Vista mensual · {MESES[ref.month - 1]} {ref.year}")

        tipo = self.var_tipo.get()
        if tipo != "Todos":
            filas = [f for f in filas if f["tipo"] == tipo]

        # Tabla
        self.tabla.delete(*self.tabla.get_children())
        for i, f in enumerate(filas):
            self.tabla.insert(
                "", "end", iid=str(f["id_transaccion"]),
                values=(f["fecha"], f["categoria"], f["tipo"].capitalize(),
                        _formato(f["monto"]), f["descripcion"] or ""),
                tags=(f["tipo"], "par" if i % 2 == 0 else "impar"),
            )
        if filas:
            self.lbl_vacio.place_forget()
        else:
            self.lbl_vacio.place(relx=0.5, rely=0.45, anchor="center")

        # Tarjetas
        total = transacciones.calcular_balance()[2]
        datos = {
            "ingresos": (ing, f"Ingresos {periodo}", COLOR_VERDE),
            "egresos": (egr, f"Egresos {periodo}", COLOR_ROJO),
            "balance": (bal, f"Balance {periodo}", COLOR_AZUL if bal >= 0 else COLOR_ROJO),
            "total": (total, "Balance total", "#6a1b9a" if total >= 0 else COLOR_ROJO),
        }
        for clave, (monto, titulo, color) in datos.items():
            valor, etiqueta = self.tarjetas[clave]
            valor.configure(text=_formato(monto), fg=color)
            etiqueta.configure(text=titulo)

        self._dibujar_graficos(ref.year, ref.month)

    def _dibujar_graficos(self, anio, mes):
        self.figura.clear()
        cuadricula = self.figura.add_gridspec(1, 2, width_ratios=[3, 2])
        eje_barras = self.figura.add_subplot(cuadricula[0])
        eje_dona = self.figura.add_subplot(cuadricula[1])

        # Barras: gastos por categoría
        datos = transacciones.gastos_por_categoria_mes(anio, mes)
        if datos:
            nombres = [d["categoria"] for d in datos][::-1]
            totales = [d["total"] for d in datos][::-1]
            colores = [PALETA_GASTOS[i % len(PALETA_GASTOS)] for i in range(len(datos))][::-1]
            barras = eje_barras.barh(nombres, totales, color=colores, height=0.6)
            maximo = max(totales)
            for barra, valor in zip(barras, totales):
                eje_barras.text(valor + maximo * 0.02, barra.get_y() + barra.get_height() / 2,
                                f"₡{valor:,.0f}", va="center", fontsize=10, color=TEXTO)
            eje_barras.set_xlim(0, maximo * 1.3)
            for lado in ("top", "right", "bottom"):
                eje_barras.spines[lado].set_visible(False)
            eje_barras.spines["left"].set_color(BORDE)
            eje_barras.set_xticks([])
            eje_barras.tick_params(axis="y", length=0, labelsize=11)
        else:
            eje_barras.text(0.5, 0.5, "Sin egresos en este mes", ha="center", va="center",
                            color=GRIS, fontsize=12, transform=eje_barras.transAxes)
            eje_barras.axis("off")
        eje_barras.set_title("Gastos por categoría", fontsize=13, fontweight="bold", color=TEXTO, loc="left")

        # Dona: ingresos vs egresos
        ing, egr, bal = transacciones.resumen_mensual(anio, mes)
        if ing + egr > 0:
            eje_dona.pie([ing, egr], colors=[COLOR_VERDE, COLOR_ROJO], startangle=90, counterclock=False,
                         wedgeprops=dict(width=0.38, edgecolor="white"))
            eje_dona.text(0, 0.08, "Balance", ha="center", va="center", fontsize=10, color=GRIS)
            eje_dona.text(0, -0.12, f"₡{bal:,.0f}", ha="center", va="center", fontsize=13,
                          fontweight="bold", color=COLOR_VERDE if bal >= 0 else COLOR_ROJO)
            eje_dona.legend(["Ingresos", "Egresos"], loc="lower center", frameon=False, ncol=2,
                            bbox_to_anchor=(0.5, -0.12), fontsize=10)
        else:
            eje_dona.text(0.5, 0.5, "Sin datos", ha="center", va="center", color=GRIS,
                          fontsize=12, transform=eje_dona.transAxes)
            eje_dona.axis("off")
        eje_dona.set_title(f"{MESES[mes - 1]} {anio}", fontsize=13, fontweight="bold", color=TEXTO)

        self.figura.tight_layout()
        self.lienzo.draw()

    def _nueva(self):
        DialogoTransaccion(self, self.refrescar)

    def _eliminar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Eliminar", "Selecciona una transacción de la tabla.")
            return
        if messagebox.askyesno("Eliminar", "¿Seguro que quieres eliminar esta transacción?"):
            transacciones.eliminar_transaccion(int(seleccion[0]))
            self.refrescar()


def iniciar():
    raiz = tk.Tk()
    raiz.title("Finanzas personales · Ingresos y egresos")
    raiz.geometry("1100x720")
    raiz.minsize(900, 600)
    raiz.configure(bg=FONDO)
    VentanaTransacciones(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    from database.conexion import inicializar_db

    inicializar_db()
    iniciar()