"""Persistencia de la funcionalidad de prueba original."""

from pathlib import Path

from .connection import DB_PATH, conexion


def contar_registros(ruta: str | Path = DB_PATH) -> int:
    with conexion(ruta) as db:
        return db.execute("SELECT COUNT(*) FROM pruebas").fetchone()[0]


def guardar_prueba(ruta: str | Path = DB_PATH) -> None:
    with conexion(ruta) as db:
        db.execute("INSERT INTO pruebas DEFAULT VALUES")
