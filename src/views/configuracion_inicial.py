"""Alta del único administrador permitido por el procedimiento inicial."""

from .formulario import Formulario


class ConfiguracionInicial(Formulario):
    def __init__(self, master, on_submit):
        super().__init__(
            master, "Configuración inicial",
            "Cree el primer administrador. Este formulario solo está disponible si no existen usuarios.",
            (
                ("nombre", "Nombre completo", False),
                ("nombre_usuario", "Nombre de usuario", False),
                ("contrasena", "Contraseña (mínimo 8 caracteres)", True),
                ("confirmacion", "Confirmar contraseña", True),
            ),
            "Crear administrador", on_submit,
        )
