from repository.postgres_repository import (
    obtener_configuracion_usuario,
    actualizar_paso_onboarding,
    actualizar_moneda,
    actualizar_dia_inicio_mes,
    completar_onboarding
)


def process_onboarding(usuario_id, text, nombre=None):
    config = obtener_configuracion_usuario(usuario_id)

    if not config:
        return "No encontré tu configuración de usuario."

    if config["onboarding_completo"]:
        return None

    paso = config["paso_onboarding"]
    texto = text.strip().upper()

    if paso is None:
        actualizar_paso_onboarding(usuario_id, "moneda")

        return (
            f"👋 Hola {nombre or ''}.\n\n"
            "Antes de comenzar, dime la moneda que usarás.\n"
            "Ejemplo: CLP, USD, EUR"
        )

    if paso == "moneda":
        if texto not in ["CLP", "USD", "EUR"]:
            return "Por ahora soportamos CLP, USD o EUR. Escribe una de esas opciones."

        actualizar_moneda(usuario_id, texto)
        actualizar_paso_onboarding(usuario_id, "dia_inicio_mes")

        return (
            "Perfecto.\n\n"
            "Ahora dime qué día comienza tu mes presupuestario.\n"
            "Ejemplo: 1, 5, 15, 25 o 30"
        )

    if paso == "dia_inicio_mes":
        try:
            dia = int(text.strip())
        except ValueError:
            return "Escribe solo el número del día. Ejemplo: 25"

        if dia < 1 or dia > 31:
            return "El día debe estar entre 1 y 31."

        actualizar_dia_inicio_mes(usuario_id, dia)
        completar_onboarding(usuario_id)

        return (
            f"✅ Listo.\n\n"
            f"Tu configuración quedó lista.\n"
            f"Moneda: {config['moneda']}\n"
            f"Día de inicio del mes presupuestario: {dia}\n\n"
            "Ahora puedes escribir:\n"
            "• gasté 35000 en supermercado\n"
            "• ingreso 1800000 sueldo\n"
            "• resumen"
        )