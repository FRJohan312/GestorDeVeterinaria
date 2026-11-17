"""Datos de un propietario independientes de Tkinter y SQLite."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Propietario:
    id: int
    nombre: str
    documento: str
    telefono: str | None
    correo: str | None
    direccion: str | None
