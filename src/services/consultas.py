"""Altas clínicas inmutables: veterinario de sesión y finalización atómica de la cita."""

import math
import re
from contextlib import contextmanager
from datetime import date, datetime, time

from database.consultas import acceso_consultas
from models.cita import Cita
from models.consulta import Consulta
from models.mascota import Mascota
from models.usuario import UsuarioGestion
from .autenticacion import ErrorValidacion, PermisoDenegado, ServicioAutenticacion


ESTADOS_ATENDIBLES = frozenset({"PROGRAMADA", "CONFIRMADA", "COMPLETADA"})


class ServicioConsultas:
    def __init__(self, autenticacion: ServicioAutenticacion):
        self.autenticacion = autenticacion

    @contextmanager
    def _acceso(self, *, escritura=False, registro=False):
        with acceso_consultas(self.autenticacion.ruta, escritura=escritura) as repositorios:
            permiso = "registrar_consultas" if escritura or registro else "consultar_consultas"
            self.autenticacion.exigir_permiso(permiso, usuarios=repositorios[3])
            if (escritura or registro) and self.autenticacion.usuario_actual.rol != "VETERINARIO":
                raise PermisoDenegado("Solo un veterinario autenticado puede registrar consultas médicas.")
            yield repositorios

    def listar(self) -> list[Consulta]:
        return self.buscar()

    def buscar(self, mascota_id=None, fecha=None, veterinario_id=None) -> list[Consulta]:
        with self._acceso() as (consultas, _, mascotas, usuarios):
            if mascota_id is not None:
                self._mascota(mascotas, mascota_id)
            fecha = None if fecha in (None, "") else self._fecha(fecha).isoformat()
            if veterinario_id is not None:
                self._identificador(veterinario_id, "veterinario")
                usuario = usuarios.buscar_por_id(veterinario_id)
                if usuario is None or usuario["rol"] != "VETERINARIO":
                    raise ErrorValidacion("Seleccione un veterinario existente.")
            return [Consulta(**dict(fila)) for fila in consultas.buscar(mascota_id, fecha, veterinario_id)]

    def obtener(self, consulta_id: int) -> Consulta:
        with self._acceso() as (consultas, _, _, _):
            self._identificador(consulta_id, "registro de consulta")
            fila = consultas.obtener(consulta_id)
            if fila is None:
                raise ErrorValidacion("La consulta seleccionada no existe.")
            return Consulta(**dict(fila))

    def mascotas_disponibles(self) -> list[Mascota]:
        with self._acceso() as (_, _, mascotas, _):
            return [Mascota(**dict(fila)) for fila in mascotas.buscar("")]

    def veterinarios_disponibles(self) -> list[UsuarioGestion]:
        with self._acceso() as (_, _, _, usuarios):
            return [UsuarioGestion(id=f["id"], nombre=f["nombre"], nombre_usuario=f["nombre_usuario"],
                                   rol=f["rol"], activo=bool(f["activo"]))
                    for f in usuarios.listar_veterinarios(incluir_inactivos=True)]

    def citas_disponibles(self, mascota_id=None) -> list[Cita]:
        with self._acceso(registro=True) as (_, citas, mascotas, _):
            if mascota_id is not None:
                self._mascota(mascotas, mascota_id)
            return [Cita(**dict(fila)) for fila in citas.buscar(
                veterinario_id=self.autenticacion.usuario_actual.id, mascota_id=mascota_id
            ) if fila["estado"] in ESTADOS_ATENDIBLES and fila["consulta_id"] is None]

    def registrar(self, mascota_id, fecha, hora, sintomas, peso=None,
                  diagnostico=None, observaciones=None, cita_id=None) -> Consulta:
        with self._acceso(escritura=True) as (consultas, citas, mascotas, _):
            veterinario_id = self.autenticacion.usuario_actual.id
            self._mascota(mascotas, mascota_id)
            fecha_hora = self._fecha_hora(fecha, hora)
            if not isinstance(sintomas, str) or not sintomas.strip():
                raise ErrorValidacion("Los síntomas son obligatorios.")
            if peso is not None:
                try:
                    if type(peso) not in (int, float):
                        raise ValueError
                    peso = float(peso)
                    if not math.isfinite(peso) or peso <= 0:
                        raise ValueError
                except (ValueError, OverflowError):
                    raise ErrorValidacion("El peso debe ser un número positivo y finito en kilogramos.") from None
            diagnostico = self._opcional(diagnostico, "diagnóstico")
            observaciones = self._opcional(observaciones, "observaciones")
            if cita_id is not None:
                self._validar_cita(citas, cita_id, mascota_id, veterinario_id)
            consulta_id = consultas.crear(mascota_id, veterinario_id, cita_id, fecha_hora, peso,
                                         sintomas.strip(), diagnostico, observaciones)
            if cita_id is not None:
                # El registro clínico acredita la atención: también finaliza una PROGRAMADA.
                # Se actualiza en esta misma transacción; no se crea una consulta parcial.
                citas.cambiar_estado(cita_id, "COMPLETADA")
            return Consulta(**dict(consultas.obtener(consulta_id)))

    @classmethod
    def _validar_cita(cls, citas, cita_id, mascota_id, veterinario_id):
        cls._identificador(cita_id, "cita")
        cita = citas.obtener(cita_id)
        if cita is None:
            raise ErrorValidacion("La cita seleccionada no existe.")
        if cita["mascota_id"] != mascota_id or cita["veterinario_id"] != veterinario_id:
            raise ErrorValidacion("La cita debe corresponder a la mascota y al veterinario de la sesión.")
        if cita["consulta_id"] is not None:
            raise ErrorValidacion("La cita ya tiene una consulta asociada.")
        if cita["estado"] not in ESTADOS_ATENDIBLES:
            raise ErrorValidacion("No se puede atender una cita cancelada o marcada como NO_ASISTIO.")

    @staticmethod
    def _identificador(valor, etiqueta):
        if type(valor) is not int or valor <= 0:
            raise ErrorValidacion(f"Seleccione un {etiqueta} válido.")

    @classmethod
    def _mascota(cls, mascotas, mascota_id):
        cls._identificador(mascota_id, "registro de mascota")
        if mascotas.obtener(mascota_id) is None:
            raise ErrorValidacion("La mascota seleccionada no existe.")

    @staticmethod
    def _opcional(valor, etiqueta):
        if valor is not None and not isinstance(valor, str):
            raise ErrorValidacion(f"El campo {etiqueta} debe ser texto.")
        return (valor.strip() or None) if valor is not None else None

    @staticmethod
    def _fecha(valor):
        try:
            if not isinstance(valor, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor.strip()) is None:
                raise ValueError
            return date.fromisoformat(valor.strip())
        except ValueError:
            raise ErrorValidacion("Ingrese una fecha válida con formato AAAA-MM-DD.") from None

    @classmethod
    def _fecha_hora(cls, fecha, hora):
        dia = cls._fecha(fecha)
        try:
            if not isinstance(hora, str) or re.fullmatch(r"[0-9]{2}:[0-9]{2}(:[0-9]{2})?", hora.strip()) is None:
                raise ValueError
            return datetime.combine(dia, time(*(int(p) for p in hora.strip().split(":")))).isoformat(sep=" ")
        except ValueError:
            raise ErrorValidacion("Ingrese una hora válida en formato HH:MM o HH:MM:SS.") from None
