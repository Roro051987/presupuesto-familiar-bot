from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.queries import (
    resumen,
    gastos_mes,
    configuracion,
    cambiar_fecha_corte,
    total_categoria
)

router = APIRouter()


class FechaCorteRequest(BaseModel):
    usuario_id: int
    dia: int


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