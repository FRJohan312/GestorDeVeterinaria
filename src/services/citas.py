"""Reglas de agenda, transiciones y acceso a la agenda propia del veterinario."""

import re
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta

from database.citas import acceso_citas
from models.cita import Cita
from models.mascota import Mascota
from models.usuario import UsuarioGestion
from .autenticacion import ErrorValidacion, PermisoDenegado, ServicioAutenticacion


ESTADOS = ("PROGRAMADA", "CONFIRMADA", "COMPLETADA", "CANCELADA", "NO_ASISTIO")
ESTADOS_ACTIVOS = frozenset({"PROGRAMADA", "CONFIRMADA"})
TRANSICIONES = {
    "PROGRAMADA": frozenset({"CONFIRMADA", "CANCELADA", "NO_ASISTIO"}),
    "CONFIRMADA": frozenset({"COMPLETADA", "CANCELADA", "NO_ASISTIO"}),
    "COMPLETADA": frozenset(), "CANCELADA": frozenset(), "NO_ASISTIO": frozenset(),
}


class ConflictoHorario(ErrorValidacion):
    """El intervalo solicitado se cruza con otra reserva del veterinario."""


def _modelo(fila):
    return Cita(**dict(fila))


class ServicioCitas:
    def __init__(self, autenticacion: ServicioAutenticacion):
        self.autenticacion = autenticacion

    @contextmanager
    def _acceso(self, *, escritura=False):
        with acceso_citas(self.autenticacion.ruta, escritura=escritura) as repositorios:
            self.autenticacion.exigir_permiso(
                "gestionar_citas" if escritura else "consultar_citas", usuarios=repositorios[2],
            )
            yield repositorios

    def _agenda(self, veterinario_id=None):
        if veterinario_id is not None and (type(veterinario_id) is not int or veterinario_id <= 0):
            raise ErrorValidacion("Seleccione un veterinario válido.")
        actual = self.autenticacion.usuario_actual
        if actual.rol == "VETERINARIO":
            if veterinario_id is not None and veterinario_id != actual.id:
                raise PermisoDenegado("Solo puede consultar su propia agenda.")
            return actual.id
        return veterinario_id

    def listar(self) -> list[Cita]:
        return self.buscar()

    def buscar(self, fecha=None, veterinario_id=None, mascota_id=None, estado=None, termino="") -> list[Cita]:
        with self._acceso() as (citas, mascotas, usuarios):
            veterinario_id = self._agenda(veterinario_id)
            fecha = None if fecha in (None, "") else self._fecha(fecha).isoformat()
            if veterinario_id is not None:
                self._veterinario(usuarios, veterinario_id, exigir_activo=False)
            if mascota_id is not None:
                self._mascota(mascotas, mascota_id)
            estado = None if estado == "" else estado
            if estado is not None and estado not in ESTADOS:
                raise ErrorValidacion("Seleccione un estado de cita válido.")
            if not isinstance(termino, str):
                raise ErrorValidacion("El texto de búsqueda no es válido.")
            return [_modelo(fila) for fila in citas.buscar(fecha, veterinario_id, mascota_id, estado, termino.strip())]

    def obtener(self, cita_id: int) -> Cita:
        with self._acceso() as (citas, _, _):
            return _modelo(self._obtener(citas, cita_id, self._agenda()))

    def mascotas_disponibles(self) -> list[Mascota]:
        with self._acceso() as (_, mascotas, _):
            return [Mascota(**dict(fila)) for fila in mascotas.buscar("")]

    def veterinarios_disponibles(self, incluir_inactivos=False) -> list[UsuarioGestion]:
        with self._acceso() as (_, _, usuarios):
            if type(incluir_inactivos) is not bool:
                raise ErrorValidacion("El filtro de veterinarios debe ser válido.")
            return [UsuarioGestion(id=f["id"], nombre=f["nombre"], nombre_usuario=f["nombre_usuario"],
                                   rol=f["rol"], activo=bool(f["activo"]))
                    for f in usuarios.listar_veterinarios(incluir_inactivos, self._agenda())]

    def programar(self, mascota_id, veterinario_id, fecha, hora_inicio, duracion_minutos, motivo) -> Cita:
        with self._acceso(escritura=True) as (citas, mascotas, usuarios):
            inicio, fin, motivo = self._validar(fecha, hora_inicio, duracion_minutos, motivo)
            self._mascota(mascotas, mascota_id)
            self._veterinario(usuarios, veterinario_id)
            self._sin_conflicto(citas, veterinario_id, inicio, fin)
            id_cita = citas.crear(mascota_id, veterinario_id, inicio, duracion_minutos, motivo)
            return _modelo(citas.obtener(id_cita))

    def modificar(self, cita_id, mascota_id, veterinario_id, fecha, hora_inicio, duracion_minutos, motivo) -> Cita:
        with self._acceso(escritura=True) as (citas, mascotas, usuarios):
            actual = self._obtener(citas, cita_id)
            if actual["estado"] not in ESTADOS_ACTIVOS:
                raise ErrorValidacion("Solo se pueden modificar citas programadas o confirmadas.")
            if actual["consulta_id"] is not None:
                raise ErrorValidacion("La cita tiene una consulta asociada y no se puede reprogramar.")
            inicio, fin, motivo = self._validar(fecha, hora_inicio, duracion_minutos, motivo)
            self._mascota(mascotas, mascota_id)
            self._veterinario(usuarios, veterinario_id)
            self._sin_conflicto(citas, veterinario_id, inicio, fin, cita_id)
            citas.modificar(cita_id, mascota_id, veterinario_id, inicio, duracion_minutos, motivo)
            return _modelo(citas.obtener(cita_id))

    def confirmar(self, cita_id) -> Cita:
        return self.cambiar_estado(cita_id, "CONFIRMADA")

    def cancelar(self, cita_id) -> Cita:
        return self.cambiar_estado(cita_id, "CANCELADA")

    def cambiar_estado(self, cita_id, estado) -> Cita:
        with self._acceso(escritura=True) as (citas, mascotas, usuarios):
            actual = self._obtener(citas, cita_id)
            if not isinstance(estado, str) or estado not in TRANSICIONES[actual["estado"]]:
                raise ErrorValidacion(f"No se permite pasar de {actual['estado']} a {estado}.")
            if actual["consulta_id"] is not None and estado != "COMPLETADA":
                raise ErrorValidacion("La cita tiene una consulta asociada y no admite ese cambio de estado.")
            if estado in ESTADOS_ACTIVOS:
                inicio, fin, _ = self._validar(actual["fecha_hora_inicio"][:10], actual["fecha_hora_inicio"][11:],
                                             actual["duracion_minutos"], actual["motivo"])
                self._mascota(mascotas, actual["mascota_id"])
                self._veterinario(usuarios, actual["veterinario_id"])
                self._sin_conflicto(citas, actual["veterinario_id"], inicio, fin, cita_id)
            citas.cambiar_estado(cita_id, estado)
            return _modelo(citas.obtener(cita_id))

    @staticmethod
    def _obtener(citas, cita_id, veterinario_id=None):
        if type(cita_id) is not int or cita_id <= 0:
            raise ErrorValidacion("Seleccione una cita válida.")
        fila = citas.obtener(cita_id, veterinario_id)
        if fila is None:
            raise ErrorValidacion("La cita no existe o no está disponible en su agenda.")
        return fila

    @staticmethod
    def _mascota(mascotas, mascota_id):
        if type(mascota_id) is not int or mascota_id <= 0 or mascotas.obtener(mascota_id) is None:
            raise ErrorValidacion("Seleccione una mascota registrada.")

    @staticmethod
    def _veterinario(usuarios, veterinario_id, exigir_activo=True):
        fila = usuarios.buscar_por_id(veterinario_id) if type(veterinario_id) is int and veterinario_id > 0 else None
        if fila is None or fila["rol"] != "VETERINARIO":
            raise ErrorValidacion("Seleccione un usuario con rol VETERINARIO.")
        if exigir_activo and not fila["activo"]:
            raise ErrorValidacion("El veterinario está inactivo. Seleccione un veterinario activo.")

    @staticmethod
    def _fecha(fecha):
        try:
            if not isinstance(fecha, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", fecha.strip()) is None:
                raise ValueError
            return date.fromisoformat(fecha.strip())
        except ValueError:
            raise ErrorValidacion("Ingrese una fecha válida con formato AAAA-MM-DD.") from None

    @classmethod
    def _validar(cls, fecha, hora, duracion, motivo):
        dia = cls._fecha(fecha)
        try:
            if not isinstance(hora, str) or re.fullmatch(r"[0-9]{2}:[0-9]{2}(:[0-9]{2})?", hora.strip()) is None:
                raise ValueError
            # El constructor valida 0..23 también en versiones que normalizan 24:00.
            inicio = datetime.combine(dia, time(*(int(parte) for parte in hora.strip().split(":"))))
        except ValueError:
            raise ErrorValidacion("Ingrese una hora válida en formato HH:MM o HH:MM:SS.") from None
        if type(duracion) is not int or duracion <= 0:
            raise ErrorValidacion("La duración debe ser un número entero de minutos mayor que cero.")
        try:
            fin = inicio + timedelta(minutes=duracion)
        except OverflowError:
            raise ErrorValidacion("La duración produce una fecha de finalización fuera de rango.") from None
        if not isinstance(motivo, str) or not motivo.strip():
            raise ErrorValidacion("El motivo de la cita es obligatorio.")
        return inicio.isoformat(sep=" "), fin.isoformat(sep=" "), motivo.strip()

    @staticmethod
    def _sin_conflicto(citas, veterinario_id, inicio, fin, excluir_id=None):
        conflicto = citas.conflicto(veterinario_id, inicio, fin, excluir_id)
        if conflicto is not None:
            raise ConflictoHorario(
                f"Conflicto de horario: el veterinario tiene una cita el {conflicto['fecha_hora_inicio']} "
                f"de {conflicto['duracion_minutos']} minutos. Seleccione otro horario o profesional."
            )
