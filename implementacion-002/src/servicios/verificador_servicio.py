import json
import os

from src.modelos.errores import ErrorDatos
from src.modelos.resolubilidad import LlaveInfo, verificar

CARPETA_CACHE = 'cache'


def interpretar_llaves(crudo) -> list:
    if not isinstance(crudo, dict) or 'llaves' not in crudo or not isinstance(crudo['llaves'], list):
        raise ErrorDatos("Ubicación de llaves: falta el campo 'llaves'")
    llaves = []
    for item in crudo['llaves']:
        if not isinstance(item, dict) or 'id' not in item or 'sala' not in item:
            raise ErrorDatos("Ubicación de llaves: cada llave requiere los campos 'id' y 'sala'")
        llaves.append(LlaveInfo(item['id'], item['sala'], item.get('enemigo')))
    return llaves


def texto_cache(id_cripta: str, version: str, llaves: list) -> str:
    partes = []
    for llave in llaves:
        texto = '{"id": ' + json.dumps(llave.id) + ', "sala": ' + json.dumps(llave.sala)
        if llave.enemigo is not None:
            texto += ', "enemigo": ' + json.dumps(llave.enemigo)
        partes.append(texto + '}')
    return ('{"cripta": ' + json.dumps(id_cripta) + ', "version": ' + json.dumps(version)
            + ', "llaves": [' + ', '.join(partes) + ']}')


def ruta_cache(carpeta: str, id_cripta: str) -> str:
    return os.path.join(carpeta, f'llaves_{id_cripta}.json')


def _leer_cache(ruta: str, id_cripta: str, version: str):
    if not os.path.isfile(ruta):
        return None
    try:
        with open(ruta, 'r', encoding='utf-8') as archivo:
            crudo = json.load(archivo)
        if crudo['cripta'] != id_cripta or crudo['version'] != version:
            return None
        return interpretar_llaves(crudo)
    except (OSError, ValueError, KeyError, TypeError, ErrorDatos):
        return None


def _guardar_cache(ruta: str, texto: str):
    try:
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as archivo:
            archivo.write(texto)
    except OSError:
        pass


def cargar_llaves(fuente, datos, carpeta: str = CARPETA_CACHE) -> list:
    ruta = ruta_cache(carpeta, datos.id)
    guardadas = _leer_cache(ruta, datos.id, datos.version)
    if guardadas is not None:
        return guardadas
    llaves = interpretar_llaves(fuente.obtener_llaves(datos.id))
    _guardar_cache(ruta, texto_cache(datos.id, datos.version, llaves))
    return llaves


def verificar_cripta(fuente, cripta, carpeta: str = CARPETA_CACHE):
    return verificar(cripta, cargar_llaves(fuente, cripta.datos, carpeta))
