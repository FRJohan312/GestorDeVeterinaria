"""Validaciones y autorización del tratamiento dentro de la transacción SQLite."""

from contextlib import contextmanager

from database.tratamientos import acceso_tratamientos
from models.tratamiento import Tratamiento
from .autenticacion import ErrorValidacion, PermisoDenegado, ServicioAutenticacion


class ServicioTratamientos:
    def __init__(self, autenticacion: ServicioAutenticacion):
        self.autenticacion = autenticacion

    @contextmanager
    def _acceso(self, consulta_id, *, escritura=False):
        with acceso_tratamientos(self.autenticacion.ruta, escritura=escritura) as repositorios:
            tratamientos, consultas, usuarios = repositorios
            permiso = "registrar_tratamientos" if escritura else "consultar_tratamientos"
            self.autenticacion.exigir_permiso(permiso, usuarios=usuarios)
            self._identificador(consulta_id, "consulta")
            consulta = consultas.obtener(consulta_id)
            if consulta is None:
                raise ErrorValidacion("La consulta seleccionada no existe.")
            if escritura and not self._es_responsable(consulta):
                raise PermisoDenegado("Solo el veterinario responsable puede registrar tratamientos para esta consulta.")
            yield tratamientos, consulta, usuarios

    def _es_responsable(self, consulta):
        usuario = self.autenticacion.usuario_actual
        return usuario.rol == "VETERINARIO" and usuario.id == consulta["veterinario_id"]

    def puede_registrar(self, consulta_id) -> bool:
        with self._acceso(consulta_id) as (_, consulta, usuarios):
            return (self._es_responsable(consulta) and
                    "registrar_tratamientos" in self.autenticacion.permisos_actuales(usuarios=usuarios))

    def listar(self, consulta_id) -> list[Tratamiento]:
        with self._acceso(consulta_id) as (tratamientos, _, _):
            return [Tratamiento(**dict(fila)) for fila in tratamientos.listar(consulta_id)]

    def obtener(self, consulta_id, tratamiento_id) -> Tratamiento:
        with self._acceso(consulta_id) as (tratamientos, _, _):
            self._identificador(tratamiento_id, "tratamiento")
            fila = tratamientos.obtener(consulta_id, tratamiento_id)
            if fila is None:
                raise ErrorValidacion("El tratamiento no existe o no pertenece a esta consulta.")
            return Tratamiento(**dict(fila))

    def registrar(self, consulta_id, descripcion, medicamento=None, dosis=None, duracion=None) -> Tratamiento:
        with self._acceso(consulta_id, escritura=True) as (tratamientos, _, _):
            if not isinstance(descripcion, str) or not descripcion.strip():
                raise ErrorValidacion("La descripción del tratamiento es obligatoria y debe ser texto.")
            medicamento = self._opcional(medicamento, "medicamento")
            dosis = self._opcional(dosis, "dosis")
            duracion = self._opcional(duracion, "duración")
            tratamiento_id = tratamientos.crear(consulta_id, descripcion.strip(), medicamento, dosis, duracion)
            return Tratamiento(**dict(tratamientos.obtener(consulta_id, tratamiento_id)))

    @staticmethod
    def _identificador(valor, etiqueta):
        if type(valor) is not int or valor <= 0:
            raise ErrorValidacion(f"Seleccione un registro de {etiqueta} válido.")

    @staticmethod
    def _opcional(valor, etiqueta):
        if valor is not None and not isinstance(valor, str):
            raise ErrorValidacion(f"El campo {etiqueta} debe ser texto.")
        return (valor.strip() or None) if valor is not None else None
