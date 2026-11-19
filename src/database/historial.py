"""Lectura del historial existente, con tratamientos por lote y sin escrituras."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .connection import DB_PATH, conexion
from .consultas import RepositorioConsultas
from .mascotas import RepositorioMascotas
from .usuarios import RepositorioUsuarios


class RepositorioHistorial:
    def __init__(self, db: sqlite3.Connection):
        self._db = db
        self.mascotas = RepositorioMascotas(db)
        self.consultas = RepositorioConsultas(db)

    def tratamientos_de_mascota(self, mascota_id) -> list[sqlite3.Row]:
        return self._db.execute(
            """SELECT t.id, t.consulta_id, t.descripcion, t.medicamento, t.dosis, t.duracion
               FROM tratamientos t JOIN consultas c ON c.id=t.consulta_id
               WHERE c.mascota_id=? ORDER BY t.id""", (mascota_id,),
        ).fetchall()


@contextmanager
def acceso_historial(ruta: str | Path = DB_PATH) -> Iterator[tuple[RepositorioHistorial, RepositorioUsuarios]]:
    with conexion(ruta) as db:
        db.execute("PRAGMA query_only = ON")
        # Mascota, atenciones y tratamientos corresponden a una misma instantánea.
        db.execute("BEGIN")
        yield RepositorioHistorial(db), RepositorioUsuarios(db)
