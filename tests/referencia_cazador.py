"""T025: referencia teórica de la decisión del cazador, independiente del juego.

Deliberadamente simple y sin compartir código con src/modelos/rutas.py,
src/modelos/cazador.py ni src/estructuras_datos/monticulo.py:

- dist_referencia: búsqueda de costo mínimo SIN cota y SIN reutilización, que en
  cada paso escoge la sala pendiente de menor costo recorriendo linealmente los
  ids 1..n (O(n²), sin montículo); distancias y marcas en listas indexadas por
  id (G5); solo puertas abiertas en ese instante; solo enteros (D1); salidas en
  orden N, S, E, O (D2).
- decision_referencia: aplica la regla del enunciado (P2 §3.2) literalmente,
  calculando la distancia DESDE CADA VECINA por separado y eligiendo con la
  clave D4: (costo(s) + dist(v), id(v), costo(s), dirección).

Devuelve tuplas comparables (accion, id_vecina, direccion, costo_accion).
"""

ATACAR = 'atacar'
ESPERAR = 'esperar'
MOVER = 'mover'


def _id_maximo(cripta) -> int:
    maximo = 0
    for sala in cripta.salas():
        if sala.id > maximo:
            maximo = sala.id
    return maximo


def dist_referencia(cripta, origen: int, destino: int, id_maximo: int = None):
    """Costo mínimo de origen a destino por puertas abiertas, o None si no hay ruta."""
    if id_maximo is None:
        id_maximo = _id_maximo(cripta)
    distancia = [-1] * (id_maximo + 1)
    asentada = [False] * (id_maximo + 1)
    distancia[origen] = 0
    while True:
        mejor = -1
        for i in range(1, id_maximo + 1):
            if distancia[i] >= 0 and not asentada[i] and (mejor < 0 or distancia[i] < distancia[mejor]):
                mejor = i
        if mejor < 0:
            return None
        if mejor == destino:
            return distancia[mejor]
        asentada[mejor] = True
        sala = cripta.sala(mejor)
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None or salida.puerta.cerrada:
                continue
            nueva = distancia[mejor] + salida.puerta.costo
            v = salida.destino
            if distancia[v] < 0 or nueva < distancia[v]:
                distancia[v] = nueva


def decision_referencia(cripta, sala_cazador: int, rango: int, sala_jugador: int):
    """Decisión literal del enunciado: (accion, id_vecina, direccion, costo_accion)."""
    if sala_cazador == sala_jugador:
        return (ATACAR, None, None, 100)
    id_maximo = _id_maximo(cripta)
    d = dist_referencia(cripta, sala_cazador, sala_jugador, id_maximo)
    if d is None or d > rango:
        return (ESPERAR, None, None, 100)
    mejor = None
    sala = cripta.sala(sala_cazador)
    for direccion in range(4):
        salida = sala.salidas[direccion]
        if salida is None or salida.puerta.cerrada:
            continue
        v = salida.destino
        dv = dist_referencia(cripta, v, sala_jugador, id_maximo)
        if dv is None:
            continue
        clave = (salida.puerta.costo + dv, v, salida.puerta.costo, direccion)
        if mejor is None or clave < mejor:
            mejor = clave
    total, v, costo, direccion = mejor
    if total != d:
        raise AssertionError('La referencia encontró una ruta inconsistente con d')
    return (MOVER, v, direccion, costo)


def distancias_desde_referencia(cripta, origen: int, id_maximo: int) -> list:
    """Todas las distancias desde origen con el mismo algoritmo lineal (-1 = inalcanzable)."""
    distancia = [-1] * (id_maximo + 1)
    asentada = [False] * (id_maximo + 1)
    distancia[origen] = 0
    while True:
        mejor = -1
        for i in range(1, id_maximo + 1):
            if distancia[i] >= 0 and not asentada[i] and (mejor < 0 or distancia[i] < distancia[mejor]):
                mejor = i
        if mejor < 0:
            return distancia
        asentada[mejor] = True
        sala = cripta.sala(mejor)
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None or salida.puerta.cerrada:
                continue
            nueva = distancia[mejor] + salida.puerta.costo
            v = salida.destino
            if distancia[v] < 0 or nueva < distancia[v]:
                distancia[v] = nueva


def matriz_referencia(cripta) -> list:
    """matriz[a][b] = distancia de a a b (-1 si no hay ruta), con listas indexadas por id."""
    id_maximo = _id_maximo(cripta)
    matriz = [None] * (id_maximo + 1)
    for sala in cripta.salas():
        matriz[sala.id] = distancias_desde_referencia(cripta, sala.id, id_maximo)
    return matriz


def decision_desde_matriz(cripta, matriz, sala_cazador: int, rango: int, sala_jugador: int):
    """Igual que decision_referencia, pero leyendo las distancias de la matriz."""
    if sala_cazador == sala_jugador:
        return (ATACAR, None, None, 100)
    d = matriz[sala_cazador][sala_jugador]
    if d < 0 or d > rango:
        return (ESPERAR, None, None, 100)
    mejor = None
    sala = cripta.sala(sala_cazador)
    for direccion in range(4):
        salida = sala.salidas[direccion]
        if salida is None or salida.puerta.cerrada:
            continue
        v = salida.destino
        dv = matriz[v][sala_jugador]
        if dv < 0:
            continue
        clave = (salida.puerta.costo + dv, v, salida.puerta.costo, direccion)
        if mejor is None or clave < mejor:
            mejor = clave
    total, v, costo, direccion = mejor
    if total != d:
        raise AssertionError('La referencia encontró una ruta inconsistente con d')
    return (MOVER, v, direccion, costo)
