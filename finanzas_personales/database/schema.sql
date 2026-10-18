-- Esquema SQLite de finanzas_personales

-- 1. Categorías (alimentación, transporte, ahorro, etc.)
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    tipo         TEXT NOT NULL CHECK (tipo IN ('ingreso', 'egreso')),
    UNIQUE (nombre, tipo)
);

-- 2. Transacciones (módulo 1)
CREATE TABLE IF NOT EXISTS transacciones (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_categoria   INTEGER NOT NULL REFERENCES categorias(id_categoria),
    monto          REAL NOT NULL CHECK (monto > 0),
    descripcion    TEXT,
    fecha          TEXT NOT NULL DEFAULT (date('now', 'localtime'))
);

-- 3. Metas (módulo 2)
CREATE TABLE IF NOT EXISTS metas (
    id_meta        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT NOT NULL,
    monto_objetivo REAL NOT NULL CHECK (monto_objetivo > 0),
    fecha_limite   TEXT NOT NULL,
    plazo          TEXT NOT NULL CHECK (plazo IN ('corto', 'largo')),
    estado         TEXT NOT NULL DEFAULT 'en_progreso'
                   CHECK (estado IN ('en_progreso', 'cumplida', 'cancelada')),
    fecha_creacion TEXT NOT NULL DEFAULT (date('now', 'localtime'))
);

-- 4. Aportes a metas (registro de cumplimiento)
CREATE TABLE IF NOT EXISTS aportes_meta (
    id_aporte INTEGER PRIMARY KEY AUTOINCREMENT,
    id_meta   INTEGER NOT NULL REFERENCES metas(id_meta) ON DELETE CASCADE,
    monto     REAL NOT NULL CHECK (monto > 0),
    fecha     TEXT NOT NULL DEFAULT (date('now', 'localtime'))
);

-- 5. Categorías iniciales (no se duplican si se ejecuta de nuevo)
INSERT OR IGNORE INTO categorias (nombre, tipo) VALUES
    ('Salario', 'ingreso'),
    ('Otros ingresos', 'ingreso'),
    ('Alimentación', 'egreso'),
    ('Transporte', 'egreso'),
    ('Vivienda', 'egreso'),
    ('Salud', 'egreso'),
    ('Entretenimiento', 'egreso'),
    ('Ahorro', 'egreso'),
    ('Otros gastos', 'egreso');
