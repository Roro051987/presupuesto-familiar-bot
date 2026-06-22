from agents.parser import parse_message
from adapters.api_client import ApiClient


def format_money(amount):
    return f"${amount:,.0f}".replace(",", ".")


def process_message(usuario_id, text):
    result = parse_message(text)
    intent = result.get("intent")

    try:
        if intent == "registrar_gasto":
            ApiClient.registrar_gasto(
                usuario_id=usuario_id,
                monto=int(result["monto"]),
                categoria=result["categoria"],
                descripcion=result.get("descripcion") or result["categoria"],
                fecha=result.get("fecha")
            )

            return (
                f"✅ Registrado gasto de "
                f"{format_money(int(result['monto']))} "
                f"en {result['categoria']}."
            )

        if intent == "registrar_ingreso":
            ApiClient.registrar_ingreso(
                usuario_id=usuario_id,
                monto=int(result["monto"]),
                categoria=result["categoria"],
                descripcion=result.get("descripcion") or result["categoria"],
                fecha=result.get("fecha")
            )

            return (
                f"✅ Registrado ingreso de "
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

        if intent == "gastos_mes":
            resultado = ApiClient.gastos(usuario_id, pagina=1)
            gastos = resultado["gastos"]

            if not gastos:
                return "No tienes gastos registrados este mes."

            total = sum(g["monto"] for g in gastos)

            lineas = ["📋 Gastos de este mes\n"]

            for i, g in enumerate(gastos, start=1):
                fecha = str(g["fecha"])[5:10]

                lineas.append(
                    f"{i}. {fecha} | {format_money(g['monto'])} | {g['categoria']}"
                )

            lineas.append(f"\nTotal mostrado: {format_money(total)}")
            lineas.append(f"Registros del mes: {resultado['total_registros']}")

            return "\n".join(lineas)

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
                f"Ingreso mensual: {ingreso_texto}\n\n"
                "Para cambiar la fecha de corte escribe:\n"
                "• cambiar fecha corte 25\n"
                "• fecha corte 1"
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

        if intent == "ayuda":
            return (
                "Puedes escribirme cosas como:\n\n"
                "• 35 lucas en el super\n"
                "• ayer pagué 48 lucas de luz\n"
                "• ingreso 1.8m sueldo\n"
                "• aprende kiosko como entretención\n"
                "• cambiar fecha corte 25\n"
                "• categorías\n"
                "• config\n"
                "• gastos del mes\n"
                "• resumen\n"
                "• presupuesto supermercado 400 lucas\n"
                "• presupuestos"
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

        return (
            "No entendí el mensaje.\n\n"
            "Ejemplos:\n"
            "• 35 lucas en el super\n"
            "• ayer pagué 48 lucas de luz\n"
            "• aprende kiosko como entretención\n"
            "• gastos del mes\n"
            "• resumen"
        )

    except Exception as e:
        return (
            "Ocurrió un error al procesar tu solicitud.\n"
            f"Detalle: {str(e)}"
        )