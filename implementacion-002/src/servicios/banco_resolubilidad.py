import random
import time

from src.estructuras_datos.busqueda_binaria import buscar
from src.modelos.resolubilidad import _alcanza_salida, _indexar_llaves, _llave_de_puerta, verificar
from src.servicios import generador_criptas as gc
from src.servicios.verificador_servicio import interpretar_llaves

LIMITE_MS = 200
SALAS_REFERENCIA = 1000


def _ahora():
    return time.perf_counter()


def _construir(texto_salas, ids_inicio, sala_salida, llave_salida, llaves):
    fuente = gc.fuente_sintetica(texto_salas, sala_inicial=ids_inicio, sala_salida=sala_salida, llave_salida=llave_salida,
                                 texto_llaves=gc.texto_llaves(llaves))
    cripta = gc.cargar_cripta_sintetica(fuente)
    return cripta, interpretar_llaves(fuente.obtener_llaves(fuente.id_cripta))


def cripta_cadena(semilla: int, salas: int, cantidad_llaves: int):
    if cantidad_llaves < 1 or cantidad_llaves > salas - 2:
        raise ValueError('La cadena necesita entre 1 y salas - 2 llaves')
    ids = gc._permutacion(random.Random(semilla), salas)
    paso = (salas - 1) // cantidad_llaves
    puerta_en = [None] * salas
    llaves = []
    for i in range(cantidad_llaves):
        posicion = i * paso
        nombre = f'itm_llave_cad_{i:04d}'
        puerta_en[posicion] = nombre
        llaves.append((nombre, ids[posicion]))
    textos = []
    for p in range(salas):
        salidas = []
        if p > 0:
            salidas.append((gc.OESTE, ids[p - 1], None, puerta_en[p - 1] is not None, puerta_en[p - 1]))
        if p < salas - 1:
            salidas.append((gc.ESTE, ids[p + 1], None, puerta_en[p] is not None, puerta_en[p]))
        textos.append(gc.texto_sala(ids[p], salidas))
    ultima = (cantidad_llaves - 1) * paso
    return _construir(textos, ids[0], ids[ultima + 1], f'itm_llave_cad_{cantidad_llaves - 1:04d}', llaves)


def cripta_cuadricula(semilla: int, ancho: int, alto: int, prob_cerrada: float = 0.2):
    g = gc.generar(semilla, ancho, alto, prob_cerrada=prob_cerrada)
    rng = random.Random(semilla + 7)
    llaves = []
    for c in range(2 * g.n):
        if g.existe[c] and g.cerrada[c]:
            llaves.append((f'itm_llave_sint_{c}', rng.randrange(1, g.n + 1)))
    return _construir(gc.fragmentos(g), 1, g.n, 'itm_llave_salida_sint', llaves)


def verificar_ingenuo(cripta, llaves):
    n = len(cripta)
    por_indice = [None] * n
    for sala in cripta.salas():
        por_indice[sala.indice] = sala
    ordenadas, ids, en_sala = _indexar_llaves(cripta, llaves)
    m = len(ordenadas)
    obtenida = [False] * m
    orden = []
    inicio = cripta.sala(cripta.datos.sala_inicial).indice
    while True:
        visitada = [False] * n
        visitada[inicio] = True
        cola = [inicio]
        cabeza = 0
        mejor = -1
        while cabeza < len(cola):
            u = cola[cabeza]
            cabeza += 1
            if en_sala[u] is not None:
                for j in en_sala[u]:
                    if not obtenida[j] and (mejor < 0 or j < mejor):
                        mejor = j
            for salida in por_indice[u].salidas:
                if salida is None:
                    continue
                v = salida.sala_destino.indice
                if visitada[v]:
                    continue
                puerta = salida.puerta
                if puerta.cerrada:
                    j = _llave_de_puerta(ids, puerta)
                    if j < 0 or not obtenida[j]:
                        continue
                visitada[v] = True
                cola.append(v)
        if mejor < 0:
            return [ordenadas[j].id for j in orden], _alcanza_salida(cripta, ids, obtenida, visitada)
        obtenida[mejor] = True
        orden.append(mejor)


def _tiempo(funcion, repeticiones):
    mejor = None
    resultado = None
    for _ in range(repeticiones):
        inicio = _ahora()
        resultado = funcion()
        duracion = (_ahora() - inicio) * 1000
        if mejor is None or duracion < mejor:
            mejor = duracion
    return mejor, resultado


def _fila(escenario, semilla, salas, llaves, ms_reactivo, ms_ingenuo, mismo_orden, resoluble):
    fila = {'escenario': escenario, 'semilla': semilla, 'salas': salas, 'llaves': llaves,
            'ms_reactivo': round(ms_reactivo, 3), 'ms_ingenuo': round(ms_ingenuo, 3) if ms_ingenuo is not None else 'n/a',
            'resoluble': 'si' if resoluble else 'no'}
    if mismo_orden is not None:
        fila['mismo_orden'] = 'si' if mismo_orden else 'NO'
    if salas >= SALAS_REFERENCIA:
        fila['limite_ms'] = LIMITE_MS
        fila['resultado'] = 'CUMPLE' if ms_reactivo < LIMITE_MS else 'NO CUMPLE'
    return fila


def medir_cadenas(semilla=2026, salas=SALAS_REFERENCIA, cantidades=(10, 25, 50, 100, 500), repeticiones=3) -> list:
    filas = []
    for cantidad in cantidades:
        cripta, llaves = cripta_cadena(semilla, salas, cantidad)
        ms_reactivo, reporte = _tiempo(lambda: verificar(cripta, llaves), repeticiones)
        ms_ingenuo, ingenuo = _tiempo(lambda: verificar_ingenuo(cripta, llaves), 1)
        filas.append(_fila(f'cadena_{cantidad}_llaves', semilla, salas, cantidad, ms_reactivo, ms_ingenuo,
                           reporte.orden_llaves == ingenuo[0] and reporte.resoluble == ingenuo[1], reporte.resoluble))
    return filas


def medir_cuadricula(semilla=2026, ancho=25, alto=40, repeticiones=3) -> list:
    cripta, llaves = cripta_cuadricula(semilla, ancho, alto)
    ms_reactivo, reporte = _tiempo(lambda: verificar(cripta, llaves), repeticiones)
    ms_ingenuo, ingenuo = _tiempo(lambda: verificar_ingenuo(cripta, llaves), 1)
    return [_fila('cuadricula_con_llaves', semilla, ancho * alto, len(llaves), ms_reactivo, ms_ingenuo,
                  reporte.orden_llaves == ingenuo[0] and reporte.resoluble == ingenuo[1], reporte.resoluble)]


def medir_determinismo(semilla=2026) -> list:
    a = cripta_cadena(semilla, 200, 20)
    b = cripta_cadena(semilla, 200, 20)
    ordenes = [verificar(a[0], a[1]).orden_llaves, verificar(b[0], b[1]).orden_llaves]
    return [_fila('determinismo_resolubilidad', semilla, 200, 20, 0.0, None, ordenes[0] == ordenes[1], True)]


def ejecutar_resolubilidad(rapido: bool = False) -> dict:
    if rapido:
        filas = medir_cadenas(salas=120, cantidades=(5, 10, 20), repeticiones=1) + medir_cuadricula(ancho=10, alto=10, repeticiones=1)
    else:
        filas = medir_cadenas() + medir_cuadricula()
    return {'resolubilidad': filas, 'resolubilidad_determinismo': medir_determinismo()}
