import re
import unicodedata

from repository.postgres_repository import (
    get_connection,
    normalizar_rut,
    vincular_usuario_por_rut,
    actualizar_dia_inicio_mes,
    actualizar_ingreso_mensual
)


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.replace(",", ".")
    text = unicodedata.normalize("NFD", text)
    return "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )


def parse_amount(text: str):
    text = normalize_text(text)

    if re.search(r"(1|un)\s+palo\s+y\s+medio", text):
        return 1500000

    if re.search(r"medio\s+palo", text):
        return 500000

    if re.search(r"(1|un)\s+palo", text):
        return 1000000

    match = re.search(r"(\d+)\s+palos", text)
    if match:
        return int(match.group(1)) * 1000000

    match = re.search(r"(\d+(?:\.\d+)?)\s*m\b", text)
    if match:
        return int(float(match.group(1)) * 1000000)

    match = re.search(r"(\d+(?:\.\d+)?)\s+millones", text)
    if match:
        return int(float(match.group(1)) * 1000000)

    match = re.search(r"(\d+)\s*luca[s]?", text)
    if match:
        return int(match.group(1)) * 1000

    match = re.search(r"(\d+)\s*mil\b", text)
    if match:
        return int(match.group(1)) * 1000

    match = re.search(r"\b(\d{1,3}(?:\.\d{3})+)\b", text)
    if match:
        return int(match.group(1).replace(".", ""))

    match = re.search(r"\b(\d+)\b", text)
    if match:
        return int(match.group(1))

    return None


def rut_valido(rut: str) -> bool:
    rut = normalizar_rut(rut)

    if not rut or "-" not in rut:
        return False

    cuerpo, dv = rut.split("-")

    if not cuerpo.isdigit():
        return False

    if not re.match(r"^[0-9K]$", dv):
        return False

    suma = 0
    multiplo = 2

    for digito in reversed(cuerpo):
        suma += int(digito) * multiplo
        multiplo += 1

        if multiplo > 7:
            multiplo = 2

    resto = suma % 11
    dv_calculado = 11 - resto

    if dv_calculado == 11:
        dv_calculado = "0"
    elif dv_calculado == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(dv_calculado)

    return dv == dv_calculado


def obtener_config_onboarding(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO configuracion_usuario (
            usuario_id,
            moneda,
            dia_inicio_mes,
            onboarding_completo,
            paso_onboarding
        )
        VALUES (
            %s,
            'CLP',
            1,
            FALSE,
            'rut'
        )
        ON CONFLICT (usuario_id)
        DO NOTHING
    """, (usuario_id,))

    conn.commit()

    cur.execute("""
        SELECT
            moneda,
            dia_inicio_mes,
            ingreso_mensual,
            onboarding_completo,
            paso_onboarding
        FROM configuracion_usuario
        WHERE usuario_id = %s
    """, (usuario_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "moneda": row[0],
        "dia_inicio_mes": row[1],
        "ingreso_mensual": row[2],
        "onboarding_completo": row[3],
        "paso_onboarding": row[4]
    }


def actualizar_paso_onboarding(usuario_id, paso):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE configuracion_usuario
        SET paso_onboarding = %s
        WHERE usuario_id = %s
    """, (
        paso,
        usuario_id
    ))

    conn.commit()
    cur.close()
    conn.close()


def actualizar_moneda(usuario_id, moneda):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE configuracion_usuario
        SET moneda = %s
        WHERE usuario_id = %s
    """, (
        moneda,
        usuario_id
    ))

    conn.commit()
    cur.close()
    conn.close()


def completar_onboarding(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE configuracion_usuario
        SET
            onboarding_completo = TRUE,
            paso_onboarding = NULL
        WHERE usuario_id = %s
    """, (usuario_id,))

    conn.commit()
    cur.close()
    conn.close()


def process_onboarding(
    usuario_id,
    text,
    nombre=None,
    telegram_user_id=None,
    username=None
):
    config = obtener_config_onboarding(usuario_id)

    if not config:
        return (
            "No pude cargar tu configuración inicial. "
            "Intenta nuevamente en unos minutos."
        )

    if config["onboarding_completo"]:
        return None

    paso = config["paso_onboarding"] or "rut"
    mensaje = text.strip() if text else ""

    if paso == "rut":
        if not mensaje:
            return (
                f"👋 Hola {nombre or ''}.\n\n"
                "Para configurar tu presupuesto necesito tu RUT.\n\n"
                "Escríbelo con o sin puntos, por ejemplo:\n"
                "• 12.345.678-9\n"
                "• 12345678-9"
            )

        rut = normalizar_rut(mensaje)

        if not rut_valido(rut):
            return (
                "El RUT ingresado no parece válido.\n\n"
                "Inténtalo nuevamente, por ejemplo:\n"
                "• 12.345.678-9"
            )

        resultado = vincular_usuario_por_rut(
            usuario_id_actual=usuario_id,
            rut=rut,
            telegram_user_id=telegram_user_id,
            nombre=nombre,
            username=username
        )

        usuario_id_final = resultado["usuario_id"]

        obtener_config_onboarding(usuario_id_final)
        actualizar_paso_onboarding(usuario_id_final, "moneda")

        if resultado["existente"]:
            return (
                "✅ RUT reconocido.\n\n"
                f"Usaré el presupuesto existente asociado al usuario #{usuario_id_final}.\n\n"
                "Ahora dime qué moneda quieres usar.\n"
                "Por ejemplo: CLP"
            )

        return (
            "✅ RUT registrado correctamente.\n\n"
            f"Tu código de usuario es #{usuario_id_final}.\n\n"
            "Ahora dime qué moneda quieres usar.\n"
            "Por ejemplo: CLP"
        )

    if paso == "moneda":
        if not mensaje:
            return (
                "Indícame la moneda que quieres usar.\n\n"
                "Ejemplo:\n"
                "• CLP"
            )

        moneda = mensaje.upper().strip()

        if len(moneda) < 2 or len(moneda) > 5:
            return (
                "La moneda no parece válida.\n\n"
                "Ejemplo:\n"
                "• CLP"
            )

        actualizar_moneda(usuario_id, moneda)
        actualizar_paso_onboarding(usuario_id, "fecha_corte")

        return (
            f"✅ Moneda configurada: {moneda}\n\n"
            "Ahora dime el día de corte o inicio de tu mes presupuestario.\n\n"
            "Ejemplos:\n"
            "• 1\n"
            "• 25"
        )

    if paso == "fecha_corte":
        dia = parse_amount(mensaje)

        if not dia:
            return (
                "Indícame el día de corte con un número.\n\n"
                "Ejemplos:\n"
                "• 1\n"
                "• 25"
            )

        dia = int(dia)

        if dia < 1 or dia > 31:
            return "El día de corte debe estar entre 1 y 31."

        actualizar_dia_inicio_mes(usuario_id, dia)
        actualizar_paso_onboarding(usuario_id, "ingreso_mensual")

        return (
            f"✅ Fecha de corte configurada: día {dia}\n\n"
            "Ahora dime tu ingreso mensual esperado.\n\n"
            "Ejemplos:\n"
            "• 2 millones\n"
            "• 1800000\n\n"
            "Si prefieres configurarlo después, escribe: omitir"
        )

    if paso == "ingreso_mensual":
        normalized = normalize_text(mensaje)

        if normalized in ["omitir", "saltar", "despues", "después"]:
            completar_onboarding(usuario_id)

            return (
                "✅ Configuración inicial completada.\n\n"
                f"Tu código de usuario es #{usuario_id}.\n\n"
                "Ya puedes registrar movimientos, por ejemplo:\n"
                "• 35 lucas en el super\n"
                "• ingreso 1.8m sueldo\n"
                "• /resumen"
            )

        ingreso = parse_amount(mensaje)

        if not ingreso:
            return (
                "No pude interpretar el ingreso mensual.\n\n"
                "Ejemplos:\n"
                "• 2 millones\n"
                "• 1800000\n\n"
                "También puedes escribir: omitir"
            )

        actualizar_ingreso_mensual(usuario_id, ingreso)
        completar_onboarding(usuario_id)

        return (
            f"✅ Ingreso mensual esperado configurado en ${ingreso:,.0f}.\n\n"
            f"Tu código de usuario es #{usuario_id}.\n\n"
            "Configuración inicial completada.\n\n"
            "Ya puedes registrar movimientos, por ejemplo:\n"
            "• 35 lucas en el super\n"
            "• ingreso 1.8m sueldo\n"
            "• /resumen"
        ).replace(",", ".")

    actualizar_paso_onboarding(usuario_id, "rut")

    return (
        "Vamos a configurar tu presupuesto desde el inicio.\n\n"
        "Primero indícame tu RUT."
    )