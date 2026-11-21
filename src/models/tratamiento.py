"""Datos públicos e inmutables de un tratamiento registrado."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tratamiento:
    id: int
    consulta_id: int
    descripcion: str
    medicamento: str | None
    dosis: str | None
    duracion: str | None
