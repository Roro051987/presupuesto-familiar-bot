from repository.postgres_repository import (
    obtener_resumen_mes,
    obtener_total_categoria,
    borrar_ultimo_movimiento,
    obtener_gastos_mes,
    aprender_alias_categoria,
    obtener_categorias,
    obtener_configuracion,
    actualizar_dia_inicio_mes,
    guardar_presupuesto_categoria,
    obtener_presupuestos_categoria
)


def resumen(usuario_id):
    return obtener_resumen_mes(usuario_id)


def total_categoria(usuario_id, categoria):
    return obtener_total_categoria(usuario_id, categoria)


def borrar_ultimo(usuario_id):
    return borrar_ultimo_movimiento(usuario_id)


def gastos_mes(usuario_id, pagina=1):
    return obtener_gastos_mes(usuario_id, pagina=pagina)


def aprender_categoria(usuario_id, alias, categoria):
    return aprender_alias_categoria(usuario_id, alias, categoria)


def categorias():
    return obtener_categorias()


def configuracion(usuario_id):
    return obtener_configuracion(usuario_id)


def cambiar_fecha_corte(usuario_id, dia):
    return actualizar_dia_inicio_mes(usuario_id, dia)

def configurar_presupuesto_categoria(usuario_id, categoria, monto):
    return guardar_presupuesto_categoria(
        usuario_id,
        categoria,
        monto
    )

def presupuestos_categoria(usuario_id):
    return obtener_presupuestos_categoria(usuario_id)