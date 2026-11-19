import time
import uuid
import requests
from src.adaptadores.errores import ErrorCliente, PresupuestoAgotado
from src.adaptadores.fuente_datos import FuenteDatos
LIMITE_LOTE = 10
TIMEOUT_SEGUNDOS = 10

class ApiClient(FuenteDatos):
    base_url = 'https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1'

    def __init__(self, base_url: str=None, esperar=time.sleep):
        if base_url is not None:
            self.base_url = base_url
        self._esperar = esperar
        self.client_id = str(uuid.uuid4())
        self.headers = {'X-Cripta-Client-Id': self.client_id}
        self.solicitudes_realizadas = 0
        self.presupuesto = None

    @property
    def solicitudes_restantes(self):
        if self.presupuesto is None:
            return None
        return self.presupuesto - self.solicitudes_realizadas

    def establecer_presupuesto(self, presupuesto: int):
        self.presupuesto = presupuesto

    def _reservar_solicitud(self, operacion: str):
        if self.presupuesto is not None and self.solicitudes_realizadas >= self.presupuesto:
            raise PresupuestoAgotado(f"Presupuesto de solicitudes agotado ({self.presupuesto}) antes de ejecutar '{operacion}'")
        self.solicitudes_realizadas += 1

    def _cuerpo_json(self, respuesta, operacion: str):
        try:
            return respuesta.json()
        except ValueError as e:
            raise ErrorCliente(f"Respuesta no válida (JSON) en '{operacion}': {e}") from e

    def _segundos_reintento(self, respuesta, operacion: str):
        cuerpo = self._cuerpo_json(respuesta, operacion)
        try:
            segundos = cuerpo['reintentar_en']
        except (KeyError, TypeError) as e:
            raise ErrorCliente(f"HTTP 429 sin 'reintentar_en' en '{operacion}': {respuesta.text}") from e
        if isinstance(segundos, bool) or not isinstance(segundos, (int, float)) or segundos < 0:
            raise ErrorCliente(f"HTTP 429 con 'reintentar_en' inválido en '{operacion}': {segundos!r}")
        return segundos

    def _get(self, endpoint: str, operacion: str, params: dict=None) -> dict:
        url = f'{self.base_url}{endpoint}'
        while True:
            self._reservar_solicitud(operacion)
            try:
                respuesta = requests.get(url, headers=self.headers, params=params, timeout=TIMEOUT_SEGUNDOS)
            except requests.RequestException as e:
                raise ErrorCliente(f"Fallo de red en '{operacion}' ({endpoint}): {e}") from e
            if respuesta.status_code == 200:
                return self._cuerpo_json(respuesta, operacion)
            if respuesta.status_code == 429:
                self._esperar(self._segundos_reintento(respuesta, operacion))
                continue
            raise ErrorCliente(f"Error HTTP {respuesta.status_code} en '{operacion}' ({endpoint}): {respuesta.text}")

    def obtener_criptas(self) -> dict:
        return self._get('/criptas', 'listar criptas')

    def obtener_datos_cripta(self, cripta_id: str) -> dict:
        datos = self._get(f'/criptas/{cripta_id}', f'datos generales de {cripta_id}')
        if isinstance(datos, dict) and 'presupuesto_solicitudes' in datos:
            self.establecer_presupuesto(datos['presupuesto_solicitudes'])
        return datos

    def obtener_esqueleto(self, cripta_id: str, pagina: int=1) -> dict:
        return self._get(f'/criptas/{cripta_id}/salas', f'esqueleto de {cripta_id} página {pagina}', params={'pagina': pagina})

    def obtener_contenido_lote(self, cripta_id: str, ids_salas: list[int]) -> dict:
        if not ids_salas or len(ids_salas) > LIMITE_LOTE:
            raise ValueError(f'El contenido se solicita por lotes de 1 a {LIMITE_LOTE} salas')
        return self._get(f'/criptas/{cripta_id}/contenido', f'contenido de salas {list(ids_salas)} en {cripta_id}', params={'salas': ','.join((str(i) for i in ids_salas))})

    def obtener_catalogo_lote(self, ids_entidades: list[str]) -> dict:
        if not ids_entidades or len(ids_entidades) > LIMITE_LOTE:
            raise ValueError(f'El catálogo se solicita por lotes de 1 a {LIMITE_LOTE} ids')
        return self._get('/catalogo', f'catálogo {list(ids_entidades)}', params={'ids': ','.join((str(i) for i in ids_entidades))})

    def obtener_version_cripta(self, cripta_id: str) -> dict:
        return self._get(f'/criptas/{cripta_id}/version', f'versión de {cripta_id}')

    def obtener_version_catalogo(self) -> dict:
        return self._get('/catalogo/version', 'versión del catálogo')

    def obtener_llaves(self, cripta_id: str) -> dict:
        return self._get(f'/criptas/{cripta_id}/llaves', f'llaves de {cripta_id}')
