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
    obtener_presupuestos_categoria,
    obtener_usuario_por_rut,
    actualizar_rut_usuario,
    obtener_ingresos_mes,
    editar_movimiento_por_id,
    eliminar_movimiento_por_id,
    crear_categoria_personalizada,
    actualizar_ingreso_mensual
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

def usuario_por_rut(rut):
    return obtener_usuario_por_rut(rut)


def configurar_rut_usuario(usuario_id, rut):
    return actualizar_rut_usuario(usuario_id, rut)


def ingresos_mes(usuario_id, pagina=1):
    return obtener_ingresos_mes(
        usuario_id,
        pagina=pagina
    )


def editar_movimiento(
    usuario_id,
    movimiento_id,
    monto=None,
    categoria=None,
    descripcion=None,
    fecha=None
):
    return editar_movimiento_por_id(
        usuario_id=usuario_id,
        movimiento_id=movimiento_id,
        monto=monto,
        categoria=categoria,
        descripcion=descripcion,
        fecha=fecha
    )


def eliminar_movimiento(
    usuario_id,
    movimiento_id
):
    return eliminar_movimiento_por_id(
        usuario_id,
        movimiento_id
    )


def crear_categoria_usuario(
    usuario_id,
    nombre,
    tipo="gasto"
):
    return crear_categoria_personalizada(
        usuario_id,
        nombre,
        tipo
    )


def configurar_ingreso_mensual(
    usuario_id,
    ingreso_mensual
):
    return actualizar_ingreso_mensual(
        usuario_id,
        ingreso_mensual
    )