"""Navegación de una sola ventana, con sesión compartida en memoria."""

import sqlite3
import tkinter as tk
from tkinter import messagebox

from services.autenticacion import (
    ConfiguracionInicialCerrada, ErrorAutenticacion, ErrorValidacion,
    PermisoDenegado, ServicioAutenticacion,
)
from services.prototipo import contar_registros, guardar_prueba
from services.usuarios import ServicioUsuarios
from .configuracion_inicial import ConfiguracionInicial
from .dashboard import Dashboard
from .login import Login
from .pruebas import Pruebas
from .usuarios import FormularioContrasena, FormularioUsuario, Usuarios


ERROR_DATOS = "No se pudo acceder a los datos. Compruebe que el archivo esté disponible e inténtelo de nuevo."


class Aplicacion(tk.Tk):
    def __init__(self, autenticacion: ServicioAutenticacion):
        super().__init__()
        self.autenticacion = autenticacion
        self.servicio_usuarios = ServicioUsuarios(autenticacion)
        self.vista = None
        self.title("Gestor De Veterinaria")
        self.geometry("660x620")
        self.minsize(560, 580)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        try:
            if autenticacion.requiere_configuracion():
                self._cambiar_vista(ConfiguracionInicial, on_submit=self._crear_administrador)
            else:
                self.mostrar_login()
        except sqlite3.Error:
            messagebox.showerror("Gestor De Veterinaria", ERROR_DATOS, parent=self)
            self.destroy()
            raise

    def _cambiar_vista(self, clase, **opciones):
        if self.vista is not None:
            self.vista.destroy()
        self.vista = clase(self, **opciones)
        self.vista.pack(fill="both", expand=True)

    def mostrar_login(self, mensaje=""):
        self._cambiar_vista(Login, on_submit=self._iniciar_sesion)
        self.vista.mostrar_error(mensaje)

    def _crear_administrador(self, **datos):
        try:
            self.autenticacion.crear_primer_administrador(**datos)
        except ConfiguracionInicialCerrada as error:
            self.mostrar_login(str(error))
        except ErrorValidacion as error:
            self.vista.mostrar_error(str(error))
        except sqlite3.Error:
            self.vista.mostrar_error(ERROR_DATOS)
        else:
            self.vista.limpiar_secretos()
            self.mostrar_login()

    def _iniciar_sesion(self, **datos):
        try:
            self.autenticacion.iniciar_sesion(**datos)
        except (ErrorValidacion, ErrorAutenticacion) as error:
            self.vista.mostrar_error(str(error))
        except sqlite3.Error:
            self.vista.mostrar_error(ERROR_DATOS)
        else:
            self.vista.limpiar_secretos()
            self.mostrar_dashboard()

    def mostrar_dashboard(self):
        try:
            permisos = self.autenticacion.permisos_actuales()
        except PermisoDenegado as error:
            self._acceso_denegado(str(error))
        except sqlite3.Error:
            self.cerrar_sesion()
            self.vista.mostrar_error(ERROR_DATOS)
        else:
            self._cambiar_vista(
                Dashboard, usuario=self.autenticacion.usuario_actual, permisos=permisos,
                on_pruebas=self.mostrar_pruebas, on_logout=self.cerrar_sesion,
                on_usuarios=self.mostrar_usuarios,
            )

    def _operar_usuarios(self, operacion, al_completar):
        try:
            resultado = operacion()
        except PermisoDenegado as error:
            self._acceso_denegado(str(error))
        except ErrorValidacion as error:
            self.vista.mostrar_error(str(error))
        except sqlite3.Error:
            messagebox.showerror("Gestor De Veterinaria", ERROR_DATOS, parent=self)
        else:
            if self.autenticacion.usuario_actual is None:
                self.mostrar_login("Su sesión ha finalizado tras modificar su cuenta. Inicie sesión nuevamente.")
            else:
                al_completar(resultado)

    def mostrar_usuarios(self, mensaje=""):
        def mostrar(usuarios):
            self._cambiar_vista(
                Usuarios, usuarios=usuarios, on_registrar=self._registrar_usuario,
                on_editar=self._editar_usuario, on_estado=self._cambiar_estado_usuario,
                on_contrasena=self._cambiar_contrasena_usuario,
                on_actualizar=self.mostrar_usuarios, on_volver=self.mostrar_dashboard,
            )
            self.vista.mensaje.set(mensaje)
        self._operar_usuarios(self.servicio_usuarios.listar, mostrar)

    def _registrar_usuario(self):
        def mostrar(_):
            self._cambiar_vista(
                FormularioUsuario, on_submit=self._guardar_usuario_nuevo,
                on_cancel=self.mostrar_usuarios,
            )
        self._operar_usuarios(self.servicio_usuarios.listar, mostrar)

    def _guardar_usuario_nuevo(self, **datos):
        self._operar_usuarios(
            lambda: self.servicio_usuarios.registrar(**datos),
            lambda _: self.mostrar_usuarios("Usuario registrado correctamente."),
        )

    def _editar_usuario(self, usuario_id):
        def mostrar(usuario):
            self._cambiar_vista(
                FormularioUsuario, usuario=usuario, on_cancel=self.mostrar_usuarios,
                on_submit=lambda **datos: self._operar_usuarios(
                    lambda: self.servicio_usuarios.modificar(usuario_id, **datos),
                    lambda _: self.mostrar_usuarios("Usuario actualizado correctamente."),
                ),
            )
        self._operar_usuarios(lambda: self.servicio_usuarios.obtener(usuario_id), mostrar)

    def _cambiar_estado_usuario(self, usuario_id):
        def confirmar(usuario):
            accion = "desactivar" if usuario.activo else "activar"
            if messagebox.askyesno(
                "Gestor De Veterinaria", f"¿Desea {accion} la cuenta {usuario.nombre_usuario}?", parent=self
            ):
                self._operar_usuarios(
                    lambda: self.servicio_usuarios.cambiar_estado(usuario_id, not usuario.activo),
                    lambda _: self.mostrar_usuarios("Estado actualizado correctamente."),
                )
        self._operar_usuarios(lambda: self.servicio_usuarios.obtener(usuario_id), confirmar)

    def _cambiar_contrasena_usuario(self, usuario_id):
        def mostrar(usuario):
            self._cambiar_vista(
                FormularioContrasena, usuario=usuario, on_cancel=self.mostrar_usuarios,
                on_submit=lambda **datos: self._operar_usuarios(
                    lambda: self.servicio_usuarios.cambiar_contrasena(usuario_id, **datos),
                    lambda _: self.mostrar_usuarios("Contraseña actualizada correctamente."),
                ),
            )
        self._operar_usuarios(lambda: self.servicio_usuarios.obtener(usuario_id), mostrar)

    def mostrar_pruebas(self):
        try:
            cantidad = contar_registros(self.autenticacion)
        except PermisoDenegado as error:
            self._acceso_denegado(str(error))
        except sqlite3.Error:
            messagebox.showerror("Gestor De Veterinaria", ERROR_DATOS, parent=self)
        else:
            self._cambiar_vista(
                Pruebas, cantidad=cantidad, on_guardar=self._guardar_prueba,
                on_volver=self.mostrar_dashboard,
            )

    def _guardar_prueba(self):
        try:
            guardar_prueba(self.autenticacion)
            cantidad = contar_registros(self.autenticacion)
        except PermisoDenegado as error:
            self._acceso_denegado(str(error))
        except sqlite3.Error:
            self.vista.mostrar_error(ERROR_DATOS)
        else:
            self.vista.actualizar(cantidad)

    def _acceso_denegado(self, mensaje):
        self.autenticacion.cerrar_sesion()
        self.mostrar_login(mensaje)

    def cerrar_sesion(self):
        self.autenticacion.cerrar_sesion()
        self.mostrar_login()

    def destroy(self):
        self.autenticacion.cerrar_sesion()
        super().destroy()
