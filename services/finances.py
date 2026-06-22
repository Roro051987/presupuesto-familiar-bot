from repository.postgres_repository import (
    registrar_movimiento,
    obtener_o_crear_presupuesto_mes
)


def registrar_gasto(
    usuario_id,
    monto,
    categoria,
    descripcion="",
    fecha=None,
    force=False
):
    presupuesto_id = obtener_o_crear_presupuesto_mes(usuario_id)

    return registrar_movimiento(
        usuario_id=usuario_id,
        presupuesto_id=presupuesto_id,
        tipo="gasto",
        monto=monto,
        categoria=categoria,
        descripcion=descripcion,
        fecha=fecha,
        force=force
    )


def registrar_ingreso(
    usuario_id,
    monto,
    categoria,
    descripcion="",
    fecha=None,
    force=False
):
    presupuesto_id = obtener_o_crear_presupuesto_mes(usuario_id)

    return registrar_movimiento(
        usuario_id=usuario_id,
        presupuesto_id=presupuesto_id,
        tipo="ingreso",
        monto=monto,
        categoria=categoria,
        descripcion=descripcion,
        fecha=fecha,
        force=force
    )