"""Listado y formularios de mascotas; el propietario se selecciona de datos locales."""

import tkinter as tk
from tkinter import ttk

from services.mascotas import SEXOS
from .formulario import Formulario


def etiqueta_propietario(propietario):
    return f"{propietario.nombre} — Documento: {propietario.documento}"


class Mascotas(ttk.Frame):
    def __init__(self, master, mascotas, propietarios, puede_gestionar, on_buscar,
                 on_seleccionar, on_registrar, on_editar, on_propietarios, on_volver,
                 busqueda="", propietario_id=None, seleccionar=None, on_historial=None):
        super().__init__(master, padding=20)
        self._propietarios = list(propietarios)
        self._on_buscar = on_buscar
        self._on_seleccionar = on_seleccionar
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        ttk.Label(self, text="Gestor De Veterinaria", font=("Arial", 20, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Label(self, text="Mascotas" if puede_gestionar else "Mascotas — solo consulta",
                  font=("Arial", 14, "bold")).grid(row=1, column=0, sticky="w", pady=(0, 6))
        filtro = ttk.Frame(self)
        filtro.grid(row=2, column=0, sticky="ew", pady=6)
        filtro.columnconfigure(0, weight=1)
        ttk.Label(filtro, text="Buscar por nombre, especie o propietario").grid(row=0, column=0, sticky="w")
        self.busqueda = tk.StringVar(self, value=busqueda)
        self.entrada_busqueda = ttk.Entry(filtro, textvariable=self.busqueda)
        self.entrada_busqueda.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.entrada_busqueda.bind("<Return>", self.buscar)
        self.boton_buscar = ttk.Button(filtro, text="Buscar", command=self.buscar)
        self.boton_buscar.grid(row=1, column=1, padx=3)
        self.boton_limpiar = ttk.Button(filtro, text="Mostrar todas", command=lambda: on_buscar("", None))
        self.boton_limpiar.grid(row=1, column=2, padx=3)
        ttk.Label(filtro, text="Propietario").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.selector_propietario = ttk.Combobox(
            filtro, state="readonly", values=("Todos los propietarios",) + tuple(
                etiqueta_propietario(p) for p in self._propietarios
            ),
        )
        self.selector_propietario.grid(row=3, column=0, columnspan=3, sticky="ew")
        self.selector_propietario.current(0)
        for indice, propietario in enumerate(self._propietarios, start=1):
            if propietario.id == propietario_id:
                self.selector_propietario.current(indice)
                break
        self.selector_propietario.bind("<<ComboboxSelected>>", self.buscar)
        contenedor = ttk.Frame(self)
        contenedor.grid(row=3, column=0, sticky="nsew", pady=6)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)
        columnas = (("nombre", "Nombre"), ("especie", "Especie"), ("raza", "Raza"),
                    ("sexo", "Sexo"), ("propietario_nombre", "Propietario"),
                    ("propietario_documento", "Documento del propietario"))
        self.tabla = ttk.Treeview(contenedor, columns=tuple(c for c, _ in columnas),
                                  show="headings", selectmode="browse", height=4)
        for clave, etiqueta in columnas:
            self.tabla.heading(clave, text=etiqueta)
            self.tabla.column(clave, width=150, minwidth=90)
        vertical = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        panel = ttk.LabelFrame(self, text="Detalle de la mascota", padding=4)
        panel.grid(row=4, column=0, sticky="ew", pady=4)
        panel.columnconfigure(0, weight=1)
        self.detalle = tk.Text(panel, height=4, width=1, wrap="word", state="disabled")
        barra = ttk.Scrollbar(panel, orient="vertical", command=self.detalle.yview)
        self.detalle.configure(yscrollcommand=barra.set)
        self.detalle.grid(row=0, column=0, sticky="ew")
        barra.grid(row=0, column=1, sticky="ns")
        self.mensaje = tk.StringVar(self, value=f"Mascotas encontradas: {len(mascotas)}")
        ttk.Label(self, textvariable=self.mensaje, wraplength=510).grid(row=5, column=0, sticky="w", pady=3)
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=510).grid(
            row=6, column=0, sticky="w", pady=3
        )
        acciones = ttk.Frame(self)
        acciones.grid(row=7, column=0, sticky="ew", pady=4)
        for columna in range(2):
            acciones.columnconfigure(columna, weight=1)
        self.boton_registrar = None
        self.boton_editar = None
        if puede_gestionar:
            self.boton_registrar = ttk.Button(acciones, text="Registrar mascota", command=on_registrar)
            self.boton_registrar.grid(row=0, column=0, sticky="ew", padx=(0, 4))
            self.boton_editar = ttk.Button(acciones, text="Editar seleccionada", state="disabled",
                                           command=lambda: self._editar(on_editar))
            self.boton_editar.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(acciones, text="Ir a propietarios", command=on_propietarios).grid(
            row=1, column=0, sticky="ew", padx=(0, 4), pady=4
        )
        ttk.Button(acciones, text="Volver", command=on_volver).grid(
            row=1, column=1, sticky="ew", padx=(4, 0), pady=4
        )
        self.boton_historial = None
        if on_historial is not None:
            self.boton_historial = ttk.Button(acciones, text="Ver historial médico", state="disabled",
                                             command=lambda: self._editar(on_historial))
            self.boton_historial.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        for mascota in mascotas:
            self.tabla.insert("", "end", iid=str(mascota.id), values=tuple(
                getattr(mascota, clave) or "" for clave, _ in columnas
            ))
        self.mostrar_detalle(None)
        self.tabla.bind("<<TreeviewSelect>>", self._cambio_seleccion)
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))
        if not propietarios:
            self.mensaje.set("No hay propietarios. Registre uno en Propietarios antes de crear mascotas.")
        self.entrada_busqueda.focus_set()

    def buscar(self, event=None):
        indice = self.selector_propietario.current()
        propietario_id = self._propietarios[indice - 1].id if indice > 0 else None
        self._on_buscar(self.busqueda.get(), propietario_id)
        return "break"

    def _cambio_seleccion(self, event=None):
        seleccion = self.tabla.selection()
        if self.boton_editar is not None:
            self.boton_editar.state(["!disabled"] if seleccion else ["disabled"])
        self.mostrar_detalle(None)
        if seleccion:
            self._on_seleccionar(int(seleccion[0]))

    def _editar(self, callback):
        seleccion = self.tabla.selection()
        if seleccion:
            callback(int(seleccion[0]))
        else:
            self.mostrar_error("Seleccione una mascota de la tabla.")

    def mostrar_detalle(self, mascota):
        if self.boton_historial is not None:
            self.boton_historial.state(["!disabled"] if mascota is not None else ["disabled"])
        texto = "Seleccione una mascota para consultar sus datos."
        if mascota is not None:
            texto = (f"Nombre: {mascota.nombre}\nEspecie: {mascota.especie}\n"
                     f"Raza: {mascota.raza or 'Sin registrar'}\nSexo: {mascota.sexo}\n"
                     f"Fecha de nacimiento: {mascota.fecha_nacimiento or 'Sin registrar'}\n"
                     f"Propietario: {mascota.propietario_nombre}\nDocumento: {mascota.propietario_documento}")
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", texto)
        self.detalle.configure(state="disabled")

    def mostrar_error(self, mensaje):
        self.error.set(mensaje)


class FormularioMascota(Formulario):
    alto_minimo = 700

    def __init__(self, master, propietarios, on_submit, on_cancel, mascota=None, propietario_id=None):
        self._propietarios = list(propietarios)

        def enviar_datos(**datos):
            indice = self.entradas["propietario_id"].current()
            datos["propietario_id"] = self._propietarios[indice].id if indice >= 0 else None
            on_submit(**datos)

        super().__init__(
            master, "Registrar mascota" if mascota is None else "Editar mascota",
            "Nombre, especie, sexo y propietario son obligatorios. Raza y fecha son opcionales.",
            (("nombre", "Nombre", False), ("especie", "Especie", False), ("raza", "Raza (opcional)", False),
             ("sexo", "Sexo", False), ("fecha_nacimiento", "Fecha de nacimiento (AAAA-MM-DD)", False),
             ("propietario_id", "Propietario", False)),
            "Guardar mascota", enviar_datos, opciones={
                "sexo": SEXOS, "propietario_id": tuple(etiqueta_propietario(p) for p in propietarios),
            }, on_cancel=on_cancel,
        )
        self.valores["sexo"].set("DESCONOCIDO")
        if mascota is not None:
            for campo in ("nombre", "especie", "raza", "sexo", "fecha_nacimiento"):
                self.valores[campo].set(getattr(mascota, campo) or "")
            propietario_id = mascota.propietario_id
        for indice, propietario in enumerate(self._propietarios):
            if propietario.id == propietario_id:
                self.entradas["propietario_id"].current(indice)
                break
