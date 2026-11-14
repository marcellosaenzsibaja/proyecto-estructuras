import os
import random
import tempfile
import time
from src.estructuras_datos.agenda import Agenda, Evento
from src.estructuras_datos.cache_fichas import CacheFichas
from src.estructuras_datos.inventario import Inventario
from src.estructuras_datos.ordenamiento import insercion, mezcla, ordenar
from src.modelos.acciones import ESPERAR, Accion
from src.modelos.contenido import ContenidoSala, ProveedorContenido
from src.modelos.cripta import Cripta, DatosCripta, EstadisticasJugador
from src.modelos.entidades import Objeto, Sala
from src.modelos.fichas import ARMA, PERGAMINO, FichaObjeto
from src.modelos.partida import Partida
from src.servicios.guardado import cargar_binario, cargar_json, guardar_binario, guardar_json, tomar_snapshot

def _medir(funcion, *args, **kwargs):
    inicio = time.perf_counter()
    resultado = funcion(*args, **kwargs)
    return (time.perf_counter() - inicio, resultado)

class _ProveedorVacio(ProveedorContenido):

    def contenido_disponible(self, id_sala):
        return True

    def obtener_contenido(self, id_sala):
        return ContenidoSala()

    def ficha(self, id_ficha):
        raise KeyError(id_ficha)

def _cripta_minima() -> Cripta:
    datos = DatosCripta('bench', 'v1', 1, 1, 99, None, 50, 20, EstadisticasJugador(10000, 6, 2, 100))
    cripta = Cripta(datos)
    cripta.agregar_sala(Sala(1, 'Sala de pruebas'))
    return cripta

def medir_agenda(n: int=2000) -> dict:
    agenda = Agenda()
    azar = random.Random(1)
    eventos = [Evento(azar.randint(0, 10000), i, 'x') for i in range(n)]
    t_insertar, _ = _medir(lambda: [agenda.insertar(e) for e in eventos])
    t_extraer, _ = _medir(lambda: [agenda.extraer_minimo() for _ in range(n)])
    return {'n': n, 'segundos_insertar': t_insertar, 'segundos_extraer_en_orden': t_extraer}

def medir_cache_fichas(n: int=2000, capacidad: int=200) -> dict:
    cache = CacheFichas(capacidad)
    ficha = FichaObjeto('itm_x', ARMA, 'X', 1, 1, ataque_bonus=1)
    t_poner, _ = _medir(lambda: [cache.poner(f'itm_{i}', ficha) for i in range(n)])
    t_hit, _ = _medir(lambda: [cache.obtener(f'itm_{i}') for i in range(n - capacidad, n)])
    return {'n': n, 'capacidad': capacidad, 'segundos_poner': t_poner, 'segundos_obtener_hit': t_hit, 'desalojos': cache.desalojos}

def medir_inventario(n: int=2000) -> dict:
    inventario = Inventario(n)
    ficha = FichaObjeto('itm_x', ARMA, 'X', 1, 1, ataque_bonus=1)
    objetos = [Objeto(i, ficha) for i in range(n)]
    t_agregar, _ = _medir(lambda: [inventario.agregar(o) for o in objetos])
    inventario.ir_al_inicio()
    t_recorrido, _ = _medir(lambda: [inventario.avanzar() for _ in range(n - 1)])
    return {'n': n, 'segundos_agregar': t_agregar, 'segundos_recorrer_completo': t_recorrido}

def medir_historial(n: int=200) -> dict:
    partida = Partida(_cripta_minima(), _ProveedorVacio(), semilla=1)
    partida.iniciar()
    t_acciones, _ = _medir(lambda: [partida.ejecutar(Accion(ESPERAR)) for _ in range(n)])
    disponibles = partida.pergaminos_disponibles
    ficha_pergamino = FichaObjeto('itm_bench_perg', PERGAMINO, 'Pergamino', 1, 1)

    def _deshacer_todos():
        for _ in range(disponibles):
            partida.jugador.inventario.agregar(Objeto(-1, ficha_pergamino))
            partida._usar_pergamino()
    t_deshacer, _ = _medir(_deshacer_todos)
    return {'acciones': n, 'segundos_acciones': t_acciones, 'pergaminos_acumulados': disponibles, 'segundos_deshacer_todos': t_deshacer}

def medir_ordenamiento(n: int=5000) -> dict:
    azar = random.Random(3)
    desordenado = [azar.randint(0, n) for _ in range(n)]
    casi_ordenado = list(range(n))
    casi_ordenado[n // 2], casi_ordenado[n // 2 + 1] = (casi_ordenado[n // 2 + 1], casi_ordenado[n // 2])
    t_mezcla, _ = _medir(mezcla, desordenado)
    t_insercion, _ = _medir(insercion, desordenado)
    t_auto_desordenado, _ = _medir(ordenar, desordenado)
    t_auto_casi_ordenado, _ = _medir(ordenar, casi_ordenado)
    return {'n': n, 'segundos_mezcla_en_desorden': t_mezcla, 'segundos_insercion_en_desorden': t_insercion, 'segundos_automatico_en_desorden': t_auto_desordenado, 'segundos_automatico_casi_ordenado': t_auto_casi_ordenado}

def medir_guardado(acciones: int=50) -> dict:
    partida = Partida(_cripta_minima(), _ProveedorVacio(), semilla=1)
    partida.iniciar()
    for _ in range(acciones):
        partida.ejecutar(Accion(ESPERAR))
    snapshot = tomar_snapshot(partida)
    with tempfile.TemporaryDirectory() as carpeta:
        ruta_bin = os.path.join(carpeta, 'p.bin')
        ruta_json = os.path.join(carpeta, 'p.json')
        t_guardar_bin, _ = _medir(guardar_binario, snapshot, ruta_bin)
        t_guardar_json, _ = _medir(guardar_json, snapshot, ruta_json)
        t_cargar_bin, _ = _medir(cargar_binario, ruta_bin)
        t_cargar_json, _ = _medir(cargar_json, ruta_json)
        bytes_bin = os.path.getsize(ruta_bin)
        bytes_json = os.path.getsize(ruta_json)
    return {'segundos_guardar_binario': t_guardar_bin, 'segundos_guardar_json': t_guardar_json, 'segundos_cargar_binario': t_cargar_bin, 'segundos_cargar_json': t_cargar_json, 'bytes_binario': bytes_bin, 'bytes_json': bytes_json}

def ejecutar_todo(rapido: bool = False) -> dict:
    from src.servicios.banco_cazador import ejecutar_cazador
    resultados = {'agenda': medir_agenda(), 'cache_fichas': medir_cache_fichas(), 'inventario': medir_inventario(), 'historial': medir_historial(), 'ordenamiento': medir_ordenamiento(), 'guardado': medir_guardado()}
    # Segunda parte: terreno y cazador (specs/001-terreno-cazador, US5).
    resultados.update(ejecutar_cazador(rapido))
    return resultados

def formatear(resultados: dict) -> str:
    lineas = []
    for subsistema, metricas in resultados.items():
        lineas.append(f'[{subsistema}]')
        if isinstance(metricas, list):
            lineas.extend(_formatear_filas(metricas))
            continue
        for clave, valor in metricas.items():
            if isinstance(valor, float):
                lineas.append(f'  {clave}: {valor * 1000:.3f} ms')
            else:
                lineas.append(f'  {clave}: {valor}')
    return '\n'.join(lineas)


def _formatear_filas(filas: list) -> list:
    """Una línea por escenario con los campos del contrato de --bench."""
    lineas = []
    for fila in filas:
        partes = []
        for clave, valor in fila.items():
            if clave == 'escenario':
                continue
            if isinstance(valor, float):
                partes.append(f'{clave}={valor:.3f}')
            else:
                partes.append(f'{clave}={valor}')
        lineas.append(f"  {fila['escenario']}: " + ' '.join(partes))
    return lineas
