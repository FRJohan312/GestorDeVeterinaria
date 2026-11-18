"""Agenda parametrizada; las cancelaciones actualizan el estado sin borrar filas."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .connection import DB_PATH, conexion
from .mascotas import RepositorioMascotas
from .usuarios import RepositorioUsuarios


SELECCION = """
    SELECT c.id, c.mascota_id, c.veterinario_id, c.fecha_hora_inicio,
           c.duracion_minutos, c.motivo, c.estado, m.nombre AS mascota_nombre,
           p.id AS propietario_id, p.nombre AS propietario_nombre,
           p.documento AS propietario_documento, u.nombre AS veterinario_nombre,
           u.nombre_usuario AS veterinario_usuario, co.id AS consulta_id
    FROM citas c
    JOIN mascotas m ON m.id=c.mascota_id
    JOIN propietarios p ON p.id=m.propietario_id
    JOIN usuarios u ON u.id=c.veterinario_id
    LEFT JOIN consultas co ON co.cita_id=c.id
"""


class RepositorioCitas:
    def __init__(self, db: sqlite3.Connection):
        self._db = db
        db.create_function("casefold", 1, str.casefold, deterministic=True)

    def buscar(self, fecha=None, veterinario_id=None, mascota_id=None, estado=None, termino=""):
        return self._db.execute(
            SELECCION + """
            WHERE (? IS NULL OR substr(c.fecha_hora_inicio, 1, 10)=?)
              AND (? IS NULL OR c.veterinario_id=?)
              AND (? IS NULL OR c.mascota_id=?)
              AND (? IS NULL OR c.estado=?)
              AND (instr(casefold(m.nombre), casefold(?)) > 0
                OR instr(casefold(p.nombre), casefold(?)) > 0
                OR instr(casefold(p.documento), casefold(?)) > 0
                OR instr(casefold(u.nombre), casefold(?)) > 0)
            ORDER BY c.fecha_hora_inicio, c.id
            """,
            (fecha, fecha, veterinario_id, veterinario_id, mascota_id, mascota_id, estado, estado,
             termino, termino, termino, termino),
        ).fetchall()

    def obtener(self, cita_id: int, veterinario_id=None) -> sqlite3.Row | None:
        return self._db.execute(
            SELECCION + " WHERE c.id=? AND (? IS NULL OR c.veterinario_id=?)",
            (cita_id, veterinario_id, veterinario_id),
        ).fetchone()

    def conflicto(self, veterinario_id, inicio, fin, excluir_id=None) -> sqlite3.Row | None:
        return self._db.execute(
            """SELECT id, fecha_hora_inicio, duracion_minutos FROM citas
               WHERE veterinario_id=? AND estado IN ('PROGRAMADA', 'CONFIRMADA')
                 AND (? IS NULL OR id!=?) AND fecha_hora_inicio < ?
                 AND (datetime(fecha_hora_inicio, '+' || duracion_minutos || ' minutes') > ?
                      OR datetime(fecha_hora_inicio, '+' || duracion_minutos || ' minutes') IS NULL)
               ORDER BY fecha_hora_inicio LIMIT 1""",
            (veterinario_id, excluir_id, excluir_id, fin, inicio),
        ).fetchone()

    def crear(self, mascota_id, veterinario_id, inicio, duracion, motivo) -> int:
        return self._db.execute(
            """INSERT INTO citas(mascota_id, veterinario_id, fecha_hora_inicio, duracion_minutos, motivo, estado)
               VALUES (?, ?, ?, ?, ?, 'PROGRAMADA')""",
            (mascota_id, veterinario_id, inicio, duracion, motivo),
        ).lastrowid

    def modificar(self, cita_id, mascota_id, veterinario_id, inicio, duracion, motivo) -> None:
        self._db.execute(
            """UPDATE citas SET mascota_id=?, veterinario_id=?, fecha_hora_inicio=?,
               duracion_minutos=?, motivo=? WHERE id=?""",
            (mascota_id, veterinario_id, inicio, duracion, motivo, cita_id),
        )

    def cambiar_estado(self, cita_id, estado):
        self._db.execute("UPDATE citas SET estado=? WHERE id=?", (estado, cita_id))


@contextmanager
def acceso_citas(ruta: str | Path = DB_PATH, *, escritura=False) -> Iterator[tuple]:
    with conexion(ruta) as db:
        db.execute("BEGIN IMMEDIATE" if escritura else "BEGIN")
        yield RepositorioCitas(db), RepositorioMascotas(db), RepositorioUsuarios(db)
