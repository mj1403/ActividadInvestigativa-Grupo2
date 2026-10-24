from datetime import date, datetime, timedelta
from html import escape

from modulos import metas as modulo_metas
from modulos import transacciones as modulo_transacciones
from servicios.correo import enviar_correo

SIMBOLO_MONEDA = "₡"
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _a_fecha(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(valor, "%Y-%m-%d").date()


def formato_monto(valor):
    return f"{SIMBOLO_MONEDA}{float(valor):,.2f}"


def obtener_transacciones(desde=None, hasta=None):
    todas = [dict(fila) for fila in modulo_transacciones.listar_transacciones()]
    if desde is not None and hasta is not None:
        return filtrar_periodo(todas, desde, hasta)
    return todas


def filtrar_periodo(transacciones, desde, hasta):
    desde, hasta = _a_fecha(desde), _a_fecha(hasta)
    return [t for t in transacciones if desde <= _a_fecha(t["fecha"]) <= hasta]


def balance_periodo(transacciones):
    ingresos = sum(float(t["monto"]) for t in transacciones if t["tipo"] == "ingreso")
    egresos = sum(float(t["monto"]) for t in transacciones if t["tipo"] == "egreso")
    return {"ingresos": ingresos, "egresos": egresos, "balance": ingresos - egresos}


def gasto_por_categoria(transacciones):
    totales = {}
    for t in transacciones:
        if t["tipo"] == "egreso":
            categoria = t["categoria"]
            totales[categoria] = totales.get(categoria, 0) + float(t["monto"])

    total_egresos = sum(totales.values())
    resultado = [
        {
            "categoria": categoria,
            "total": total,
            "porcentaje": round(total / total_egresos * 100, 1) if total_egresos else 0.0,
        }
        for categoria, total in totales.items()
    ]
    return sorted(resultado, key=lambda fila: fila["total"], reverse=True)


def detectar_habitos(transacciones, dias=None):
    egresos = [t for t in transacciones if t["tipo"] == "egreso"]
    if not egresos:
        return ["No hay gastos registrados en este periodo."]

    balance = balance_periodo(transacciones)
    gastos = gasto_por_categoria(transacciones)
    habitos = []

    # 1. Categoría donde más se gasta
    principal = gastos[0]
    habitos.append(
        f"Tu categoría con más gasto fue {principal['categoria']}: "
        f"{formato_monto(principal['total'])} ({principal['porcentaje']}% de tus gastos)."
    )

    # 2. Promedio diario
    if dias is None:
        fechas = [_a_fecha(t["fecha"]) for t in egresos]
        dias = (max(fechas) - min(fechas)).days + 1
    habitos.append(f"Gastaste en promedio {formato_monto(balance['egresos'] / dias)} por día.")

    # 3. Día de la semana en que más se gasta
    por_dia = {}
    for t in egresos:
        nombre_dia = DIAS_SEMANA[_a_fecha(t["fecha"]).weekday()]
        por_dia[nombre_dia] = por_dia.get(nombre_dia, 0) + float(t["monto"])
    dia_fuerte = max(por_dia, key=por_dia.get)
    habitos.append(f"El día en que más gastas es el {dia_fuerte}.")

    # 4. Cuánto de lo que entra se gasta
    if balance["ingresos"] > 0:
        porcentaje = balance["egresos"] / balance["ingresos"] * 100
        habitos.append(f"Gastaste el {porcentaje:.1f}% de tus ingresos.")
    if balance["egresos"] > balance["ingresos"]:
        habitos.append("Atención: tus gastos superan tus ingresos en este periodo.")

    return habitos


def construir_reporte_html(titulo, balance, gastos, habitos, metas, cumplimiento):
    color_balance = "#2e7d32" if balance["balance"] >= 0 else "#c62828"
    celda = "padding:6px 10px;border-bottom:1px solid #e0e0e0;"

    filas_gastos = "".join(
        f"<tr><td style='{celda}'>{escape(g['categoria'])}</td>"
        f"<td style='{celda}text-align:right'>{formato_monto(g['total'])}</td>"
        f"<td style='{celda}text-align:right'>{g['porcentaje']}%</td></tr>"
        for g in gastos
    ) or f"<tr><td colspan='3' style='{celda}'>Sin gastos en este periodo.</td></tr>"

    items_habitos = "".join(f"<li style='margin-bottom:4px'>{escape(h)}</li>" for h in habitos)

    bloques_metas = "".join(
        f"<p style='margin:12px 0 4px'>{escape(m['nombre'])} — <b>{m['porcentaje']}%</b></p>"
        f"<div style='background:#e0e0e0;border-radius:4px;height:10px'>"
        f"<div style='background:#1565c0;border-radius:4px;height:10px;"
        f"width:{m['porcentaje']}%'></div></div>"
        for m in metas
    ) or "<p>No hay metas registradas.</p>"

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;color:#222;max-width:560px;margin:auto;padding:16px">
  <h2 style="color:#1565c0;margin-bottom:4px">{escape(titulo)}</h2>

  <h3>Balance</h3>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="{celda}">Ingresos</td>
        <td style="{celda}text-align:right">{formato_monto(balance['ingresos'])}</td></tr>
    <tr><td style="{celda}">Egresos</td>
        <td style="{celda}text-align:right">{formato_monto(balance['egresos'])}</td></tr>
    <tr><td style="{celda}"><b>Balance</b></td>
        <td style="{celda}text-align:right;color:{color_balance}"><b>{formato_monto(balance['balance'])}</b></td></tr>
  </table>

  <h3>Gastos por categoría</h3>
  <table style="width:100%;border-collapse:collapse">{filas_gastos}</table>

  <h3>Tus hábitos de gasto</h3>
  <ul style="padding-left:20px">{items_habitos}</ul>

  <h3>Progreso de tus metas (promedio: {cumplimiento['porcentaje_promedio']}%)</h3>
  <p style="margin:0;color:#555">Cumplidas: {cumplimiento['cumplidas']} · En progreso: {cumplimiento['en_progreso']}</p>
  {bloques_metas}
</body>
</html>"""


def generar_reporte(periodo="semanal"):
    hoy = date.today()

    if periodo == "semanal":
        desde = hoy - timedelta(days=6)
        transacciones = obtener_transacciones(desde, hoy)
        titulo = f"Reporte semanal ({desde:%d/%m/%Y} - {hoy:%d/%m/%Y})"
        dias = 7
    elif periodo == "inmediato":
        transacciones = obtener_transacciones()
        titulo = f"Reporte al {hoy:%d/%m/%Y}"
        dias = None
    else:
        raise ValueError('periodo debe ser "semanal" o "inmediato"')

    balance = balance_periodo(transacciones)
    gastos = gasto_por_categoria(transacciones)
    habitos = detectar_habitos(transacciones, dias)
    metas = [m for m in modulo_metas.listar_metas() if m["estado"] != "cancelada"]
    cumplimiento = modulo_metas.resumen_cumplimiento()
    html = construir_reporte_html(titulo, balance, gastos, habitos, metas, cumplimiento)
    return titulo, html


def enviar_reporte(destinatario, periodo="semanal"):
    asunto, html = generar_reporte(periodo)
    enviar_correo(destinatario, asunto, html)