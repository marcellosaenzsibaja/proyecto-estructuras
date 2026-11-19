"""Generador de criptas sintéticas sembradas (pruebas y --bench).

Reglas (specs/001-terreno-cazador/tasks.md, «Generación de criptas»):

- G1: produce TEXTO JSON con la forma exacta del esqueleto del servicio; nunca
  crea diccionarios. El texto se entrega a una FuenteMemoria, que lo lee con
  json.loads, y la cripta se construye con el cargador real.
- G2: toda salida tiene su pareja opuesta con la misma sala de vuelta, el mismo
  costo, el mismo estado de puerta y la misma llave.
- G3: una única instancia random.Random(semilla), consumida siempre en el mismo
  orden; misma semilla y parámetros producen los mismos textos.
- G4: ids 1..n asignados con una permutación Fisher-Yates sembrada; posiciones
  p = fila * ancho + columna; conexiones numeradas (E de p = 2p, S de p = 2p+1);
  todo el estado de una conexión en listas de tamaño 2n.
- G5: todo recorrido marca visitadas en listas indexadas; nada de set ni dict.
"""
import json
import random

from src.adaptadores.fuente_memoria import FuenteMemoria

LETRAS = ('N', 'S', 'E', 'O')
NORTE, SUR, ESTE, OESTE = 0, 1, 2, 3


class CuadriculaSintetica:
    """Estado interno de una cripta sintética, todo en listas indexadas (G4)."""

    __slots__ = ('ancho', 'alto', 'n', 'id_de_posicion', 'posicion_de_id', 'existe', 'en_arbol',
                 'declara_costo', 'costo', 'cerrada', 'desplazamiento_id', 'desplazamiento_llave', 'extra')

    def __init__(self, ancho: int, alto: int):
        self.ancho = ancho
        self.alto = alto
        self.n = ancho * alto
        self.id_de_posicion = [0] * self.n
        self.posicion_de_id = [0] * (self.n + 1)
        self.existe = [False] * (2 * self.n)
        self.en_arbol = [False] * (2 * self.n)
        self.declara_costo = [False] * (2 * self.n)
        self.costo = [0] * (2 * self.n)
        self.cerrada = [False] * (2 * self.n)
        self.desplazamiento_id = 0
        self.desplazamiento_llave = 0
        # Salidas adicionales por posición (pasillos hacia otra cuadrícula):
        # lista indexada por posición; cada elemento es None o una lista de
        # tuplas (direccion, id_destino, costo, cerrada, llave).
        self.extra = [None] * self.n

    def vecina(self, p: int, direccion: int) -> int:
        """Posición vecina en la cuadrícula o -1 si cae fuera."""
        fila, columna = divmod(p, self.ancho)
        if direccion == NORTE:
            return p - self.ancho if fila > 0 else -1
        if direccion == SUR:
            return p + self.ancho if fila < self.alto - 1 else -1
        if direccion == ESTE:
            return p + 1 if columna < self.ancho - 1 else -1
        return p - 1 if columna > 0 else -1

    def numero_conexion(self, p: int, direccion: int) -> int:
        """Número de la conexión que sale de p en esa dirección (G4)."""
        if direccion == ESTE:
            return 2 * p
        if direccion == SUR:
            return 2 * p + 1
        if direccion == OESTE:
            return 2 * (p - 1)
        return 2 * (p - self.ancho) + 1

    def id_sala(self, p: int) -> int:
        return self.id_de_posicion[p] + self.desplazamiento_id

    def salidas(self, p: int) -> list:
        """Salidas de la posición p en orden N, S, E, O: (dir, id_destino, costo|None, cerrada, llave|None)."""
        resultado = []
        for direccion in range(4):
            v = self.vecina(p, direccion)
            if v >= 0:
                c = self.numero_conexion(p, direccion)
                if self.existe[c]:
                    costo = self.costo[c] if self.declara_costo[c] else None
                    llave = f'itm_llave_sint_{c + self.desplazamiento_llave}' if self.cerrada[c] else None
                    resultado.append((direccion, self.id_sala(v), costo, self.cerrada[c], llave))
                    continue
            if self.extra[p] is not None:
                for salida in self.extra[p]:
                    if salida[0] == direccion:
                        resultado.append(salida)
        return resultado


def _permutacion(rng: random.Random, n: int) -> list:
    """Fisher-Yates explícito sobre [1..n] (G4)."""
    ids = list(range(1, n + 1))
    i = n - 1
    while i >= 1:
        j = rng.randrange(i + 1)
        ids[i], ids[j] = ids[j], ids[i]
        i -= 1
    return ids


def generar(semilla: int, ancho: int, alto: int, costo_min: int = 1, costo_max: int = 300, prob_cerrada: float = 0.0,
            prob_sin_costo: float = 0.0, prob_hueco: float = 0.0, conexa: bool = True, conexa_abierta: bool = False) -> CuadriculaSintetica:
    """Construye el estado interno de la cripta consumiendo rng siempre en el mismo orden (G3)."""
    if ancho < 1 or alto < 1:
        raise ValueError('La cuadrícula debe tener al menos una sala')
    if costo_min < 1 or costo_max < costo_min:
        raise ValueError('Los costos deben cumplir 1 <= costo_min <= costo_max')
    rng = random.Random(semilla)
    g = CuadriculaSintetica(ancho, alto)
    n = g.n
    # 1. Permutación de ids.
    g.id_de_posicion = _permutacion(rng, n)
    for p in range(n):
        g.posicion_de_id[g.id_de_posicion[p]] = p
    # 2. Árbol de expansión por recorrido en profundidad (G5: lista indexada + pila).
    if conexa:
        visitada = [False] * n
        visitada[0] = True
        pila = [0]
        while pila:
            p = pila[-1]
            candidatas = []
            for direccion in range(4):
                v = g.vecina(p, direccion)
                if v >= 0 and not visitada[v]:
                    candidatas.append(direccion)
            if candidatas:
                direccion = candidatas[rng.randrange(len(candidatas))]
                v = g.vecina(p, direccion)
                g.en_arbol[g.numero_conexion(p, direccion)] = True
                visitada[v] = True
                pila.append(v)
            else:
                pila.pop()
    # Conexiones que existen en la cuadrícula, en orden ascendente de número.
    numeros = []
    for p in range(n):
        if g.vecina(p, ESTE) >= 0:
            numeros.append(2 * p)
        if g.vecina(p, SUR) >= 0:
            numeros.append(2 * p + 1)
    # 3. Huecos (el sorteo se hace siempre, aunque la conexión esté en el árbol).
    for c in numeros:
        sorteo = rng.random()
        g.existe[c] = g.en_arbol[c] or sorteo >= prob_hueco
    # 4. Costos.
    for c in numeros:
        sorteo = rng.random()
        valor = rng.randint(costo_min, costo_max)
        if g.existe[c]:
            g.declara_costo[c] = sorteo >= prob_sin_costo
            g.costo[c] = valor
    # 5. Puertas cerradas.
    for c in numeros:
        sorteo = rng.random()
        if g.existe[c]:
            g.cerrada[c] = sorteo < prob_cerrada and not (conexa_abierta and g.en_arbol[c])
    return g


def texto_sala(id_sala: int, salidas: list) -> str:
    """Fragmento JSON de una sala con la forma del esqueleto (G1), sin crear diccionarios."""
    partes = ['{"id": ', json.dumps(id_sala), ', "nombre": ', json.dumps(f'Sala sintética {id_sala}'), ', "salidas": {']
    primera = True
    for direccion, destino, costo, cerrada, llave in salidas:
        if not primera:
            partes.append(', ')
        primera = False
        partes.append(json.dumps(LETRAS[direccion]))
        partes.append(': {"sala": ')
        partes.append(json.dumps(destino))
        if costo is not None:
            partes.append(', "costo": ')
            partes.append(json.dumps(costo))
        if cerrada:
            partes.append(', "cerrada": true')
            if llave is not None:
                partes.append(', "llave": ')
                partes.append(json.dumps(llave))
        partes.append('}')
    partes.append('}}')
    return ''.join(partes)


def fragmentos(g: CuadriculaSintetica) -> list:
    """Un fragmento de texto JSON por sala, ordenados por id ascendente (G1)."""
    resultado = []
    for id_local in range(1, g.n + 1):
        p = g.posicion_de_id[id_local]
        resultado.append(texto_sala(g.id_sala(p), g.salidas(p)))
    return resultado


def cripta_sintetica(semilla: int, ancho: int, alto: int, **parametros) -> list:
    """Lista de fragmentos JSON (uno por sala) de una cripta sintética sembrada."""
    return fragmentos(generar(semilla, ancho, alto, **parametros))


def paginar(textos_salas: list, tam_pagina: int = 50, semilla=None) -> list:
    """Une los fragmentos en textos de página con la forma del servicio.

    Con semilla, el orden de las salas se baraja con Fisher-Yates sembrado (D5).
    """
    if tam_pagina < 1:
        raise ValueError('El tamaño de página debe ser al menos 1')
    orden = list(textos_salas)
    if semilla is not None:
        rng = random.Random(semilla)
        i = len(orden) - 1
        while i >= 1:
            j = rng.randrange(i + 1)
            orden[i], orden[j] = orden[j], orden[i]
            i -= 1
    total = max(1, (len(orden) + tam_pagina - 1) // tam_pagina)
    paginas = []
    for numero in range(total):
        trozo = orden[numero * tam_pagina:(numero + 1) * tam_pagina]
        paginas.append('{"pagina": ' + json.dumps(numero + 1) + ', "total_paginas": ' + json.dumps(total)
                       + ', "salas": [' + ', '.join(trozo) + ']}')
    return paginas


def texto_datos_generales(id_cripta: str, salas_total: int, paginas: int, sala_inicial: int, sala_salida: int,
                          version: str = 'v-sintetica', llave_salida: str = 'itm_llave_salida_sint', presupuesto: int = 1000,
                          inventario_max: int = 10, vida_max: int = 30, ataque: int = 6, defensa: int = 2, velocidad: int = 100) -> str:
    """Texto JSON de los datos generales de una cripta sintética."""
    return ('{"id": ' + json.dumps(id_cripta) + ', "version": ' + json.dumps(version)
            + ', "salas_total": ' + json.dumps(salas_total) + ', "paginas": ' + json.dumps(paginas)
            + ', "salas_por_pagina": 50, "sala_inicial": ' + json.dumps(sala_inicial)
            + ', "sala_salida": ' + json.dumps(sala_salida) + ', "llave_salida": ' + json.dumps(llave_salida)
            + ', "presupuesto_solicitudes": ' + json.dumps(presupuesto) + ', "inventario_max": ' + json.dumps(inventario_max)
            + ', "jugador": {"vida_max": ' + json.dumps(vida_max) + ', "ataque": ' + json.dumps(ataque)
            + ', "defensa": ' + json.dumps(defensa) + ', "velocidad": ' + json.dumps(velocidad) + '}}')


def ficha_cazador(id_ficha: str, rango: int, velocidad: int = 100, vida_max: int = 18, ataque: int = 6, defensa: int = 2,
                  nombre: str = 'Cazador sintético') -> str:
    """Texto JSON de una ficha de catálogo con comportamiento cazador."""
    return ('{"id": ' + json.dumps(id_ficha) + ', "clase": "enemigo", "nombre": ' + json.dumps(nombre)
            + ', "vida_max": ' + json.dumps(vida_max) + ', "ataque": ' + json.dumps(ataque)
            + ', "defensa": ' + json.dumps(defensa) + ', "velocidad": ' + json.dumps(velocidad)
            + ', "comportamiento": "cazador", "rango": ' + json.dumps(rango) + ', "suelta": []}')


def distancias_lineales(g: CuadriculaSintetica, origen_id: int) -> list:
    """Distancias de costo mínimo desde origen_id por puertas abiertas, O(n²) (G5).

    Lista indexada por id (tamaño n + 1); -1 significa inalcanzable. Se usa solo
    para elegir el ancla de cripta_ampliada_x10.
    """
    n = g.n
    distancia = [-1] * (n + 1)
    asentada = [False] * (n + 1)
    distancia[origen_id] = 0
    while True:
        mejor = -1
        for i in range(1, n + 1):
            if distancia[i] >= 0 and not asentada[i] and (mejor < 0 or distancia[i] < distancia[mejor]):
                mejor = i
        if mejor < 0:
            return distancia
        asentada[mejor] = True
        p = g.posicion_de_id[mejor]
        for direccion, destino, costo, cerrada, _ in g.salidas(p):
            if cerrada or destino > n:
                continue
            nueva = distancia[mejor] + (100 if costo is None else costo)
            if distancia[destino] < 0 or nueva < distancia[destino]:
                distancia[destino] = nueva


def cripta_ampliada_x10(semilla: int, ancho: int, alto: int, sala_jugador: int, rango: int, **parametros) -> list:
    """Cripta 10 veces más grande cuya región a distancia <= rango de sala_jugador es idéntica a la base.

    Regenera la base con la misma semilla y parámetros y le cuelga, debajo, otra
    cuadrícula de ancho x (9 * alto) salas (ids n+1..10n) mediante un único
    pasillo de costo rango + 1 desde una sala de la última fila cuya distancia
    al jugador es mayor que rango. Como todo camino hacia las salas nuevas
    atraviesa ese pasillo, ninguna sala nueva queda dentro de la región ni en
    su borde (SC-004).
    """
    base = generar(semilla, ancho, alto, **parametros)
    distancia = distancias_lineales(base, sala_jugador)
    ancla = -1
    for columna in range(ancho):
        p = (alto - 1) * ancho + columna
        id_p = base.id_sala(p)
        if distancia[id_p] < 0 or distancia[id_p] > rango:
            if ancla < 0 or id_p < base.id_sala(ancla):
                ancla = p
    if ancla < 0:
        raise ValueError('Ninguna sala de la última fila está fuera del rango; use una base más grande o un rango menor')
    extra = generar(semilla + 1, ancho, 9 * alto, **parametros)
    extra.desplazamiento_id = base.n
    extra.desplazamiento_llave = 2 * base.n
    columna_ancla = ancla % ancho
    entrada = columna_ancla  # posición en la fila 0 de la cuadrícula extra
    costo_pasillo = rango + 1
    base.extra[ancla] = [(SUR, extra.id_sala(entrada), costo_pasillo, False, None)]
    extra.extra[entrada] = [(NORTE, base.id_sala(ancla), costo_pasillo, False, None)]
    return fragmentos(base) + fragmentos(extra)


def texto_llaves(llaves: list) -> str:
    """Texto JSON de la ubicación de llaves; cada llave es (id, sala) o (id, sala, enemigo)."""
    partes = []
    for llave in llaves:
        texto = '{"id": ' + json.dumps(llave[0]) + ', "sala": ' + json.dumps(llave[1])
        if len(llave) > 2 and llave[2] is not None:
            texto += ', "enemigo": ' + json.dumps(llave[2])
        partes.append(texto + '}')
    return '{"llaves": [' + ', '.join(partes) + ']}'


def fuente_sintetica(textos_salas: list, sala_inicial: int = 1, sala_salida: int = None, tam_pagina: int = 50,
                     semilla_paginas=None, textos_contenido=None, textos_catalogo=None, id_cripta: str = 'sintetica',
                     texto_llaves=None, **datos) -> FuenteMemoria:
    """FuenteMemoria lista para el cargador real, con los textos dados (G1)."""
    paginas = paginar(textos_salas, tam_pagina, semilla_paginas)
    n = len(textos_salas)
    texto_datos = texto_datos_generales(id_cripta, n, len(paginas), sala_inicial, sala_salida if sala_salida is not None else n, **datos)
    return FuenteMemoria(id_cripta, texto_datos, paginas, textos_contenido, textos_catalogo, texto_llaves=texto_llaves)


def cargar_cripta_sintetica(fuente: FuenteMemoria):
    """Construye la Cripta con el cargador real a partir de una FuenteMemoria (G1)."""
    from src.servicios.cargador_cripta import cargar_datos, cargar_esqueleto
    datos = cargar_datos(fuente, fuente.id_cripta)
    return cargar_esqueleto(fuente, datos)
