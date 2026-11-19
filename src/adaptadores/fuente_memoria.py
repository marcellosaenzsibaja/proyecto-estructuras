"""Fuente de datos en memoria para criptas sintéticas (pruebas y --bench).

Implementa la misma interfaz que el cliente de red y que el modo --offline
(P1 §3.4). Guarda las respuestas como texto JSON y las lee con json.loads en
cada solicitud, de modo que el modelo recibe exactamente lo mismo que recibiría
del servicio. Los diccionarios que devuelve son solo el producto de esa
lectura (constitución, Principio I).
"""
import json

from src.adaptadores.errores import ErrorCliente
from src.adaptadores.fuente_datos import FuenteDatos

LIMITE_LOTE = 10


class FuenteMemoria(FuenteDatos):

    def __init__(self, id_cripta: str, texto_datos: str, paginas: list, textos_contenido=None, textos_catalogo=None, version_catalogo='cat-sintetico', texto_llaves=None):
        self.id_cripta = id_cripta
        self._texto_datos = texto_datos
        self._paginas = list(paginas)
        # Contenido por id de sala: lista indexada por id (posición 0 sin uso).
        self._contenido = list(textos_contenido) if textos_contenido is not None else []
        # Catálogo: lista de pares (id, texto); se recorre linealmente.
        self._catalogo = list(textos_catalogo) if textos_catalogo is not None else []
        self._version_catalogo = version_catalogo
        self._texto_llaves = texto_llaves if texto_llaves is not None else '{"llaves": []}'
        self.solicitudes_realizadas = 0
        self.presupuesto = None

    def establecer_presupuesto(self, presupuesto: int):
        self.presupuesto = presupuesto

    def _leer(self, texto: str, operacion: str):
        self.solicitudes_realizadas += 1
        try:
            return json.loads(texto)
        except ValueError as error:
            raise ErrorCliente(f'Texto JSON inválido en la fuente en memoria ({operacion}): {error}') from error

    def _verificar_cripta(self, cripta_id: str):
        if cripta_id != self.id_cripta:
            raise ErrorCliente(f"La fuente en memoria no tiene la cripta '{cripta_id}'")

    def obtener_criptas(self) -> dict:
        texto = '{"criptas": [{"id": ' + json.dumps(self.id_cripta) + ', "nombre": "Cripta sintética", "salas": 0, "dificultad": 0}]}'
        return self._leer(texto, 'listar criptas')

    def obtener_datos_cripta(self, cripta_id: str) -> dict:
        self._verificar_cripta(cripta_id)
        datos = self._leer(self._texto_datos, f'datos generales de {cripta_id}')
        if 'presupuesto_solicitudes' in datos:
            self.establecer_presupuesto(datos['presupuesto_solicitudes'])
        return datos

    def obtener_esqueleto(self, cripta_id: str, pagina: int = 1) -> dict:
        self._verificar_cripta(cripta_id)
        if pagina < 1 or pagina > len(self._paginas):
            raise ErrorCliente(f'La cripta {cripta_id} no tiene la página {pagina}')
        return self._leer(self._paginas[pagina - 1], f'esqueleto de {cripta_id} página {pagina}')

    def obtener_contenido_lote(self, cripta_id: str, ids_salas: list) -> dict:
        self._verificar_cripta(cripta_id)
        if not ids_salas or len(ids_salas) > LIMITE_LOTE:
            raise ValueError(f'El contenido se solicita por lotes de 1 a {LIMITE_LOTE} salas')
        partes = []
        for id_sala in ids_salas:
            if 0 < id_sala < len(self._contenido) and self._contenido[id_sala] is not None:
                partes.append(self._contenido[id_sala])
            else:
                partes.append('{"sala": ' + json.dumps(id_sala) + ', "enemigos": [], "objetos": [], "trampas": []}')
        return self._leer('{"contenido": [' + ', '.join(partes) + ']}', f'contenido de {cripta_id}')

    def obtener_catalogo_lote(self, ids_entidades: list) -> dict:
        if not ids_entidades or len(ids_entidades) > LIMITE_LOTE:
            raise ValueError(f'El catálogo se solicita por lotes de 1 a {LIMITE_LOTE} ids')
        partes = []
        for id_entidad in ids_entidades:
            encontrada = None
            for id_ficha, texto in self._catalogo:
                if id_ficha == id_entidad:
                    encontrada = texto
                    break
            if encontrada is None:
                raise ErrorCliente(f"La fuente en memoria no tiene la ficha '{id_entidad}'")
            partes.append(encontrada)
        return self._leer('{"entidades": [' + ', '.join(partes) + ']}', 'catálogo')

    def obtener_version_cripta(self, cripta_id: str) -> dict:
        self._verificar_cripta(cripta_id)
        datos = json.loads(self._texto_datos)
        return self._leer('{"id": ' + json.dumps(cripta_id) + ', "version": ' + json.dumps(datos['version']) + '}', f'versión de {cripta_id}')

    def obtener_version_catalogo(self) -> dict:
        return self._leer('{"version": ' + json.dumps(self._version_catalogo) + '}', 'versión del catálogo')

    def obtener_llaves(self, cripta_id: str) -> dict:
        self._verificar_cripta(cripta_id)
        return self._leer(self._texto_llaves, f'llaves de {cripta_id}')
