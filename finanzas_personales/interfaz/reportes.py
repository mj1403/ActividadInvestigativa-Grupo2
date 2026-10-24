import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO))

from modulos import reportes as modulo_reportes


PATRON_CORREO = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def ventana_reportes(parent=None):
    propia = parent is None
    root = tk.Tk() if propia else tk.Toplevel(parent)
    root.title("Reportes")
    root.resizable(False, False)

    marco = ttk.Frame(root, padding=18)
    marco.grid(row=0, column=0, sticky="nsew")

    ttk.Label(marco, text="Periodo:").grid(
        row=0, column=0, sticky="w", padx=(0, 12), pady=(0, 10)
    )

    periodo = tk.StringVar(value="semanal")
    ttk.Radiobutton(
        marco, text="Últimos 7 días", variable=periodo, value="semanal"
    ).grid(row=0, column=1, sticky="w", pady=(0, 10))
    ttk.Radiobutton(
        marco, text="Todo", variable=periodo, value="inmediato"
    ).grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 10))

    ttk.Label(marco, text="Correo:").grid(
        row=1, column=0, sticky="w", padx=(0, 12), pady=(0, 8)
    )
    correo = tk.StringVar()
    entrada_correo = ttk.Entry(marco, textvariable=correo, width=42)
    entrada_correo.grid(
        row=1, column=1, columnspan=2, sticky="ew", pady=(0, 8)
    )

    estado = tk.StringVar(value="")
    etiqueta_estado = ttk.Label(
        marco, textvariable=estado, wraplength=360
    )
    etiqueta_estado.grid(
        row=3, column=0, columnspan=3, sticky="w", pady=(10, 0)
    )

    def finalizar_envio(exito, detalle):
        boton.configure(state="normal", text="Enviar reporte al correo")
        if exito:
            estado.set(f"Reporte enviado a {detalle}")
            messagebox.showinfo(
                "Reporte enviado",
                f"El reporte se envió correctamente a {detalle}.",
                parent=root,
            )
        else:
            estado.set("No se pudo enviar el reporte.")
            messagebox.showerror(
                "Error al enviar el reporte",
                detalle,
                parent=root,
            )

    def enviar_en_hilo(destinatario, periodo_elegido):
        try:
            modulo_reportes.enviar_reporte(destinatario, periodo_elegido)
        except Exception as error:
            detalle = str(error) or "Ocurrió un error al enviar el reporte."
            root.after(0, lambda detalle=detalle: finalizar_envio(False, detalle))
        else:
            root.after(
                0,
                lambda destinatario=destinatario: finalizar_envio(
                    True, destinatario
                ),
            )

    def al_enviar():
        destinatario = correo.get().strip()
        periodo_elegido = periodo.get()

        if not destinatario or not PATRON_CORREO.match(destinatario):
            messagebox.showwarning(
                "Correo inválido",
                "Escribe una dirección de correo válida.",
                parent=root,
            )
            entrada_correo.focus_set()
            return

        boton.configure(state="disabled", text="Enviando...")
        estado.set("Enviando reporte, por favor espera...")
        hilo = threading.Thread(
            target=enviar_en_hilo,
            args=(destinatario, periodo_elegido),
            daemon=True,
        )
        hilo.start()

    boton = ttk.Button(
        marco,
        text="Enviar reporte al correo",
        command=al_enviar,
    )
    boton.grid(
        row=2, column=1, columnspan=2, sticky="ew", pady=(2, 0)
    )

    entrada_correo.focus_set()
    if propia:
        root.mainloop()
    return root


if __name__ == "__main__":
    ventana_reportes()
