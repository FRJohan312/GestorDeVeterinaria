"""Conexiones y transacciones SQLite de la aplicación."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


# Se conserva el nombre histórico para reutilizar el volumen y sus datos.
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "GestorDeVeterinariar.db"


@contextmanager
def conexion(ruta: str | Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Abre una conexión; confirma o revierte la transacción y siempre cierra."""
    if str(ruta) != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(ruta), timeout=5)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        # INSERT OR REPLACE también debe respetar el trigger contra borrados.
        db.execute("PRAGMA recursive_triggers = ON")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
