import requests
from config.settings import API_URL


class ApiClient:

    @staticmethod
    def resumen(usuario_id):
        r = requests.get(f"{API_URL}/usuarios/{usuario_id}/resumen")
        r.raise_for_status()
        return r.json()

    
    @staticmethod
    def gastos(usuario_id, pagina=1):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/gastos",
            params={"pagina": pagina}
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def categorias():
        r = requests.get(f"{API_URL}/categorias")
        r.raise_for_status()
        return r.json()

    @staticmethod
    def configuracion(usuario_id):
        r = requests.get(f"{API_URL}/usuarios/{usuario_id}/config")
        r.raise_for_status()
        return r.json()

    @staticmethod
    def registrar_gasto(usuario_id, monto, categoria, descripcion, fecha=None):
        r = requests.post(
            f"{API_URL}/movimientos/gasto",
            json={
                "usuario_id": usuario_id,
                "monto": monto,
                "categoria": categoria,
                "descripcion": descripcion,
                "fecha": fecha
            }
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def registrar_ingreso(usuario_id, monto, categoria, descripcion, fecha=None):
        r = requests.post(
            f"{API_URL}/movimientos/ingreso",
            json={
                "usuario_id": usuario_id,
                "monto": monto,
                "categoria": categoria,
                "descripcion": descripcion,
                "fecha": fecha
            }
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    def borrar_ultimo(usuario_id):
        r = requests.post(
            f"{API_URL}/usuarios/{usuario_id}/movimientos/borrar-ultimo"
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
            }
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
            }
        )
        r.raise_for_status()
        return r.json()
    
    @staticmethod
    def total_categoria(usuario_id, categoria):
        r = requests.get(
            f"{API_URL}/usuarios/{usuario_id}/gastos/categoria/{categoria}"
        )
        r.raise_for_status()
        return r.json()
    
    