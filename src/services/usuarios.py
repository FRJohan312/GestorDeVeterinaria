"""Administración de cuentas con autorización y reglas transaccionales."""

from contextlib import contextmanager

from database.usuarios import acceso_usuarios
from models.usuario import UsuarioGestion
from .autenticacion import ErrorValidacion, ServicioAutenticacion
from .seguridad import generar_hash_contrasena


ROLES = ("ADMINISTRADOR", "VETERINARIO")


def _publico(fila) -> UsuarioGestion:
    return UsuarioGestion(
        id=fila["id"], nombre=fila["nombre"], nombre_usuario=fila["nombre_usuario"],
        rol=fila["rol"], activo=bool(fila["activo"]),
    )


class ServicioUsuarios:
    def __init__(self, autenticacion: ServicioAutenticacion):
        self.autenticacion = autenticacion

    @contextmanager
    def _acceso(self, *, escritura=False):
        with acceso_usuarios(self.autenticacion.ruta, escritura=escritura) as usuarios:
            # Se comprueba con la misma conexión y, al escribir, bajo BEGIN IMMEDIATE.
            self.autenticacion.exigir_permiso("gestionar_usuarios", usuarios=usuarios)
            yield usuarios

    def listar(self) -> list[UsuarioGestion]:
        with self._acceso() as usuarios:
            return [_publico(fila) for fila in usuarios.listar()]

    def obtener(self, usuario_id: int) -> UsuarioGestion:
        with self._acceso() as usuarios:
            return _publico(self._obtener(usuarios, usuario_id))

    def registrar(
        self, nombre: str, nombre_usuario: str, rol: str, contrasena: str, confirmacion: str
    ) -> UsuarioGestion:
        with self._acceso(escritura=True) as usuarios:
            nombre, nombre_usuario = self._validar_datos(nombre, nombre_usuario, rol)
            self._validar_nombre_unico(usuarios, nombre_usuario)
            self._validar_contrasena(contrasena, confirmacion)
            resumen = generar_hash_contrasena(contrasena)
            usuario_id = usuarios.crear(nombre, nombre_usuario, resumen, rol)
            return _publico(usuarios.buscar_por_id(usuario_id))

    def modificar(self, usuario_id: int, nombre: str, nombre_usuario: str, rol: str) -> UsuarioGestion:
        with self._acceso(escritura=True) as usuarios:
            actual = self._obtener(usuarios, usuario_id)
            nombre, nombre_usuario = self._validar_datos(nombre, nombre_usuario, rol)
            self._validar_nombre_unico(usuarios, nombre_usuario, usuario_id)
            self._proteger_administrador(usuarios, actual, rol, bool(actual["activo"]))
            if (actual["rol"] == "VETERINARIO" and rol != "VETERINARIO"
                    and usuarios.tiene_historial_veterinario(usuario_id)):
                raise ErrorValidacion("No se puede cambiar el rol de un veterinario con citas o consultas.")
            usuarios.modificar(usuario_id, nombre, nombre_usuario, rol)
            resultado = _publico(usuarios.buscar_por_id(usuario_id))
        self._cerrar_sesion_si_corresponde(resultado)
        return resultado

    def cambiar_estado(self, usuario_id: int, activo: bool) -> UsuarioGestion:
        with self._acceso(escritura=True) as usuarios:
            actual = self._obtener(usuarios, usuario_id)
            if not isinstance(activo, bool):
                raise ErrorValidacion("El estado debe ser activo o inactivo.")
            self._proteger_administrador(usuarios, actual, actual["rol"], activo)
            usuarios.cambiar_estado(usuario_id, activo)
            resultado = _publico(usuarios.buscar_por_id(usuario_id))
        self._cerrar_sesion_si_corresponde(resultado)
        return resultado

    def cambiar_contrasena(self, usuario_id: int, contrasena: str, confirmacion: str) -> None:
        with self._acceso(escritura=True) as usuarios:
            self._obtener(usuarios, usuario_id)
            self._validar_contrasena(contrasena, confirmacion)
            usuarios.cambiar_contrasena(usuario_id, generar_hash_contrasena(contrasena))

    @staticmethod
    def _obtener(usuarios, usuario_id):
        if type(usuario_id) is not int or usuario_id <= 0:
            raise ErrorValidacion("Seleccione un usuario válido.")
        fila = usuarios.buscar_por_id(usuario_id)
        if fila is None:
            raise ErrorValidacion("El usuario seleccionado ya no existe.")
        return fila

    @staticmethod
    def _validar_datos(nombre, nombre_usuario, rol):
        if any(not isinstance(valor, str) or not valor.strip() for valor in (nombre, nombre_usuario)):
            raise ErrorValidacion("Complete el nombre y el nombre de usuario.")
        if rol not in ROLES:
            raise ErrorValidacion("Seleccione el rol ADMINISTRADOR o VETERINARIO.")
        return nombre.strip(), nombre_usuario.strip()

    @staticmethod
    def _validar_contrasena(contrasena, confirmacion):
        if any(not isinstance(valor, str) or not valor.strip() for valor in (contrasena, confirmacion)):
            raise ErrorValidacion("Ingrese la contraseña y su confirmación.")
        if len(contrasena) < 8:
            raise ErrorValidacion("La contraseña debe tener al menos 8 caracteres.")
        if contrasena != confirmacion:
            raise ErrorValidacion("La contraseña y su confirmación no coinciden.")

    @staticmethod
    def _validar_nombre_unico(usuarios, nombre_usuario, excluir_id=None):
        if usuarios.nombre_en_uso(nombre_usuario, excluir_id):
            raise ErrorValidacion("El nombre de usuario ya está registrado.")

    @staticmethod
    def _proteger_administrador(usuarios, actual, rol, activo):
        if (actual["rol"] == "ADMINISTRADOR" and actual["activo"]
                and (rol != "ADMINISTRADOR" or not activo)
                and usuarios.contar_administradores_activos() <= 1):
            raise ErrorValidacion("No se puede desactivar ni cambiar el rol del último administrador activo.")

    def _cerrar_sesion_si_corresponde(self, usuario):
        actual = self.autenticacion.usuario_actual
        if actual is not None and actual.id == usuario.id and (
            not usuario.activo or usuario.rol != "ADMINISTRADOR"
        ):
            self.autenticacion.cerrar_sesion()
