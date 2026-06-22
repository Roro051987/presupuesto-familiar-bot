import csv
import tempfile

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    filters
)

from config.settings import TELEGRAM_BOT_TOKEN
from repository.postgres_repository import obtener_o_crear_usuario
from agents.onboarding import process_onboarding
from agents.orchestrator import process_message
from adapters.api_client import ApiClient

from agents.onboarding import (
    process_onboarding,
    obtener_config_onboarding
)


COMMAND_MAP = {
    "/ayuda": "ayuda",
    "/resumen": "resumen",
    "/saldo": "cuanto me queda",
    "/gastos": "gastos del mes",
    "/ingresos": "ingresos del mes",
    "/borrar": "borra ultimo movimiento",
    "/categorias": "categorias",
    "/config": "config",
    "/presupuestos": "presupuestos",
}


def format_money(amount):
    return f"${amount:,.0f}".replace(",", ".")


def format_fecha(fecha):
    return str(fecha)[5:10]


def build_movimientos_message(resultado, tipo):
    key = "gastos" if tipo == "gastos" else "ingresos"
    titulo = "📋 Gastos de este mes" if tipo == "gastos" else "📥 Ingresos de este mes"

    movimientos = resultado[key]
    pagina = resultado["pagina"]
    total_paginas = resultado["total_paginas"]
    total_registros = resultado["total_registros"]

    if not movimientos:
        return f"No tienes {tipo} registrados este mes."

    if total_paginas > 1:
        titulo += f" ({pagina}/{total_paginas})"

    lineas = [titulo, ""]

    for mov in movimientos:
        lineas.append(
            f"#{mov['id']} | {format_fecha(mov['fecha'])} | "
            f"{format_money(mov['monto'])} | {mov['categoria']}"
        )

    lineas.append("")
    lineas.append(f"Registros del mes: {total_registros}")

    return "\n".join(lineas)


def build_movimientos_keyboard(resultado, tipo):
    total_registros = resultado["total_registros"]
    pagina = resultado["pagina"]
    total_paginas = resultado["total_paginas"]

    if total_registros <= 15:
        return None

    if 16 <= total_registros <= 20:
        buttons = [
            InlineKeyboardButton("1", callback_data=f"{tipo}:1"),
            InlineKeyboardButton("2", callback_data=f"{tipo}:2")
        ]
        return InlineKeyboardMarkup([buttons])

    buttons = [
        InlineKeyboardButton("1", callback_data=f"{tipo}:1"),
        InlineKeyboardButton(f"Página {pagina}", callback_data=f"{tipo}:{pagina}")
    ]

    if pagina < total_paginas:
        buttons.append(
            InlineKeyboardButton(str(pagina + 1), callback_data=f"{tipo}:{pagina + 1}")
        )

    return InlineKeyboardMarkup([buttons])


async def send_movimientos_page(update, usuario_id, tipo, pagina=1):
    if tipo == "gastos":
        resultado = ApiClient.gastos(usuario_id, pagina=pagina)
    else:
        resultado = ApiClient.ingresos(usuario_id, pagina=pagina)

    texto = build_movimientos_message(resultado, tipo)
    keyboard = build_movimientos_keyboard(resultado, tipo)

    await update.message.reply_text(
        texto,
        reply_markup=keyboard
    )


async def movimientos_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    telegram_user = query.from_user

    usuario_id = obtener_o_crear_usuario(
        telegram_user_id=str(telegram_user.id),
        nombre=telegram_user.first_name,
        username=telegram_user.username
    )

    tipo, pagina_texto = query.data.split(":")
    pagina = int(pagina_texto)

    if tipo == "gastos":
        resultado = ApiClient.gastos(usuario_id, pagina=pagina)
    else:
        resultado = ApiClient.ingresos(usuario_id, pagina=pagina)

    texto = build_movimientos_message(resultado, tipo)
    keyboard = build_movimientos_keyboard(resultado, tipo)

    await query.edit_message_text(
        text=texto,
        reply_markup=keyboard
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = update.effective_user

    usuario_id = obtener_o_crear_usuario(
        telegram_user_id=str(telegram_user.id),
        nombre=telegram_user.first_name,
        username=telegram_user.username
    )

    config = obtener_config_onboarding(usuario_id)

    if not config or not config["onboarding_completo"]:
        await update.message.reply_text(
            f"👋 Hola {telegram_user.first_name}.\n\n"
            "Para comenzar necesito tu RUT.\n\n"
            "Ejemplos:\n"
            "• 12.345.678-9\n"
            "• 12345678-9"
        )
        return

    await update.message.reply_text(
        "👋 Hola.\n\n"
        "Tu presupuesto ya está configurado.\n\n"
        "Puedes escribir:\n"
        "• 35 lucas en el super\n"
        "• ayer pagué 48 lucas de luz\n"
        "• ingreso 1.8m sueldo\n"
        "• /gastos\n"
        "• /ingresos\n"
        "• /presupuestos\n"
        "• /resumen\n\n"
        "También puedes usar el menú de comandos con /"
    )

async def command_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    command = update.message.text.split()[0]

    telegram_user = update.effective_user

    usuario_id = obtener_o_crear_usuario(
        telegram_user_id=str(telegram_user.id),
        nombre=telegram_user.first_name,
        username=telegram_user.username
    )

    if command == "/gastos":
        await send_movimientos_page(
            update,
            usuario_id,
            tipo="gastos",
            pagina=1
        )
        return

    if command == "/ingresos":
        await send_movimientos_page(
            update,
            usuario_id,
            tipo="ingresos",
            pagina=1
        )
        return

    mapped_message = COMMAND_MAP.get(command, "ayuda")

    await handle_user_message(
        update,
        context,
        mapped_message
    )


async def exportar_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    telegram_user = update.effective_user

    usuario_id = obtener_o_crear_usuario(
        telegram_user_id=str(telegram_user.id),
        nombre=telegram_user.first_name,
        username=telegram_user.username
    )

    todos_los_gastos = []
    pagina = 1

    while True:
        resultado = ApiClient.gastos(usuario_id, pagina=pagina)
        gastos = resultado.get("gastos", [])

        todos_los_gastos.extend(gastos)

        if pagina >= resultado.get("total_paginas", 1):
            break

        pagina += 1

    if not todos_los_gastos:
        await update.message.reply_text(
            "No tienes gastos registrados este mes."
        )
        return

    with tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        suffix=".csv",
        delete=False,
        encoding="utf-8"
    ) as file:
        writer = csv.writer(file)

        writer.writerow([
            "ID",
            "Fecha",
            "Categoría",
            "Monto",
            "Descripción"
        ])

        for gasto in todos_los_gastos:
            writer.writerow([
                gasto["id"],
                gasto["fecha"],
                gasto["categoria"],
                gasto["monto"],
                gasto["descripcion"]
            ])

        ruta = file.name

    await update.message.reply_document(
        document=open(ruta, "rb"),
        filename="gastos_mes.csv"
    )


async def receive_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    mensaje = update.message.text

    await handle_user_message(
        update,
        context,
        mensaje
    )


async def handle_user_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    mensaje: str
):
    telegram_user = update.effective_user

    usuario_id = obtener_o_crear_usuario(
        telegram_user_id=str(telegram_user.id),
        nombre=telegram_user.first_name,
        username=telegram_user.username
    )

    respuesta_onboarding = process_onboarding(
        usuario_id=usuario_id,
        text=mensaje,
        nombre=telegram_user.first_name,
        telegram_user_id=str(telegram_user.id),
        username=telegram_user.username
    )

    if respuesta_onboarding:
        await update.message.reply_text(respuesta_onboarding)
        return

    respuesta = process_message(
        usuario_id,
        mensaje
    )

    await update.message.reply_text(respuesta)


def start_bot():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", command_handler))
    app.add_handler(CommandHandler("resumen", command_handler))
    app.add_handler(CommandHandler("saldo", command_handler))
    app.add_handler(CommandHandler("gastos", command_handler))
    app.add_handler(CommandHandler("ingresos", command_handler))
    app.add_handler(CommandHandler("borrar", command_handler))
    app.add_handler(CommandHandler("categorias", command_handler))
    app.add_handler(CommandHandler("config", command_handler))
    app.add_handler(CommandHandler("presupuestos", command_handler))
    app.add_handler(CommandHandler("exportar", exportar_command))

    app.add_handler(
        CallbackQueryHandler(
            movimientos_callback_handler,
            pattern=r"^(gastos|ingresos):\d+$"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_message
        )
    )

    print("Bot iniciado...")

    app.run_polling()