from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config.settings import API_KEY


PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc"
}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in PUBLIC_PATHS:
            return await call_next(request)

        api_key = request.headers.get("x-api-key")

        if not api_key or api_key != API_KEY:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "API Key inválida o ausente"
                }
            )

        return await call_next(request)