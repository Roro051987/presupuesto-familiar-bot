from fastapi import APIRouter
from pydantic import BaseModel

from services.queries import (
    categorias,
    aprender_categoria
)

router = APIRouter()


class AprenderCategoriaRequest(BaseModel):
    usuario_id: int
    alias: str
    categoria: str


@router.get("/categorias")
def obtener_lista_categorias():
    rows = categorias()

    return [
        {
            "nombre": row[0],
            "tipo": row[1]
        }
        for row in rows
    ]


@router.post("/usuarios/categorias/aprender")
def aprender_alias(request: AprenderCategoriaRequest):
    aprender_categoria(
        request.usuario_id,
        request.alias,
        request.categoria
    )

    return {"ok": True}