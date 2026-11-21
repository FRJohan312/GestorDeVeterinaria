"""Permisos de los servicios actuales y de las futuras operaciones."""

PERMISOS_POR_ROL = {
    "ADMINISTRADOR": frozenset({
        "gestionar_propietarios", "consultar_propietarios", "gestionar_mascotas", "consultar_mascotas", "gestionar_citas",
        "consultar_citas", "consultar_consultas", "consultar_tratamientos", "consultar_historial", "gestionar_usuarios", "usar_pruebas",
    }),
    "VETERINARIO": frozenset({
        "consultar_propietarios", "consultar_mascotas", "consultar_citas",
        "registrar_consultas", "consultar_consultas", "consultar_historial",
        "consultar_tratamientos", "registrar_tratamientos",
    }),
}
