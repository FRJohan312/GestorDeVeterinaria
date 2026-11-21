"""Listado, detalle y alta de tratamientos con callbacks de servicios."""

import tkinter as tk
from tkinter import ttk

from .formulario import Formulario


def informacion_consulta(consulta):
    return (f"Consulta #{consulta.id} — {consulta.fecha}\nMascota: {consulta.mascota_nombre}\n"
            f"Veterinario responsable: {consulta.veterinario_nombre}")


class Tratamientos(ttk.Frame):
    alto_minimo = 740

    def __init__(self, master, consulta, tratamientos, puede_registrar, on_seleccionar,
                 on_registrar, on_volver, seleccionar=None):
        super().__init__(master, padding=20)
        self.consulta = consulta
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        ttk.Label(self, text="Gestión de Tratamientos", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Tratamientos", font=("Arial", 14, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        ttk.Label(self, text=informacion_consulta(consulta), wraplength=510).grid(row=2, column=0, sticky="w", pady=6)
        panel = ttk.Frame(self)
        panel.grid(row=3, column=0, sticky="nsew", pady=8)
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        campos = (("descripcion", "Descripción"), ("medicamento", "Medicamento"),
                  ("dosis", "Dosis"), ("duracion", "Duración"))
        self.tabla = ttk.Treeview(panel, columns=tuple(c for c, _ in campos), show="headings", selectmode="browse", height=5)
        for clave, etiqueta in campos:
            self.tabla.heading(clave, text=etiqueta)
            self.tabla.column(clave, width=180, minwidth=100)
        vertical = ttk.Scrollbar(panel, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(panel, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        detalle = ttk.LabelFrame(self, text="Detalle del tratamiento — solo lectura", padding=4)
        detalle.grid(row=4, column=0, sticky="ew", pady=6)
        detalle.columnconfigure(0, weight=1)
        self.detalle = tk.Text(detalle, height=9, width=1, wrap="word", state="disabled")
        barra = ttk.Scrollbar(detalle, orient="vertical", command=self.detalle.yview)
        self.detalle.configure(yscrollcommand=barra.set)
        self.detalle.grid(row=0, column=0, sticky="ew")
        barra.grid(row=0, column=1, sticky="ns")
        self.mensaje = tk.StringVar(self, value=f"Tratamientos registrados: {len(tratamientos)}")
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.mensaje, wraplength=510).grid(row=5, column=0, sticky="w", pady=3)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=510).grid(row=6, column=0, sticky="w", pady=3)
        self.boton_registrar = None
        if puede_registrar:
            self.boton_registrar = ttk.Button(self, text="Agregar tratamiento", command=on_registrar)
            self.boton_registrar.grid(row=7, column=0, sticky="ew", pady=4)
        self.boton_volver = ttk.Button(self, text="Volver a la consulta", command=on_volver)
        self.boton_volver.grid(row=8, column=0, sticky="ew", pady=4)
        for tratamiento in tratamientos:
            self.tabla.insert("", "end", iid=str(tratamiento.id), values=tuple(
                getattr(tratamiento, c) or "" for c, _ in campos
            ))
        self.mostrar_detalle(None)

        def seleccion(event=None):
            self.mostrar_detalle(None)
            if self.tabla.selection():
                on_seleccionar(int(self.tabla.selection()[0]))

        self.tabla.bind("<<TreeviewSelect>>", seleccion)
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))

    def mostrar_detalle(self, tratamiento):
        texto = "Seleccione un tratamiento para consultar sus datos."
        if tratamiento is not None:
            texto = (f"Tratamiento #{tratamiento.id} — Consulta #{tratamiento.consulta_id}\n\n"
                     f"Descripción:\n{tratamiento.descripcion}\n\nMedicamento:\n{tratamiento.medicamento or 'Sin registrar'}\n\n"
                     f"Dosis:\n{tratamiento.dosis or 'Sin registrar'}\n\nDuración:\n{tratamiento.duracion or 'Sin registrar'}")
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", texto)
        self.detalle.configure(state="disabled")

    def mostrar_error(self, mensaje):
        self.error.set(mensaje)


class FormularioTratamiento(Formulario):
    alto_minimo = 740

    def __init__(self, master, consulta, on_submit, on_cancel):
        def enviar(**datos):
            datos["descripcion"] = self.entradas["descripcion"].get("1.0", "end-1c")
            on_submit(**datos)

        super().__init__(
            master, "Registrar tratamiento", informacion_consulta(consulta),
            (("descripcion", "Descripción (obligatoria)", False),
             ("medicamento", "Medicamento (opcional)", False),
             ("dosis", "Dosis (opcional)", False), ("duracion", "Duración (opcional)", False)),
            "Guardar tratamiento", enviar, on_cancel=on_cancel,
            constructores={"descripcion": lambda m, v: tk.Text(m, height=4, width=1, wrap="word")},
        )
