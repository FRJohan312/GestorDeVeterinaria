"""Persistencia de mascotas sobre el esquema actual, sin borrados ni reemplazos."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .connection import DB_PATH, conexion
from .propietarios import RepositorioPropietarios
from .usuarios import RepositorioUsuarios


SELECCION = """
    SELECT m.id, m.nombre, m.especie, m.raza, m.sexo, m.fecha_nacimiento,
           m.propietario_id, p.nombre AS propietario_nombre,
           p.documento AS propietario_documento
    FROM mascotas AS m JOIN propietarios AS p ON p.id=m.propietario_id
"""


class RepositorioMascotas:
    def __init__(self, db: sqlite3.Connection):
        self._db = db
        db.create_function("casefold", 1, str.casefold, deterministic=True)

    def buscar(self, termino: str, propietario_id: int | None = None) -> list[sqlite3.Row]:
        return self._db.execute(
            SELECCION + """
            WHERE (instr(casefold(m.nombre), casefold(?)) > 0
                OR instr(casefold(m.especie), casefold(?)) > 0
                OR instr(casefold(p.nombre), casefold(?)) > 0
                OR instr(casefold(p.documento), casefold(?)) > 0)
              AND (? IS NULL OR m.propietario_id=?)
            ORDER BY m.nombre COLLATE NOCASE, m.id
            """,
            (termino, termino, termino, termino, propietario_id, propietario_id),
        ).fetchall()

    def obtener(self, mascota_id: int) -> sqlite3.Row | None:
        return self._db.execute(SELECCION + " WHERE m.id=?", (mascota_id,)).fetchone()

    def crear(self, nombre, especie, raza, sexo, fecha_nacimiento, propietario_id) -> int:
        return self._db.execute(
            """INSERT INTO mascotas(nombre, especie, raza, sexo, fecha_nacimiento, propietario_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nombre, especie, raza, sexo, fecha_nacimiento, propietario_id),
        ).lastrowid

    def modificar(self, mascota_id, nombre, especie, raza, sexo, fecha_nacimiento, propietario_id) -> None:
        self._db.execute(
            """UPDATE mascotas SET nombre=?, especie=?, raza=?, sexo=?, fecha_nacimiento=?, propietario_id=?
               WHERE id=?""",
            (nombre, especie, raza, sexo, fecha_nacimiento, propietario_id, mascota_id),
        )


@contextmanager
def acceso_mascotas(
    ruta: str | Path = DB_PATH, *, escritura: bool = False
) -> Iterator[tuple[RepositorioMascotas, RepositorioPropietarios, RepositorioUsuarios]]:
    """Autoriza y comprueba el propietario dentro de la misma transacción."""
    with conexion(ruta) as db:
        db.execute("BEGIN IMMEDIATE" if escritura else "BEGIN")
        yield RepositorioMascotas(db), RepositorioPropietarios(db), RepositorioUsuarios(db)
