from datetime import date, datetime

from database.conexion import obtener_conexion

PLAZOS = ("corto", "largo")
ESTADOS = ("en_progreso", "cumplida", "cancelada")

# Meta con su monto acumulado, porcentaje y restante calculados en SQL.
CONSULTA_PROGRESO = (
    "SELECT m.id_meta, m.nombre, m.monto_objetivo, m.fecha_limite, m.plazo, "
    "m.estado, m.fecha_creacion, "
    "COALESCE(SUM(a.monto), 0) AS monto_acumulado "
    "FROM metas m "
    "LEFT JOIN aportes_meta a ON a.id_meta = m.id_meta "
)
AGRUPAR = "GROUP BY m.id_meta "


def _validar_fecha(texto):
    """Verifica que la fecha tenga formato AAAA-MM-DD y la devuelve como texto."""
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD.")


def _validar_plazo(plazo):
    if plazo not in PLAZOS:
        raise ValueError("El plazo debe ser 'corto' o 'largo'.")


def _validar_monto(monto, campo="El monto"):
    if monto is None or monto <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")


def _con_progreso(fila):
    """Convierte una fila de CONSULTA_PROGRESO en un diccionario con el progreso."""
    meta = dict(fila)
    objetivo = meta["monto_objetivo"]
    acumulado = meta["monto_acumulado"]
    meta["porcentaje"] = min(round(acumulado / objetivo * 100, 1), 100.0)
    meta["restante"] = max(objetivo - acumulado, 0)
    meta["dias_restantes"] = (
        date.fromisoformat(meta["fecha_limite"]) - date.today()
    ).days
    return meta


def _actualizar_estado(conexion, id_meta):
    """Marca la meta como 'cumplida' o 'en_progreso' según lo aportado.
    Una meta cancelada no cambia de estado."""
    conexion.execute(
        "UPDATE metas SET estado = CASE "
        "WHEN (SELECT COALESCE(SUM(monto), 0) FROM aportes_meta "
        "      WHERE id_meta = metas.id_meta) >= monto_objetivo "
        "THEN 'cumplida' ELSE 'en_progreso' END "
        "WHERE id_meta = ? AND estado <> 'cancelada'",
        (id_meta,),
    )


# ---------- Crear, editar y eliminar metas ----------

def crear_meta(nombre, monto_objetivo, fecha_limite, plazo):
    """Crea una meta. fecha_limite en 'AAAA-MM-DD'; plazo: 'corto' o 'largo'."""
    if not nombre or not nombre.strip():
        raise ValueError("La meta necesita un nombre.")
    _validar_monto(monto_objetivo, "El monto objetivo")
    fecha_limite = _validar_fecha(fecha_limite)
    _validar_plazo(plazo)
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "INSERT INTO metas (nombre, monto_objetivo, fecha_limite, plazo) "
            "VALUES (?, ?, ?, ?)",
            (nombre.strip(), monto_objetivo, fecha_limite, plazo),
        )
        return cursor.lastrowid


def editar_meta(id_meta, nombre=None, monto_objetivo=None, fecha_limite=None, plazo=None):
    """Edita solo los campos indicados. Devuelve True si la meta existía."""
    cambios, parametros = [], []
    if nombre is not None:
        if not nombre.strip():
            raise ValueError("El nombre no puede quedar vacío.")
        cambios.append("nombre = ?")
        parametros.append(nombre.strip())
    if monto_objetivo is not None:
        _validar_monto(monto_objetivo, "El monto objetivo")
        cambios.append("monto_objetivo = ?")
        parametros.append(monto_objetivo)
    if fecha_limite is not None:
        cambios.append("fecha_limite = ?")
        parametros.append(_validar_fecha(fecha_limite))
    if plazo is not None:
        _validar_plazo(plazo)
        cambios.append("plazo = ?")
        parametros.append(plazo)
    if not cambios:
        raise ValueError("No se indicó ningún campo para editar.")

    parametros.append(id_meta)
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            f"UPDATE metas SET {', '.join(cambios)} WHERE id_meta = ?", parametros
        )
        if cursor.rowcount == 0:
            return False
        # Si cambió el objetivo, la meta puede pasar a cumplida o volver a en progreso.
        _actualizar_estado(conexion, id_meta)
        return True


def eliminar_meta(id_meta):
    """Elimina una meta y sus aportes (ON DELETE CASCADE). True si existía."""
    with obtener_conexion() as conexion:
        cursor = conexion.execute("DELETE FROM metas WHERE id_meta = ?", (id_meta,))
        return cursor.rowcount > 0


def cancelar_meta(id_meta):
    """Marca la meta como cancelada sin borrar su historial. True si existía."""
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "UPDATE metas SET estado = 'cancelada' WHERE id_meta = ?", (id_meta,)
        )
        return cursor.rowcount > 0


def reactivar_meta(id_meta):
    """Quita el estado 'cancelada' y recalcula si está en progreso o cumplida."""
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "UPDATE metas SET estado = 'en_progreso' "
            "WHERE id_meta = ? AND estado = 'cancelada'",
            (id_meta,),
        )
        if cursor.rowcount == 0:
            return False
        _actualizar_estado(conexion, id_meta)
        return True


# ---------- Consultas ----------

def obtener_meta(id_meta):
    """Devuelve la meta con su progreso (dict) o None si no existe."""
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            CONSULTA_PROGRESO + "WHERE m.id_meta = ? " + AGRUPAR, (id_meta,)
        ).fetchone()
    return _con_progreso(fila) if fila else None


def listar_metas(plazo=None, estado=None):
    """Lista las metas con su progreso. Se puede filtrar por plazo y/o estado."""
    condiciones, parametros = [], []
    if plazo:
        _validar_plazo(plazo)
        condiciones.append("m.plazo = ?")
        parametros.append(plazo)
    if estado:
        if estado not in ESTADOS:
            raise ValueError("Estado inválido.")
        condiciones.append("m.estado = ?")
        parametros.append(estado)
    donde = ("WHERE " + " AND ".join(condiciones) + " ") if condiciones else ""
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            CONSULTA_PROGRESO + donde + AGRUPAR + "ORDER BY m.fecha_limite, m.id_meta",
            parametros,
        ).fetchall()
    return [_con_progreso(f) for f in filas]


# ---------- Registro de cumplimiento (aportes) ----------

def registrar_aporte(id_meta, monto, fecha=None):
    """Registra un aporte a una meta. Si con él se alcanza el objetivo,
    la meta pasa a 'cumplida'. Devuelve el id del aporte."""
    _validar_monto(monto)
    fecha = _validar_fecha(fecha) if fecha else date.today().isoformat()
    with obtener_conexion() as conexion:
        meta = conexion.execute(
            "SELECT estado FROM metas WHERE id_meta = ?", (id_meta,)
        ).fetchone()
        if meta is None:
            raise ValueError("La meta no existe.")
        if meta["estado"] == "cancelada":
            raise ValueError("No se pueden registrar aportes en una meta cancelada.")
        cursor = conexion.execute(
            "INSERT INTO aportes_meta (id_meta, monto, fecha) VALUES (?, ?, ?)",
            (id_meta, monto, fecha),
        )
        _actualizar_estado(conexion, id_meta)
        return cursor.lastrowid


def eliminar_aporte(id_aporte):
    """Elimina un aporte y recalcula el estado de su meta. True si existía."""
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            "SELECT id_meta FROM aportes_meta WHERE id_aporte = ?", (id_aporte,)
        ).fetchone()
        if fila is None:
            return False
        conexion.execute("DELETE FROM aportes_meta WHERE id_aporte = ?", (id_aporte,))
        _actualizar_estado(conexion, fila["id_meta"])
        return True


def listar_aportes(id_meta):
    """Aportes de una meta, del más reciente al más antiguo."""
    with obtener_conexion() as conexion:
        return conexion.execute(
            "SELECT id_aporte, fecha, monto FROM aportes_meta "
            "WHERE id_meta = ? ORDER BY fecha DESC, id_aporte DESC",
            (id_meta,),
        ).fetchall()


# ---------- Visualización del progreso ----------

def barra_progreso(porcentaje, ancho=20):
    """Barra de texto, por ejemplo: [██████░░░░░░░░░░░░░░] 30.0%"""
    llenos = int(round(ancho * porcentaje / 100))
    return f"[{'█' * llenos}{'░' * (ancho - llenos)}] {porcentaje:.1f}%"


def resumen_cumplimiento():
    """Resumen global de las metas (lo usa el módulo de reportes).
    Devuelve dict: total, cumplidas, en_progreso, canceladas y
    porcentaje_promedio de las metas no canceladas."""
    metas = listar_metas()
    activas = [m for m in metas if m["estado"] != "cancelada"]
    promedio = sum(m["porcentaje"] for m in activas) / len(activas) if activas else 0.0
    return {
        "total": len(metas),
        "cumplidas": sum(m["estado"] == "cumplida" for m in metas),
        "en_progreso": sum(m["estado"] == "en_progreso" for m in metas),
        "canceladas": sum(m["estado"] == "cancelada" for m in metas),
        "porcentaje_promedio": round(promedio, 1),
    }


def graficar_progreso(guardar_en=None):
    """Gráfico de barras horizontales con el % de avance de cada meta activa.
    Si se da guardar_en (ruta .png) guarda la imagen; si no, abre la ventana."""
    import importlib
    matplotlib = importlib.import_module("matplotlib")

    if guardar_en:
        matplotlib.use("Agg")
    # Import dynamically so static analyzers don't require pyplot's source files.
    import importlib
    plt = importlib.import_module("matplotlib.pyplot")

    metas = [m for m in listar_metas() if m["estado"] != "cancelada"]
    if not metas:
        raise ValueError("No hay metas para graficar.")

    nombres = [m["nombre"] for m in metas]
    porcentajes = [m["porcentaje"] for m in metas]
    colores = ["#2e7d32" if m["estado"] == "cumplida" else "#1976d2" for m in metas]

    fig, ax = plt.subplots(figsize=(8, 1 + 0.6 * len(metas)))
    barras = ax.barh(nombres, porcentajes, color=colores)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Progreso (%)")
    ax.set_title("Progreso de metas financieras")
    ax.invert_yaxis()
    for barra, p in zip(barras, porcentajes):
        ax.text(p + 1, barra.get_y() + barra.get_height() / 2, f"{p:.1f}%", va="center")
    fig.tight_layout()
    if guardar_en:
        fig.savefig(guardar_en, dpi=120)
        plt.close(fig)
    else:
        plt.show()