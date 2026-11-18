"""Registro clínico y datos relacionados para consulta de solo lectura."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Consulta:
    id: int
    mascota_id: int
    veterinario_id: int
    cita_id: int | None
    fecha: str
    peso: float | None
    sintomas: str
    diagnostico: str | None
    observaciones: str | None
    mascota_nombre: str
    propietario_nombre: str
    propietario_documento: str
    veterinario_nombre: str
    veterinario_usuario: str
    cita_fecha_hora_inicio: str | None
    cita_estado: str | None
