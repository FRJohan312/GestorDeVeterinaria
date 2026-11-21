"""Historial de solo lectura compuesto por los modelos clínicos existentes."""

from dataclasses import dataclass

from .consulta import Consulta
from .mascota import Mascota
from .tratamiento import Tratamiento


@dataclass(frozen=True)
class AtencionHistorial:
    consulta: Consulta
    tratamientos: tuple[Tratamiento, ...]


@dataclass(frozen=True)
class HistorialMascota:
    mascota: Mascota
    atenciones: tuple[AtencionHistorial, ...]
