import subprocess
import sys
import tkinter as tk
from pathlib import Path

from database.conexion import inicializar_db

RAIZ = Path(__file__).resolve().parent

# ---------- Paleta ----------
COLOR_AZUL = "#1976d2"
COLOR_AZUL_OSCURO = "#1565c0"
COLOR_VERDE = "#2e7d32"
COLOR_ROJO = "#c62828"
COLOR_MORADO = "#6a1b9a"
FONDO = "#f4f6fb"
BLANCO = "#ffffff"
BORDE = "#e3e8ef"
TEXTO = "#1f2937"
GRIS = "#6b7280"


def _abrir(modulo):
    """Abre cada pantalla en su propio proceso, así no chocan entre sí."""
    subprocess.Popen(
        [sys.executable, "-c", f"from {modulo} import iniciar; iniciar()"],
        cwd=RAIZ,
    )


def _formato(monto):
    return f"₡{monto:,.2f}"


class Tarjeta(tk.Frame):
    """Tarjeta clicable con franja de color, símbolo, título y descripción."""

    def __init__(self, master, color, simbolo, titulo, descripcion, comando):
        super().__init__(master, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE, cursor="pointinghand")
        self.comando = comando
        self.fondo_normal = BLANCO
        self.fondo_hover = "#f0f6fd"
        self.widgets = [self]

        tk.Frame(self, bg=color, height=8).pack(fill="x")

        cuerpo = tk.Frame(self, bg=BLANCO)
        cuerpo.pack(fill="both", expand=True, padx=24, pady=22)

        circulo = tk.Label(cuerpo, text=simbolo, bg=color, fg="white",
                           font=("Helvetica", 30, "bold"), width=3, height=1)
        circulo.pack(anchor="w")

        tk.Label(cuerpo, text=titulo, bg=BLANCO, fg=TEXTO,
                 font=("Helvetica", 20, "bold"), anchor="w").pack(fill="x", pady=(16, 4))
        tk.Label(cuerpo, text=descripcion, bg=BLANCO, fg=GRIS, font=("Helvetica", 13),
                 anchor="w", justify="left", wraplength=280).pack(fill="x")
        tk.Label(cuerpo, text="Abrir  →", bg=BLANCO, fg=color,
                 font=("Helvetica", 14, "bold"), anchor="w").pack(fill="x", pady=(18, 0))

        self._enlazar(self)

    def _enlazar(self, widget):
        if widget is not self:
            self.widgets.append(widget)
        widget.bind("<Button-1>", lambda e: self.comando())
        widget.bind("<Enter>", lambda e: self._pintar(self.fondo_hover))
        widget.bind("<Leave>", lambda e: self._pintar(self.fondo_normal))
        for hijo in widget.winfo_children():
            self._enlazar(hijo)

    def _pintar(self, color):
        for w in self.widgets:
            # Los círculos y franjas de color conservan su fondo
            if isinstance(w, tk.Label) and w.cget("bg") not in (BLANCO, self.fondo_hover):
                continue
            if isinstance(w, tk.Frame) and w is not self and w.cget("height") == 8:
                continue
            w.configure(bg=color)


def main():
    inicializar_db()

    ventana = tk.Tk()
    ventana.title("Finanzas personales")
    ventana.configure(bg=FONDO)
    ventana.resizable(False, False)

    ancho, alto = 820, 560
    x = (ventana.winfo_screenwidth() - ancho) // 2
    y = (ventana.winfo_screenheight() - alto) // 3
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ----- Encabezado -----
    barra = tk.Frame(ventana, bg=COLOR_AZUL)
    barra.pack(fill="x")
    tk.Label(barra, text="Finanzas personales", bg=COLOR_AZUL, fg="white",
             font=("Helvetica", 28, "bold"), anchor="w").pack(fill="x", padx=32, pady=(22, 0))
    tk.Label(barra, text="Controla tus ingresos, egresos y metas en un solo lugar",
             bg=COLOR_AZUL, fg="#cfe0f5", font=("Helvetica", 14), anchor="w").pack(fill="x", padx=32, pady=(2, 22))

    # ----- Resumen rápido -----
    resumen = tk.Frame(ventana, bg=FONDO)
    resumen.pack(fill="x", padx=32, pady=(22, 6))
    etiquetas = {}
    for i, (clave, titulo, color) in enumerate((
        ("balance", "Balance total", COLOR_MORADO),
        ("metas", "Metas en progreso", COLOR_AZUL),
    )):
        caja = tk.Frame(resumen, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        caja.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
        resumen.columnconfigure(i, weight=1, uniform="resumen")
        tk.Frame(caja, bg=color, width=6).pack(side="left", fill="y")
        interior = tk.Frame(caja, bg=BLANCO)
        interior.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        tk.Label(interior, text=titulo, bg=BLANCO, fg=GRIS, font=("Helvetica", 12), anchor="w").pack(fill="x")
        valor = tk.Label(interior, text="—", bg=BLANCO, fg=color, font=("Helvetica", 20, "bold"), anchor="w")
        valor.pack(fill="x")
        etiquetas[clave] = valor

    def actualizar_resumen(evento=None):
        if evento is not None and evento.widget is not ventana:
            return
        try:
            from modulos import transacciones

            balance = transacciones.calcular_balance()[2]
            etiquetas["balance"].configure(text=_formato(balance),
                                           fg=COLOR_MORADO if balance >= 0 else COLOR_ROJO)
        except Exception:
            etiquetas["balance"].configure(text="—")
        try:
            from modulos import metas

            etiquetas["metas"].configure(text=str(metas.resumen_cumplimiento()["en_progreso"]))
        except Exception:
            etiquetas["metas"].configure(text="—")

    actualizar_resumen()
    ventana.bind("<FocusIn>", actualizar_resumen)

    # ----- Tarjetas de navegación -----
    zona = tk.Frame(ventana, bg=FONDO)
    zona.pack(fill="both", expand=True, padx=32, pady=(10, 24))
    zona.columnconfigure(0, weight=1, uniform="col")
    zona.columnconfigure(1, weight=1, uniform="col")
    zona.rowconfigure(0, weight=1)

    Tarjeta(
        zona, COLOR_VERDE, "₡", "Ingresos y egresos",
        "Registra tus movimientos del día y del mes y mira en qué gastas.",
        lambda: _abrir("interfaz.app_transacciones"),
    ).grid(row=0, column=0, sticky="nsew", padx=(0, 8))

    Tarjeta(
        zona, COLOR_AZUL, "★", "Metas financieras",
        "Define objetivos de ahorro, registra aportes y sigue tu progreso.",
        lambda: _abrir("interfaz.app_metas"),
    ).grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    ventana.mainloop()


if __name__ == "__main__":
    main()