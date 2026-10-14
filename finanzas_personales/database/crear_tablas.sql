-- 1. Crear la base de datos (solo si no existe)
IF DB_ID('finanzas_db') IS NULL
    CREATE DATABASE finanzas_db;
GO

USE finanzas_db;
GO

-- 2. Categorías (alimentación, transporte, ahorro, etc.)
IF OBJECT_ID('dbo.categorias') IS NULL
CREATE TABLE dbo.categorias (
    id_categoria INT IDENTITY(1,1) PRIMARY KEY,
    nombre       NVARCHAR(50) NOT NULL,
    tipo         NVARCHAR(10) NOT NULL
                 CHECK (tipo IN ('ingreso', 'egreso')),
    CONSTRAINT UQ_categorias_nombre_tipo UNIQUE (nombre, tipo)
);
GO

-- 3. Transacciones (módulo 1)
IF OBJECT_ID('dbo.transacciones') IS NULL
CREATE TABLE dbo.transacciones (
    id_transaccion INT IDENTITY(1,1) PRIMARY KEY,
    id_categoria   INT NOT NULL
                   REFERENCES dbo.categorias(id_categoria),
    monto          DECIMAL(12,2) NOT NULL CHECK (monto > 0),
    descripcion    NVARCHAR(200) NULL,
    fecha          DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE)
);
GO

-- 4. Metas (módulo 2)
IF OBJECT_ID('dbo.metas') IS NULL
CREATE TABLE dbo.metas (
    id_meta        INT IDENTITY(1,1) PRIMARY KEY,
    nombre         NVARCHAR(100) NOT NULL,
    monto_objetivo DECIMAL(12,2) NOT NULL CHECK (monto_objetivo > 0),
    fecha_limite   DATE NOT NULL,
    plazo          NVARCHAR(10) NOT NULL
                   CHECK (plazo IN ('corto', 'largo')),
    estado         NVARCHAR(15) NOT NULL DEFAULT 'en_progreso'
                   CHECK (estado IN ('en_progreso', 'cumplida', 'cancelada')),
    fecha_creacion DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE)
);
GO

-- 5. Aportes a metas (registro de cumplimiento)
IF OBJECT_ID('dbo.aportes_meta') IS NULL
CREATE TABLE dbo.aportes_meta (
    id_aporte INT IDENTITY(1,1) PRIMARY KEY,
    id_meta   INT NOT NULL
              REFERENCES dbo.metas(id_meta) ON DELETE CASCADE,
    monto     DECIMAL(12,2) NOT NULL CHECK (monto > 0),
    fecha     DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE)
);
GO

-- 6. Categorías iniciales (no duplica si se ejecuta de nuevo)
INSERT INTO dbo.categorias (nombre, tipo)
SELECT v.nombre, v.tipo
FROM (VALUES
    ('Salario', 'ingreso'), ('Otros ingresos', 'ingreso'),
    ('Alimentación', 'egreso'), ('Transporte', 'egreso'),
    ('Vivienda', 'egreso'), ('Salud', 'egreso'),
    ('Entretenimiento', 'egreso'), ('Ahorro', 'egreso'),
    ('Otros gastos', 'egreso')
) AS v(nombre, tipo)
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.categorias c
    WHERE c.nombre = v.nombre AND c.tipo = v.tipo
);
GO