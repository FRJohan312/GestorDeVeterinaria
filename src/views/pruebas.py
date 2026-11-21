"""Vista separada del contador original; mantiene su tabla y su funcionamiento."""

import tkinter as tk
from tkinter import ttk


class Pruebas(ttk.Frame):
    def __init__(self, master, cantidad, on_guardar, on_volver):
        super().__init__(master, padding=30)
        # ttk.Label(self, text="Pruebas del prototipo", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(self, text="Nada que ver aquí", font=("Arial", 20, "bold")).pack(pady=12)
    #     self.estado = tk.StringVar(self)
    #     self.actualizar(cantidad)
    #     ttk.Label(self, textvariable=self.estado).pack(pady=10)
    #     self.boton_guardar = ttk.Button(self, text="Guardar dato de prueba", command=on_guardar)
    #     self.boton_guardar.pack(pady=10)
    #     self.error = tk.StringVar(self)
    #     ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=500).pack(pady=8)
    #     ttk.Button(self, text="Volver al panel", command=on_volver).pack(pady=10)

    # def actualizar(self, cantidad):
    #     self.estado.set(f"Registros guardados: {cantidad}")

    # def mostrar_error(self, mensaje):
    #     self.error.set(mensaje)
