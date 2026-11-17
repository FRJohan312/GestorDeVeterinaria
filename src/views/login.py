"""Formulario de inicio de sesión."""

from .formulario import Formulario


class Login(Formulario):
    def __init__(self, master, on_submit):
        super().__init__(
            master, "Iniciar sesión", "Ingrese los datos de su cuenta para continuar.",
            (("nombre_usuario", "Nombre de usuario", False), ("contrasena", "Contraseña", True)),
            "Iniciar sesión", on_submit,
        )
