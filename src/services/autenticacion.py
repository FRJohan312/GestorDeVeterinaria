"""Configuración inicial, autenticación y autorización sin depender de Tkinter."""

from pathlib import Path

from database import DB_PATH
from database.usuarios import RepositorioUsuarios, acceso_usuarios
from models.usuario import UsuarioAutenticado
from .permisos import PERMISOS_POR_ROL
from .seguridad import generar_hash_contrasena, verificar_contrasena


class ErrorValidacion(ValueError):
    """Los datos del formulario no cumplen las reglas de entrada."""


class ErrorAutenticacion(ValueError):
    """Credenciales inválidas o cuenta no disponible."""


class ConfiguracionInicialCerrada(ValueError):
    """Ya existe algún usuario; la configuración inicial no puede repetirse."""


class PermisoDenegado(PermissionError):
    """La sesión no autoriza la operación solicitada."""


def _usuario_publico(fila) -> UsuarioAutenticado:
    return UsuarioAutenticado(
        id=fila["id"], nombre=fila["nombre"],
        nombre_usuario=fila["nombre_usuario"], rol=fila["rol"],
    )


class ServicioAutenticacion:
    def __init__(self, ruta: str | Path = DB_PATH):
        self.ruta = ruta
        self._usuario_actual: UsuarioAutenticado | None = None

    @property
    def usuario_actual(self) -> UsuarioAutenticado | None:
        return self._usuario_actual

    def requiere_configuracion(self) -> bool:
        with acceso_usuarios(self.ruta) as usuarios:
            return not usuarios.existen()

    def crear_primer_administrador(
        self, nombre: str, nombre_usuario: str, contrasena: str, confirmacion: str
    ) -> int:
        if not self.requiere_configuracion():
            raise ConfiguracionInicialCerrada("La configuración inicial ya fue realizada. Inicie sesión.")
        if any(not isinstance(valor, str) or not valor.strip()
               for valor in (nombre, nombre_usuario, contrasena, confirmacion)):
            raise ErrorValidacion("Complete todos los campos.")
        if len(contrasena) < 8:
            raise ErrorValidacion("La contraseña debe tener al menos 8 caracteres.")
        if contrasena != confirmacion:
            raise ErrorValidacion("La contraseña y su confirmación no coinciden.")
        resumen = generar_hash_contrasena(contrasena)
        with acceso_usuarios(self.ruta, escritura=True) as usuarios:
            # La comprobación se repite bajo el bloqueo de escritura, antes del alta.
            if usuarios.existen():
                raise ConfiguracionInicialCerrada("La configuración inicial ya fue realizada. Inicie sesión.")
            return usuarios.crear(nombre.strip(), nombre_usuario.strip(), resumen, "ADMINISTRADOR")

    def iniciar_sesion(self, nombre_usuario: str, contrasena: str) -> UsuarioAutenticado:
        self.cerrar_sesion()
        if (not isinstance(nombre_usuario, str) or not nombre_usuario.strip()
                or not isinstance(contrasena, str) or not contrasena.strip()):
            raise ErrorValidacion("Ingrese el nombre de usuario y la contraseña.")
        with acceso_usuarios(self.ruta) as usuarios:
            fila = usuarios.buscar_por_nombre(nombre_usuario.strip())
        if (fila is None or not verificar_contrasena(contrasena, fila["contrasena_hash"])
                or not fila["activo"] or fila["rol"] not in PERMISOS_POR_ROL):
            raise ErrorAutenticacion("Usuario o contraseña incorrectos, o cuenta desactivada.")
        self._usuario_actual = _usuario_publico(fila)
        return self._usuario_actual

    def cerrar_sesion(self) -> None:
        self._usuario_actual = None

    def permisos_actuales(self, *, usuarios: RepositorioUsuarios | None = None) -> frozenset[str]:
        """Revalida actividad y rol en SQLite antes de autorizar una operación."""
        if self._usuario_actual is None:
            raise PermisoDenegado("Debe iniciar sesión para continuar.")
        if usuarios is None:
            with acceso_usuarios(self.ruta) as repositorio:
                return self.permisos_actuales(usuarios=repositorio)
        fila = usuarios.buscar_por_id(self._usuario_actual.id)
        if fila is None or not fila["activo"] or fila["rol"] not in PERMISOS_POR_ROL:
            self.cerrar_sesion()
            raise PermisoDenegado("La cuenta ya no está disponible. Inicie sesión nuevamente.")
        self._usuario_actual = _usuario_publico(fila)
        return PERMISOS_POR_ROL[self._usuario_actual.rol]

    def exigir_permiso(self, permiso: str, *, usuarios: RepositorioUsuarios | None = None) -> None:
        """Cada futuro servicio debe invocarlo antes de ejecutar su operación."""
        if permiso not in self.permisos_actuales(usuarios=usuarios):
            raise PermisoDenegado("Su usuario no tiene permiso para realizar esta operación.")
