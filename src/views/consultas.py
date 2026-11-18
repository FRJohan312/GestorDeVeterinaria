"""Registro clínico, filtros y detalle de solo lectura; sin operaciones SQL."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from services.autenticacion import ErrorValidacion
from .citas import SelectorHora, etiqueta_mascota, etiqueta_veterinario
from .formulario import Formulario


class Consultas(ttk.Frame):
    alto_minimo = 740

    def __init__(self, master, consultas, mascotas, veterinarios, puede_registrar,
                 on_buscar, on_seleccionar, on_registrar, on_volver, filtros=None, seleccionar=None,
                 on_tratamientos=None):
        super().__init__(master, padding=20)
        from .calendario import CalendarioFecha

        self._mascotas = list(mascotas)
        self._veterinarios = list(veterinarios)
        self._on_buscar = on_buscar
        self._on_seleccionar = on_seleccionar
        self._busqueda_pendiente = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        filtros = filtros or {}
        ttk.Label(self, text="Gestor De Veterinaria", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Consultas veterinarias", font=("Arial", 14, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        filtro = ttk.Frame(self)
        filtro.grid(row=2, column=0, sticky="ew", pady=6)
        for columna in range(2):
            filtro.columnconfigure(columna, weight=1)
        ttk.Label(filtro, text="Mascota").grid(row=0, column=0, sticky="w")
        ttk.Label(filtro, text="Veterinario").grid(row=0, column=1, sticky="w")
        self.selector_mascota = self._selector(filtro, self._mascotas, etiqueta_mascota, "Todas las mascotas", filtros.get("mascota_id"))
        self.selector_mascota.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        self.selector_veterinario = self._selector(filtro, self._veterinarios, etiqueta_veterinario, "Todos los veterinarios", filtros.get("veterinario_id"))
        self.selector_veterinario.grid(row=1, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(filtro, text="Fecha de atención (opcional)").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.fecha = tk.StringVar(self)
        self.entrada_fecha = CalendarioFecha(filtro, textvariable=self.fecha, permitir_vacio=True)
        self.entrada_fecha.grid(row=3, column=0, sticky="ew", padx=(0, 4))
        if filtros.get("fecha"):
            self.entrada_fecha.set_date(datetime.fromisoformat(filtros["fecha"].strip()).date())
        else:
            self.fecha.set("")
        self.entrada_fecha.bind("<<DateEntrySelected>>", self._fecha_seleccionada)
        self.entrada_fecha.bind("<Return>", self.buscar)
        botones = ttk.Frame(filtro)
        botones.grid(row=3, column=1, sticky="ew", padx=(4, 0))
        self.boton_buscar = ttk.Button(botones, text="Buscar", command=self.buscar)
        self.boton_buscar.pack(side="left", expand=True, fill="x")
        self.boton_limpiar = ttk.Button(botones, text="Limpiar filtros", command=lambda: on_buscar({}))
        self.boton_limpiar.pack(side="left", expand=True, fill="x")
        for selector in (self.selector_mascota, self.selector_veterinario):
            selector.bind("<<ComboboxSelected>>", self.buscar)
        contenedor = ttk.Frame(self)
        contenedor.grid(row=3, column=0, sticky="nsew", pady=6)
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)
        columnas = (("fecha", "Fecha y hora"), ("mascota_nombre", "Mascota"), ("propietario_nombre", "Propietario"),
                    ("veterinario_nombre", "Veterinario"), ("peso", "Peso (kg)"), ("cita_id", "Cita"))
        self.tabla = ttk.Treeview(contenedor, columns=tuple(c for c, _ in columnas), show="headings", selectmode="browse", height=5)
        for clave, texto in columnas:
            self.tabla.heading(clave, text=texto)
            self.tabla.column(clave, width=150, minwidth=80)
        vertical = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        panel = ttk.LabelFrame(self, text="Detalle clínico — solo lectura", padding=4)
        panel.grid(row=4, column=0, sticky="ew", pady=6)
        panel.columnconfigure(0, weight=1)
        self.detalle = tk.Text(panel, height=8, width=1, wrap="word", state="disabled")
        barra = ttk.Scrollbar(panel, orient="vertical", command=self.detalle.yview)
        self.detalle.configure(yscrollcommand=barra.set)
        self.detalle.grid(row=0, column=0, sticky="ew")
        barra.grid(row=0, column=1, sticky="ns")
        self.mensaje = tk.StringVar(self, value=f"Atenciones encontradas: {len(consultas)}")
        ttk.Label(self, textvariable=self.mensaje, wraplength=510).grid(row=5, column=0, sticky="w", pady=3)
        self.error = tk.StringVar(self)
        ttk.Label(self, textvariable=self.error, foreground="#9c2020", wraplength=510).grid(row=6, column=0, sticky="w", pady=3)
        self.boton_registrar = None
        if puede_registrar:
            self.boton_registrar = ttk.Button(self, text="Registrar consulta médica", command=on_registrar)
            self.boton_registrar.grid(row=7, column=0, sticky="ew", pady=4)
        self.boton_tratamientos = ttk.Button(self, text="Ver tratamientos", state="disabled",
                                            command=lambda: on_tratamientos(int(self.tabla.selection()[0])))
        if on_tratamientos is not None:
            self.boton_tratamientos.grid(row=8, column=0, sticky="ew", pady=4)
        ttk.Button(self, text="Volver al panel", command=on_volver).grid(row=9, column=0, sticky="ew", pady=4)
        for consulta in consultas:
            self.tabla.insert("", "end", iid=str(consulta.id), values=tuple(
                getattr(consulta, c) if getattr(consulta, c) is not None else "" for c, _ in columnas
            ))
        self.mostrar_detalle(None)
        self.tabla.bind("<<TreeviewSelect>>", self._seleccion)
        if seleccionar is not None and self.tabla.exists(str(seleccionar)):
            self.tabla.selection_set(str(seleccionar))
            self.tabla.see(str(seleccionar))

    @staticmethod
    def _selector(master, filas, etiqueta, todos, seleccionado):
        selector = ttk.Combobox(master, values=(todos,) + tuple(etiqueta(f) for f in filas), state="readonly")
        selector.current(next((i for i, f in enumerate(filas, 1) if f.id == seleccionado), 0))
        return selector

    def buscar(self, event=None):
        mascota = self.selector_mascota.current()
        vet = self.selector_veterinario.current()
        self._on_buscar(dict(mascota_id=self._mascotas[mascota - 1].id if mascota > 0 else None,
                             veterinario_id=self._veterinarios[vet - 1].id if vet > 0 else None, fecha=self.fecha.get()))
        return "break"

    def _fecha_seleccionada(self, event=None):
        if self._busqueda_pendiente is not None:
            self.after_cancel(self._busqueda_pendiente)
        self._busqueda_pendiente = self.after_idle(self._aplicar_fecha)

    def _aplicar_fecha(self):
        self._busqueda_pendiente = None
        self.buscar()

    def _seleccion(self, event=None):
        self.mostrar_detalle(None)
        self.boton_tratamientos.state(["disabled"])
        if self.tabla.selection():
            self._on_seleccionar(int(self.tabla.selection()[0]))

    def mostrar_detalle(self, consulta):
        self.boton_tratamientos.state(["!disabled"] if consulta is not None else ["disabled"])
        texto = "Seleccione una atención para visualizar su información clínica."
        if consulta is not None:
            cita = f"{consulta.cita_id} — {consulta.cita_estado}" if consulta.cita_id is not None else "Sin cita"
            peso = f"{consulta.peso:g} kg" if consulta.peso is not None else "Sin registrar"
            texto = (f"Fecha y hora: {consulta.fecha}\nMascota: {consulta.mascota_nombre}\n"
                     f"Propietario: {consulta.propietario_nombre} ({consulta.propietario_documento})\n"
                     f"Veterinario: {consulta.veterinario_nombre} ({consulta.veterinario_usuario})\nCita: {cita}\nPeso: {peso}\n\n"
                     f"Síntomas:\n{consulta.sintomas}\n\nDiagnóstico:\n{consulta.diagnostico or 'Sin registrar'}\n\n"
                     f"Observaciones:\n{consulta.observaciones or 'Sin registrar'}")
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", texto)
        self.detalle.configure(state="disabled")

    def mostrar_error(self, mensaje):
        self.error.set(mensaje)

    def destroy(self):
        if self._busqueda_pendiente is not None:
            self.after_cancel(self._busqueda_pendiente)
            self._busqueda_pendiente = None
        super().destroy()


class FormularioConsulta(ttk.Frame):
    """Formulario compartido dentro de un panel desplazable para los textos clínicos."""

    alto_minimo = 740
    ancho_minimo = 600

    def __init__(self, master, mascotas, citas, usuario, on_submit, on_cancel, on_citas, cita=None):
        super().__init__(master)
        from .calendario import CalendarioFecha

        self._mascotas = list(mascotas)
        self._citas = list(citas)
        self._on_citas = on_citas
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0, background=ttk.Style(self).lookup("TFrame", "background"))
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=barra.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")

        def texto(master, variable):
            return tk.Text(master, height=3, wrap="word", width=1)

        def hora(master, variable):
            selector = SelectorHora(master, variable, minutos_permitidos=tuple(f"{m:02d}" for m in range(60)),
                                    hora_inicial=datetime.now().strftime("%H:%M"))
            for combo in (selector.horas, selector.minutos):
                combo.bind("<Return>", lambda evento: self.formulario.enviar())
            return selector

        def enviar(**datos):
            indice = self.entradas["mascota_id"].current()
            datos["mascota_id"] = self._mascotas[indice].id if indice >= 0 else None
            indice = self.entradas["cita_id"].current()
            datos["cita_id"] = self._citas[indice - 1].id if indice > 0 else None
            try:
                datos["hora"] = self.entradas["hora"].obtener()
            except ErrorValidacion as error:
                self.mostrar_error(str(error))
                return
            for campo in ("sintomas", "diagnostico", "observaciones"):
                datos[campo] = self.entradas[campo].get("1.0", "end-1c")
            peso = datos["peso"].strip()
            try:
                datos["peso"] = float(peso.replace(",", ".")) if peso else None
            except ValueError:
                datos["peso"] = peso
            on_submit(**datos)

        self.formulario = Formulario(
            self.canvas, "Registrar consulta médica", f"Veterinario responsable: {usuario.nombre} ({usuario.nombre_usuario}).",
            (("mascota_id", "Mascota (obligatoria)", False), ("cita_id", "Cita asociada (opcional)", False),
             ("fecha", "Fecha de atención", False), ("hora", "Hora de atención", False),
             ("peso", "Peso en kg (opcional)", False), ("sintomas", "Síntomas (obligatorios)", False),
             ("diagnostico", "Diagnóstico (opcional)", False), ("observaciones", "Observaciones (opcionales)", False)),
            "Finalizar y guardar consulta", enviar, on_cancel=on_cancel,
            opciones={"mascota_id": tuple(etiqueta_mascota(m) for m in mascotas), "cita_id": ("Sin cita",)},
            constructores={"fecha": lambda m, v: CalendarioFecha(m, textvariable=v), "hora": hora,
                           "sintomas": texto, "diagnostico": texto, "observaciones": texto},
        )
        ventana = self.canvas.create_window(0, 0, window=self.formulario, anchor="nw")
        self.formulario.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(ventana, width=e.width))
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-int(e.delta / 120), "units"))
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.valores, self.entradas = self.formulario.valores, self.formulario.entradas
        self.boton, self.error = self.formulario.boton, self.formulario.error
        self.entradas["mascota_id"].bind("<<ComboboxSelected>>", self._cambio_mascota)
        self.entradas["cita_id"].bind("<<ComboboxSelected>>", self._cambio_cita)
        self.actualizar_citas(citas, cita.id if cita is not None else None)
        if cita is not None:
            self._seleccionar_mascota(cita.mascota_id)

    def actualizar_citas(self, citas, seleccion=None):
        self._citas = list(citas)
        self.entradas["cita_id"].configure(values=("Sin cita",) + tuple(
            f"Cita {c.id}: {c.mascota_nombre} — {c.fecha_hora_inicio} ({c.estado})" for c in citas
        ))
        self.entradas["cita_id"].current(next((i for i, c in enumerate(citas, 1) if c.id == seleccion), 0))

    def _seleccionar_mascota(self, mascota_id):
        for indice, mascota in enumerate(self._mascotas):
            if mascota.id == mascota_id:
                self.entradas["mascota_id"].current(indice)
                break

    def _cambio_cita(self, event=None):
        indice = self.entradas["cita_id"].current()
        if indice > 0:
            self._seleccionar_mascota(self._citas[indice - 1].mascota_id)

    def _cambio_mascota(self, event=None):
        indice = self.entradas["mascota_id"].current()
        if indice >= 0:
            seleccion = self.entradas["cita_id"].current()
            cita_id = self._citas[seleccion - 1].id if seleccion > 0 else None
            self.error.set("")
            citas = self._on_citas(self._mascotas[indice].id)
            if self.winfo_exists():
                # Un error conserva los textos, pero descarta las opciones de otra mascota.
                self.actualizar_citas(citas if citas is not None else (), cita_id)

    def mostrar_error(self, mensaje):
        self.formulario.mostrar_error(mensaje)
        self.update_idletasks()
        self.canvas.yview_moveto(1)
