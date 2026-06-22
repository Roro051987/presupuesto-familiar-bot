import psycopg
from datetime import date
from config.settings import DATABASE_URL
 

def get_connection():
    return psycopg.connect(DATABASE_URL)


def obtener_o_crear_usuario(telegram_user_id, nombre=None, username=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM usuarios
        WHERE telegram_user_id = %s
    """, (str(telegram_user_id),))

    row = cur.fetchone()

    if row:
        usuario_id = row[0]
    else:
        cur.execute("""
            INSERT INTO usuarios (telegram_user_id, nombre, username)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (str(telegram_user_id), nombre, username))

        usuario_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO configuracion_usuario (usuario_id)
            VALUES (%s)
            ON CONFLICT (usuario_id) DO NOTHING
        """, (usuario_id,))

    conn.commit()
    cur.close()
    conn.close()

    return usuario_id


def obtener_o_crear_presupuesto_mes(usuario_id):
    hoy = date.today()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM presupuestos
        WHERE usuario_id = %s
          AND anio = %s
          AND mes = %s
    """, (usuario_id, hoy.year, hoy.month))

    row = cur.fetchone()

    if row:
        presupuesto_id = row[0]
    else:
        cur.execute("""
            INSERT INTO presupuestos (usuario_id, anio, mes, nombre)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            usuario_id,
            hoy.year,
            hoy.month,
            f"Presupuesto {hoy.month}/{hoy.year}"
        ))

        presupuesto_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return presupuesto_id

def obtener_categoria(nombre):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre
        FROM categorias
        WHERE lower(nombre) = lower(%s)
        LIMIT 1
    """, (nombre,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

def registrar_movimiento(
    usuario_id,
    presupuesto_id,
    tipo,
    monto,
    categoria,
    descripcion="",
    fecha=None
):
    categoria_db = resolver_categoria_usuario(usuario_id, categoria)

    if not categoria_db:
        raise Exception(f"Categoría '{categoria}' no existe")

    categoria_id = categoria_db[0]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO movimientos (
        usuario_id,
        presupuesto_id,
        categoria_id,
        tipo,
        monto,
        descripcion,
        fecha
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        COALESCE(%s, CURRENT_DATE)
    )
        RETURNING id
    """, (
        usuario_id,
        presupuesto_id,
        categoria_id,
        tipo,
        monto,
        descripcion,
        fecha
    ))

    movimiento_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return movimiento_id

def obtener_resumen_mes(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            tipo,
            COALESCE(SUM(monto), 0)
        FROM movimientos
        WHERE usuario_id = %s
        GROUP BY tipo
    """, (usuario_id,))

    rows = cur.fetchall()

    ingresos = 0
    gastos = 0

    for tipo, total in rows:
        if tipo == "ingreso":
            ingresos = total
        elif tipo == "gasto":
            gastos = total

    cur.close()
    conn.close()

    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "saldo": ingresos - gastos
    }

def obtener_total_categoria(usuario_id, categoria):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(SUM(m.monto), 0)
        FROM movimientos m
        JOIN categorias c
            ON c.id = m.categoria_id
        WHERE
            m.usuario_id = %s
            AND lower(c.nombre) = lower(%s)
            AND m.tipo = 'gasto'
    """, (
        usuario_id,
        categoria
    ))

    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    return total

def obtener_configuracion_usuario(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            moneda,
            dia_inicio_mes,
            onboarding_completo,
            paso_onboarding,
            ingreso_mensual
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
        "onboarding_completo": row[2],
        "paso_onboarding": row[3],
        "ingreso_mensual": row[4]
    }


def actualizar_paso_onboarding(usuario_id, paso):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE configuracion_usuario
        SET paso_onboarding = %s
        WHERE usuario_id = %s
    """, (paso, usuario_id))

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
    """, (moneda.upper(), usuario_id))

    conn.commit()
    cur.close()
    conn.close()


def actualizar_dia_inicio_mes(usuario_id, dia):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE configuracion_usuario
        SET dia_inicio_mes = %s
        WHERE usuario_id = %s
    """, (dia, usuario_id))

    conn.commit()
    cur.close()
    conn.close()


def completar_onboarding(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE configuracion_usuario
        SET onboarding_completo = TRUE,
            paso_onboarding = NULL
        WHERE usuario_id = %s
    """, (usuario_id,))

    conn.commit()
    cur.close()
    conn.close()

def obtener_categoria_por_nombre(nombre):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre
        FROM categorias
        WHERE lower(nombre) = lower(%s)
        LIMIT 1
    """, (nombre,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def aprender_alias_categoria(usuario_id, alias, categoria):
    categoria_db = obtener_categoria_por_nombre(categoria)

    if not categoria_db:
        raise Exception(f"La categoría '{categoria}' no existe")

    categoria_id = categoria_db[0]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO categoria_alias_usuario (
            usuario_id,
            alias,
            categoria_id
        )
        VALUES (%s, lower(%s), %s)
        ON CONFLICT (usuario_id, alias)
        DO UPDATE SET categoria_id = EXCLUDED.categoria_id
    """, (
        usuario_id,
        alias,
        categoria_id
    ))

    conn.commit()
    cur.close()
    conn.close()


def resolver_categoria_usuario(usuario_id, categoria_texto):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.nombre
        FROM categoria_alias_usuario a
        JOIN categorias c ON c.id = a.categoria_id
        WHERE a.usuario_id = %s
          AND lower(a.alias) = lower(%s)
        LIMIT 1
    """, (
        usuario_id,
        categoria_texto
    ))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row

    return obtener_categoria_por_nombre(categoria_texto)


def borrar_ultimo_movimiento(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, tipo, monto
        FROM movimientos
        WHERE usuario_id = %s
          AND eliminado = FALSE
        ORDER BY created_at DESC
        LIMIT 1
    """, (usuario_id,))

    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None

    movimiento_id, tipo, monto = row

    cur.execute("""
        UPDATE movimientos
        SET eliminado = TRUE
        WHERE id = %s
    """, (movimiento_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": movimiento_id,
        "tipo": tipo,
        "monto": monto
    }


def obtener_gastos_mes(usuario_id, pagina=1, page_size=10):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM movimientos
        WHERE usuario_id = %s
          AND tipo = 'gasto'
          AND eliminado = FALSE
          AND date_trunc('month', fecha) = date_trunc('month', CURRENT_DATE)
    """, (usuario_id,))

    total_registros = cur.fetchone()[0]

    if total_registros <= 15:
        limit = total_registros
        offset = 0
        pagina = 1
        page_size_real = total_registros
    else:
        limit = page_size
        offset = (pagina - 1) * page_size
        page_size_real = page_size

    cur.execute("""
        SELECT
            m.fecha,
            c.nombre,
            m.monto,
            COALESCE(m.descripcion, '')
        FROM movimientos m
        LEFT JOIN categorias c ON c.id = m.categoria_id
        WHERE m.usuario_id = %s
          AND m.tipo = 'gasto'
          AND m.eliminado = FALSE
          AND date_trunc('month', m.fecha) = date_trunc('month', CURRENT_DATE)
        ORDER BY m.fecha DESC, m.created_at DESC
        LIMIT %s OFFSET %s
    """, (usuario_id, limit, offset))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    total_paginas = 1 if total_registros <= 15 else ((total_registros + page_size - 1) // page_size)

    return {
        "gastos": [
            {
                "fecha": row[0],
                "categoria": row[1],
                "monto": row[2],
                "descripcion": row[3]
            }
            for row in rows
        ],
        "pagina": pagina,
        "page_size": page_size_real,
        "total_registros": total_registros,
        "total_paginas": total_paginas
    } 

def obtener_categorias():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT nombre, tipo
        FROM categorias
        ORDER BY tipo, nombre
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

def obtener_categorias():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT nombre, tipo
        FROM categorias
        ORDER BY tipo, nombre
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

def obtener_configuracion(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            moneda,
            dia_inicio_mes,
            ingreso_mensual
        FROM configuracion_usuario
        WHERE usuario_id = %s
    """, (usuario_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

def actualizar_dia_inicio_mes(usuario_id, dia):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE configuracion_usuario
        SET dia_inicio_mes = %s
        WHERE usuario_id = %s
    """, (dia, usuario_id))

    conn.commit()
    cur.close()
    conn.close()

def guardar_presupuesto_categoria(usuario_id, categoria, monto):
    categoria_db = obtener_categoria_por_nombre(categoria)

    if not categoria_db:
        raise Exception(f"La categoría '{categoria}' no existe")

    categoria_id = categoria_db[0]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO presupuestos_categoria (
            usuario_id,
            categoria_id,
            anio,
            mes,
            monto
        )
        VALUES (
            %s,
            %s,
            EXTRACT(YEAR FROM CURRENT_DATE)::INT,
            EXTRACT(MONTH FROM CURRENT_DATE)::INT,
            %s
        )
        ON CONFLICT (usuario_id, categoria_id, anio, mes)
        DO UPDATE SET
            monto = EXCLUDED.monto,
            updated_at = NOW()
    """, (
        usuario_id,
        categoria_id,
        monto
    ))

    conn.commit()
    cur.close()
    conn.close()


def obtener_presupuestos_categoria(usuario_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.nombre AS categoria,
            pc.monto AS presupuesto,
            COALESCE(SUM(m.monto), 0) AS gastado
        FROM presupuestos_categoria pc
        JOIN categorias c
            ON c.id = pc.categoria_id
        LEFT JOIN movimientos m
            ON m.usuario_id = pc.usuario_id
           AND m.categoria_id = pc.categoria_id
           AND m.tipo = 'gasto'
           AND m.eliminado = FALSE
           AND date_trunc('month', m.fecha) = date_trunc('month', CURRENT_DATE)
        WHERE pc.usuario_id = %s
          AND pc.anio = EXTRACT(YEAR FROM CURRENT_DATE)::INT
          AND pc.mes = EXTRACT(MONTH FROM CURRENT_DATE)::INT
        GROUP BY
            c.nombre,
            pc.monto
        ORDER BY
            c.nombre
    """, (usuario_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "categoria": row[0],
            "presupuesto": row[1],
            "gastado": row[2],
            "disponible": row[1] - row[2],
            "porcentaje": round((row[2] / row[1]) * 100, 1) if row[1] else 0
        }
        for row in rows
    ]