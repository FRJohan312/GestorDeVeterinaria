"""Operaciones del prototipo consumidas por la presentación."""

from pathlib import Path

from database import DB_PATH, inicializar_bd
from database import prototipo
from .autenticacion import ServicioAutenticacion


def inicializar_aplicacion(ruta: str | Path = DB_PATH) -> None:
    inicializar_bd(ruta)


def contar_registros(autenticacion: ServicioAutenticacion) -> int:
    autenticacion.exigir_permiso("usar_pruebas")
    return prototipo.contar_registros(autenticacion.ruta)


def guardar_prueba(autenticacion: ServicioAutenticacion) -> None:
    autenticacion.exigir_permiso("usar_pruebas")
    prototipo.guardar_prueba(autenticacion.ruta)
