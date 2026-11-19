from src.estructuras_datos.busqueda_binaria import ultimo_menor_o_igual

K_POR_DEFECTO = 100

CURSOR_SIG = 'cursor_sig'
CURSOR_ANT = 'cursor_ant'
TIPOS_CURSOR = (CURSOR_SIG, CURSOR_ANT)


class EntradaLinea:

    __slots__ = ('numero', 'tiempo', 'tipo', 'argumento')

    def __init__(self, numero: int, tiempo: int, tipo: str, argumento=None):
        self.numero = numero
        self.tiempo = tiempo
        self.tipo = tipo
        self.argumento = argumento

    @property
    def es_cursor(self) -> bool:
        return self.tipo in TIPOS_CURSOR


class PuntoControl:

    __slots__ = ('numero', 'tiempo', 'indice_entrada', 'snapshot', 'estado_azar')

    def __init__(self, numero: int, tiempo: int, indice_entrada: int, snapshot, estado_azar):
        self.numero = numero
        self.tiempo = tiempo
        self.indice_entrada = indice_entrada
        self.snapshot = snapshot
        self.estado_azar = estado_azar


class LineaTiempo:

    def __init__(self, k: int = K_POR_DEFECTO, activa: bool = True):
        if k < 1:
            raise ValueError('K debe ser un entero mayor o igual que 1')
        self.k = k
        self.activa = activa
        self.entradas = []
        self.puntos = []
        self.tiempos_punto = []
        self.numeros_punto = []
        self.acciones = 0
        self.reaplicadas = 0

    def registrar_accion(self, numero: int, tiempo: int, tipo: str, argumento=None):
        if not self.activa:
            return
        self.entradas.append(EntradaLinea(numero, tiempo, tipo, argumento))
        self.acciones = numero

    def registrar_cursor(self, tiempo: int, tipo: str):
        if not self.activa:
            return
        self.entradas.append(EntradaLinea(0, tiempo, tipo, None))

    def debe_tomar_punto(self, numero: int) -> bool:
        if not self.activa:
            return False
        if not self.numeros_punto:
            return True
        return numero - self.numeros_punto[-1] >= self.k

    def tomar_punto(self, partida, indice_entrada=None):
        if not self.activa:
            return
        from src.servicios.guardado import tomar_snapshot
        if indice_entrada is None:
            indice_entrada = len(self.entradas)
        self.agregar_punto(partida.acciones_jugador, partida.reloj.tiempo_virtual, indice_entrada,
                           tomar_snapshot(partida, incluir_linea=False), partida.azar.getstate())

    def agregar_punto(self, numero, tiempo, indice_entrada, snapshot, estado_azar):
        punto = PuntoControl(numero, tiempo, indice_entrada, snapshot, estado_azar)
        self.puntos.append(punto)
        self.tiempos_punto.append(punto.tiempo)
        self.numeros_punto.append(punto.numero)
        return punto

    def punto_base(self):
        return self.puntos[0] if self.puntos else None

    def punto_en_o_antes(self, tiempo: int):
        i = ultimo_menor_o_igual(self.tiempos_punto, tiempo)
        return None if i < 0 else self.puntos[i]

    def punto_hasta_accion(self, numero: int):
        i = ultimo_menor_o_igual(self.numeros_punto, numero)
        return None if i < 0 else self.puntos[i]

    def tiempo_maximo(self) -> int:
        return self.entradas[-1].tiempo if self.entradas else 0

    def recortar(self, numero: int, tiempo: int):
        if not self.activa:
            return
        while self.entradas and (self.entradas[-1].numero > numero or
                                 (self.entradas[-1].numero == 0 and self.entradas[-1].tiempo > tiempo)):
            self.entradas.pop()
        while self.numeros_punto and self.numeros_punto[-1] > numero:
            self.puntos.pop()
            self.tiempos_punto.pop()
            self.numeros_punto.pop()
        self.acciones = numero

    def acciones_hasta(self, tiempo: int, estricto: bool = True):
        limite = 0
        for entrada in self.entradas:
            if entrada.numero == 0:
                continue
            if entrada.tiempo < tiempo or (not estricto and entrada.tiempo == tiempo):
                limite = entrada.numero
        return limite

    def copias(self) -> int:
        return len(self.puntos)

    def tamano(self) -> int:
        return len(self.entradas)


def _partida_inerte(partida, punto):
    from src.servicios.guardado import restaurar_partida
    nueva = restaurar_partida(punto.snapshot, partida.cripta, partida.proveedor,
                              k_checkpoint=partida.linea.k)
    nueva.linea.activa = False
    nueva.registra_linea = False
    nueva.azar.setstate(punto.estado_azar)
    return nueva


def _reaplicar(nueva, entradas, desde: int, hasta_numero: int, limite_tiempo):
    from src.modelos.acciones import Accion
    from src.modelos.partida import EN_CURSO
    acciones = []
    for i in range(desde, len(entradas)):
        entrada = entradas[i]
        if entrada.numero == 0:
            acciones.append(entrada)
        elif entrada.numero <= hasta_numero:
            acciones.append(entrada)
        else:
            break
    reales = [e for e in acciones if e.numero != 0]
    ultima = reales[-1].numero if reales else None
    for entrada in acciones:
        if nueva.estado != EN_CURSO:
            break
        if entrada.es_cursor:
            nueva.mover_cursor(1 if entrada.tipo == CURSOR_SIG else -1)
            continue
        if limite_tiempo is not None and entrada.numero == ultima:
            nueva.limite_tiempo = limite_tiempo
        nueva.ejecutar(Accion(entrada.tipo, entrada.argumento))
    return len(reales)


def asegurar_puntos(partida):
    from src.modelos.acciones import Accion
    from src.modelos.partida import EN_CURSO
    linea = partida.linea
    if len(linea.puntos) > 1 or not linea.puntos or linea.acciones <= linea.k:
        return
    base = linea.puntos[0]
    nueva = _partida_inerte(partida, base)
    for indice, entrada in enumerate(linea.entradas):
        if nueva.estado != EN_CURSO:
            break
        if entrada.es_cursor:
            nueva.mover_cursor(1 if entrada.tipo == CURSOR_SIG else -1)
            continue
        nueva.ejecutar(Accion(entrada.tipo, entrada.argumento))
        if entrada.numero % linea.k == 0 and entrada.numero > 0:
            from src.servicios.guardado import tomar_snapshot
            linea.agregar_punto(nueva.acciones_jugador, nueva.reloj.tiempo_virtual, indice + 1,
                                tomar_snapshot(nueva, incluir_linea=False), nueva.azar.getstate())


def reconstruir_en(partida, tiempo: int):
    linea = partida.linea
    asegurar_puntos(partida)
    punto = linea.punto_en_o_antes(tiempo)
    if punto is None:
        return None
    nueva = _partida_inerte(partida, punto)
    hasta = linea.acciones_hasta(tiempo, estricto=True)
    reaplicadas = _reaplicar(nueva, linea.entradas, punto.indice_entrada, hasta, tiempo)
    linea.reaplicadas = reaplicadas
    if nueva.reloj.tiempo_virtual < tiempo:
        nueva.avanzar_hasta(tiempo)
    return nueva


def reconstruir_antes_de(partida, numero: int):
    linea = partida.linea
    asegurar_puntos(partida)
    punto = linea.punto_hasta_accion(numero - 1)
    if punto is None:
        return None
    nueva = _partida_inerte(partida, punto)
    reaplicadas = _reaplicar(nueva, linea.entradas, punto.indice_entrada, numero - 1, None)
    linea.reaplicadas = reaplicadas
    return nueva
