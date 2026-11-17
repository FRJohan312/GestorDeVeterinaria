"""Tabla y formularios de administración de cuentas, sin acceso directo a SQLite."""

import tkinter as tk
from tkinter import ttk

from services.usuarios import ROLES
from .formulario import Formulario


class Usuarios(ttk.Frame):
    def __init__(self, master, usuarios, on_registrar, on_editar, on_estado,
                 on_contrasena, on_actualizar, on_volver):
        super().__init__(master, padding=24)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        ttk.Label(self, text="Gestor De Veterinaria", font=("Arial", 20, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )
        ttk.Label(self, text="Gestión de usuarios", font=("Arial", 14, "bold")).grid(
            row=1, column=0, sticky="w", pady=(0, 12)
        )
        contenedor = ttk.Frame(self)
        contenedor.grid(row=2, column=0, sticky="nsew")
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(
            contenedor, columns=("nombre", "usuario", "rol", "estado"),
            show="headings", selectmode="browse", height=9,
        )
        for clave, titulo, ancho in (
            ("nombre", "Nombre", 150), ("usuario", "Nombre de usuario", 140),
            ("rol", "Rol", 150), ("estado", "Estado", 85),
        ):
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=ancho, minwidth=80)
        vertical = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        acciones = ttk.Frame(self)
        acciones.grid(row=3, column=0, sticky="ew", pady=12)
        for columna in range(2):
            acciones.columnconfigure(columna, weight=1)
        self.boton_registrar = ttk.Button(acciones, text="Registrar usuario", command=on_registrar)
        self.boton_editar = ttk.Button(acciones, text="Editar", command=lambda: self._seleccionar(on_editar))
        self.boton_estado = ttk.Button(acciones, text="Activar / desactivar", command=lambda: self._seleccionar(on_estado))
        self.boton_contrasena = ttk.Button(acciones, text="Cambiar contraseña", command=lambda: self._seleccionar(on_contrasena))
        for indice, boton in enumerate((self.boton_registrar, self.boton_editar, self.boton_estado, self.boton_contrasena)):
            boton.grid(row=indice // 2, column=indice % 2, sticky="ew", padx=4, pady=4)
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=510).grid(
            row=4, column=0, sticky="w", pady=4
        )
        self.mensaje = tk.StringVar(self)
        ttk.Label(self, textvariable=self.mensaje, wraplength=510).grid(row=5, column=0, sticky="w", pady=4)
        ttk.Button(self, text="Actualizar lista", command=on_actualizar).grid(row=6, column=0, sticky="ew", pady=4)
        ttk.Button(self, text="Volver al panel", command=on_volver).grid(row=7, column=0, sticky="ew", pady=4)
        self.tabla.bind("<<TreeviewSelect>>", self._cambio_seleccion)
        self.actualizar(usuarios)

    def actualizar(self, usuarios, seleccionar=None):
        self._usuarios = {usuario.id: usuario for usuario in usuarios}
        self.tabla.delete(*self.tabla.get_children())
        for usuario in usuarios:
            self.tabla.insert("", "end", iid=str(usuario.id), values=(
                usuario.nombre, usuario.nombre_usuario, usuario.rol, "Activo" if usuario.activo else "Inactivo",
            ))
        if seleccionar in self._usuarios:
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))
        self._cambio_seleccion()

    def _cambio_seleccion(self, event=None):
        seleccion = self.tabla.selection()
        for boton in (self.boton_editar, self.boton_estado, self.boton_contrasena):
            boton.state(["!disabled"] if seleccion else ["disabled"])
        if seleccion:
            usuario = self._usuarios[int(seleccion[0])]
            self.boton_estado.configure(text="Desactivar cuenta" if usuario.activo else "Activar cuenta")

    def _seleccionar(self, callback):
        seleccion = self.tabla.selection()
        if seleccion:
            self.mostrar_error("")
            callback(int(seleccion[0]))
        else:
            self.mostrar_error("Seleccione un usuario de la tabla.")

    def mostrar_error(self, mensaje):
        self.mensaje.set("")
        self.error.set(mensaje)


class FormularioUsuario(Formulario):
    def __init__(self, master, on_submit, on_cancel, usuario=None):
        campos = [
            ("nombre", "Nombre completo", False),
            ("nombre_usuario", "Nombre de usuario", False),
            ("rol", "Rol", False),
        ]
        if usuario is None:
            campos.extend((
                ("contrasena", "Contraseña (mínimo 8 caracteres)", True),
                ("confirmacion", "Confirmar contraseña", True),
            ))
        super().__init__(
            master, "Registrar usuario" if usuario is None else "Editar usuario",
            "Complete los datos de la cuenta.", campos, "Guardar", on_submit,
            opciones={"rol": ROLES}, on_cancel=on_cancel,
        )
        self.valores["rol"].set("VETERINARIO" if usuario is None else usuario.rol)
        if usuario is not None:
            self.valores["nombre"].set(usuario.nombre)
            self.valores["nombre_usuario"].set(usuario.nombre_usuario)


class FormularioContrasena(Formulario):
    def __init__(self, master, usuario, on_submit, on_cancel):
        super().__init__(
            master, "Cambiar contraseña", f"Cuenta: {usuario.nombre_usuario}",
            (("contrasena", "Nueva contraseña (mínimo 8 caracteres)", True),
             ("confirmacion", "Confirmar contraseña", True)),
            "Guardar contraseña", on_submit, on_cancel=on_cancel,
        )
