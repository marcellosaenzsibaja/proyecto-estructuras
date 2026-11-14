import json
import os
from src.modelos.acciones import Accion
from src.modelos.errores import ErrorDatos

class Bitacora:

    def __init__(self, ruta: str):
        self.ruta = ruta
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        self._archivo = open(ruta, 'a', encoding='utf-8')

    def iniciar(self, cripta_id: str, version_cripta: str, semilla: int, version_catalogo=None):
        self._escribir({'tipo': 'encabezado', 'cripta_id': cripta_id, 'version_cripta': version_cripta, 'version_catalogo': version_catalogo, 'semilla': semilla})

    def registrar(self, accion: Accion):
        self._escribir({'tipo': accion.tipo, 'argumento': accion.argumento})

    def _escribir(self, registro: dict):
        self._archivo.write(json.dumps(registro, ensure_ascii=False) + '\n')
        self._archivo.flush()

    def cerrar(self):
        self._archivo.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.cerrar()

def leer(ruta: str):
    try:
        with open(ruta, 'r', encoding='utf-8') as archivo:
            lineas = [json.loads(linea) for linea in archivo if linea.strip()]
    except (OSError, ValueError) as error:
        raise ErrorDatos(f"No se pudo leer la bitácora '{ruta}': {error}") from error
    if not lineas or lineas[0].get('tipo') != 'encabezado':
        raise ErrorDatos(f'Bitácora inválida o sin encabezado: {ruta}')
    encabezado = lineas[0]
    acciones = [Accion(linea['tipo'], linea.get('argumento')) for linea in lineas[1:]]
    return (encabezado, acciones)

def verificar_version(encabezado: dict, cripta, version_catalogo=None):
    if encabezado.get('cripta_id') != cripta.datos.id or encabezado.get('version_cripta') != cripta.datos.version:
        raise ErrorDatos(f"La bitácora no es compatible con esta cripta (esperaba {cripta.datos.id}@{cripta.datos.version}, la bitácora es de {encabezado.get('cripta_id')}@{encabezado.get('version_cripta')})")
    registrada = encabezado.get('version_catalogo')
    if version_catalogo is not None and registrada is not None and (registrada != version_catalogo):
        raise ErrorDatos(f"La bitácora no es compatible: fue grabada con la versión de catálogo '{registrada}', y la disponible ahora es '{version_catalogo}'. No se puede garantizar una reproducción fiel.")

def reproducir(ruta: str, cripta, proveedor, version_catalogo=None, en_cada_paso=None):
    from src.modelos.partida import EN_CURSO, Partida
    encabezado, acciones = leer(ruta)
    verificar_version(encabezado, cripta, version_catalogo)
    partida = Partida(cripta, proveedor, encabezado['semilla'])
    partida.iniciar()
    for accion in acciones:
        if partida.estado != EN_CURSO:
            break
        resultado = partida.ejecutar(accion)
        if en_cada_paso is not None:
            en_cada_paso(partida, accion, resultado)
    return partida
