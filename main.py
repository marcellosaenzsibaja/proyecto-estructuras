import argparse
import random
import sys
from src.adaptadores.api_client import ApiClient
from src.adaptadores.errores import ErrorCliente
from src.adaptadores.fuente_sin_conexion import FuenteSinConexion
from src.controladores.controlador_juego import ControladorJuego
from src.estructuras_datos.cache_fichas import CAPACIDAD_POR_DEFECTO
from src.modelos.errores import ContenidoNoDisponible, ErrorDatos
from src.modelos.partida import EN_CURSO, Partida
from src.servicios import banco_pruebas
from src.servicios import bitacora as servicio_bitacora
from src.servicios import cache_persistente, guardado, puntajes
from src.servicios.cargador_cripta import cargar_datos, cargar_esqueleto
from src.servicios.proveedor_red import ProveedorRed
from src.vistas.vista_consola import VistaConsola

def leer_argumentos(argv):
    parser = argparse.ArgumentParser(description='Cripta')
    parser.add_argument('--cripta', help='id de la cripta a jugar')
    parser.add_argument('--semilla', type=int, help='semilla del generador aleatorio')
    parser.add_argument('--offline', metavar='CARPETA', help='jugar sin conexión leyendo de esta carpeta (generada antes con herramientas/exportar_offline.py)')
    parser.add_argument('--cache-size', type=int, default=CAPACIDAD_POR_DEFECTO, help='capacidad de la caché de fichas de catálogo')
    parser.add_argument('--cache-ruta', metavar='RUTA', default='cache_fichas.json', help='archivo donde persiste la caché de fichas de catálogo entre ejecuciones')
    parser.add_argument('--bitacora', metavar='RUTA', help='archivo donde grabar la bitácora de esta partida')
    parser.add_argument('--replay', metavar='RUTA', help='reproduce una bitácora grabada antes, sin interacción, y termina')
    parser.add_argument('--cargar', metavar='RUTA', help='retoma una partida guardada (.bin o .json)')
    parser.add_argument('--puntajes-ruta', metavar='RUTA', default=puntajes.RUTA_POR_DEFECTO, help='archivo de la tabla de puntajes')
    parser.add_argument('--bench', action='store_true', help='mide el desempeño de los subsistemas propios del proyecto y termina')
    return parser.parse_args(argv)

def _fuente(args):
    if args.offline:
        return FuenteSinConexion(args.offline)
    return ApiClient()

def _preparar_cripta(args, cliente, vista, id_cripta=None):
    if id_cripta is None:
        id_cripta = args.cripta
    if id_cripta is None:
        id_cripta = vista.seleccionar_cripta(cliente.obtener_criptas()['criptas'])
    datos = cargar_datos(cliente, id_cripta)
    cripta = cargar_esqueleto(cliente, datos)
    version_catalogo = cliente.obtener_version_catalogo()['version']
    cache = cache_persistente.cargar_cache(args.cache_ruta, version_catalogo, args.cache_size)
    proveedor = ProveedorRed(cliente, cripta, cache)
    return (cripta, proveedor, cache, version_catalogo)

def _mostrar_solicitudes(cliente, cache=None):
    if hasattr(cliente, 'solicitudes_realizadas'):
        presupuesto = cliente.presupuesto if cliente.presupuesto is not None else '?'
        print(f'\nSolicitudes realizadas: {cliente.solicitudes_realizadas} de {presupuesto}')
    if cache is not None:
        print(f'Caché de fichas: {cache.aciertos} aciertos, {cache.fallos} fallos, {cache.desalojos} desalojos ({len(cache)}/{cache.capacidad} en memoria)')

def _ejecutar_replay(args, vista) -> int:
    encabezado, _ = servicio_bitacora.leer(args.replay)
    cliente = _fuente(args)
    cache = None
    try:
        cripta, proveedor, cache, version_catalogo = _preparar_cripta(args, cliente, vista, id_cripta=encabezado['cripta_id'])

        def _mostrar_paso(partida, accion, resultado):
            vista.mostrar_mensaje(f'[{partida.reloj.tiempo_virtual}] {accion.tipo} {accion.argumento} -> {resultado.estado}')
        partida = servicio_bitacora.reproducir(args.replay, cripta, proveedor, version_catalogo=version_catalogo, en_cada_paso=_mostrar_paso)
        vista.mostrar_final(partida, abandonada=partida.estado == EN_CURSO)
        cache_persistente.guardar_cache(cache, args.cache_ruta, version_catalogo)
    finally:
        _mostrar_solicitudes(cliente, cache)
    return 0

def _ejecutar_partida(args, vista) -> int:
    cliente = _fuente(args)
    cache = None
    try:
        cripta, proveedor, cache, version_catalogo = _preparar_cripta(args, cliente, vista)
        if args.cargar:
            cargador = guardado.cargar_json if args.cargar.endswith('.json') else guardado.cargar_binario
            partida = guardado.restaurar_partida(cargador(args.cargar), cripta, proveedor)
        else:
            semilla = args.semilla
            if semilla is None:
                semilla = random.SystemRandom().randrange(2 ** 32)
            partida = Partida(cripta, proveedor, semilla)
        bitacora = servicio_bitacora.Bitacora(args.bitacora or 'bitacora.log')
        if not args.cargar:
            bitacora.iniciar(cripta.datos.id, cripta.datos.version, partida.semilla, version_catalogo)
        try:
            ControladorJuego(partida, vista, bitacora=bitacora, ruta_puntajes=args.puntajes_ruta).ejecutar()
        finally:
            bitacora.cerrar()
            cache_persistente.guardar_cache(cache, args.cache_ruta, version_catalogo)
    finally:
        _mostrar_solicitudes(cliente, cache)
    return 0

def main(argv=None) -> int:
    args = leer_argumentos(argv)
    if args.bench:
        print(banco_pruebas.formatear(banco_pruebas.ejecutar_todo()))
        return 0
    vista = VistaConsola()
    try:
        if args.replay:
            return _ejecutar_replay(args, vista)
        return _ejecutar_partida(args, vista)
    except (ErrorCliente, ErrorDatos, ContenidoNoDisponible) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
if __name__ == '__main__':
    sys.exit(main())
