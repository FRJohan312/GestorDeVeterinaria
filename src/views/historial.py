"""Exploración del historial médico, exclusivamente de lectura y sin SQL."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from .citas import etiqueta_mascota


def fecha_legible(valor):
    return datetime.fromisoformat(valor).strftime("%d/%m/%Y %H:%M:%S") if valor else "Sin registrar"


class Historial(ttk.Frame):
    alto_minimo = 740
    ancho_minimo = 660

    def __init__(self, master, mascotas, on_buscar, on_consultar, on_volver, historial=None):
        super().__init__(master, padding=15)
        self._on_buscar = on_buscar
        self._on_consultar = on_consultar
        self._atenciones = {}
        self._tratamientos = {}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        ttk.Label(self, text="Gestión de Historial", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Historial médico — solo lectura", font=("Arial", 14, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        filtros = ttk.Frame(self)
        filtros.grid(row=2, column=0, sticky="ew", pady=4)
        filtros.columnconfigure(0, weight=1)
        ttk.Label(filtros, text="Buscar mascota por nombre, especie o propietario").grid(row=0, column=0, sticky="w")
        self.busqueda = tk.StringVar(self)
        self.entrada_busqueda = ttk.Entry(filtros, textvariable=self.busqueda)
        self.entrada_busqueda.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        self.entrada_busqueda.bind("<Return>", self.buscar)
        self.boton_buscar = ttk.Button(filtros, text="Buscar", command=self.buscar)
        self.boton_buscar.grid(row=1, column=1, padx=3)
        self.boton_limpiar = ttk.Button(filtros, text="Mostrar todas", command=self._limpiar_busqueda)
        self.boton_limpiar.grid(row=1, column=2, padx=3)
        self.selector_mascota = ttk.Combobox(filtros, state="readonly")
        self.selector_mascota.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5, padx=(0, 5))
        self.selector_mascota.bind("<<ComboboxSelected>>", self.consultar)
        self.boton_consultar = ttk.Button(filtros, text="Ver / actualizar", command=self.consultar)
        self.boton_consultar.grid(row=2, column=2, padx=3)
        self.datos_mascota = tk.StringVar(self)
        ttk.Label(self, textvariable=self.datos_mascota, wraplength=620).grid(row=3, column=0, sticky="ew", pady=4)

        self.paneles = ttk.Panedwindow(self, orient="vertical")
        self.paneles.grid(row=4, column=0, sticky="nsew")
        consultas = ttk.LabelFrame(self.paneles, text="Consultas — más recientes primero", padding=4)
        self.tabla_consultas = self._tabla(consultas, (
            ("fecha", "Fecha y hora", 160), ("veterinario", "Veterinario", 150), ("diagnostico", "Diagnóstico", 230),
        ), altura=4)
        self.paneles.add(consultas, weight=2)
        clinica = ttk.LabelFrame(self.paneles, text="Detalle de la consulta", padding=4)
        self.detalle_consulta = self._texto(clinica, altura=6)
        self.paneles.add(clinica, weight=2)
        tratamientos = ttk.LabelFrame(self.paneles, text="Tratamientos de la consulta seleccionada", padding=4)
        tratamientos.columnconfigure(0, weight=1)
        tratamientos.rowconfigure(0, weight=1)
        tabla = ttk.Frame(tratamientos)
        tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla_tratamientos = self._tabla(tabla, (
            ("descripcion", "Descripción", 220), ("medicamento", "Medicamento", 150),
            ("dosis", "Dosis", 140), ("duracion", "Duración", 140),
        ), altura=3)
        self.mensaje_tratamientos = tk.StringVar(self)
        ttk.Label(tratamientos, textvariable=self.mensaje_tratamientos).grid(row=1, column=0, sticky="w", pady=2)
        panel_detalle = ttk.Frame(tratamientos)
        panel_detalle.grid(row=2, column=0, sticky="nsew")
        self.detalle_tratamiento = self._texto(panel_detalle, altura=4)
        self.paneles.add(tratamientos, weight=3)
        self.mensaje = tk.StringVar(self)
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.mensaje, wraplength=620).grid(row=5, column=0, sticky="w", pady=3)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=620).grid(row=6, column=0, sticky="w", pady=3)
        self.boton_volver = ttk.Button(self, text="Volver", command=on_volver)
        self.boton_volver.grid(row=7, column=0, sticky="ew", pady=4)
        self.tabla_consultas.bind("<<TreeviewSelect>>", self._seleccionar_consulta)
        self.tabla_tratamientos.bind("<<TreeviewSelect>>", self._seleccionar_tratamiento)
        self.mostrar_mascotas(mascotas)
        if historial is not None:
            self.mostrar_historial(historial)

    @staticmethod
    def _tabla(panel, columnas, altura):
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)
        tabla = ttk.Treeview(panel, columns=tuple(c for c, _, _ in columnas), show="headings", selectmode="browse", height=altura)
        for clave, etiqueta, ancho in columnas:
            tabla.heading(clave, text=etiqueta)
            tabla.column(clave, width=ancho, minwidth=90)
        vertical = ttk.Scrollbar(panel, orient="vertical", command=tabla.yview)
        horizontal = ttk.Scrollbar(panel, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        return tabla

    @staticmethod
    def _texto(panel, altura):
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)
        texto = tk.Text(panel, height=altura, width=1, state="disabled", wrap="word")
        barra = ttk.Scrollbar(panel, orient="vertical", command=texto.yview)
        texto.configure(yscrollcommand=barra.set)
        texto.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        return texto

    @staticmethod
    def _escribir(campo, texto):
        campo.configure(state="normal")
        campo.delete("1.0", "end")
        campo.insert("1.0", texto)
        campo.configure(state="disabled")

    def buscar(self, event=None):
        self._on_buscar(self.busqueda.get())
        return "break"

    def _limpiar_busqueda(self):
        self.busqueda.set("")
        self.buscar()

    def consultar(self, event=None):
        indice = self.selector_mascota.current()
        if indice < 0:
            self.mostrar_error("Seleccione una mascota para consultar su historial.")
        else:
            self.mostrar_historial(None)
            self._on_consultar(self._mascotas[indice].id)

    def mostrar_mascotas(self, mascotas):
        self._mascotas = list(mascotas)
        self.selector_mascota.set("")
        self.selector_mascota.configure(values=tuple(f"#{m.id} — {etiqueta_mascota(m)}" for m in mascotas))
        self.boton_consultar.state(["!disabled"] if mascotas else ["disabled"])
        self.mostrar_historial(None)
        self.mensaje.set(f"Mascotas encontradas: {len(mascotas)}. Seleccione una para consultar su historial."
                         if mascotas else "No se encontraron mascotas. Registre una o cambie la búsqueda.")

    def mostrar_historial(self, historial):
        self.error.set("")
        self._atenciones = {}
        self.tabla_consultas.delete(*self.tabla_consultas.get_children())
        self._limpiar_consulta()
        self.datos_mascota.set("Seleccione una mascota para visualizar sus datos y antecedentes.")
        self.mensaje.set("")
        if historial is None:
            return
        mascota = historial.mascota
        indice = next((i for i, m in enumerate(self._mascotas) if m.id == mascota.id), None)
        if indice is not None:
            self.selector_mascota.current(indice)
        self.datos_mascota.set(
            f"{mascota.nombre} — {mascota.especie} | Raza: {mascota.raza or 'Sin registrar'} | Sexo: {mascota.sexo}\n"
            f"Nacimiento: {mascota.fecha_nacimiento or 'Sin registrar'} | "
            f"Propietario: {mascota.propietario_nombre} ({mascota.propietario_documento})"
        )
        for atencion in historial.atenciones:
            consulta = atencion.consulta
            self._atenciones[consulta.id] = atencion
            self.tabla_consultas.insert("", "end", iid=str(consulta.id), values=(
                fecha_legible(consulta.fecha), consulta.veterinario_nombre, consulta.diagnostico or "Sin registrar",
            ))
        self.mensaje.set(f"Consultas registradas: {len(historial.atenciones)}. Seleccione una atención."
                         if historial.atenciones else "Esta mascota aún no tiene consultas registradas.")
        if historial.atenciones:
            self.tabla_consultas.selection_set(str(historial.atenciones[0].consulta.id))
            self._seleccionar_consulta()

    def _limpiar_consulta(self):
        self._tratamientos = {}
        self.tabla_tratamientos.delete(*self.tabla_tratamientos.get_children())
        self._escribir(self.detalle_consulta, "Seleccione una consulta para visualizar sus detalles.")
        self._escribir(self.detalle_tratamiento, "Seleccione un tratamiento para leer su información completa.")
        self.mensaje_tratamientos.set("Seleccione una consulta.")

    def _seleccionar_consulta(self, event=None):
        self._limpiar_consulta()
        seleccion = self.tabla_consultas.selection()
        atencion = self._atenciones.get(int(seleccion[0])) if seleccion else None
        if atencion is None:
            return
        consulta = atencion.consulta
        peso = f"{consulta.peso:g} kg" if consulta.peso is not None else "Sin registrar"
        cita = (f"#{consulta.cita_id} — {consulta.cita_estado}, programada para {fecha_legible(consulta.cita_fecha_hora_inicio)}"
                if consulta.cita_id is not None else "Sin cita")
        self._escribir(self.detalle_consulta,
                       f"Consulta #{consulta.id} — {fecha_legible(consulta.fecha)}\n"
                       f"Veterinario: {consulta.veterinario_nombre} ({consulta.veterinario_usuario})\nCita: {cita}\n"
                       f"Peso: {peso}\n\nSíntomas:\n{consulta.sintomas}\n\nDiagnóstico:\n{consulta.diagnostico or 'Sin registrar'}\n\n"
                       f"Observaciones:\n{consulta.observaciones or 'Sin registrar'}")
        for tratamiento in atencion.tratamientos:
            self._tratamientos[tratamiento.id] = tratamiento
            self.tabla_tratamientos.insert("", "end", iid=str(tratamiento.id), values=(
                tratamiento.descripcion, tratamiento.medicamento or "Sin registrar",
                tratamiento.dosis or "Sin registrar", tratamiento.duracion or "Sin registrar",
            ))
        self.mensaje_tratamientos.set(f"Tratamientos registrados: {len(atencion.tratamientos)}."
                                      if atencion.tratamientos else "Esta consulta no tiene tratamientos registrados.")
        if atencion.tratamientos:
            self.tabla_tratamientos.selection_set(str(atencion.tratamientos[0].id))
            self._seleccionar_tratamiento()

    def _seleccionar_tratamiento(self, event=None):
        seleccion = self.tabla_tratamientos.selection()
        tratamiento = self._tratamientos.get(int(seleccion[0])) if seleccion else None
        texto = "Seleccione un tratamiento para leer su información completa."
        if tratamiento is not None:
            texto = (f"Descripción:\n{tratamiento.descripcion}\n\nMedicamento:\n{tratamiento.medicamento or 'Sin registrar'}\n\n"
                     f"Dosis:\n{tratamiento.dosis or 'Sin registrar'}\n\nDuración:\n{tratamiento.duracion or 'Sin registrar'}")
        self._escribir(self.detalle_tratamiento, texto)

    def mostrar_error(self, mensaje):
        self.error.set(mensaje)
