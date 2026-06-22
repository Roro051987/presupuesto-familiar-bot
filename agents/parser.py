import re
import unicodedata
from datetime import date, timedelta


CATEGORY_MAP = {
    "super": "supermercado",
    "supermercado": "supermercado",
    "jumbo": "supermercado",
    "lider": "supermercado",
    "líder": "supermercado",
    "unimarc": "supermercado",
    "tottus": "supermercado",
    "santa isabel": "supermercado",

    "farmacia": "salud",
    "remedios": "salud",
    "medicamentos": "salud",
    "cruz verde": "salud",
    "salcobrand": "salud",
    "ahumada": "salud",

    "luz": "luz",
    "agua": "agua",
    "internet": "internet",
    "wifi": "internet",
    "gas": "gas",

    "bencina": "transporte",
    "combustible": "transporte",
    "uber": "transporte",
    "cabify": "transporte",
    "metro": "transporte",
    "micro": "transporte",

    "sueldo": "sueldo",
    "salario": "sueldo",
    "deposito": "sueldo",
    "depósito": "sueldo",

    "comida": "entretención",
    "restaurant": "entretención",
    "restaurante": "entretención",
    "cine": "entretención",

    "otros": "otros"
}


GASTO_WORDS = [
    "gaste", "gasto", "pague", "pago", "compre", "compra"
]

INGRESO_WORDS = [
    "ingreso", "recibi", "depositaron",
    "pagaron", "sueldo", "me pagaron", "me depositaron"
]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.replace(",", ".")
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Mn"
    )
    return text


def normalize_category(text: str) -> str:
    text = normalize_text(text)

    for key, value in CATEGORY_MAP.items():
        if normalize_text(key) in text:
            return value

    return text.strip() or "otros"


def parse_fecha(text: str) -> str:
    normalized = normalize_text(text)
    hoy = date.today()

    if "antes de ayer" in normalized or "anteayer" in normalized:
        return (hoy - timedelta(days=2)).isoformat()

    if "ayer" in normalized:
        return (hoy - timedelta(days=1)).isoformat()

    return hoy.isoformat()


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

    match = re.search(r"(\d+)\s*k\b", text)
    if match:
        return int(match.group(1)) * 1000

    match = re.search(r"\b(\d{1,3}(?:\.\d{3})+)\b", text)
    if match:
        return int(match.group(1).replace(".", ""))

    match = re.search(r"\b(\d+)\b", text)
    if match:
        return int(match.group(1))

    return None


def parse_movimiento_id(text: str):
    normalized = normalize_text(text)

    match = re.search(r"(movimiento|gasto|ingreso)\s+#?(\d+)", normalized)
    if match:
        return int(match.group(2))

    match = re.search(r"#(\d+)", normalized)
    if match:
        return int(match.group(1))

    return None


def detect_intent(text: str) -> str:
    normalized = normalize_text(text)

    if normalized in ["resumen", "resumen mes", "resumen del mes"]:
        return "resumen"

    if normalized in ["ayuda", "help", "comandos"]:
        return "ayuda"

    if normalized in ["categorias", "categorías"]:
        return "categorias"

    if normalized in ["config", "configuracion", "configuración", "ver config", "ver configuracion"]:
        return "config"

    if normalized in ["presupuestos", "presupuesto categorias", "presupuestos categorias"]:
        return "presupuestos_categoria"

    if normalized.startswith("presupuesto "):
        return "configurar_presupuesto_categoria"

    if normalized.startswith("crear categoria ") or normalized.startswith("crear categoría "):
        return "crear_categoria"

    if normalized.startswith("nueva categoria ") or normalized.startswith("nueva categoría "):
        return "crear_categoria"

    if "ingreso mensual" in normalized:
        return "configurar_ingreso_mensual"

    if (
        normalized.startswith("cambiar fecha corte")
        or normalized.startswith("cambiar fecha de corte")
        or normalized.startswith("fecha corte")
        or normalized.startswith("fecha de corte")
    ):
        return "cambiar_fecha_corte"

    if "cuanto me queda" in normalized or "saldo" in normalized:
        return "saldo"

    if (
        normalized.startswith("ingresos")
        or "ingresos del mes" in normalized
        or "ver ingresos" in normalized
    ):
        return "ingresos_mes"

    if (
        normalized.startswith("gastos")
        or "gastos del mes" in normalized
        or "todos los gastos" in normalized
        or "ver gastos" in normalized
    ):
        return "gastos_mes"

    if (
        "borra ultimo" in normalized
        or "elimina ultimo" in normalized
        or "borrar ultimo" in normalized
        or "eliminar ultimo" in normalized
    ):
        return "borrar_ultimo_movimiento"

    if normalized.startswith("elimina movimiento") or normalized.startswith("eliminar movimiento"):
        return "eliminar_movimiento"

    if normalized.startswith("borra movimiento") or normalized.startswith("borrar movimiento"):
        return "eliminar_movimiento"

    if normalized.startswith("edita movimiento") or normalized.startswith("editar movimiento"):
        return "editar_movimiento"

    if normalized.startswith("cambia movimiento") or normalized.startswith("cambiar movimiento"):
        return "editar_movimiento"

    if normalized.startswith("aprende ") and " como " in normalized:
        return "aprender_categoria"

    if "cuanto" in normalized and "gaste" in normalized:
        return "consulta_categoria"

    if any(word in normalized for word in INGRESO_WORDS):
        return "registrar_ingreso"

    if any(word in normalized for word in GASTO_WORDS):
        return "registrar_gasto"

    if parse_amount(normalized):
        return "registrar_gasto"

    return "desconocido"


def extract_category(text: str) -> str:
    normalized = normalize_text(text)

    cleaned = re.sub(r"\d+(?:\.\d+)?\s*(lucas?|k|m|mil|palos?|millones)?", "", normalized)
    cleaned = cleaned.replace("un palo y medio", "")
    cleaned = cleaned.replace("un palo", "")
    cleaned = cleaned.replace("medio palo", "")
    cleaned = cleaned.replace("palo y medio", "")

    remove_words = [
        "gaste", "gasto", "pague", "pago", "compre", "compra",
        "en", "de", "por", "el", "la", "los", "las",
        "me", "depositaron", "pagaron", "recibi", "ingreso",
        "ayer", "hoy", "antes", "anteayer"
    ]

    for word in remove_words:
        cleaned = re.sub(rf"\b{word}\b", "", cleaned)

    cleaned = " ".join(cleaned.split())

    return normalize_category(cleaned)


def parse_message(text: str) -> dict:
    normalized = normalize_text(text)
    intent = detect_intent(normalized)

    if intent in [
        "resumen",
        "saldo",
        "ayuda",
        "categorias",
        "config",
        "gastos_mes",
        "ingresos_mes",
        "presupuestos_categoria",
        "borrar_ultimo_movimiento"
    ]:
        return {"intent": intent}

    if intent == "cambiar_fecha_corte":
        dia = parse_amount(normalized)

        return {
            "intent": "cambiar_fecha_corte",
            "dia": int(dia) if dia else None
        }

    if intent == "configurar_ingreso_mensual":
        monto = parse_amount(normalized)

        return {
            "intent": "configurar_ingreso_mensual",
            "ingreso_mensual": monto
        }

    if intent == "crear_categoria":
        nombre = normalized
        nombre = nombre.replace("crear categoria", "")
        nombre = nombre.replace("crear categoría", "")
        nombre = nombre.replace("nueva categoria", "")
        nombre = nombre.replace("nueva categoría", "")
        nombre = " ".join(nombre.split())

        return {
            "intent": "crear_categoria",
            "nombre": nombre,
            "tipo": "gasto"
        }

    if intent == "configurar_presupuesto_categoria":
        monto = parse_amount(normalized)

        categoria_texto = normalized.replace("presupuesto", "", 1)
        categoria_texto = re.sub(
            r"\d+(?:\.\d+)?\s*(lucas?|k|m|mil|palos?|millones)?",
            "",
            categoria_texto
        )
        categoria_texto = " ".join(categoria_texto.split())

        return {
            "intent": "configurar_presupuesto_categoria",
            "categoria": normalize_category(categoria_texto),
            "monto": monto
        }

    if intent == "eliminar_movimiento":
        movimiento_id = parse_movimiento_id(normalized)

        return {
            "intent": "eliminar_movimiento",
            "movimiento_id": movimiento_id
        }

    if intent == "editar_movimiento":
        movimiento_id = parse_movimiento_id(normalized)
        monto = parse_amount(normalized)
        categoria = extract_category(normalized)

        return {
            "intent": "editar_movimiento",
            "movimiento_id": movimiento_id,
            "monto": monto,
            "categoria": categoria if categoria not in ["otros", "movimiento"] else None,
            "fecha": parse_fecha(normalized)
        }

    if intent == "aprender_categoria":
        partes = normalized.replace("aprende ", "", 1).split(" como ")

        if len(partes) != 2:
            return {"intent": "desconocido"}

        return {
            "intent": "aprender_categoria",
            "alias": partes[0].strip(),
            "categoria": normalize_category(partes[1].strip())
        }

    if intent == "consulta_categoria":
        categoria = normalized
        categoria = categoria.replace("cuanto", "")
        categoria = categoria.replace("gaste", "")
        categoria = categoria.replace("en", "")
        categoria = " ".join(categoria.split())

        return {
            "intent": "consulta_categoria",
            "categoria": normalize_category(categoria)
        }

    if intent in ["registrar_gasto", "registrar_ingreso"]:
        monto = parse_amount(normalized)

        if not monto:
            return {"intent": "desconocido"}

        categoria = extract_category(normalized)

        if intent == "registrar_ingreso" and categoria == "otros":
            categoria = "sueldo"

        return {
            "intent": intent,
            "monto": monto,
            "categoria": categoria,
            "descripcion": categoria,
            "fecha": parse_fecha(normalized)
        }

    return {"intent": "desconocido"}