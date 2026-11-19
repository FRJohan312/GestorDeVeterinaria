"""Consulta autorizada del historial completo sin modificar información clínica."""

from contextlib import contextmanager

from database.historial import acceso_historial
from models.consulta import Consulta
from models.historial import AtencionHistorial, HistorialMascota
from models.mascota import Mascota
from models.tratamiento import Tratamiento
from .autenticacion import ErrorValidacion, ServicioAutenticacion


class ServicioHistorial:
    def __init__(self, autenticacion: ServicioAutenticacion):
        self.autenticacion = autenticacion

    @contextmanager
    def _acceso(self):
        with acceso_historial(self.autenticacion.ruta) as (historial, usuarios):
            self.autenticacion.exigir_permiso("consultar_historial", usuarios=usuarios)
            yield historial

    def buscar_mascotas(self, termino: str = "") -> list[Mascota]:
        with self._acceso() as historial:
            if not isinstance(termino, str):
                raise ErrorValidacion("La búsqueda de mascota debe ser texto.")
            return [Mascota(**dict(fila)) for fila in historial.mascotas.buscar(termino.strip())]

    def obtener(self, mascota_id: int) -> HistorialMascota:
        with self._acceso() as historial:
            if type(mascota_id) is not int or mascota_id <= 0:
                raise ErrorValidacion("Seleccione una mascota válida para consultar el historial.")
            mascota = historial.mascotas.obtener(mascota_id)
            if mascota is None:
                raise ErrorValidacion("La mascota seleccionada no existe.")
            consultas = historial.consultas.buscar(mascota_id=mascota_id)
            por_consulta = {}
            for fila in historial.tratamientos_de_mascota(mascota_id):
                tratamiento = Tratamiento(**dict(fila))
                por_consulta.setdefault(tratamiento.consulta_id, []).append(tratamiento)
            return HistorialMascota(
                mascota=Mascota(**dict(mascota)),
                atenciones=tuple(AtencionHistorial(
                    consulta=Consulta(**dict(fila)), tratamientos=tuple(por_consulta.get(fila["id"], ())),
                ) for fila in consultas),
            )
