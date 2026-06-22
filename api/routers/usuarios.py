from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.queries import (
    resumen,
    gastos_mes,
    configuracion,
    cambiar_fecha_corte,
    total_categoria,
    configurar_presupuesto_categoria,
    presupuestos_categoria,
    ingresos_mes,
    editar_movimiento,
    eliminar_movimiento,
    crear_categoria_usuario,
    configurar_ingreso_mensual,
    configurar_rut_usuario,
    usuario_por_rut
)

router = APIRouter()

class EditarMovimientoRequest(BaseModel):
    monto: int | None = None
    categoria: str | None = None
    descripcion: str | None = None
    fecha: str | None = None


class CategoriaPersonalizadaRequest(BaseModel):
    nombre: str
    tipo: str = "gasto"


class IngresoMensualRequest(BaseModel):
    ingreso_mensual: int


class RutUsuarioRequest(BaseModel):
    rut: str

class FechaCorteRequest(BaseModel):
    usuario_id: int
    dia: int

class PresupuestoCategoriaRequest(BaseModel):
    categoria: str
    monto: int

@router.get("/usuarios/{usuario_id}/resumen")
def obtener_resumen(usuario_id: int):
    return resumen(usuario_id)


@router.get("/usuarios/{usuario_id}/gastos")
def obtener_gastos(usuario_id: int, pagina: int = 1):
    return gastos_mes(usuario_id, pagina=pagina)


@router.get("/usuarios/{usuario_id}/gastos/categoria/{categoria}")
def obtener_total_categoria(usuario_id: int, categoria: str):
    return {
        "categoria": categoria,
        "total": total_categoria(usuario_id, categoria)
    }


@router.get("/usuarios/{usuario_id}/config")
def obtener_config(usuario_id: int):
    config = configuracion(usuario_id)

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Configuración no encontrada"
        )

    moneda, dia_inicio_mes, ingreso_mensual = config

    return {
        "moneda": moneda,
        "dia_inicio_mes": dia_inicio_mes,
        "ingreso_mensual": ingreso_mensual
    }


@router.post("/usuarios/config/fecha-corte")
def actualizar_fecha_corte(request: FechaCorteRequest):
    if request.dia < 1 or request.dia > 31:
        raise HTTPException(
            status_code=400,
            detail="El día debe estar entre 1 y 31"
        )

    cambiar_fecha_corte(
        request.usuario_id,
        request.dia
    )

    return {
        "ok": True,
        "dia_inicio_mes": request.dia
    }

@router.post("/usuarios/{usuario_id}/presupuestos/categoria")
def guardar_presupuesto_usuario_categoria(
    usuario_id: int,
    request: PresupuestoCategoriaRequest
):
    configurar_presupuesto_categoria(
        usuario_id,
        request.categoria,
        request.monto
    )

    return {
        "ok": True,
        "categoria": request.categoria,
        "monto": request.monto
    }


@router.get("/usuarios/{usuario_id}/presupuestos/categorias")
def obtener_presupuestos_usuario_categoria(usuario_id: int):
    return presupuestos_categoria(usuario_id)

@router.get("/usuarios/rut/{rut}")
def obtener_usuario_por_rut_endpoint(rut: str):
    usuario = usuario_por_rut(rut)

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return usuario


@router.post("/usuarios/{usuario_id}/rut")
def configurar_rut_usuario_endpoint(
    usuario_id: int,
    request: RutUsuarioRequest
):
    rut = configurar_rut_usuario(
        usuario_id,
        request.rut
    )

    return {
        "ok": True,
        "usuario_id": usuario_id,
        "rut": rut
    }


@router.get("/usuarios/{usuario_id}/ingresos")
def obtener_ingresos(
    usuario_id: int,
    pagina: int = 1
):
    return ingresos_mes(
        usuario_id,
        pagina=pagina
    )


@router.patch("/usuarios/{usuario_id}/movimientos/{movimiento_id}")
def editar_movimiento_endpoint(
    usuario_id: int,
    movimiento_id: int,
    request: EditarMovimientoRequest
):
    movimiento = editar_movimiento(
        usuario_id=usuario_id,
        movimiento_id=movimiento_id,
        monto=request.monto,
        categoria=request.categoria,
        descripcion=request.descripcion,
        fecha=request.fecha
    )

    if not movimiento:
        raise HTTPException(
            status_code=404,
            detail="Movimiento no encontrado"
        )

    return {
        "ok": True,
        "movimiento": movimiento
    }


@router.delete("/usuarios/{usuario_id}/movimientos/{movimiento_id}")
def eliminar_movimiento_endpoint(
    usuario_id: int,
    movimiento_id: int
):
    movimiento = eliminar_movimiento(
        usuario_id,
        movimiento_id
    )

    if not movimiento:
        raise HTTPException(
            status_code=404,
            detail="Movimiento no encontrado"
        )

    return {
        "ok": True,
        "movimiento": movimiento
    }


@router.post("/usuarios/{usuario_id}/categorias")
def crear_categoria_usuario_endpoint(
    usuario_id: int,
    request: CategoriaPersonalizadaRequest
):
    crear_categoria_usuario(
        usuario_id,
        request.nombre,
        request.tipo
    )

    return {
        "ok": True,
        "usuario_id": usuario_id,
        "nombre": request.nombre,
        "tipo": request.tipo
    }


@router.patch("/usuarios/{usuario_id}/config/ingreso-mensual")
def configurar_ingreso_mensual_endpoint(
    usuario_id: int,
    request: IngresoMensualRequest
):
    ingreso = configurar_ingreso_mensual(
        usuario_id,
        request.ingreso_mensual
    )

    return {
        "ok": True,
        "usuario_id": usuario_id,
        "ingreso_mensual": ingreso
    }