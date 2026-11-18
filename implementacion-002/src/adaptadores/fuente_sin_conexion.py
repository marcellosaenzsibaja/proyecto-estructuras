import json
import os
from src.adaptadores.errores import ErrorCliente
from src.adaptadores.fuente_datos import FuenteDatos
LIMITE_LOTE = 10

class FuenteSinConexion(FuenteDatos):

    def __init__(self, carpeta: str):
        if not os.path.isdir(carpeta):
            raise ErrorCliente(f"No existe la carpeta de datos sin conexión '{carpeta}'")
        self.carpeta = carpeta
        self.solicitudes_realizadas = 0
        self.presupuesto = None

    def establecer_presupuesto(self, presupuesto: int):
        self.presupuesto = presupuesto

    def _leer(self, partes, operacion: str) -> dict:
        ruta = os.path.join(self.carpeta, *partes)
        if not os.path.isfile(ruta):
            raise ErrorCliente(f"Falta el archivo sin conexión para '{operacion}': {ruta}")
        try:
            with open(ruta, 'r', encoding='utf-8') as archivo:
                self.solicitudes_realizadas += 1
                return json.load(archivo)
        except (OSError, ValueError) as error:
            raise ErrorCliente(f"No se pudo leer '{ruta}' ({operacion}): {error}") from error

    def obtener_criptas(self) -> dict:
        return self._leer(('criptas.json',), 'listar criptas')

    def obtener_datos_cripta(self, cripta_id: str) -> dict:
        datos = self._leer((cripta_id, 'datos_generales.json'), f'datos generales de {cripta_id}')
        if isinstance(datos, dict) and 'presupuesto_solicitudes' in datos:
            self.establecer_presupuesto(datos['presupuesto_solicitudes'])
        return datos

    def obtener_esqueleto(self, cripta_id: str, pagina: int=1) -> dict:
        return self._leer((cripta_id, 'esqueleto', f'pagina_{pagina}.json'), f'esqueleto de {cripta_id} página {pagina}')

    def obtener_contenido_lote(self, cripta_id: str, ids_salas: list) -> dict:
        if not ids_salas or len(ids_salas) > LIMITE_LOTE:
            raise ValueError(f'El contenido se solicita por lotes de 1 a {LIMITE_LOTE} salas')
        contenido = [self._leer((cripta_id, 'salas', f'{id_sala}.json'), f'contenido de la sala {id_sala} en {cripta_id}') for id_sala in ids_salas]
        return {'contenido': contenido}

    def obtener_catalogo_lote(self, ids_entidades: list) -> dict:
        if not ids_entidades or len(ids_entidades) > LIMITE_LOTE:
            raise ValueError(f'El catálogo se solicita por lotes de 1 a {LIMITE_LOTE} ids')
        entidades = [self._leer(('catalogo', 'entidades', f'{id_entidad}.json'), f"ficha de catálogo '{id_entidad}'") for id_entidad in ids_entidades]
        return {'entidades': entidades}

    def obtener_version_cripta(self, cripta_id: str) -> dict:
        return self._leer((cripta_id, 'version.json'), f'versión de {cripta_id}')

    def obtener_version_catalogo(self) -> dict:
        return self._leer(('catalogo', 'version.json'), 'versión del catálogo')

    def obtener_llaves(self, cripta_id: str) -> dict:
        return self._leer((cripta_id, 'llaves.json'), f'llaves de {cripta_id}')
