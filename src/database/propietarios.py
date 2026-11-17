"""Acceso parametrizado a la tabla existente, sin reemplazos ni eliminaciones."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .connection import DB_PATH, conexion
from .usuarios import RepositorioUsuarios


class RepositorioPropietarios:
    def __init__(self, db: sqlite3.Connection):
        self._db = db
        # Búsqueda Unicode sin cambiar el esquema ni interpretar comodines.
        db.create_function("casefold", 1, str.casefold, deterministic=True)

    def buscar(self, termino: str) -> list[sqlite3.Row]:
        return self._db.execute(
            """SELECT id, nombre, documento, telefono, correo, direccion FROM propietarios
               WHERE instr(casefold(nombre), casefold(?)) > 0
                  OR instr(casefold(documento), casefold(?)) > 0
               ORDER BY nombre COLLATE NOCASE, id""",
            (termino, termino),
        ).fetchall()

    def obtener(self, propietario_id: int) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT id, nombre, documento, telefono, correo, direccion FROM propietarios WHERE id=?",
            (propietario_id,),
        ).fetchone()

    def documento_en_uso(self, documento: str, excluir_id: int | None = None) -> bool:
        fila = self._db.execute("SELECT id FROM propietarios WHERE documento=?", (documento,)).fetchone()
        return fila is not None and fila["id"] != excluir_id

    def crear(self, nombre, documento, telefono, correo, direccion) -> int:
        return self._db.execute(
            """INSERT INTO propietarios(nombre, documento, telefono, correo, direccion)
               VALUES (?, ?, ?, ?, ?)""",
            (nombre, documento, telefono, correo, direccion),
        ).lastrowid

    def modificar(self, propietario_id, nombre, documento, telefono, correo, direccion) -> None:
        self._db.execute(
            """UPDATE propietarios SET nombre=?, documento=?, telefono=?, correo=?, direccion=?
               WHERE id=?""",
            (nombre, documento, telefono, correo, direccion, propietario_id),
        )


@contextmanager
def acceso_propietarios(
    ruta: str | Path = DB_PATH, *, escritura: bool = False
) -> Iterator[tuple[RepositorioPropietarios, RepositorioUsuarios]]:
    """Comparte una transacción para autorizar al usuario y operar sobre propietarios."""
    with conexion(ruta) as db:
        db.execute("BEGIN IMMEDIATE" if escritura else "BEGIN")
        yield RepositorioPropietarios(db), RepositorioUsuarios(db)
