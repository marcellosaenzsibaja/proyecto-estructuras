import json
import os
from src.estructuras_datos.cache_fichas import CacheFichas
from src.modelos.errores import ErrorDatos
from src.servicios.fabrica_fichas import dict_desde_ficha, ficha_desde_dict

def guardar_cache(cache: CacheFichas, ruta: str, version_catalogo: str):
    datos = {'version_catalogo': version_catalogo, 'fichas': [dict_desde_ficha(ficha) for _, ficha in cache.entradas_en_orden_de_uso()]}
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    temporal = f'{ruta}.tmp'
    with open(temporal, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False)
    os.replace(temporal, ruta)

def cargar_cache(ruta: str, version_catalogo: str, capacidad: int) -> CacheFichas:
    cache = CacheFichas(capacidad)
    if not os.path.isfile(ruta):
        return cache
    try:
        with open(ruta, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
    except (OSError, ValueError):
        return cache
    if not isinstance(datos, dict) or datos.get('version_catalogo') != version_catalogo:
        return cache
    fichas = datos.get('fichas')
    if not isinstance(fichas, list):
        return cache
    for crudo in reversed(fichas):
        try:
            ficha = ficha_desde_dict(crudo)
        except ErrorDatos:
            continue
        cache.poner(ficha.id, ficha)
    return cache
