"""Elementos compartidos de los formularios de acceso."""

import tkinter as tk
from tkinter import ttk


class Formulario(ttk.Frame):
    def __init__(self, master, titulo, descripcion, campos, texto_boton, on_submit,
                 *, opciones=None, on_cancel=None, constructores=None):
        super().__init__(master, padding=30)
        self._on_submit = on_submit
        self._enviando = False
        self.valores = {}
        self.entradas = {}
        self._secretos = []
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Gestor De Veterinaria", font=("Arial", 20, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )
        ttk.Label(self, text=titulo, font=("Arial", 14, "bold")).grid(row=1, column=0, sticky="w")
        ttk.Label(self, text=descripcion, wraplength=500).grid(
            row=2, column=0, sticky="w", pady=(6, 14)
        )
        fila = 3
        for clave, etiqueta, secreto in campos:
            ttk.Label(self, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=(6, 2))
            variable = tk.StringVar(self)
            if constructores and clave in constructores:
                entrada = constructores[clave](self, variable)
            elif opciones and clave in opciones:
                entrada = ttk.Combobox(self, textvariable=variable, values=opciones[clave], state="readonly")
            else:
                entrada = ttk.Entry(self, textvariable=variable, show="*" if secreto else "")
            entrada.grid(row=fila + 1, column=0, sticky="ew")
            if not isinstance(entrada, tk.Text):
                entrada.bind("<Return>", self.enviar)
            self.valores[clave] = variable
            self.entradas[clave] = entrada
            if secreto:
                self._secretos.append(clave)
            fila += 2
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=500).grid(
            row=fila, column=0, sticky="w", pady=(12, 4)
        )
        self.boton = ttk.Button(self, text=texto_boton, command=self.enviar)
        self.boton.grid(row=fila + 1, column=0, sticky="ew", pady=8)
        self.boton.bind("<Return>", self.enviar)
        if on_cancel is not None:
            ttk.Button(self, text="Cancelar", command=on_cancel).grid(
                row=fila + 2, column=0, sticky="ew", pady=4
            )
        next(iter(self.entradas.values())).focus_set()

    def mostrar_error(self, mensaje):
        self.error.set(mensaje)

    def limpiar_secretos(self):
        for clave in self._secretos:
            self.valores[clave].set("")

    def enviar(self, event=None):
        if self._enviando:
            return "break"
        self._enviando = True
        self.error.set("")
        self.boton.state(["disabled"])
        self.update_idletasks()
        try:
            self._on_submit(**{clave: variable.get() for clave, variable in self.valores.items()})
        finally:
            if self.winfo_exists():
                self.limpiar_secretos()
                self.boton.state(["!disabled"])
                self._enviando = False
        return "break"
