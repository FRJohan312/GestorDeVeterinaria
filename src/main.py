"""Punto de entrada de la aplicación de escritorio."""

import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox

from services.autenticacion import ServicioAutenticacion
from services.prototipo import inicializar_aplicacion
from views.aplicacion import Aplicacion, ERROR_DATOS


def main() -> int:
    try:
        inicializar_aplicacion()
    except sqlite3.Error:
        ventana = tk.Tk()
        ventana.withdraw()
        messagebox.showerror("VetSoft", ERROR_DATOS, parent=ventana)
        ventana.destroy()
        return 1
    try:
        ventana = Aplicacion(ServicioAutenticacion())
    except sqlite3.Error:
        return 1
    ventana.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
