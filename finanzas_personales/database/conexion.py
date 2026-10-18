import sqlite3
from pathlib import Path

CARPETA_DATABASE = Path(__file__).resolve().parent
RAIZ = CARPETA_DATABASE.parent
RUTA_DB = RAIZ / "datos" / "finanzas.db"
RUTA_SCHEMA = CARPETA_DATABASE / "schema.sql"


def obtener_conexion():
    """Abre la conexión a la base de datos SQLite."""
    RUTA_DB.parent.mkdir(exist_ok=True)
    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_db():
    """Crea las tablas y las categorías iniciales si todavía no existen."""
    esquema = RUTA_SCHEMA.read_text(encoding="utf-8")
    with obtener_conexion() as conexion:
        conexion.executescript(esquema)
