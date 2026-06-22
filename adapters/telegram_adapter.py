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
from adapters.api_client import ApiClient
from config.settings import TELEGRAM_BOT_TOKEN

from repository.postgres_repository import obtener_o_crear_usuario
from agents.onboarding import process_onboarding
from agents.orchestrator import process_message
from services.queries import gastos_mes


COMMAND_MAP = {
    "/ayuda": "ayuda",
    "/resumen": "resumen",
    "/saldo": "cuanto me queda",
    "/gastos": "gastos del mes",
    "/borrar": "borra ultimo movimiento",
    "/categorias": "categorias",
    "/config": "config",
    "/presupuestos": "presupuestos",
}

def format_money(amount):
    return f"${amount:,.0f}".replace(",", ".")

def build_gastos_message(resultado):
    gastos = resultado["gastos"]
    pagina = resultado["pagina"]
    total_paginas = resultado["total_paginas"]
    total_registros = resultado["total_registros"]

    if not gastos:
        return "No tienes gastos registrados este mes."

    titulo = "📋 Gastos de este mes"

    if total_paginas > 1:
        titulo += f" ({pagina}/{total_paginas})"

    lineas = [titulo, ""]

    inicio = 1 if total_registros <= 15 else ((pagina - 1) * 10) + 1

    for i, gasto in enumerate(gastos, start=inicio):
        fecha = gasto["fecha"]

        if hasattr(fecha, "strftime"):
            fecha_texto = fecha.strftime("%d-%m")
        else:
            fecha_texto = str(fecha)[5:10]

        lineas.append(
            f"{i}. {fecha_texto} | {format_money(gasto['monto'])} | {gasto['categoria']}"
        )
    
    lineas.append("")
    lineas.append(f"Registros del mes: {total_registros}")
    
    return "\n".join(lineas)

def build_gastos_keyboard(resultado):
    total_registros = resultado["total_registros"]
    pagina = resultado["pagina"]
    total_paginas = resultado["total_paginas"]

    if total_registros <= 15:
        return None

    if 16 <= total_registros <= 20:
        buttons = [
            InlineKeyboardButton("1", callback_data="gastos:1"),
            InlineKeyboardButton("2", callback_data="gastos:2")
        ]

        return InlineKeyboardMarkup([buttons])

    buttons = [
        InlineKeyboardButton("1", callback_data="gastos:1"),
        InlineKeyboardButton(f"Página {pagina}", callback_data=f"gastos:{pagina}")
    ]

    if pagina < total_paginas:
        buttons.append(
            InlineKeyboardButton(str(pagina + 1), callback_data=f"gastos:{pagina + 1}")
        )

    return InlineKeyboardMarkup([buttons])

async def send_gastos_page(update, usuario_id, pagina=1):
    resultado = ApiClient.gastos(usuario_id, pagina=pagina)

    texto = build_gastos_message(resultado)
    keyboard = build_gastos_keyboard(resultado)

    await update.message.reply_text(
        texto,
        reply_markup=keyboard
    )

async def gastos_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_user = query.from_user

    usuario_id = obtener_o_crear_usuario(
        telegram_user_id=str(telegram_user.id),
        nombre=telegram_user.first_name,
        username=telegram_user.username
    )

    pagina = int(query.data.split(":")[1])

    resultado = ApiClient.gastos(usuario_id, pagina=pagina)

    texto = build_gastos_message(resultado)
    keyboard = build_gastos_keyboard(resultado)

    await query.edit_message_text(
        text=texto,
        reply_markup=keyboard
    )

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    telegram_user = update.effective_user

    usuario_id = obtener_o_crear_usuario(
        telegram_user_id=str(telegram_user.id),
        nombre=telegram_user.first_name,
        username=telegram_user.username
    )

    respuesta_onboarding = process_onboarding(
        usuario_id=usuario_id,
        text="",
        nombre=telegram_user.first_name
    )

    if respuesta_onboarding:
        await update.message.reply_text(respuesta_onboarding)
        return

    await update.message.reply_text(
        "👋 Hola.\n\n"
        "Tu presupuesto ya está configurado.\n\n"
        "Puedes escribir:\n"
        "• 35 lucas en el super\n"
        "• ayer pagué 48 lucas de luz\n"
        "• ingreso 1.8m sueldo\n"
        "• gastos del mes\n"
        "• config\n"
        "• resumen\n\n"
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
        await send_gastos_page(
            update,
            usuario_id,
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

    gastos = gastos_mes(usuario_id)

    if not gastos:
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
            "Fecha",
            "Categoría",
            "Monto",
            "Descripción"
        ])

        for gasto in gastos:
            writer.writerow([
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
        nombre=telegram_user.first_name
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
    app.add_handler(CommandHandler("borrar", command_handler))
    app.add_handler(CommandHandler("categorias", command_handler))
    app.add_handler(CommandHandler("config", command_handler))
    app.add_handler(CommandHandler("exportar", exportar_command))
    app.add_handler(CallbackQueryHandler(gastos_callback_handler, pattern=r"^gastos:\d+$"))
    app.add_handler(CommandHandler("presupuestos", command_handler))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_message
        )
    )

    print("Bot iniciado...")

    app.run_polling()


    