"""Agenda y formularios Tkinter; las reglas de horarios pertenecen al servicio."""

import tkinter as tk
from datetime import date
from tkinter import ttk

from services.autenticacion import ErrorValidacion
from services.citas import ESTADOS, ESTADOS_ACTIVOS, TRANSICIONES
from .formulario import Formulario


def etiqueta_mascota(mascota):
    return f"{mascota.nombre} — {mascota.propietario_nombre}, doc. {mascota.propietario_documento} (mascota {mascota.id})"


def etiqueta_veterinario(usuario):
    return f"{usuario.nombre} ({usuario.nombre_usuario})" + (" — inactivo" if not usuario.activo else "")


class Citas(ttk.Frame):
    alto_minimo = 780

    def __init__(self, master, citas, mascotas, veterinarios, puede_gestionar, on_buscar,
                 on_seleccionar, on_programar, on_editar, on_estado, on_volver, filtros=None, seleccionar=None,
                 on_consulta=None):
        super().__init__(master, padding=20)
        self._mascotas = list(mascotas)
        self._veterinarios = list(veterinarios)
        self._on_buscar = on_buscar
        self._on_seleccionar = on_seleccionar
        self._busqueda_fecha_pendiente = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        ttk.Label(self, text="Gestor De Veterinaria", font=("Arial", 20, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Label(self, text="Citas" if puede_gestionar else "Mi agenda — solo consulta",
                  font=("Arial", 14, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        filtro = ttk.Frame(self)
        filtro.grid(row=2, column=0, sticky="ew", pady=6)
        for columna in range(2):
            filtro.columnconfigure(columna, weight=1)
        filtros = filtros or {}
        self.fecha = tk.StringVar(self, value=filtros.get("fecha") or "")
        self.termino = tk.StringVar(self, value=filtros.get("termino") or "")
        ttk.Label(filtro, text="Fecha (AAAA-MM-DD, opcional)").grid(row=0, column=0, sticky="w")
        ttk.Label(filtro, text="Estado").grid(row=0, column=1, sticky="w")
        from .calendario import CalendarioFecha

        filtro_fecha = ttk.Frame(filtro)
        filtro_fecha.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        filtro_fecha.columnconfigure(0, weight=1)
        self.entrada_fecha = CalendarioFecha(filtro_fecha, textvariable=self.fecha, permitir_vacio=True, width=12)
        self.entrada_fecha.grid(row=0, column=0, sticky="ew")
        if filtros.get("fecha"):
            self.entrada_fecha.set_date(date.fromisoformat(filtros["fecha"].strip()))
        else:
            self.fecha.set("")
        self.boton_quitar_fecha = ttk.Button(filtro_fecha, text="Quitar fecha", command=self.quitar_fecha)
        self.boton_quitar_fecha.grid(row=0, column=1, padx=(4, 0))
        self.entrada_fecha.bind("<Return>", self.buscar)
        self.entrada_fecha.bind("<<DateEntrySelected>>", self._fecha_seleccionada)
        self.selector_estado = ttk.Combobox(filtro, values=("Todos los estados",) + ESTADOS, state="readonly")
        self.selector_estado.grid(row=1, column=1, sticky="ew", padx=(4, 0))
        self.selector_estado.current(ESTADOS.index(filtros["estado"]) + 1 if filtros.get("estado") else 0)
        ttk.Label(filtro, text="Veterinario").grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Label(filtro, text="Mascota").grid(row=2, column=1, sticky="w", pady=(4, 0))
        self.selector_veterinario = self._selector(filtro, self._veterinarios, etiqueta_veterinario,
                                                  "Todos los permitidos", filtros.get("veterinario_id"))
        self.selector_veterinario.grid(row=3, column=0, sticky="ew", padx=(0, 4))
        self.selector_mascota = self._selector(filtro, self._mascotas, etiqueta_mascota,
                                              "Todas las mascotas", filtros.get("mascota_id"))
        self.selector_mascota.grid(row=3, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(filtro, text="Buscar mascota, propietario o veterinario").grid(row=4, column=0, sticky="w", pady=(4, 0))
        self.entrada_busqueda = ttk.Entry(filtro, textvariable=self.termino)
        self.entrada_busqueda.grid(row=5, column=0, sticky="ew", padx=(0, 4))
        self.entrada_busqueda.bind("<Return>", self.buscar)
        botones_filtro = ttk.Frame(filtro)
        botones_filtro.grid(row=5, column=1, sticky="ew", padx=(4, 0))
        self.boton_buscar = ttk.Button(botones_filtro, text="Buscar", command=self.buscar)
        self.boton_buscar.pack(side="left", fill="x", expand=True)
        self.boton_limpiar = ttk.Button(botones_filtro, text="Limpiar filtros", command=lambda: on_buscar({}))
        self.boton_limpiar.pack(side="left", fill="x", expand=True)
        for selector in (self.selector_veterinario, self.selector_mascota, self.selector_estado):
            selector.bind("<<ComboboxSelected>>", self.buscar)
        contenedor = ttk.Frame(self)
        contenedor.grid(row=3, column=0, sticky="nsew", pady=6)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)
        columnas = (("mascota_nombre", "Mascota"), ("propietario_nombre", "Propietario"),
                    ("veterinario_nombre", "Veterinario"), ("fecha_hora_inicio", "Inicio"),
                    ("duracion_minutos", "Minutos"), ("estado", "Estado"))
        self.tabla = ttk.Treeview(contenedor, columns=tuple(c for c, _ in columnas),
                                  show="headings", selectmode="browse", height=4)
        for clave, etiqueta in columnas:
            self.tabla.heading(clave, text=etiqueta)
            self.tabla.column(clave, width=160, minwidth=90)
        vertical = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        panel = ttk.LabelFrame(self, text="Detalle de la cita", padding=4)
        panel.grid(row=4, column=0, sticky="ew", pady=4)
        panel.columnconfigure(0, weight=1)
        self.detalle = tk.Text(panel, height=4, width=1, wrap="word", state="disabled")
        barra = ttk.Scrollbar(panel, orient="vertical", command=self.detalle.yview)
        self.detalle.configure(yscrollcommand=barra.set)
        self.detalle.grid(row=0, column=0, sticky="ew")
        barra.grid(row=0, column=1, sticky="ns")
        self.mensaje = tk.StringVar(self, value=f"Citas encontradas: {len(citas)}")
        ttk.Label(self, textvariable=self.mensaje, wraplength=510).grid(row=5, column=0, sticky="w", pady=3)
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=510).grid(row=6, column=0, sticky="w", pady=3)
        acciones = ttk.Frame(self)
        acciones.grid(row=7, column=0, sticky="ew", pady=4)
        for columna in range(2):
            acciones.columnconfigure(columna, weight=1)
        self.boton_programar = None
        self.boton_editar = None
        self.boton_consulta = None
        self.botones_estado = {}
        if puede_gestionar:
            self.boton_programar = ttk.Button(acciones, text="Programar cita", command=on_programar)
            self.boton_programar.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
            self.boton_editar = ttk.Button(acciones, text="Editar / reprogramar", state="disabled",
                                           command=lambda: self._seleccionar(on_editar))
            self.boton_editar.grid(row=0, column=1, sticky="ew", padx=3, pady=3)
            for indice, (estado, texto) in enumerate((("CONFIRMADA", "Confirmar"), ("CANCELADA", "Cancelar cita"),
                                                     ("COMPLETADA", "Marcar completada"), ("NO_ASISTIO", "No asistió"))):
                boton = ttk.Button(acciones, text=texto, state="disabled",
                                   command=lambda e=estado: self._seleccionar(lambda id: on_estado(id, e)))
                boton.grid(row=1 + indice // 2, column=indice % 2, sticky="ew", padx=3, pady=3)
                self.botones_estado[estado] = boton
        if on_consulta is not None:
            self.boton_consulta = ttk.Button(acciones, text="Registrar consulta", state="disabled",
                                             command=lambda: self._seleccionar(on_consulta))
            self.boton_consulta.grid(row=3, column=0, columnspan=2, sticky="ew", padx=3, pady=3)
        ttk.Button(self, text="Volver al panel", command=on_volver).grid(row=8, column=0, sticky="ew", pady=4)
        for cita in citas:
            self.tabla.insert("", "end", iid=str(cita.id), values=tuple(getattr(cita, c) for c, _ in columnas))
        self.mostrar_detalle(None)
        self.tabla.bind("<<TreeviewSelect>>", self._cambio_seleccion)
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))

    def _selector(self, master, filas, etiqueta, todos, seleccionado):
        selector = ttk.Combobox(master, values=(todos,) + tuple(etiqueta(f) for f in filas), state="readonly")
        selector.current(0)
        for indice, fila in enumerate(filas, 1):
            if fila.id == seleccionado:
                selector.current(indice)
                break
        return selector

    def buscar(self, event=None):
        vet = self.selector_veterinario.current()
        mascota = self.selector_mascota.current()
        estado = self.selector_estado.current()
        self._on_buscar(dict(fecha=self.fecha.get(), termino=self.termino.get(),
                             veterinario_id=self._veterinarios[vet - 1].id if vet > 0 else None,
                             mascota_id=self._mascotas[mascota - 1].id if mascota > 0 else None,
                             estado=ESTADOS[estado - 1] if estado > 0 else None))
        return "break"

    def quitar_fecha(self):
        self.fecha.set("")
        return self.buscar()

    def _fecha_seleccionada(self, event=None):
        # DateEntry debe terminar de cerrar su desplegable antes de reconstruir la vista.
        if self._busqueda_fecha_pendiente is not None:
            self.after_cancel(self._busqueda_fecha_pendiente)
        self._busqueda_fecha_pendiente = self.after_idle(self._aplicar_fecha)

    def _aplicar_fecha(self):
        self._busqueda_fecha_pendiente = None
        self.buscar()

    def destroy(self):
        if self._busqueda_fecha_pendiente is not None:
            self.after_cancel(self._busqueda_fecha_pendiente)
            self._busqueda_fecha_pendiente = None
        super().destroy()

    def _cambio_seleccion(self, event=None):
        self.mostrar_detalle(None)
        seleccion = self.tabla.selection()
        if seleccion:
            self._on_seleccionar(int(seleccion[0]))

    def _seleccionar(self, callback):
        seleccion = self.tabla.selection()
        if seleccion:
            callback(int(seleccion[0]))
        else:
            self.mostrar_error("Seleccione una cita de la tabla.")

    def mostrar_detalle(self, cita):
        texto = "Seleccione una cita para consultar su detalle."
        if self.boton_consulta is not None:
            atendible = cita is not None and cita.estado in ("PROGRAMADA", "CONFIRMADA", "COMPLETADA") and cita.consulta_id is None
            self.boton_consulta.state(["!disabled"] if atendible else ["disabled"])
        if self.boton_editar is not None:
            editable = cita is not None and cita.estado in ESTADOS_ACTIVOS and cita.consulta_id is None
            self.boton_editar.state(["!disabled"] if editable else ["disabled"])
            for estado, boton in self.botones_estado.items():
                permitido = cita is not None and estado in TRANSICIONES[cita.estado]
                permitido = permitido and (cita.consulta_id is None or estado == "COMPLETADA")
                boton.state(["!disabled"] if permitido else ["disabled"])
        if cita is not None:
            texto = (f"Mascota: {cita.mascota_nombre}\nPropietario: {cita.propietario_nombre} ({cita.propietario_documento})\n"
                     f"Veterinario: {cita.veterinario_nombre} ({cita.veterinario_usuario})\n"
                     f"Inicio: {cita.fecha_hora_inicio}\nFin: {cita.fecha_hora_fin}\n"
                     f"Duración: {cita.duracion_minutos} minutos\nEstado: {cita.estado}\nMotivo: {cita.motivo}")
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", texto)
        self.detalle.configure(state="disabled")

    def mostrar_error(self, mensaje):
        self.error.set(mensaje)


HORAS = tuple(f"{hora:02d}" for hora in range(24))
MINUTOS = tuple(f"{minuto:02d}" for minuto in range(0, 60, 5))


class SelectorHora(ttk.Frame):
    """Dos selectores; conserva la precisión de una hora histórica sin redondearla."""

    def __init__(self, master, variable, original=None, *, minutos_permitidos=MINUTOS, hora_inicial="09:00"):
        super().__init__(master)
        self._variable = variable
        self._original = original
        self._minutos_permitidos = tuple(minutos_permitidos)
        self._trazas = []
        self.hora = tk.StringVar(self, value=original[:2] if original else hora_inicial[:2])
        self.minuto = tk.StringVar(self, value=original[3:5] if original else hora_inicial[3:5])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        ttk.Label(self, text="Hora").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Minutos").grid(row=0, column=2, sticky="w")
        self.horas = ttk.Combobox(self, values=HORAS, textvariable=self.hora, state="readonly", width=5)
        self.minutos = ttk.Combobox(self, values=self._minutos_permitidos, textvariable=self.minuto, state="readonly", width=5)
        self.horas.grid(row=1, column=0, sticky="ew")
        ttk.Label(self, text=":").grid(row=1, column=1, padx=8)
        self.minutos.grid(row=1, column=2, sticky="ew")
        self.aviso = tk.StringVar(self)
        ttk.Label(self, textvariable=self.aviso, wraplength=490).grid(row=2, column=0, columnspan=3, sticky="w", pady=(3, 0))
        for valor in (self.hora, self.minuto):
            self._trazas.append((valor, valor.trace_add("write", self._actualizar)))
        self._actualizar()

    def _es_original(self):
        return self._original is not None and f"{self.hora.get()}:{self.minuto.get()}" == self._original[:5]

    def _actualizar(self, *_):
        hora = self._original if self._es_original() else f"{self.hora.get()}:{self.minuto.get()}:00"
        self._variable.set(hora)
        especial = self._original and (self._original[3:5] not in self._minutos_permitidos or self._original[6:] != "00")
        if especial and self._es_original():
            self.aviso.set(f"Hora existente: {self._original}. Se conserva mientras no cambie la hora o los minutos.")
        else:
            self.aviso.set("Formato de 24 horas; minutos en intervalos de cinco." if self._minutos_permitidos == MINUTOS
                           else "Formato de 24 horas; minutos de 00 a 59.")

    def obtener(self):
        if self.hora.get() not in HORAS:
            raise ErrorValidacion("Seleccione una hora entre 00 y 23.")
        if not self._es_original() and self.minuto.get() not in self._minutos_permitidos:
            raise ErrorValidacion("Seleccione los minutos en intervalos de cinco." if self._minutos_permitidos == MINUTOS
                                  else "Seleccione minutos válidos de la lista.")
        return self._original if self._es_original() else f"{self.hora.get()}:{self.minuto.get()}:00"

    def destroy(self):
        for variable, traza in self._trazas:
            variable.trace_remove("write", traza)
        super().destroy()


class FormularioCita(Formulario):
    alto_minimo = 700

    def __init__(self, master, mascotas, veterinarios, on_submit, on_cancel, cita=None):
        self._mascotas = list(mascotas)
        self._veterinarios = list(veterinarios)
        self._hora_original = cita.fecha_hora_inicio[11:] if cita is not None else None

        def enviar_datos(**datos):
            try:
                datos["hora_inicio"] = self.entradas["hora_inicio"].obtener()
            except ErrorValidacion as error:
                self.mostrar_error(str(error))
                return
            for campo, filas in (("mascota_id", self._mascotas), ("veterinario_id", self._veterinarios)):
                indice = self.entradas[campo].current()
                datos[campo] = filas[indice].id if indice >= 0 else None
            try:
                datos["duracion_minutos"] = int(datos["duracion_minutos"])
            except ValueError:
                pass  # El servicio devuelve el mensaje de validación.
            on_submit(**datos)

        super().__init__(
            master, "Programar cita" if cita is None else "Editar / reprogramar cita",
            "Seleccione una mascota y un veterinario activo. Todos los campos son obligatorios.",
            (("mascota_id", "Mascota", False), ("veterinario_id", "Veterinario activo", False),
             ("fecha", "Fecha (AAAA-MM-DD)", False), ("hora_inicio", "Hora de inicio", False),
             ("duracion_minutos", "Duración en minutos", False), ("motivo", "Motivo", False)),
            "Guardar cita", enviar_datos, opciones={
                "mascota_id": tuple(etiqueta_mascota(m) for m in self._mascotas),
                "veterinario_id": tuple(etiqueta_veterinario(v) for v in self._veterinarios),
            }, on_cancel=on_cancel,
            constructores={"fecha": self._crear_fecha, "hora_inicio": self._crear_hora},
        )
        self.valores["duracion_minutos"].set("30")
        if cita is not None:
            self.entradas["fecha"].set_date(date.fromisoformat(cita.fecha_hora_inicio[:10]))
            self.valores["duracion_minutos"].set(str(cita.duracion_minutos))
            self.valores["motivo"].set(cita.motivo)
            for campo, filas in (("mascota_id", self._mascotas), ("veterinario_id", self._veterinarios)):
                for indice, fila in enumerate(filas):
                    if fila.id == getattr(cita, campo):
                        self.entradas[campo].current(indice)
                        break

    @staticmethod
    def _crear_fecha(master, variable):
        # Se carga al abrir el formulario; las pruebas de servicios no dependen de Tkcalendar.
        from .calendario import CalendarioFecha

        return CalendarioFecha(master, textvariable=variable)

    def _crear_hora(self, master, variable):
        selector = SelectorHora(master, variable, self._hora_original)
        for combo in (selector.horas, selector.minutos):
            combo.bind("<Return>", self.enviar)
        return selector
