"""Datos públicos de la sesión; nunca incluyen la contraseña ni su hash."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UsuarioAutenticado:
    id: int
    nombre: str
    nombre_usuario: str
    rol: str


@dataclass(frozen=True)
class UsuarioGestion:
    """Datos para administrar cuentas sin exponer sus hashes."""

    id: int
    nombre: str
    nombre_usuario: str
    rol: str
    activo: bool
