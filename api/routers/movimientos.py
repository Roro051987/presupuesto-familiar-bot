from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.finances import registrar_gasto, registrar_ingreso
from services.queries import borrar_ultimo

router = APIRouter()


class MovimientoRequest(BaseModel):
    usuario_id: int
    monto: int
    categoria: str
    descripcion: str | None = None
    fecha: str | None = None


@router.post("/movimientos/gasto")
def crear_gasto(request: MovimientoRequest):
    try:
        movimiento_id = registrar_gasto(
            usuario_id=request.usuario_id,
            monto=request.monto,
            categoria=request.categoria,
            descripcion=request.descripcion or request.categoria,
            fecha=request.fecha
        )

        return {
            "ok": True,
            "movimiento_id": movimiento_id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/movimientos/ingreso")
def crear_ingreso(request: MovimientoRequest):
    try:
        movimiento_id = registrar_ingreso(
            usuario_id=request.usuario_id,
            monto=request.monto,
            categoria=request.categoria,
            descripcion=request.descripcion or request.categoria,
            fecha=request.fecha
        )

        return {
            "ok": True,
            "movimiento_id": movimiento_id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/usuarios/{usuario_id}/movimientos/borrar-ultimo")
def borrar_ultimo_movimiento(usuario_id: int):
    mov = borrar_ultimo(usuario_id)

    if not mov:
        return {
            "ok": False,
            "message": "No hay movimientos para borrar"
        }

    return {
        "ok": True,
        "movimiento": mov
    }