"""Esquema inicial, restricciones e índices; sin borrados ni reemplazos."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pruebas (
    id INTEGER PRIMARY KEY AUTOINCREMENT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    nombre_usuario TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (length(trim(nombre_usuario)) > 0),
    contrasena_hash TEXT NOT NULL CHECK (length(trim(contrasena_hash)) > 0),
    rol TEXT NOT NULL CHECK (rol IN ('ADMINISTRADOR', 'VETERINARIO')),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS propietarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    documento TEXT NOT NULL UNIQUE CHECK (length(trim(documento)) > 0),
    telefono TEXT,
    correo TEXT,
    direccion TEXT
);

CREATE TABLE IF NOT EXISTS mascotas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    especie TEXT NOT NULL CHECK (length(trim(especie)) > 0),
    raza TEXT,
    sexo TEXT NOT NULL DEFAULT 'DESCONOCIDO'
        CHECK (sexo IN ('MACHO', 'HEMBRA', 'DESCONOCIDO')),
    fecha_nacimiento TEXT CHECK (fecha_nacimiento IS NULL OR (
        length(fecha_nacimiento) = 10
        AND date(fecha_nacimiento, '+0 days') IS NOT NULL
        AND date(fecha_nacimiento, '+0 days') = fecha_nacimiento
    )),
    propietario_id INTEGER NOT NULL
        REFERENCES propietarios(id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id INTEGER NOT NULL
        REFERENCES mascotas(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    veterinario_id INTEGER NOT NULL
        REFERENCES usuarios(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    fecha_hora_inicio TEXT NOT NULL CHECK (
        length(fecha_hora_inicio) = 19
        AND strftime('%Y-%m-%d %H:%M:%S', fecha_hora_inicio, '+0 days') IS NOT NULL
        AND strftime('%Y-%m-%d %H:%M:%S', fecha_hora_inicio, '+0 days') = fecha_hora_inicio
    ),
    duracion_minutos INTEGER NOT NULL CHECK (
        typeof(duracion_minutos) = 'integer' AND duracion_minutos > 0
    ),
    motivo TEXT NOT NULL CHECK (length(trim(motivo)) > 0),
    estado TEXT NOT NULL DEFAULT 'PROGRAMADA'
        CHECK (estado IN ('PROGRAMADA', 'CONFIRMADA', 'COMPLETADA', 'CANCELADA', 'NO_ASISTIO'))
);

CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id INTEGER NOT NULL
        REFERENCES mascotas(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    veterinario_id INTEGER NOT NULL
        REFERENCES usuarios(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    cita_id INTEGER UNIQUE
        REFERENCES citas(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    fecha TEXT NOT NULL CHECK (
        length(fecha) = 19
        AND strftime('%Y-%m-%d %H:%M:%S', fecha, '+0 days') IS NOT NULL
        AND strftime('%Y-%m-%d %H:%M:%S', fecha, '+0 days') = fecha
    ),
    peso REAL CHECK (peso IS NULL OR (typeof(peso) IN ('real', 'integer') AND peso > 0)),
    sintomas TEXT NOT NULL CHECK (length(trim(sintomas)) > 0),
    diagnostico TEXT,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS tratamientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consulta_id INTEGER NOT NULL
        REFERENCES consultas(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    descripcion TEXT NOT NULL CHECK (length(trim(descripcion)) > 0),
    medicamento TEXT,
    dosis TEXT,
    duracion TEXT
);

CREATE INDEX IF NOT EXISTS idx_mascotas_propietario ON mascotas(propietario_id);
CREATE INDEX IF NOT EXISTS idx_citas_mascota ON citas(mascota_id);
CREATE INDEX IF NOT EXISTS idx_citas_agenda ON citas(veterinario_id, fecha_hora_inicio);
CREATE INDEX IF NOT EXISTS idx_consultas_historial ON consultas(mascota_id, fecha);
CREATE INDEX IF NOT EXISTS idx_consultas_veterinario ON consultas(veterinario_id);
CREATE INDEX IF NOT EXISTS idx_tratamientos_consulta ON tratamientos(consulta_id);

CREATE TRIGGER IF NOT EXISTS citas_validar_veterinario_insert
BEFORE INSERT ON citas
WHEN NOT EXISTS (SELECT 1 FROM usuarios WHERE id = NEW.veterinario_id AND rol = 'VETERINARIO')
BEGIN
    SELECT RAISE(ABORT, 'La cita requiere un usuario con rol VETERINARIO');
END;

CREATE TRIGGER IF NOT EXISTS citas_validar_veterinario_update
BEFORE UPDATE OF veterinario_id ON citas
WHEN NOT EXISTS (SELECT 1 FROM usuarios WHERE id = NEW.veterinario_id AND rol = 'VETERINARIO')
BEGIN
    SELECT RAISE(ABORT, 'La cita requiere un usuario con rol VETERINARIO');
END;

CREATE TRIGGER IF NOT EXISTS consultas_validar_veterinario_insert
BEFORE INSERT ON consultas
WHEN NOT EXISTS (SELECT 1 FROM usuarios WHERE id = NEW.veterinario_id AND rol = 'VETERINARIO')
BEGIN
    SELECT RAISE(ABORT, 'La consulta requiere un usuario con rol VETERINARIO');
END;

CREATE TRIGGER IF NOT EXISTS consultas_validar_veterinario_update
BEFORE UPDATE OF veterinario_id ON consultas
WHEN NOT EXISTS (SELECT 1 FROM usuarios WHERE id = NEW.veterinario_id AND rol = 'VETERINARIO')
BEGIN
    SELECT RAISE(ABORT, 'La consulta requiere un usuario con rol VETERINARIO');
END;

CREATE TRIGGER IF NOT EXISTS usuarios_preservar_rol_veterinario
BEFORE UPDATE OF rol ON usuarios
WHEN NEW.rol != 'VETERINARIO' AND (
    EXISTS (SELECT 1 FROM citas WHERE veterinario_id = OLD.id)
    OR EXISTS (SELECT 1 FROM consultas WHERE veterinario_id = OLD.id)
)
BEGIN
    SELECT RAISE(ABORT, 'El usuario tiene citas o consultas como veterinario');
END;

CREATE TRIGGER IF NOT EXISTS consultas_validar_cita_insert
BEFORE INSERT ON consultas
WHEN NEW.cita_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM citas WHERE id = NEW.cita_id
    AND mascota_id = NEW.mascota_id AND veterinario_id = NEW.veterinario_id
)
BEGIN
    SELECT RAISE(ABORT, 'La consulta y la cita deben compartir mascota y veterinario');
END;

CREATE TRIGGER IF NOT EXISTS consultas_validar_cita_update
BEFORE UPDATE OF cita_id, mascota_id, veterinario_id ON consultas
WHEN NEW.cita_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM citas WHERE id = NEW.cita_id
    AND mascota_id = NEW.mascota_id AND veterinario_id = NEW.veterinario_id
)
BEGIN
    SELECT RAISE(ABORT, 'La consulta y la cita deben compartir mascota y veterinario');
END;

CREATE TRIGGER IF NOT EXISTS citas_preservar_consulta
BEFORE UPDATE OF mascota_id, veterinario_id ON citas
WHEN EXISTS (
    SELECT 1 FROM consultas WHERE cita_id = OLD.id
    AND (mascota_id != NEW.mascota_id OR veterinario_id != NEW.veterinario_id)
)
BEGIN
    SELECT RAISE(ABORT, 'La cita tiene una consulta asociada con otra mascota o veterinario');
END;

CREATE TRIGGER IF NOT EXISTS consultas_conservar_historial
BEFORE DELETE ON consultas
BEGIN
    SELECT RAISE(ABORT, 'No se permite eliminar consultas del historial medico');
END;
"""
