"""Listado, búsqueda, detalle y formularios de propietarios sin SQL en la vista."""

import tkinter as tk
from tkinter import ttk

from .formulario import Formulario


CAMPOS = (
    ("nombre", "Nombre"), ("documento", "Documento"), ("telefono", "Teléfono"),
    ("correo", "Correo"), ("direccion", "Dirección"),
)


class Propietarios(ttk.Frame):
    def __init__(self, master, propietarios, puede_gestionar, on_buscar, on_seleccionar,
                 on_registrar, on_editar, on_volver, busqueda="", seleccionar=None):
        super().__init__(master, padding=24)
        self._on_buscar = on_buscar
        self._on_seleccionar = on_seleccionar
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        ttk.Label(self, text="Gestor De Veterinaria", font=("Arial", 20, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        ttk.Label(
            self, text="Propietarios" if puede_gestionar else "Propietarios — solo consulta",
            font=("Arial", 14, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))
        filtro = ttk.Frame(self)
        filtro.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        filtro.columnconfigure(0, weight=1)
        ttk.Label(filtro, text="Buscar por nombre o documento").grid(row=0, column=0, sticky="w")
        self.busqueda = tk.StringVar(self, value=busqueda)
        self.entrada_busqueda = ttk.Entry(filtro, textvariable=self.busqueda)
        self.entrada_busqueda.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.entrada_busqueda.bind("<Return>", self.buscar)
        self.boton_buscar = ttk.Button(filtro, text="Buscar", command=self.buscar)
        self.boton_buscar.grid(row=1, column=1, padx=3)
        self.boton_limpiar = ttk.Button(filtro, text="Mostrar todos", command=self.limpiar_busqueda)
        self.boton_limpiar.grid(row=1, column=2, padx=3)
        contenedor = ttk.Frame(self)
        contenedor.grid(row=3, column=0, sticky="nsew")
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)
        self.tabla = ttk.Treeview(
            contenedor, columns=tuple(clave for clave, _ in CAMPOS),
            show="headings", selectmode="browse", height=6,
        )
        for clave, etiqueta in CAMPOS:
            self.tabla.heading(clave, text=etiqueta)
            self.tabla.column(clave, width=150, minwidth=90)
        vertical = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        panel_detalle = ttk.LabelFrame(self, text="Datos del propietario seleccionado", padding=6)
        panel_detalle.grid(row=4, column=0, sticky="ew", pady=8)
        panel_detalle.columnconfigure(0, weight=1)
        self.detalle = tk.Text(panel_detalle, height=5, wrap="word", state="disabled", width=1)
        barra_detalle = ttk.Scrollbar(panel_detalle, orient="vertical", command=self.detalle.yview)
        self.detalle.configure(yscrollcommand=barra_detalle.set)
        self.detalle.grid(row=0, column=0, sticky="ew")
        barra_detalle.grid(row=0, column=1, sticky="ns")
        self.mensaje = tk.StringVar(self, value=f"Propietarios encontrados: {len(propietarios)}")
        ttk.Label(self, textvariable=self.mensaje, wraplength=510).grid(row=5, column=0, sticky="w", pady=4)
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=510).grid(
            row=6, column=0, sticky="w", pady=4
        )
        acciones = ttk.Frame(self)
        acciones.grid(row=7, column=0, sticky="ew", pady=6)
        acciones.columnconfigure(0, weight=1)
        acciones.columnconfigure(1, weight=1)
        self.boton_registrar = None
        self.boton_editar = None
        if puede_gestionar:
            self.boton_registrar = ttk.Button(acciones, text="Registrar propietario", command=on_registrar)
            self.boton_registrar.grid(row=0, column=0, sticky="ew", padx=(0, 4))
            self.boton_editar = ttk.Button(
                acciones, text="Editar seleccionado", state="disabled",
                command=lambda: self._editar(on_editar),
            )
            self.boton_editar.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(self, text="Volver al panel", command=on_volver).grid(row=8, column=0, sticky="ew", pady=4)
        for propietario in propietarios:
            self.tabla.insert("", "end", iid=str(propietario.id), values=tuple(
                getattr(propietario, clave) or "" for clave, _ in CAMPOS
            ))
        self.mostrar_detalle(None)
        self.tabla.bind("<<TreeviewSelect>>", self._cambio_seleccion)
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))
        self.entrada_busqueda.focus_set()

    def buscar(self, event=None):
        self._on_buscar(self.busqueda.get())
        return "break"

    def limpiar_busqueda(self):
        self._on_buscar("")

    def _cambio_seleccion(self, event=None):
        seleccion = self.tabla.selection()
        if self.boton_editar is not None:
            self.boton_editar.state(["!disabled"] if seleccion else ["disabled"])
        if seleccion:
            self._on_seleccionar(int(seleccion[0]))
        else:
            self.mostrar_detalle(None)

    def _editar(self, callback):
        seleccion = self.tabla.selection()
        if seleccion:
            callback(int(seleccion[0]))
        else:
            self.mostrar_error("Seleccione un propietario de la tabla.")

    def mostrar_detalle(self, propietario):
        texto = "Seleccione una fila para consultar todos sus datos."
        if propietario is not None:
            texto = "\n".join(
                f"{etiqueta}: {getattr(propietario, clave) or 'Sin registrar'}" for clave, etiqueta in CAMPOS
            )
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", texto)
        self.detalle.configure(state="disabled")

    def mostrar_error(self, mensaje):
        self.error.set(mensaje)


class FormularioPropietario(Formulario):
    def __init__(self, master, on_submit, on_cancel, propietario=None):
        super().__init__(
            master, "Registrar propietario" if propietario is None else "Editar propietario",
            "Nombre y documento son obligatorios. Los demás campos son opcionales.",
            tuple((clave, etiqueta, False) for clave, etiqueta in CAMPOS),
            "Guardar propietario", on_submit, on_cancel=on_cancel,
        )
        if propietario is not None:
            for clave, _ in CAMPOS:
                self.valores[clave].set(getattr(propietario, clave) or "")
