"""Registro, consulta y edición con validaciones y autorización en servicios."""

import re
from contextlib import contextmanager

from database.propietarios import acceso_propietarios
from models.propietario import Propietario
from .autenticacion import ErrorValidacion, ServicioAutenticacion


def _modelo(fila) -> Propietario:
    return Propietario(**dict(fila))


class ServicioPropietarios:
    def __init__(self, autenticacion: ServicioAutenticacion):
        self.autenticacion = autenticacion

    @contextmanager
    def _acceso(self, *, escritura=False):
        with acceso_propietarios(self.autenticacion.ruta, escritura=escritura) as (propietarios, usuarios):
            permiso = "gestionar_propietarios" if escritura else "consultar_propietarios"
            self.autenticacion.exigir_permiso(permiso, usuarios=usuarios)
            yield propietarios

    def listar(self) -> list[Propietario]:
        return self.buscar("")

    def buscar(self, termino: str) -> list[Propietario]:
        with self._acceso() as propietarios:
            if not isinstance(termino, str):
                raise ErrorValidacion("La búsqueda debe ser un texto con nombre o documento.")
            return [_modelo(fila) for fila in propietarios.buscar(termino.strip())]

    def obtener(self, propietario_id: int) -> Propietario:
        with self._acceso() as propietarios:
            return _modelo(self._obtener(propietarios, propietario_id))

    def registrar(self, nombre: str, documento: str, telefono=None, correo=None, direccion=None) -> Propietario:
        with self._acceso(escritura=True) as propietarios:
            datos = self._validar(nombre, documento, telefono, correo, direccion)
            self._validar_documento(propietarios, datos[1])
            propietario_id = propietarios.crear(*datos)
            return _modelo(propietarios.obtener(propietario_id))

    def modificar(self, propietario_id: int, nombre: str, documento: str,
                  telefono=None, correo=None, direccion=None) -> Propietario:
        with self._acceso(escritura=True) as propietarios:
            self._obtener(propietarios, propietario_id)
            datos = self._validar(nombre, documento, telefono, correo, direccion)
            self._validar_documento(propietarios, datos[1], propietario_id)
            propietarios.modificar(propietario_id, *datos)
            return _modelo(propietarios.obtener(propietario_id))

    @staticmethod
    def _obtener(propietarios, propietario_id):
        if type(propietario_id) is not int or propietario_id <= 0:
            raise ErrorValidacion("Seleccione un propietario válido.")
        fila = propietarios.obtener(propietario_id)
        if fila is None:
            raise ErrorValidacion("El propietario seleccionado ya no existe.")
        return fila

    @staticmethod
    def _validar(nombre, documento, telefono, correo, direccion):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorValidacion("El nombre del propietario es obligatorio.")
        if not isinstance(documento, str) or not documento.strip():
            raise ErrorValidacion("El documento del propietario es obligatorio y debe ingresarse como texto.")
        opcionales = []
        for etiqueta, valor in (("teléfono", telefono), ("correo", correo), ("dirección", direccion)):
            if valor is not None and not isinstance(valor, str):
                raise ErrorValidacion(f"El campo {etiqueta} debe ser texto.")
            opcionales.append((valor.strip() or None) if valor is not None else None)
        if opcionales[1] is not None and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", opcionales[1]) is None:
            raise ErrorValidacion("Ingrese un correo válido, por ejemplo nombre@dominio.com.")
        return nombre.strip(), documento.strip(), *opcionales

    @staticmethod
    def _validar_documento(propietarios, documento, excluir_id=None):
        if propietarios.documento_en_uso(documento, excluir_id):
            raise ErrorValidacion("El documento ya está registrado para otro propietario.")
