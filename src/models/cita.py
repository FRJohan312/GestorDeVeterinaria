"""Datos de agenda independientes de la interfaz y de SQLite."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Cita:
    id: int
    mascota_id: int
    veterinario_id: int
    fecha_hora_inicio: str
    duracion_minutos: int
    motivo: str
    estado: str
    mascota_nombre: str
    propietario_id: int
    propietario_nombre: str
    propietario_documento: str
    veterinario_nombre: str
    veterinario_usuario: str
    consulta_id: int | None

    @property
    def fecha_hora_fin(self) -> str:
        inicio = datetime.fromisoformat(self.fecha_hora_inicio)
        return (inicio + timedelta(minutes=self.duracion_minutos)).isoformat(sep=" ")
