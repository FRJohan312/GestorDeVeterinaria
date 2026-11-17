"""API de la capa de persistencia de Gestor De Veterinaria."""

from .connection import DB_PATH, conexion
from .initialization import inicializar_bd

__all__ = ["DB_PATH", "conexion", "inicializar_bd"]
