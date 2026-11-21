"""Consultas parametrizadas de usuarios y unidad de trabajo transaccional."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .connection import DB_PATH, conexion


class RepositorioUsuarios:
    """Opera con la conexión proporcionada, sin controlar la sesión de acceso."""

    def __init__(self, db: sqlite3.Connection):
        self._db = db

    def existen(self) -> bool:
        return self._db.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone() is not None

    def buscar_por_nombre(self, nombre_usuario: str) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT * FROM usuarios WHERE nombre_usuario = ?", (nombre_usuario,)
        ).fetchone()

    def buscar_por_id(self, usuario_id: int) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT id, nombre, nombre_usuario, rol, activo FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()

    def listar(self) -> list[sqlite3.Row]:
        return self._db.execute(
            "SELECT id, nombre, nombre_usuario, rol, activo FROM usuarios ORDER BY nombre COLLATE NOCASE, id"
        ).fetchall()

    def listar_veterinarios(self, incluir_inactivos=False, usuario_id=None) -> list[sqlite3.Row]:
        return self._db.execute(
            """SELECT id, nombre, nombre_usuario, rol, activo FROM usuarios
               WHERE rol='VETERINARIO' AND (? OR activo=1) AND (? IS NULL OR id=?)
               ORDER BY nombre COLLATE NOCASE, id""",
            (incluir_inactivos, usuario_id, usuario_id),
        ).fetchall()

    def nombre_en_uso(self, nombre_usuario: str, excluir_id: int | None = None) -> bool:
        # NOCASE protege ASCII en SQLite; casefold también cubre nombres con tildes.
        return any(
            fila["id"] != excluir_id
            and fila["nombre_usuario"].casefold() == nombre_usuario.casefold()
            for fila in self.listar()
        )

    def contar_administradores_activos(self) -> int:
        return self._db.execute(
            "SELECT count(*) FROM usuarios WHERE rol='ADMINISTRADOR' AND activo=1"
        ).fetchone()[0]

    def tiene_historial_veterinario(self, usuario_id: int) -> bool:
        return bool(self._db.execute(
            """SELECT EXISTS(SELECT 1 FROM citas WHERE veterinario_id=?)
               OR EXISTS(SELECT 1 FROM consultas WHERE veterinario_id=?)""",
            (usuario_id, usuario_id),
        ).fetchone()[0])

    def modificar(self, usuario_id: int, nombre: str, nombre_usuario: str, rol: str) -> None:
        self._db.execute(
            "UPDATE usuarios SET nombre=?, nombre_usuario=?, rol=? WHERE id=?",
            (nombre, nombre_usuario, rol, usuario_id),
        )

    def cambiar_estado(self, usuario_id: int, activo: bool) -> None:
        self._db.execute("UPDATE usuarios SET activo=? WHERE id=?", (activo, usuario_id))

    def cambiar_contrasena(self, usuario_id: int, contrasena_hash: str) -> None:
        self._db.execute(
            "UPDATE usuarios SET contrasena_hash=? WHERE id=?", (contrasena_hash, usuario_id)
        )

    def crear(self, nombre: str, nombre_usuario: str, contrasena_hash: str, rol: str) -> int:
        cursor = self._db.execute(
            """INSERT INTO usuarios(nombre, nombre_usuario, contrasena_hash, rol, activo)
               VALUES (?, ?, ?, ?, 1)""",
            (nombre, nombre_usuario, contrasena_hash, rol),
        )
        return cursor.lastrowid


@contextmanager
def acceso_usuarios(
    ruta: str | Path = DB_PATH, *, escritura: bool = False
) -> Iterator[RepositorioUsuarios]:
    """Reserva la escritura antes de validar las reglas de cada modificación."""
    with conexion(ruta) as db:
        if escritura:
            db.execute("BEGIN IMMEDIATE")
        yield RepositorioUsuarios(db)
