"""Mediciones de --bench para terreno y cazador (specs/001-terreno-cazador, US5).

Escenarios (contrato contracts/interfaz-y-bench.md):
- cazador_decision: 1 frente a 30 cazadores, rango pequeño frente a grande,
  compartido frente a individual (FR-032).
- cola_prioridad: montículo binario propio frente a lista con búsqueda lineal
  (research R1, alternativa ingenua).
- reutilizacion: reutilizar frente a recalcular siempre, con puertas estables e
  inestables (FR-033).
- escala: salas examinadas y tiempo con cripta x1 y x10 con la misma región en
  rango (FR-030, SC-004).
- ciclo_eventos: tiempo máximo entre dos decisiones del jugador con >= 30
  cazadores activos, con CUMPLE / NO CUMPLE frente a 20 ms (FR-031, SC-003).
- revision_p1: agenda e historial de retroceso con la carga nueva (FR-034).
- determinismo: misma semilla, mismas criptas sintéticas (FR-035).

No instancia la vista. Las criptas sintéticas salen del generador de T001.
"""
import random
import time
import zlib

from src.estructuras_datos.agenda import Agenda, Evento
from src.estructuras_datos.monticulo import MonticuloMin
from src.modelos.acciones import ESPERAR, MOVER, Accion
from src.modelos.cazador import COMPARTIDO, INDIVIDUAL, DecisorCazadores
from src.modelos.contenido import ContenidoSala, ProveedorContenido
from src.modelos.fichas import CAZADOR, PERGAMINO, FichaEnemigo, FichaObjeto
from src.modelos.entidades import Objeto
from src.modelos.partida import EN_CURSO, Partida
from src.servicios import generador_criptas as gc

LIMITE_CICLO_MS = 20
RANGO_PEQUENO = 300
RANGO_GRANDE = 5000


def _ahora():
    return time.perf_counter()


def _fila(escenario, semilla, salas, cazadores, examinadas_media, ms_media, ms_max, reutilizaciones=None, **extra):
    fila = {'escenario': escenario, 'semilla': semilla, 'salas': salas, 'cazadores': cazadores,
            'examinadas_media': round(examinadas_media, 2), 'ms_media': ms_media, 'ms_max': ms_max}
    if reutilizaciones is not None:
        fila['reutilizaciones'] = reutilizaciones
    fila.update(extra)
    return fila


def _cripta(semilla, ancho, alto, **parametros):
    textos = gc.cripta_sintetica(semilla, ancho, alto, **parametros)
    return gc.cargar_cripta_sintetica(gc.fuente_sintetica(textos))


def _sala_central(cripta, ancho, alto, semilla):
    g = gc.generar(semilla, ancho, alto)
    return cripta.sala(g.id_sala((alto // 2) * ancho + ancho // 2))


# -- cazador_decision ---------------------------------------------------------

def medir_decision(semilla=11, ancho=40, alto=40) -> list:
    cripta = _cripta(semilla, ancho, alto, costo_min=1, costo_max=300, prob_cerrada=0.1)
    jugador = _sala_central(cripta, ancho, alto, semilla)
    n = len(cripta)
    filas = []
    for cantidad in (1, 30):
        rng = random.Random(semilla + cantidad)
        salas = [cripta.sala(rng.randint(1, n)) for _ in range(cantidad)]
        for nombre_rango, rango in (('pequeno', RANGO_PEQUENO), ('grande', RANGO_GRANDE)):
            for modo in (COMPARTIDO, INDIVIDUAL):
                decisor = DecisorCazadores(cripta, modo, reutilizar=False)
                tiempos = []
                for sala in salas:
                    inicio = _ahora()
                    decisor.decidir(sala, rango, jugador)
                    tiempos.append((_ahora() - inicio) * 1000)
                filas.append(_fila(f'cazador_{modo}_{cantidad}_rango_{nombre_rango}', semilla, n, cantidad,
                                   decisor.salas_examinadas_total / cantidad, sum(tiempos) / len(tiempos), max(tiempos)))
        # Ciclo completo con cálculo compartido incremental y reutilización:
        decisor = DecisorCazadores(cripta, COMPARTIDO, reutilizar=True)
        inicio = _ahora()
        for sala in salas:
            decisor.decidir(sala, RANGO_GRANDE, jugador)
        total = (_ahora() - inicio) * 1000
        filas.append(_fila(f'cazador_compartido_incremental_{cantidad}_ciclo', semilla, n, cantidad,
                           decisor.salas_examinadas_total / cantidad, total / cantidad, total, decisor.reutilizaciones,
                           busquedas=decisor.busquedas))
    return filas


# -- cola_prioridad -----------------------------------------------------------

class _ListaLineal:
    """Alternativa ingenua: extraer el mínimo recorriendo toda la lista, O(k)."""

    def __init__(self):
        self._elementos = []

    def insertar(self, costo, indice):
        self._elementos.append((costo, indice))

    def extraer_minimo(self):
        elementos = self._elementos
        mejor = 0
        for i in range(1, len(elementos)):
            if elementos[i] < elementos[mejor]:
                mejor = i
        return elementos.pop(mejor)


def medir_cola_prioridad(semilla=5) -> list:
    filas = []
    for operaciones in (2000, 10000):
        rng = random.Random(semilla)
        secuencia = []
        pendientes = 0
        for _ in range(operaciones):
            if pendientes and rng.random() < 0.45:
                secuencia.append(None)
                pendientes -= 1
            else:
                secuencia.append((rng.randint(0, 50000), rng.randint(0, 10000)))
                pendientes += 1
        for nombre, clase in (('monticulo', MonticuloMin), ('lista_lineal', _ListaLineal)):
            cola = clase()
            inicio = _ahora()
            for operacion in secuencia:
                if operacion is None:
                    cola.extraer_minimo()
                else:
                    cola.insertar(*operacion)
            ms = (_ahora() - inicio) * 1000
            filas.append(_fila(f'cola_{nombre}_{operaciones}_operaciones', semilla, 0, 0, 0, ms / operaciones, None, ms_total=ms))
    return filas


# -- reutilizacion ------------------------------------------------------------

def _simular_reutilizacion(cripta, semilla, reutilizar, cambios_por_paso, cerca, pasos=60, cazadores=30, rango=1500):
    n = len(cripta)
    rng = random.Random(semilla)
    decisor = DecisorCazadores(cripta, COMPARTIDO, reutilizar=reutilizar)
    posiciones = [rng.randint(1, n) for _ in range(cazadores)]
    jugador = rng.randint(1, n)
    tiempos = []
    for paso in range(pasos):
        for _ in range(cambios_por_paso):
            if cerca:
                sala = cripta.sala(jugador)
            else:
                sala = cripta.sala(rng.randint(1, n))
            salida = sala.salidas[rng.randrange(4)]
            if salida is not None:
                salida.puerta.cerrada = not salida.puerta.cerrada
                decisor.notificar_puerta(salida.puerta)
        inicio = _ahora()
        for k in range(cazadores):
            decision = decisor.decidir(cripta.sala(posiciones[k]), rango, cripta.sala(jugador))
            if decision.id_vecina is not None:
                posiciones[k] = decision.id_vecina
        tiempos.append((_ahora() - inicio) * 1000)
        if paso % 5 == 4:
            abiertas = [s.destino for s in cripta.sala(jugador).salidas if s is not None and not s.puerta.cerrada]
            if abiertas:
                jugador = abiertas[rng.randrange(len(abiertas))]
    return decisor, tiempos


def medir_reutilizacion(semilla=21, ancho=40, alto=40) -> list:
    filas = []
    for nombre, cambios, cerca in (('puertas_estables', 1, False), ('puertas_inestables', 4, True)):
        for reutilizar in (True, False):
            cripta = _cripta(semilla, ancho, alto, costo_min=1, costo_max=300, prob_cerrada=0.1)
            decisor, tiempos = _simular_reutilizacion(cripta, semilla, reutilizar, cambios, cerca)
            etiqueta = 'reutilizar' if reutilizar else 'recalcular_siempre'
            filas.append(_fila(f'reutilizacion_{nombre}_{etiqueta}', semilla, len(cripta), 30,
                               decisor.salas_examinadas_total / max(1, decisor.busquedas + decisor.reutilizaciones),
                               sum(tiempos) / len(tiempos), max(tiempos), decisor.reutilizaciones, busquedas=decisor.busquedas))
    return filas


# -- escala ------------------------------------------------------------------

def medir_escala(semilla=3, ancho=20, alto=20, rango=400) -> list:
    base_g = gc.generar(semilla, ancho, alto)
    jugador_id = base_g.id_sala((alto // 2) * ancho + ancho // 2)
    base = gc.cargar_cripta_sintetica(gc.fuente_sintetica(gc.fragmentos(base_g)))
    grande = gc.cargar_cripta_sintetica(gc.fuente_sintetica(gc.cripta_ampliada_x10(semilla, ancho, alto, jugador_id, 2 * rango)))
    filas = []
    for nombre, cripta in (('x1', base), ('x10', grande)):
        for modo in (COMPARTIDO, INDIVIDUAL):
            decisor = DecisorCazadores(cripta, modo, reutilizar=False)
            jugador = cripta.sala(jugador_id)
            cazador = None
            for salida in jugador.salidas:
                if salida is not None:
                    cazador = salida.sala_destino
                    break
            tiempos = []
            for _ in range(20):
                inicio = _ahora()
                decisor.decidir(cazador, rango, jugador)
                tiempos.append((_ahora() - inicio) * 1000)
            filas.append(_fila(f'escala_{nombre}_{modo}', semilla, len(cripta), 1, decisor.salas_examinadas_total / 20,
                               sum(tiempos) / len(tiempos), max(tiempos)))
    return filas


# -- ciclo_eventos -----------------------------------------------------------

class _ProveedorCazadores(ProveedorContenido):
    """Proveedor de bench: la sala inicial trae los cazadores; las demás, vacías."""

    def __init__(self, sala_inicial, ficha, cantidad):
        self._sala_inicial = sala_inicial
        self._ficha = ficha
        self._cantidad = cantidad

    def contenido_disponible(self, id_sala):
        return True

    def obtener_contenido(self, id_sala):
        if id_sala == self._sala_inicial:
            return ContenidoSala(enemigos=[(f'e-{i}', self._ficha, None) for i in range(1, self._cantidad + 1)])
        return ContenidoSala()

    def ficha(self, id_ficha):
        return self._ficha


def _partida_con_cazadores(semilla, ancho, alto, cantidad, rango):
    textos = gc.cripta_sintetica(semilla, ancho, alto, costo_min=1, costo_max=300, prob_cerrada=0.05, conexa_abierta=True)
    fuente = gc.fuente_sintetica(textos, sala_inicial=1, vida_max=10 ** 9, defensa=10 ** 6)
    cripta = gc.cargar_cripta_sintetica(fuente)
    ficha = FichaEnemigo('ent_cazador_bench', 'Cazador', 18, 1, 2, 120, CAZADOR, (), None, rango)
    partida = Partida(cripta, _ProveedorCazadores(1, ficha, cantidad), semilla)
    partida.iniciar()
    return partida


def _correr_ciclo(semilla, ancho, alto, cazadores, rango, acciones, con_linea=True):
    partida = _partida_con_cazadores(semilla, ancho, alto, cazadores, rango)
    if not con_linea:
        partida.registra_linea = False
        partida.linea.activa = False
    partida.decisor_cazadores  # se crea fuera de la medición (infraestructura)
    rng = random.Random(semilla)
    tiempos = []
    for _ in range(acciones):
        if partida.estado != EN_CURSO:
            break
        sala = partida.sala_actual
        abiertas = [d for d in range(4) if sala.salidas[d] is not None and not sala.salidas[d].puerta.cerrada]
        accion = Accion(MOVER, abiertas[rng.randrange(len(abiertas))]) if abiertas else Accion(ESPERAR)
        inicio = _ahora()
        partida.ejecutar(accion)
        tiempos.append((_ahora() - inicio) * 1000)
    return partida, tiempos


def medir_ciclo(semilla=7, ancho=40, alto=40, cazadores=30, rango=1500, acciones=150, repeticiones=3) -> list:
    """Tiempo por ciclo entre dos decisiones del jugador con >= 30 cazadores activos.

    El escenario se repite con la misma semilla (exactamente el mismo trabajo) y,
    para cada acción, se toma el mínimo de las repeticiones, como hace timeit,
    para descartar interrupciones del sistema operativo. Se informa además el
    peor valor bruto observado.
    """
    filas = []
    for con_linea in (True, False):
        corridas = [_correr_ciclo(semilla, ancho, alto, cazadores, rango, acciones, con_linea)
                    for _ in range(repeticiones)]
        partida = corridas[0][0]
        largo = min(len(t) for _, t in corridas)
        minimos = [min(t[i] for _, t in corridas) for i in range(largo)]
        peor_bruto = max(max(t) for _, t in corridas)
        decisor = partida.decisor_cazadores
        activos = sum(1 for s in partida.cripta.salas() for e in s.enemigos if e.activo)
        ms_max = max(minimos)
        nombre = 'ciclo_eventos_30_cazadores' if con_linea else 'ciclo_eventos_30_cazadores_sin_linea'
        filas.append(_fila(nombre, semilla, len(partida.cripta), activos,
                           decisor.salas_examinadas_total / max(1, decisor.busquedas + decisor.reutilizaciones),
                           sum(minimos) / len(minimos), ms_max, decisor.reutilizaciones,
                           busquedas=decisor.busquedas, ms_max_bruto=peor_bruto,
                           repeticiones=repeticiones, k=partida.linea.k if con_linea else 'sin_linea',
                           copias=partida.linea.copias(), limite_ms=LIMITE_CICLO_MS,
                           resultado='CUMPLE' if ms_max < LIMITE_CICLO_MS else 'NO CUMPLE'))
    return filas


# -- revision_p1 -------------------------------------------------------------

def medir_revision_p1(semilla=9) -> list:
    filas = []
    # Agenda con eventos de 30 cazadores y costos variables: intervalos 1..300 a velocidades 70..200.
    for n in (2000, 20000):
        rng = random.Random(semilla)
        agenda = Agenda()
        inicio = _ahora()
        reloj = 0
        secuencia = 0
        for i in range(30):
            agenda.insertar(Evento(rng.randint(1, 300), secuencia, 'x'))
            secuencia += 1
        for _ in range(n):
            evento = agenda.extraer_minimo()
            reloj = evento.tiempo
            intervalo = max(1, rng.randint(1, 300) * 100 // rng.randint(70, 200))
            agenda.insertar(Evento(reloj + intervalo, secuencia, 'x'))
            secuencia += 1
        ms = (_ahora() - inicio) * 1000
        filas.append(_fila(f'revision_agenda_{n}_eventos_30_cazadores', semilla, 0, 30, 0, ms / n, None, ms_total=ms))
    # Historial de retroceso con 30 cazadores persiguiendo y costos variables.
    partida = _partida_con_cazadores(semilla, 30, 30, 30, 1500)
    ficha_pergamino = FichaObjeto('itm_bench_perg', PERGAMINO, 'Pergamino', 1, 1)
    rng = random.Random(semilla)
    inicio = _ahora()
    for _ in range(50):
        sala = partida.sala_actual
        abiertas = [d for d in range(4) if sala.salidas[d] is not None and not sala.salidas[d].puerta.cerrada]
        partida.ejecutar(Accion(MOVER, abiertas[rng.randrange(len(abiertas))]) if abiertas else Accion(ESPERAR))
    ms_acciones = (_ahora() - inicio) * 1000
    disponibles = partida.pergaminos_disponibles
    inicio = _ahora()
    for _ in range(disponibles):
        partida.jugador.inventario.agregar(Objeto(-1, ficha_pergamino))
        partida._usar_pergamino()
    ms_deshacer = (_ahora() - inicio) * 1000
    filas.append(_fila('revision_historial_50_acciones_30_cazadores', semilla, len(partida.cripta), 30, 0,
                       ms_acciones / 50, None, ms_total=ms_acciones, deshacer_ms=ms_deshacer, pergaminos=disponibles))
    return filas


# -- determinismo ------------------------------------------------------------

def medir_determinismo(semilla=2026) -> list:
    huellas = []
    for _ in range(2):
        textos = gc.cripta_sintetica(semilla, 40, 40, prob_cerrada=0.1, prob_sin_costo=0.2, prob_hueco=0.1)
        huellas.append(zlib.crc32(''.join(textos).encode('utf-8')))
    return [_fila('determinismo_criptas_sinteticas', semilla, 1600, 0, 0, 0.0, 0.0,
                  huella=huellas[0], reproducible='si' if huellas[0] == huellas[1] else 'NO')]


def ejecutar_cazador(rapido: bool = False) -> dict:
    """Todas las secciones del cazador para --bench (orden del contrato).

    rapido=True usa criptas más chicas para las pruebas automáticas; los
    resultados deterministas (salas examinadas, reutilizaciones) siguen
    dependiendo solo de la semilla.
    """
    lado = 16 if rapido else 40
    return {
        'cazador_decision': medir_decision(ancho=lado, alto=lado),
        'cola_prioridad': medir_cola_prioridad(),
        'reutilizacion': medir_reutilizacion(ancho=lado, alto=lado),
        'escala': medir_escala(ancho=12 if rapido else 20, alto=12 if rapido else 20, rango=250 if rapido else 400),
        'ciclo_eventos': medir_ciclo(ancho=lado, alto=lado, acciones=40 if rapido else 150, repeticiones=1 if rapido else 3),
        'revision_p1': medir_revision_p1(),
        'determinismo': medir_determinismo(),
    }
