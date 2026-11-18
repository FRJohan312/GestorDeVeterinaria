"""Registro y lectura clínica sobre el esquema existente, sin UPDATE ni DELETE de consultas."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .connection import DB_PATH, conexion
from .citas import RepositorioCitas
from .mascotas import RepositorioMascotas
from .usuarios import RepositorioUsuarios


SELECCION = """
    SELECT co.id, co.mascota_id, co.veterinario_id, co.cita_id, co.fecha, co.peso,
           co.sintomas, co.diagnostico, co.observaciones, m.nombre AS mascota_nombre,
           p.nombre AS propietario_nombre, p.documento AS propietario_documento,
           u.nombre AS veterinario_nombre, u.nombre_usuario AS veterinario_usuario,
           c.fecha_hora_inicio AS cita_fecha_hora_inicio, c.estado AS cita_estado
    FROM consultas co
    JOIN mascotas m ON m.id=co.mascota_id
    JOIN propietarios p ON p.id=m.propietario_id
    JOIN usuarios u ON u.id=co.veterinario_id
    LEFT JOIN citas c ON c.id=co.cita_id
"""


class RepositorioConsultas:
    def __init__(self, db: sqlite3.Connection):
        self._db = db

    def buscar(self, mascota_id=None, fecha=None, veterinario_id=None) -> list[sqlite3.Row]:
        return self._db.execute(
            SELECCION + """
            WHERE (? IS NULL OR co.mascota_id=?)
              AND (? IS NULL OR substr(co.fecha,1,10)=?)
              AND (? IS NULL OR co.veterinario_id=?)
            ORDER BY co.fecha DESC, co.id DESC""",
            (mascota_id, mascota_id, fecha, fecha, veterinario_id, veterinario_id),
        ).fetchall()

    def obtener(self, consulta_id) -> sqlite3.Row | None:
        return self._db.execute(SELECCION + " WHERE co.id=?", (consulta_id,)).fetchone()

    def crear(self, mascota_id, veterinario_id, cita_id, fecha, peso, sintomas, diagnostico, observaciones) -> int:
        return self._db.execute(
            """INSERT INTO consultas(mascota_id,veterinario_id,cita_id,fecha,peso,sintomas,diagnostico,observaciones)
               VALUES (?,?,?,?,?,?,?,?)""",
            (mascota_id, veterinario_id, cita_id, fecha, peso, sintomas, diagnostico, observaciones),
        ).lastrowid


@contextmanager
def acceso_consultas(ruta: str | Path = DB_PATH, *, escritura=False) -> Iterator[tuple]:
    with conexion(ruta) as db:
        db.execute("BEGIN IMMEDIATE" if escritura else "BEGIN")
        yield RepositorioConsultas(db), RepositorioCitas(db), RepositorioMascotas(db), RepositorioUsuarios(db)
