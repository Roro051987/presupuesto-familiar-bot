from agents.parser import parse_message
from adapters.api_client import ApiClient


def format_money(amount):
    return f"${amount:,.0f}".replace(",", ".")


def format_fecha(fecha):
    return str(fecha)[5:10]


def format_movimientos_response(titulo, data, key):
    movimientos = data[key]

    if not movimientos:
        return f"No tienes {titulo.lower()} registrados este mes."

    pagina = data.get("pagina", 1)
    total_paginas = data.get("total_paginas", 1)
    total_registros = data.get("total_registros", len(movimientos))

    encabezado = f"📋 {titulo}"

    if total_paginas > 1:
        encabezado += f" ({pagina}/{total_paginas})"

    lineas = [encabezado, ""]

    for mov in movimientos:
        lineas.append(
            f"#{mov['id']} | {format_fecha(mov['fecha'])} | "
            f"{format_money(mov['monto'])} | {mov['categoria']}"
        )

    lineas.append("")
    lineas.append(f"Registros del mes: {total_registros}")

    return "\n".join(lineas)


def process_message(usuario_id, text):
    result = parse_message(text)
    intent = result.get("intent")

    try:
        if intent == "registrar_gasto":
            response = ApiClient.registrar_gasto(
                usuario_id=usuario_id,
                monto=int(result["monto"]),
                categoria=result["categoria"],
                descripcion=result.get("descripcion") or result["categoria"],
                fecha=result.get("fecha")
            )

            if response.get("duplicate"):
                mov = response["movimiento"]
                return (
                    "⚠️ Parece que ya existe un gasto similar.\n\n"
                    f"Movimiento #{mov['id']}\n"
                    f"Monto: {format_money(mov['monto'])}\n"
                    f"Fecha: {mov['fecha']}\n\n"
                    "Si quieres registrarlo igual, escribe el gasto nuevamente agregando: forzar"
                )

            return (
                f"✅ Registré un gasto de "
                f"{format_money(int(result['monto']))} "
                f"en {response.get('categoria', result['categoria'])}."
            )

        if intent == "registrar_ingreso":
            response = ApiClient.registrar_ingreso(
                usuario_id=usuario_id,
                monto=int(result["monto"]),
                categoria=result["categoria"],
                descripcion=result.get("descripcion") or result["categoria"],
                fecha=result.get("fecha")
            )

            if response.get("duplicate"):
                mov = response["movimiento"]
                return (
                    "⚠️ Parece que ya existe un ingreso similar.\n\n"
                    f"Movimiento #{mov['id']}\n"
                    f"Monto: {format_money(mov['monto'])}\n"
                    f"Fecha: {mov['fecha']}\n\n"
                    "Si quieres registrarlo igual, escribe el ingreso nuevamente agregando: forzar"
                )

            return (
                f"✅ Registré un ingreso de "
                f"{format_money(int(result['monto']))}."
            )

        if intent == "resumen":
            r = ApiClient.resumen(usuario_id)

            return (
                "📊 Resumen del mes\n\n"
                f"Ingresos: {format_money(r['ingresos'])}\n"
                f"Gastos: {format_money(r['gastos'])}\n"
                f"Disponible: {format_money(r['saldo'])}"
            )

        if intent == "consulta_categoria":
            response = ApiClient.total_categoria(
                usuario_id,
                result["categoria"]
            )

            return (
                f"Has gastado "
                f"{format_money(response['total'])} "
                f"en {result['categoria']}."
            )

        if intent == "saldo":
            r = ApiClient.resumen(usuario_id)
            return f"Te queda disponible {format_money(r['saldo'])} este mes."

        if intent == "borrar_ultimo_movimiento":
            response = ApiClient.borrar_ultimo(usuario_id)

            if not response.get("ok"):
                return "No encontré movimientos para borrar."

            mov = response["movimiento"]

            return (
                f"🗑️ Eliminé el último movimiento: "
                f"{mov['tipo']} de {format_money(mov['monto'])}."
            )

        if intent == "eliminar_movimiento":
            movimiento_id = result.get("movimiento_id")

            if not movimiento_id:
                return (
                    "Indícame el número del movimiento.\n\n"
                    "Ejemplo:\n"
                    "• eliminar movimiento 184"
                )

            response = ApiClient.eliminar_movimiento(
                usuario_id,
                movimiento_id
            )

            mov = response["movimiento"]

            return (
                f"🗑️ Eliminé el movimiento #{mov['id']}.\n\n"
                f"{mov['tipo']} | {format_money(mov['monto'])} | {mov['categoria']}"
            )

        if intent == "editar_movimiento":
            movimiento_id = result.get("movimiento_id")

            if not movimiento_id:
                return (
                    "Indícame el número del movimiento a editar.\n\n"
                    "Ejemplo:\n"
                    "• editar movimiento 184 a 40 lucas\n"
                    "• cambiar movimiento 184 a salud"
                )

            response = ApiClient.editar_movimiento(
                usuario_id=usuario_id,
                movimiento_id=movimiento_id,
                monto=result.get("monto"),
                categoria=result.get("categoria"),
                fecha=result.get("fecha")
            )

            mov = response["movimiento"]

            return (
                f"✅ Edité el movimiento #{mov['id']}.\n\n"
                f"{mov['tipo']} | {format_money(mov['monto'])} | "
                f"{mov['categoria']} | {mov['fecha']}"
            )

        if intent == "gastos_mes":
            data = ApiClient.gastos(usuario_id, pagina=1)
            return format_movimientos_response(
                "Gastos de este mes",
                data,
                "gastos"
            )

        if intent == "ingresos_mes":
            data = ApiClient.ingresos(usuario_id, pagina=1)
            return format_movimientos_response(
                "Ingresos de este mes",
                data,
                "ingresos"
            )

        if intent == "aprender_categoria":
            ApiClient.aprender_categoria(
                usuario_id=usuario_id,
                alias=result["alias"],
                categoria=result["categoria"]
            )

            return (
                f"✅ Aprendido.\n\n"
                f"Cuando escribas '{result['alias']}', "
                f"lo registraré como {result['categoria']}."
            )

        if intent == "crear_categoria":
            nombre = result.get("nombre")

            if not nombre:
                return (
                    "Indícame el nombre de la categoría.\n\n"
                    "Ejemplo:\n"
                    "• crear categoría servicios financieros"
                )

            ApiClient.crear_categoria(
                usuario_id,
                nombre,
                "gasto"
            )

            return f"✅ Categoría creada: {nombre}."

        if intent == "configurar_ingreso_mensual":
            ingreso = result.get("ingreso_mensual")

            if not ingreso:
                return (
                    "Indícame el ingreso mensual esperado.\n\n"
                    "Ejemplo:\n"
                    "• ingreso mensual 2 millones"
                )

            ApiClient.configurar_ingreso_mensual(
                usuario_id,
                ingreso
            )

            return (
                f"✅ Ingreso mensual esperado configurado en "
                f"{format_money(ingreso)}."
            )

        if intent == "categorias":
            categorias_db = ApiClient.categorias()

            gastos = []
            ingresos = []

            for cat in categorias_db:
                nombre = cat["nombre"]
                tipo = cat["tipo"]

                if tipo in ["gasto", "ambos"]:
                    gastos.append(f"• {nombre}")

                if tipo in ["ingreso", "ambos"]:
                    ingresos.append(f"• {nombre}")

            return (
                "📂 Categorías disponibles\n\n"
                "💸 Gastos\n"
                f"{chr(10).join(gastos)}\n\n"
                "💰 Ingresos\n"
                f"{chr(10).join(ingresos)}"
            )

        if intent == "config":
            config = ApiClient.configuracion(usuario_id)

            ingreso = config.get("ingreso_mensual")

            ingreso_texto = (
                format_money(ingreso)
                if ingreso
                else "No configurado"
            )

            return (
                "⚙️ Configuración actual\n\n"
                f"Moneda: {config['moneda']}\n"
                f"Fecha de corte / inicio del mes: día {config['dia_inicio_mes']}\n"
                f"Ingreso mensual esperado: {ingreso_texto}\n\n"
                "Puedes cambiarlo con:\n"
                "• cambiar fecha corte 25\n"
                "• ingreso mensual 2 millones"
            )

        if intent == "cambiar_fecha_corte":
            dia = result.get("dia")

            if not dia:
                return (
                    "Indícame el día de corte.\n\n"
                    "Ejemplos:\n"
                    "• cambiar fecha corte 25\n"
                    "• fecha corte 1"
                )

            if dia < 1 or dia > 31:
                return "El día de corte debe estar entre 1 y 31."

            ApiClient.cambiar_fecha_corte(usuario_id, dia)

            return (
                f"✅ Fecha de corte actualizada.\n\n"
                f"Tu mes presupuestario comenzará el día {dia}."
            )

        if intent == "configurar_presupuesto_categoria":
            categoria = result.get("categoria")
            monto = result.get("monto")

            if not categoria or not monto:
                return (
                    "Indícame la categoría y el monto.\n\n"
                    "Ejemplos:\n"
                    "• presupuesto supermercado 400 lucas\n"
                    "• presupuesto salud 100000"
                )

            ApiClient.configurar_presupuesto_categoria(
                usuario_id,
                categoria,
                monto
            )

            return (
                f"✅ Presupuesto configurado.\n\n"
                f"{categoria}: {format_money(monto)} este mes."
            )

        if intent == "presupuestos_categoria":
            presupuestos = ApiClient.presupuestos_categoria(usuario_id)

            if not presupuestos:
                return (
                    "No tienes presupuestos por categoría configurados.\n\n"
                    "Ejemplo:\n"
                    "• presupuesto supermercado 400 lucas"
                )

            lineas = ["📊 Presupuestos por categoría\n"]

            for p in presupuestos:
                estado = "✅"

                if p["disponible"] < 0:
                    estado = "⚠️"

                lineas.append(
                    f"{estado} {p['categoria']}\n"
                    f"Presupuesto: {format_money(p['presupuesto'])}\n"
                    f"Gastado: {format_money(p['gastado'])}\n"
                    f"Disponible: {format_money(p['disponible'])}\n"
                    f"Uso: {p['porcentaje']}%\n"
                )

            return "\n".join(lineas)

        if intent == "ayuda":
            return (
                "Puedes escribirme cosas como:\n\n"
                "• 35 lucas en el super\n"
                "• ayer pagué 48 lucas de luz\n"
                "• ingreso 1.8m sueldo\n"
                "• ingresos del mes\n"
                "• gastos del mes\n"
                "• editar movimiento 184 a 40 lucas\n"
                "• eliminar movimiento 184\n"
                "• crear categoría servicios financieros\n"
                "• ingreso mensual 2 millones\n"
                "• presupuesto supermercado 400 lucas\n"
                "• presupuestos\n"
                "• resumen"
            )

        return (
            "No entendí el mensaje.\n\n"
            "Ejemplos:\n"
            "• 35 lucas en el super\n"
            "• ingreso 1.8m sueldo\n"
            "• ingresos del mes\n"
            "• editar movimiento 184 a 40 lucas\n"
            "• eliminar movimiento 184\n"
            "• presupuesto supermercado 400 lucas\n"
            "• resumen"
        )

    except Exception as e:
        return (
            "Ocurrió un error al procesar tu solicitud.\n"
            f"Detalle: {str(e)}"
        )