from datetime import date, datetime

from database.conexion import inicializar_db
from modulos import transacciones as tx


def formato(monto):
    return f"₡{monto:,.2f}"


def pedir_monto():
    while True:
        texto = input("Monto: ").strip().replace(",", "")
        try:
            monto = float(texto)
            if monto > 0:
                return monto
        except ValueError:
            pass
        print("Monto inválido. Escribe un número mayor que cero.")


def pedir_fecha(mensaje="Fecha (AAAA-MM-DD, Enter = hoy): "):
    while True:
        texto = input(mensaje).strip()
        if not texto:
            return date.today().isoformat()
        try:
            return datetime.strptime(texto, "%Y-%m-%d").date().isoformat()
        except ValueError:
            print("Formato inválido. Ejemplo: 2026-10-14")


def pedir_mes():
    while True:
        texto = input("Mes (AAAA-MM, Enter = mes actual): ").strip()
        if not texto:
            hoy = date.today()
            return hoy.year, hoy.month
        try:
            valor = datetime.strptime(texto, "%Y-%m")
            return valor.year, valor.month
        except ValueError:
            print("Formato inválido. Ejemplo: 2026-10")


def mostrar_movimientos(filas):
    if not filas:
        print("No hay movimientos.")
        return
    print(f"{'ID':<5}{'Fecha':<12}{'Tipo':<9}{'Categoría':<18}{'Monto':>16}  Descripción")
    for f in filas:
        print(
            f"{f['id_transaccion']:<5}{f['fecha']:<12}{f['tipo']:<9}"
            f"{f['categoria']:<18}{formato(f['monto']):>16}  {f['descripcion'] or ''}"
        )


def mostrar_resumen(resumen):
    ingresos, egresos, balance = resumen
    print(f"Ingresos: {formato(ingresos)}")
    print(f"Egresos:  {formato(egresos)}")
    print(f"Balance:  {formato(balance)}")


def registrar(tipo):
    categorias = tx.listar_categorias(tipo)
    validos = {c["id_categoria"] for c in categorias}
    print(f"\nCategorías de {tipo}:")
    for c in categorias:
        print(f"  {c['id_categoria']}. {c['nombre']}")
    while True:
        try:
            id_categoria = int(input("Número de categoría: "))
            if id_categoria in validos:
                break
        except ValueError:
            pass
        print("Categoría inválida.")
    monto = pedir_monto()
    descripcion = input("Descripción (opcional): ").strip() or None
    fecha = pedir_fecha()
    id_nuevo = tx.registrar_transaccion(id_categoria, monto, descripcion, fecha)
    print(f"Movimiento #{id_nuevo} guardado.")


def ver_dia():
    fecha = pedir_fecha("Día (AAAA-MM-DD, Enter = hoy): ")
    print(f"\nMovimientos del {fecha}")
    mostrar_movimientos(tx.listar_por_dia(fecha))
    print()
    mostrar_resumen(tx.resumen_diario(fecha))


def ver_mes():
    anio, mes = pedir_mes()
    print(f"\nMovimientos de {anio:04d}-{mes:02d}")
    mostrar_movimientos(tx.listar_por_mes(anio, mes))
    print()
    mostrar_resumen(tx.resumen_mensual(anio, mes))
    gastos = tx.gastos_por_categoria_mes(anio, mes)
    if gastos:
        print("\nEgresos por categoría:")
        for g in gastos:
            print(f"  {g['categoria']:<18}{formato(g['total']):>16}")


def eliminar():
    mostrar_movimientos(tx.listar_transacciones(limite=10))
    try:
        id_transaccion = int(input("\nID del movimiento a eliminar: "))
    except ValueError:
        print("ID inválido.")
        return
    if input("¿Seguro? (s/n): ").strip().lower() != "s":
        print("Cancelado.")
        return
    if tx.eliminar_transaccion(id_transaccion):
        print("Movimiento eliminado.")
    else:
        print("No existe un movimiento con ese ID.")


def menu():
    inicializar_db()
    opciones = {
        "1": ("Registrar ingreso", lambda: registrar("ingreso")),
        "2": ("Registrar egreso", lambda: registrar("egreso")),
        "3": ("Ver movimientos de un día", ver_dia),
        "4": ("Ver movimientos de un mes", ver_mes),
        "5": ("Eliminar un movimiento", eliminar),
        "6": ("Balance general", lambda: mostrar_resumen(tx.calcular_balance())),
    }
    while True:
        print("\n=== Gestión de ingresos y egresos ===")
        for clave, (texto, _) in opciones.items():
            print(f"{clave}. {texto}")
        print("0. Salir")
        eleccion = input("Elige una opción: ").strip()
        if eleccion == "0":
            print("¡Hasta luego!")
            break
        if eleccion in opciones:
            opciones[eleccion][1]()
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    menu()
