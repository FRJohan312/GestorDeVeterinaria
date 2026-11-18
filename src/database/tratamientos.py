"""Persistencia de tratamientos: inserción y lectura, sin edición ni borrado."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .connection import DB_PATH, conexion
from .consultas import RepositorioConsultas
from .usuarios import RepositorioUsuarios


class RepositorioTratamientos:
    def __init__(self, db: sqlite3.Connection):
        self._db = db

    def listar(self, consulta_id) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT * FROM tratamientos WHERE consulta_id=? ORDER BY id", (consulta_id,),
        ).fetchall()

    def obtener(self, consulta_id, tratamiento_id) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT * FROM tratamientos WHERE consulta_id=? AND id=?", (consulta_id, tratamiento_id),
        ).fetchone()

    def crear(self, consulta_id, descripcion, medicamento, dosis, duracion) -> int:
        return self._db.execute(
            """INSERT INTO tratamientos(consulta_id,descripcion,medicamento,dosis,duracion)
               VALUES (?,?,?,?,?)""", (consulta_id, descripcion, medicamento, dosis, duracion),
        ).lastrowid


@contextmanager
def acceso_tratamientos(ruta: str | Path = DB_PATH, *, escritura=False) -> Iterator[tuple]:
    with conexion(ruta) as db:
        db.execute("BEGIN IMMEDIATE" if escritura else "BEGIN")
        yield RepositorioTratamientos(db), RepositorioConsultas(db), RepositorioUsuarios(db)
