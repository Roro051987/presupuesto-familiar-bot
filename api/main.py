from fastapi import FastAPI

from api.security import ApiKeyMiddleware

from api.routers.health import router as health_router
from api.routers.movimientos import router as movimientos_router
from api.routers.usuarios import router as usuarios_router
from api.routers.categorias import router as categorias_router

app = FastAPI(
    title="Presupuesto Familiar API",
    version="1.0.0"
)

app.add_middleware(ApiKeyMiddleware)

app.include_router(health_router)
app.include_router(movimientos_router)
app.include_router(usuarios_router)
app.include_router(categorias_router)