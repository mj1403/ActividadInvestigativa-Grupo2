from modulos import metas


def _pedir_monto(texto):
    while True:
        try:
            return float(input(texto).replace(",", "."))
        except ValueError:
            print("Ingresa un número válido.")


def _pedir_id():
    while True:
        try:
            return int(input("ID de la meta: "))
        except ValueError:
            print("Ingresa un número válido.")


def _mostrar_metas(lista):
    if not lista:
        print("\nNo hay metas registradas.")
        return
    for m in lista:
        print(
            f"\n#{m['id_meta']} {m['nombre']} ({m['plazo']} plazo, {m['estado']})\n"
            f"   {metas.barra_progreso(m['porcentaje'])}\n"
            f"   Acumulado: {m['monto_acumulado']:,.2f} de {m['monto_objetivo']:,.2f}"
            f" | Falta: {m['restante']:,.2f}\n"
            f"   Fecha límite: {m['fecha_limite']} ({m['dias_restantes']} días)"
        )


def _crear():
    nombre = input("Nombre de la meta: ")
    monto = _pedir_monto("Monto objetivo: ")
    fecha = input("Fecha límite (AAAA-MM-DD): ")
    plazo = input("Plazo (corto/largo): ").strip().lower()
    id_meta = metas.crear_meta(nombre, monto, fecha, plazo)
    print(f"Meta creada con ID {id_meta}.")


def _editar():
    id_meta = _pedir_id()
    print("Deja en blanco lo que no quieras cambiar.")
    nombre = input("Nuevo nombre: ") or None
    texto_monto = input("Nuevo monto objetivo: ")
    monto = float(texto_monto.replace(",", ".")) if texto_monto else None
    fecha = input("Nueva fecha límite (AAAA-MM-DD): ") or None
    plazo = input("Nuevo plazo (corto/largo): ").strip().lower() or None
    ok = metas.editar_meta(id_meta, nombre, monto, fecha, plazo)
    print("Meta actualizada." if ok else "No existe esa meta.")


def _eliminar():
    id_meta = _pedir_id()
    if input("Se borrará la meta y sus aportes. ¿Seguro? (s/n): ").lower() == "s":
        print("Meta eliminada." if metas.eliminar_meta(id_meta) else "No existe esa meta.")


def _aportar():
    id_meta = _pedir_id()
    monto = _pedir_monto("Monto del aporte: ")
    fecha = input("Fecha (AAAA-MM-DD, Enter = hoy): ") or None
    metas.registrar_aporte(id_meta, monto, fecha)
    meta = metas.obtener_meta(id_meta)
    print(f"Aporte registrado. Progreso: {metas.barra_progreso(meta['porcentaje'])}")
    if meta["estado"] == "cumplida":
        print("¡Meta cumplida!")


def _ver_aportes():
    id_meta = _pedir_id()
    aportes = metas.listar_aportes(id_meta)
    if not aportes:
        print("Sin aportes registrados.")
    for a in aportes:
        print(f"  #{a['id_aporte']}  {a['fecha']}  {a['monto']:,.2f}")


def menu_metas():
    """Submenú del módulo 2. Llamarlo desde el menú principal."""
    opciones = {
        "1": ("Crear meta", _crear),
        "2": ("Ver metas y progreso", lambda: _mostrar_metas(metas.listar_metas())),
        "3": ("Editar meta", _editar),
        "4": ("Eliminar meta", _eliminar),
        "5": ("Registrar aporte", _aportar),
        "6": ("Ver aportes de una meta", _ver_aportes),
        "7": ("Gráfico de progreso", metas.graficar_progreso),
        "0": ("Volver", None),
    }
    while True:
        print("\n--- METAS FINANCIERAS ---")
        for clave, (texto, _) in opciones.items():
            print(f"{clave}. {texto}")
        eleccion = input("Opción: ").strip()
        if eleccion == "0":
            return
        if eleccion not in opciones:
            print("Opción no válida.")
            continue
        try:
            opciones[eleccion][1]()
        except ValueError as error:
            print(f"Error: {error}")