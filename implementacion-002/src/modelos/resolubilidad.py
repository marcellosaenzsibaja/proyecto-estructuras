from src.estructuras_datos.busqueda_binaria import buscar
from src.estructuras_datos.monticulo import MonticuloMin
from src.estructuras_datos.ordenamiento import ordenar
from src.modelos.direcciones import LETRAS
from src.modelos.errores import ErrorDatos


class LlaveInfo:
    __slots__ = ('id', 'sala', 'enemigo')

    def __init__(self, id_llave, sala, enemigo=None):
        self.id = id_llave
        self.sala = sala
        self.enemigo = enemigo


class PuertaBloqueada:
    __slots__ = ('sala_origen', 'direccion', 'sala_destino', 'llave', 'sala_llave', 'enemigo')

    def __init__(self, sala_origen, direccion, sala_destino, llave, sala_llave=None, enemigo=None):
        self.sala_origen = sala_origen
        self.direccion = direccion
        self.sala_destino = sala_destino
        self.llave = llave
        self.sala_llave = sala_llave
        self.enemigo = enemigo


class ReporteResolubilidad:

    def __init__(self, resoluble, orden_llaves, llaves_no_obtenibles, frontera, ciclos):
        self.resoluble = resoluble
        self.orden_llaves = orden_llaves
        self.llaves_no_obtenibles = llaves_no_obtenibles
        self.frontera = frontera
        self.ciclos = ciclos

    def texto(self) -> str:
        lineas = []
        if self.resoluble:
            lineas.append('Verificación de resolubilidad: la cripta es resoluble.')
            lineas.append(f'Orden de obtención de llaves ({len(self.orden_llaves)}):')
            numero = 1
            for id_llave in self.orden_llaves:
                lineas.append(f'  {numero}. {id_llave}')
                numero += 1
            return '\n'.join(lineas)
        lineas.append('Verificación de resolubilidad: la cripta NO es resoluble.')
        lineas.append(f'Llaves que no pueden obtenerse ({len(self.llaves_no_obtenibles)}):')
        for llave in self.llaves_no_obtenibles:
            lineas.append(f'  {llave.id} ({_ubicacion(llave.sala, llave.enemigo)})')
        lineas.append(f'Puertas de la frontera bloqueada ({len(self.frontera)}):')
        for puerta in self.frontera:
            destino = f'sala {puerta.sala_origen} {LETRAS[puerta.direccion]} -> sala {puerta.sala_destino}'
            if puerta.sala_llave is None:
                lineas.append(f'  {destino} requiere {puerta.llave} (llave sin ubicación en el servicio)')
            else:
                lineas.append(f'  {destino} requiere {puerta.llave} ({_ubicacion(puerta.sala_llave, puerta.enemigo)})')
        if self.ciclos:
            lineas.append(f'Ciclos de dependencia entre llaves ({len(self.ciclos)}):')
            for ciclo in self.ciclos:
                lineas.append('  [' + ' -> '.join(ciclo) + ']')
        return '\n'.join(lineas)


def _ubicacion(sala, enemigo) -> str:
    if enemigo is None:
        return f'en la sala {sala}'
    return f'la suelta el enemigo {enemigo}, que inicia en la sala {sala}'


def _id_llave(llave):
    return llave.id


def _clave_puerta(puerta):
    return (puerta.sala_origen, puerta.direccion)


def _indexar_llaves(cripta, llaves):
    ordenadas = ordenar(llaves, _id_llave)
    ids = [llave.id for llave in ordenadas]
    for i in range(1, len(ids)):
        if ids[i] == ids[i - 1]:
            raise ErrorDatos(f"La llave '{ids[i]}' aparece más de una vez en la ubicación de llaves")
    en_sala = [None] * len(cripta)
    for j in range(len(ordenadas)):
        llave = ordenadas[j]
        if not cripta.existe(llave.sala):
            raise ErrorDatos(f"La llave '{llave.id}' está en la sala {llave.sala}, que no existe en la cripta")
        indice = cripta.sala(llave.sala).indice
        if en_sala[indice] is None:
            en_sala[indice] = []
        en_sala[indice].append(j)
    return ordenadas, ids, en_sala


def _llave_de_puerta(ids, puerta) -> int:
    if puerta.llave is None:
        return -1
    return buscar(ids, puerta.llave)


def verificar(cripta, llaves) -> ReporteResolubilidad:
    datos = cripta.datos
    n = len(cripta)
    por_indice = [None] * n
    for sala in cripta.salas():
        por_indice[sala.indice] = sala
    ordenadas, ids, en_sala = _indexar_llaves(cripta, llaves)
    m = len(ordenadas)
    visitada = [False] * n
    obtenida = [False] * m
    espera = [None] * m
    sin_llave = []
    inicio = cripta.sala(datos.sala_inicial).indice
    visitada[inicio] = True
    cola = [inicio]
    cabeza = 0
    disponibles = MonticuloMin()
    orden = []
    while True:
        while cabeza < len(cola):
            u = cola[cabeza]
            cabeza += 1
            if en_sala[u] is not None:
                for j in en_sala[u]:
                    disponibles.insertar(j, j)
            sala = por_indice[u]
            for d in range(4):
                salida = sala.salidas[d]
                if salida is None:
                    continue
                v = salida.sala_destino.indice
                if visitada[v]:
                    continue
                puerta = salida.puerta
                if not puerta.cerrada:
                    visitada[v] = True
                    cola.append(v)
                    continue
                j = _llave_de_puerta(ids, puerta)
                if j < 0:
                    sin_llave.append((u, d))
                elif obtenida[j]:
                    visitada[v] = True
                    cola.append(v)
                else:
                    if espera[j] is None:
                        espera[j] = []
                    espera[j].append((u, d))
        if len(disponibles) == 0:
            break
        j = disponibles.extraer_minimo()[1]
        obtenida[j] = True
        orden.append(j)
        pendientes = espera[j]
        if pendientes is not None:
            espera[j] = None
            for u, d in pendientes:
                v = por_indice[u].salidas[d].sala_destino.indice
                if not visitada[v]:
                    visitada[v] = True
                    cola.append(v)
    if _alcanza_salida(cripta, ids, obtenida, visitada):
        return ReporteResolubilidad(True, [ordenadas[j].id for j in orden], [], [], [])
    return _diagnostico(por_indice, ordenadas, ids, en_sala, obtenida, visitada, espera, sin_llave, orden)


def _alcanza_salida(cripta, ids, obtenida, visitada) -> bool:
    datos = cripta.datos
    if datos.llave_salida is None:
        return False
    j = buscar(ids, datos.llave_salida)
    if j < 0 or not obtenida[j]:
        return False
    if not cripta.existe(datos.sala_salida):
        return False
    for salida in cripta.sala(datos.sala_salida).salidas:
        if salida is None:
            continue
        puerta = salida.puerta
        if puerta.cerrada and puerta.llave == datos.llave_salida and visitada[salida.sala_destino.indice]:
            return True
    return False


def _diagnostico(por_indice, ordenadas, ids, en_sala, obtenida, visitada, espera, sin_llave, orden) -> ReporteResolubilidad:
    m = len(ordenadas)
    no_obtenibles = [ordenadas[j] for j in range(m) if not obtenida[j]]
    frontera = []
    for j in range(m):
        pendientes = espera[j]
        if pendientes is None:
            continue
        llave = ordenadas[j]
        for u, d in pendientes:
            destino = por_indice[u].salidas[d].sala_destino
            if visitada[destino.indice]:
                continue
            frontera.append(PuertaBloqueada(por_indice[u].id, d, destino.id, llave.id, llave.sala, llave.enemigo))
    for u, d in sin_llave:
        salida = por_indice[u].salidas[d]
        if visitada[salida.sala_destino.indice]:
            continue
        frontera.append(PuertaBloqueada(por_indice[u].id, d, salida.sala_destino.id, salida.puerta.llave or '?'))
    frontera = ordenar(frontera, _clave_puerta)
    adyacencia = _dependencias(por_indice, ids, en_sala, obtenida, visitada, m)
    ciclos = _ciclos(adyacencia, obtenida, m)
    return ReporteResolubilidad(False, [ordenadas[j].id for j in orden], no_obtenibles, frontera,
                                [[ordenadas[j].id for j in ciclo] for ciclo in ciclos])


def _dependencias(por_indice, ids, en_sala, obtenida, visitada, m):
    n = len(por_indice)
    componente = [0] * n
    total = 0
    for raiz in range(n):
        if visitada[raiz] or componente[raiz] != 0:
            continue
        total += 1
        componente[raiz] = total
        cola = [raiz]
        cabeza = 0
        while cabeza < len(cola):
            u = cola[cabeza]
            cabeza += 1
            for salida in por_indice[u].salidas:
                if salida is None:
                    continue
                v = salida.sala_destino.indice
                if componente[v] != 0 or visitada[v]:
                    continue
                if salida.puerta.cerrada:
                    j = _llave_de_puerta(ids, salida.puerta)
                    if j < 0 or not obtenida[j]:
                        continue
                componente[v] = total
                cola.append(v)
    compuertas = [None] * (total + 1)
    for u in range(n):
        for salida in por_indice[u].salidas:
            if salida is None or not salida.puerta.cerrada:
                continue
            v = salida.sala_destino.indice
            if componente[u] == componente[v]:
                continue
            j = _llave_de_puerta(ids, salida.puerta)
            if j >= 0 and obtenida[j]:
                continue
            if compuertas[componente[u]] is None:
                compuertas[componente[u]] = []
            compuertas[componente[u]].append((componente[v], j))
    nivel = [-1] * (total + 1)
    nivel[0] = 0
    cola = [0]
    cabeza = 0
    while cabeza < len(cola):
        c = cola[cabeza]
        cabeza += 1
        if compuertas[c] is None:
            continue
        for vecino, _ in compuertas[c]:
            if nivel[vecino] < 0:
                nivel[vecino] = nivel[c] + 1
                cola.append(vecino)
    entradas = [None] * (total + 1)
    marca = [-1] * m
    for c in range(1, total + 1):
        if compuertas[c] is None:
            continue
        for vecino, j in compuertas[c]:
            if j < 0 or nivel[vecino] < 0 or nivel[vecino] + 1 != nivel[c]:
                continue
            if marca[j] != c:
                marca[j] = c
                if entradas[c] is None:
                    entradas[c] = []
                entradas[c].append(j)
    adyacencia = [None] * m
    for c in range(1, total + 1):
        if entradas[c] is not None:
            entradas[c] = ordenar(entradas[c])
    for u in range(n):
        if en_sala[u] is None or visitada[u]:
            continue
        lista = entradas[componente[u]]
        if lista is None:
            continue
        for j in en_sala[u]:
            adyacencia[j] = lista
    return adyacencia


def _ciclos(adyacencia, obtenida, m):
    estado = [0] * m
    posicion = [-1] * m
    ciclos = []
    for raiz in range(m):
        if obtenida[raiz] or estado[raiz] != 0:
            continue
        camino = [raiz]
        siguientes = [0]
        estado[raiz] = 1
        posicion[raiz] = 0
        while camino:
            nodo = camino[-1]
            vecinos = adyacencia[nodo]
            k = siguientes[-1]
            if vecinos is None or k >= len(vecinos):
                estado[nodo] = 2
                posicion[nodo] = -1
                camino.pop()
                siguientes.pop()
                continue
            siguientes[-1] = k + 1
            vecino = vecinos[k]
            if estado[vecino] == 0:
                estado[vecino] = 1
                posicion[vecino] = len(camino)
                camino.append(vecino)
                siguientes.append(0)
            elif estado[vecino] == 1:
                ciclos.append(_normalizar(camino[posicion[vecino]:]))
    return ordenar(ciclos, tuple)


def _normalizar(ciclo):
    menor = 0
    for i in range(1, len(ciclo)):
        if ciclo[i] < ciclo[menor]:
            menor = i
    rotado = ciclo[menor:] + ciclo[:menor]
    rotado.append(rotado[0])
    return rotado
