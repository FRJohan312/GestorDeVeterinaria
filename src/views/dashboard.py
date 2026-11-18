"""Panel principal con secciones pendientes y opciones según los permisos."""

from tkinter import ttk


SECCIONES = (
    ("Propietarios", (("gestionar_propietarios", "Gestión"), ("consultar_propietarios", "Consulta"))),
    ("Mascotas", (("gestionar_mascotas", "Gestión"), ("consultar_mascotas", "Consulta"))),
    ("Citas", (("gestionar_citas", "Gestión"), ("consultar_citas", "Consulta"))),
    ("Consultas", (("registrar_consultas", "Registro"), ("consultar_consultas", "Consulta"))),
    ("Historial médico", (("consultar_historial", "Consulta"),)),
    ("Usuarios", (("gestionar_usuarios", "Gestión"),)),
)


class Dashboard(ttk.Frame):
    def __init__(self, master, usuario, permisos, on_pruebas, on_logout, on_usuarios=None,
                 on_propietarios=None, on_mascotas=None, on_citas=None, on_consultas=None):
        super().__init__(master, padding=30)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Gestor De Veterinaria", font=("Arial", 20, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )
        ttk.Label(self, text=f"Usuario: {usuario.nombre}\nRol: {usuario.rol}").grid(
            row=1, column=0, sticky="w", pady=(0, 14)
        )
        self.secciones = {}
        fila = 2
        for titulo, acciones in SECCIONES:
            for permiso, accion in acciones:
                if permiso in permisos:
                    if permiso == "gestionar_usuarios" and on_usuarios is not None:
                        boton = ttk.Button(self, text="Usuarios", command=on_usuarios)
                    elif titulo == "Propietarios" and on_propietarios is not None:
                        boton = ttk.Button(self, text="Propietarios", command=on_propietarios)
                    elif titulo == "Mascotas" and on_mascotas is not None:
                        boton = ttk.Button(self, text="Mascotas", command=on_mascotas)
                    elif titulo == "Citas" and on_citas is not None:
                        boton = ttk.Button(self, text="Citas", command=on_citas)
                    elif titulo == "Consultas" and on_consultas is not None:
                        boton = ttk.Button(self, text="Consultas", command=on_consultas)
                    else:
                        boton = ttk.Button(self, text=f"{titulo} — {accion} pendiente", state="disabled")
                    boton.grid(row=fila, column=0, sticky="ew", pady=4)
                    self.secciones[titulo] = boton
                    fila += 1
                    break
        self.boton_pruebas = None
        if "usar_pruebas" in permisos:
            self.boton_pruebas = ttk.Button(self, text="Pruebas del prototipo", command=on_pruebas)
            self.boton_pruebas.grid(row=fila, column=0, sticky="ew", pady=(16, 4))
            fila += 1
        self.boton_logout = ttk.Button(self, text="Cerrar sesión", command=on_logout)
        self.boton_logout.grid(row=fila, column=0, sticky="ew", pady=(16, 0))
