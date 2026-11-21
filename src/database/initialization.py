"""Creación idempotente y transaccional del esquema."""

from pathlib import Path

from .connection import DB_PATH, conexion
from .schema import SCHEMA_SQL


def inicializar_bd(ruta: str | Path = DB_PATH) -> None:
    """Añade tablas, índices y triggers sin eliminar los datos existentes."""
    with conexion(ruta) as db:
        db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA_SQL + "\nCOMMIT;")
