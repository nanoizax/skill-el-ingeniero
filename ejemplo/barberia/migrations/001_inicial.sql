-- Tablas iniciales. Las horas son texto en UTC con formato AAAA-MM-DDTHH:MM:SS.ffffff (el orden del texto es el
-- orden del tiempo). El dinero son pesos enteros.
CREATE TABLE usuarios (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL CHECK (length(nombre) > 0),
    correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    rol TEXT NOT NULL CHECK (rol IN ('dueno', 'recepcion', 'barbero', 'cliente')),
    contrasena_hash TEXT NOT NULL
);

CREATE TABLE citas (
    id TEXT PRIMARY KEY,
    barbero_id TEXT NOT NULL,
    cliente_id TEXT NOT NULL,
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('confirmada', 'cancelada', 'atendida')),
    CHECK (fin > inicio)
);

CREATE TABLE cobros (
    id TEXT PRIMARY KEY,
    cita_id TEXT NOT NULL UNIQUE REFERENCES citas (id),
    barbero_id TEXT NOT NULL,
    cita_inicio TEXT NOT NULL,
    monto INTEGER NOT NULL CHECK (monto > 0),
    medio TEXT NOT NULL CHECK (medio IN ('efectivo', 'tarjeta', 'transferencia')),
    registrado_en TEXT NOT NULL
);

CREATE INDEX idx_cobros_cita_inicio ON cobros (cita_inicio);
