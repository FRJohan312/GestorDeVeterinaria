"""Datos de la mascota y de su propietario para listados y detalles."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Mascota:
    id: int
    nombre: str
    especie: str
    raza: str | None
    sexo: str
    fecha_nacimiento: str | None
    propietario_id: int
    propietario_nombre: str
    propietario_documento: str
