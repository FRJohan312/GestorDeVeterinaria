"""Gestión de mascotas con permisos y relaciones verificadas en servicios."""

import re
from contextlib import contextmanager
from datetime import date

from database.mascotas import acceso_mascotas
from models.mascota import Mascota
from models.propietario import Propietario
from .autenticacion import ErrorValidacion, ServicioAutenticacion


SEXOS = ("MACHO", "HEMBRA", "DESCONOCIDO")


def _modelo(fila) -> Mascota:
    return Mascota(**dict(fila))


class ServicioMascotas:
    def __init__(self, autenticacion: ServicioAutenticacion):
        self.autenticacion = autenticacion

    @contextmanager
    def _acceso(self, *, escritura=False):
        with acceso_mascotas(self.autenticacion.ruta, escritura=escritura) as (mascotas, propietarios, usuarios):
            permiso = "gestionar_mascotas" if escritura else "consultar_mascotas"
            self.autenticacion.exigir_permiso(permiso, usuarios=usuarios)
            yield mascotas, propietarios

    def listar(self) -> list[Mascota]:
        return self.buscar("")

    def buscar(self, termino: str, propietario_id: int | None = None) -> list[Mascota]:
        with self._acceso() as (mascotas, propietarios):
            if not isinstance(termino, str):
                raise ErrorValidacion("La búsqueda debe ser un texto con nombre, especie o propietario.")
            if propietario_id is not None:
                self._validar_propietario(propietarios, propietario_id)
            return [_modelo(fila) for fila in mascotas.buscar(termino.strip(), propietario_id)]

    def por_propietario(self, propietario_id: int) -> list[Mascota]:
        with self._acceso() as (mascotas, propietarios):
            self._validar_propietario(propietarios, propietario_id)
            return [_modelo(fila) for fila in mascotas.buscar("", propietario_id)]

    def propietarios_disponibles(self) -> list[Propietario]:
        with self._acceso() as (_, propietarios):
            return [Propietario(**dict(fila)) for fila in propietarios.buscar("")]

    def obtener(self, mascota_id: int) -> Mascota:
        with self._acceso() as (mascotas, _):
            return _modelo(self._obtener(mascotas, mascota_id))

    def registrar(self, nombre: str, especie: str, sexo: str, propietario_id: int,
                  raza=None, fecha_nacimiento=None) -> Mascota:
        with self._acceso(escritura=True) as (mascotas, propietarios):
            datos = self._validar(nombre, especie, raza, sexo, fecha_nacimiento)
            self._validar_propietario(propietarios, propietario_id)
            mascota_id = mascotas.crear(*datos, propietario_id)
            return _modelo(mascotas.obtener(mascota_id))

    def modificar(self, mascota_id: int, nombre: str, especie: str, sexo: str, propietario_id: int,
                  raza=None, fecha_nacimiento=None) -> Mascota:
        with self._acceso(escritura=True) as (mascotas, propietarios):
            self._obtener(mascotas, mascota_id)
            datos = self._validar(nombre, especie, raza, sexo, fecha_nacimiento)
            self._validar_propietario(propietarios, propietario_id)
            mascotas.modificar(mascota_id, *datos, propietario_id)
            return _modelo(mascotas.obtener(mascota_id))

    @staticmethod
    def _obtener(mascotas, mascota_id):
        if type(mascota_id) is not int or mascota_id <= 0:
            raise ErrorValidacion("Seleccione una mascota válida.")
        fila = mascotas.obtener(mascota_id)
        if fila is None:
            raise ErrorValidacion("La mascota seleccionada ya no existe.")
        return fila

    @staticmethod
    def _validar_propietario(propietarios, propietario_id):
        if type(propietario_id) is not int or propietario_id <= 0:
            raise ErrorValidacion("Seleccione un propietario existente.")
        if propietarios.obtener(propietario_id) is None:
            raise ErrorValidacion("El propietario seleccionado ya no existe. Actualice la lista de propietarios.")

    @staticmethod
    def _validar(nombre, especie, raza, sexo, fecha_nacimiento):
        for etiqueta, valor in (("nombre", nombre), ("especie", especie)):
            if not isinstance(valor, str) or not valor.strip():
                raise ErrorValidacion(f"El campo {etiqueta} es obligatorio.")
        if sexo not in SEXOS:
            raise ErrorValidacion("Seleccione el sexo MACHO, HEMBRA o DESCONOCIDO.")
        if raza is not None and not isinstance(raza, str):
            raise ErrorValidacion("La raza debe ingresarse como texto.")
        raza = (raza.strip() or None) if raza is not None else None
        if fecha_nacimiento is not None:
            if not isinstance(fecha_nacimiento, str):
                raise ErrorValidacion("Ingrese la fecha de nacimiento con formato AAAA-MM-DD.")
            fecha_nacimiento = fecha_nacimiento.strip() or None
        if fecha_nacimiento is not None:
            try:
                if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", fecha_nacimiento) is None:
                    raise ValueError
                nacimiento = date.fromisoformat(fecha_nacimiento)
            except ValueError:
                raise ErrorValidacion("Ingrese una fecha de nacimiento válida con formato AAAA-MM-DD.") from None
            if nacimiento > date.today():
                raise ErrorValidacion("La fecha de nacimiento no puede ser futura.")
        return nombre.strip(), especie.strip(), raza, sexo, fecha_nacimiento
