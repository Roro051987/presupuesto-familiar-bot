import requests
from config.settings import API_URL, API_KEY


def headers():
    return {
        "x-api-key": API_KEY
    }


class ApiClient:

    @staticmethod
    def resumen(usuario_id):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/resumen",
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def gastos(usuario_id, pagina=1):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/gastos",
            params={"pagina": pagina},
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def ingresos(usuario_id, pagina=1):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/ingresos",
            params={"pagina": pagina},
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def categorias():
        r = requests.get(
            f"{API_URL}/categorias",
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def configuracion(usuario_id):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/config",
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def total_categoria(usuario_id, categoria):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/gastos/categoria/{categoria}",
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def registrar_gasto(
        usuario_id,
        monto,
        categoria,
        descripcion,
        fecha=None,
        force=False
    ):
        r = requests.post(
            f"{API_URL}/movimientos/gasto",
            json={
                "usuario_id": usuario_id,
                "monto": monto,
                "categoria": categoria,
                "descripcion": descripcion,
                "fecha": fecha,
                "force": force
            },
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def registrar_ingreso(
        usuario_id,
        monto,
        categoria,
        descripcion,
        fecha=None,
        force=False
    ):
        r = requests.post(
            f"{API_URL}/movimientos/ingreso",
            json={
                "usuario_id": usuario_id,
                "monto": monto,
                "categoria": categoria,
                "descripcion": descripcion,
                "fecha": fecha,
                "force": force
            },
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def borrar_ultimo(usuario_id):
        r = requests.post(
            f"{API_URL}/usuarios/{usuario_id}/movimientos/borrar-ultimo",
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def eliminar_movimiento(usuario_id, movimiento_id):
        r = requests.delete(
            f"{API_URL}/usuarios/{usuario_id}/movimientos/{movimiento_id}",
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def editar_movimiento(
        usuario_id,
        movimiento_id,
        monto=None,
        categoria=None,
        descripcion=None,
        fecha=None
    ):
        payload = {}

        if monto is not None:
            payload["monto"] = monto

        if categoria is not None:
            payload["categoria"] = categoria

        if descripcion is not None:
            payload["descripcion"] = descripcion

        if fecha is not None:
            payload["fecha"] = fecha

        r = requests.patch(
            f"{API_URL}/usuarios/{usuario_id}/movimientos/{movimiento_id}",
            json=payload,
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def cambiar_fecha_corte(usuario_id, dia):
        r = requests.post(
            f"{API_URL}/usuarios/config/fecha-corte",
            json={
                "usuario_id": usuario_id,
                "dia": dia
            },
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def aprender_categoria(usuario_id, alias, categoria):
        r = requests.post(
            f"{API_URL}/usuarios/categorias/aprender",
            json={
                "usuario_id": usuario_id,
                "alias": alias,
                "categoria": categoria
            },
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def crear_categoria(usuario_id, nombre, tipo="gasto"):
        r = requests.post(
            f"{API_URL}/usuarios/{usuario_id}/categorias",
            json={
                "nombre": nombre,
                "tipo": tipo
            },
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def configurar_ingreso_mensual(usuario_id, ingreso_mensual):
        r = requests.patch(
            f"{API_URL}/usuarios/{usuario_id}/config/ingreso-mensual",
            json={
                "ingreso_mensual": ingreso_mensual
            },
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def configurar_presupuesto_categoria(usuario_id, categoria, monto):
        r = requests.post(
            f"{API_URL}/usuarios/{usuario_id}/presupuestos/categoria",
            json={
                "categoria": categoria,
                "monto": monto
            },
            headers=headers()
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def presupuestos_categoria(usuario_id):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/presupuestos/categorias",
            headers=headers()
        )
        r.raise_for_status()
        return r.json()