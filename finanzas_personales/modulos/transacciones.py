from database.conexion import obtener_conexion

CONSULTA_BASE = (
    "SELECT t.id_transaccion, t.fecha, c.nombre AS categoria, c.tipo, "
    "t.monto, t.descripcion "
    "FROM transacciones t "
    "JOIN categorias c ON c.id_categoria = t.id_categoria "
)

SUMAS = (
    "SELECT "
    "COALESCE(SUM(CASE WHEN c.tipo = 'ingreso' THEN t.monto END), 0) AS ingresos, "
    "COALESCE(SUM(CASE WHEN c.tipo = 'egreso' THEN t.monto END), 0) AS egresos "
    "FROM transacciones t "
    "JOIN categorias c ON c.id_categoria = t.id_categoria "
)


def listar_categorias(tipo=None):
    """Devuelve las categorías. Si se indica tipo ('ingreso' o 'egreso'), filtra por él."""
    consulta = "SELECT id_categoria, nombre, tipo FROM categorias"
    parametros = ()
    if tipo:
        consulta += " WHERE tipo = ?"
        parametros = (tipo,)
    consulta += " ORDER BY nombre"
    with obtener_conexion() as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def registrar_transaccion(id_categoria, monto, descripcion=None, fecha=None):
    """Guarda una transacción. Si no se da fecha, se usa la de hoy (AAAA-MM-DD)."""
    if monto <= 0:
        raise ValueError("El monto debe ser mayor que cero.")
    with obtener_conexion() as conexion:
        if fecha:
            cursor = conexion.execute(
                "INSERT INTO transacciones (id_categoria, monto, descripcion, fecha) "
                "VALUES (?, ?, ?, ?)",
                (id_categoria, monto, descripcion, fecha),
            )
        else:
            cursor = conexion.execute(
                "INSERT INTO transacciones (id_categoria, monto, descripcion) "
                "VALUES (?, ?, ?)",
                (id_categoria, monto, descripcion),
            )
        return cursor.lastrowid


def eliminar_transaccion(id_transaccion):
    """Elimina una transacción. Devuelve True si existía."""
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "DELETE FROM transacciones WHERE id_transaccion = ?",
            (id_transaccion,),
        )
        return cursor.rowcount > 0


def listar_transacciones(limite=None):
    """Todas las transacciones, de la más reciente a la más antigua."""
    consulta = CONSULTA_BASE + "ORDER BY t.fecha DESC, t.id_transaccion DESC"
    parametros = ()
    if limite:
        consulta += " LIMIT ?"
        parametros = (limite,)
    with obtener_conexion() as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def listar_por_dia(fecha):
    """Transacciones de un día. La fecha va en formato 'AAAA-MM-DD'."""
    with obtener_conexion() as conexion:
        return conexion.execute(
            CONSULTA_BASE + "WHERE t.fecha = ? ORDER BY t.id_transaccion",
            (fecha,),
        ).fetchall()


def listar_por_mes(anio, mes):
    """Transacciones de un mes (por ejemplo anio=2026, mes=10)."""
    periodo = f"{anio:04d}-{mes:02d}"
    with obtener_conexion() as conexion:
        return conexion.execute(
            CONSULTA_BASE
            + "WHERE strftime('%Y-%m', t.fecha) = ? ORDER BY t.fecha, t.id_transaccion",
            (periodo,),
        ).fetchall()


def calcular_balance():
    """Devuelve (ingresos, egresos, balance) de todo el historial."""
    with obtener_conexion() as conexion:
        fila = conexion.execute(SUMAS).fetchone()
    return fila["ingresos"], fila["egresos"], fila["ingresos"] - fila["egresos"]


def resumen_diario(fecha):
    """Devuelve (ingresos, egresos, balance) de un día."""
    with obtener_conexion() as conexion:
        fila = conexion.execute(SUMAS + "WHERE t.fecha = ?", (fecha,)).fetchone()
    return fila["ingresos"], fila["egresos"], fila["ingresos"] - fila["egresos"]


def resumen_mensual(anio, mes):
    """Devuelve (ingresos, egresos, balance) de un mes."""
    periodo = f"{anio:04d}-{mes:02d}"
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            SUMAS + "WHERE strftime('%Y-%m', t.fecha) = ?", (periodo,)
        ).fetchone()
    return fila["ingresos"], fila["egresos"], fila["ingresos"] - fila["egresos"]


def gastos_por_categoria_mes(anio, mes):
    """Total de egresos por categoría en un mes, de mayor a menor."""
    periodo = f"{anio:04d}-{mes:02d}"
    with obtener_conexion() as conexion:
        return conexion.execute(
            "SELECT c.nombre AS categoria, SUM(t.monto) AS total "
            "FROM transacciones t "
            "JOIN categorias c ON c.id_categoria = t.id_categoria "
            "WHERE c.tipo = 'egreso' AND strftime('%Y-%m', t.fecha) = ? "
            "GROUP BY c.nombre ORDER BY total DESC",
            (periodo,),
        ).fetchall()
