import time
from src.modelos.contenido import ContenidoSala, ProveedorContenido
from src.modelos.cripta import Cripta, DatosCripta, EstadisticasJugador
from src.modelos.direcciones import OPUESTA
from src.modelos.entidades import Puerta, Sala, Salida
from src.modelos.mapa_conocido import MapaConocido
from src.modelos.partida import Partida
from src.modelos.viaje import BuscadorConocido

LIMITE_PASO_MS = 5


class _ProveedorVacio(ProveedorContenido):

    def contenido_disponible(self, id_sala):
        return True

    def obtener_contenido(self, id_sala):
        return ContenidoSala()

    def ficha(self, id_ficha):
        raise KeyError(id_ficha)


def cripta_rejilla(ancho: int, alto: int, semilla: int) -> Cripta:
    salas = ancho * alto
    datos = DatosCripta('bench-mapa', 'v1', salas, 1, salas, None, 10 ** 9, 20,
                        EstadisticasJugador(10 ** 7, 6, 2, 100))
    cripta = Cripta(datos)
    for i in range(1, salas + 1):
        cripta.agregar_sala(Sala(i, f'Sala {i}'))
    for fila in range(alto):
        for columna in range(ancho):
            actual = fila * ancho + columna + 1
            if columna + 1 < ancho:
                vecina = actual + 1
                costo = 100 + (actual * 31 + semilla) % 120
                puerta = Puerta(costo=costo, costo_declarado=True)
                cripta.sala(actual).salidas[2] = Salida(vecina, puerta)
                cripta.sala(vecina).salidas[OPUESTA[2]] = Salida(actual, puerta)
            if fila + 1 < alto:
                vecina = actual + ancho
                costo = 100 + (actual * 17 + semilla) % 120
                puerta = Puerta(costo=costo, costo_declarado=True)
                cripta.sala(actual).salidas[0] = Salida(vecina, puerta)
                cripta.sala(vecina).salidas[OPUESTA[0]] = Salida(actual, puerta)
    cripta.enlazar_puertas()
    return cripta


def _partida_con_mapa_completo(ancho, alto, semilla):
    cripta = cripta_rejilla(ancho, alto, semilla)
    partida = Partida(cripta, _ProveedorVacio(), semilla)
    partida.registra_linea = False
    partida.linea.activa = False
    partida.iniciar()
    for sala in cripta.salas():
        partida.mapa.explorar(sala)
        partida.mapa.observar_puertas(sala)
    return partida


def medir_consultas(semilla=31, tamanos=((10, 10), (20, 20), (40, 40)), consultas=200000) -> list:
    filas = []
    for ancho, alto in tamanos:
        partida = _partida_con_mapa_completo(ancho, alto, semilla)
        salas = list(partida.cripta.salas())
        inicio = time.perf_counter()
        for i in range(consultas):
            sala = salas[i % len(salas)]
            partida.mapa.estado_de(sala)
            partida.mapa.puerta_recordada(sala, i % 4)
        total = (time.perf_counter() - inicio) * 1000
        filas.append({'escenario': f'mapa_consultas_{ancho * alto}_exploradas', 'semilla': semilla,
                      'exploradas': partida.mapa.total_exploradas(), 'consultas': consultas * 2,
                      'ms_total': round(total, 3),
                      'ns_por_consulta': round(total * 1e6 / (consultas * 2), 1)})
    return filas


def medir_exploracion(semilla=31, ancho=10) -> list:
    """Misma vecindad local, mapa ya conocido de tamanos muy distintos (003 FR-051, SC-004).

    El ancho de la rejilla y la posicion del objetivo son identicos en las dos
    filas, para que la exploracion revele exactamente la misma vecindad; solo
    cambia cuantas salas lejanas estaban ya exploradas.
    """
    filas = []
    for alto, filas_previas, etiqueta in ((12, 4, 'mapa_pequeno'), (60, 40, 'mapa_grande')):
        cripta = cripta_rejilla(ancho, alto, semilla)
        mapa = MapaConocido(len(cripta))
        previas = 0
        for fila in range(filas_previas):
            for columna in range(ancho):
                mapa.explorar(cripta.sala(fila * ancho + columna + 1))
                previas += 1
        objetivo = cripta.sala((alto - 3) * ancho + ancho // 2 + 1)
        mapa.reiniciar_conteos()
        inicio = time.perf_counter()
        mapa.observar_puertas(objetivo)
        mapa.explorar(objetivo)
        for direccion in range(4):
            salida = objetivo.salidas[direccion]
            if salida is not None and salida.sala_destino is not None:
                mapa.explorar(salida.sala_destino)
        total = (time.perf_counter() - inicio) * 1000
        filas.append({'escenario': f'exploracion_antorcha_{etiqueta}', 'semilla': semilla,
                      'exploradas_antes': previas, 'reveladas': 5,
                      'salas_tocadas': mapa.salas_tocadas, 'puertas_tocadas': mapa.puertas_tocadas,
                      'ms_media': round(total, 4)})
    return filas


def medir_paso_de_viaje(semilla=31, ancho=20, alto=20, muestras=60, etiqueta=None) -> list:
    partida = _partida_con_mapa_completo(ancho, alto, semilla)
    salas = list(partida.cripta.salas())
    destino = salas[-1].id
    tiempos = []
    examinadas = 0
    for i in range(muestras):
        partida.jugador.sala_id = salas[(i * 37) % len(salas)].id
        inicio = time.perf_counter()
        resultado = partida.ruta_conocida(destino)
        tiempos.append((time.perf_counter() - inicio) * 1000)
        if resultado is not None:
            examinadas = max(examinadas, partida.buscador_conocido.examinadas)
    maximo = max(tiempos)
    nombre = etiqueta or f'viaje_paso_mapa_completo_{len(salas)}_salas'
    return [{'escenario': nombre, 'semilla': semilla, 'salas': len(salas),
             'exploradas': partida.mapa.total_exploradas(), 'examinadas_max': examinadas,
             'ms_media': round(sum(tiempos) / len(tiempos), 3), 'ms_max': round(maximo, 3),
             'limite_ms': LIMITE_PASO_MS,
             'resultado': 'CUMPLE' if maximo < LIMITE_PASO_MS else 'NO CUMPLE'}]


def medir_paso_referencia_y_estres(semilla=31) -> list:
    """El limite de FR-053 se mide en la cripta de referencia; 1600 salas es estres.

    El enunciado aplica los 5 ms al mapa conocido completo de la cripta de
    referencia, y las criptas que publica el servicio van de ~20 salas a varios
    cientos. La fila de 1600 salas es el tamano sintetico de estres de la
    capacidad 001 y se reporta aunque no cumpla, para no esconderlo.
    """
    filas = medir_paso_de_viaje(semilla, 20, 20, etiqueta='viaje_paso_referencia_400_salas')
    estres = medir_paso_de_viaje(semilla, 40, 40, etiqueta='viaje_paso_estres_1600_salas')
    estres[0]['nota'] = 'estres_fuera_de_la_escala_de_referencia'
    filas.extend(estres)
    return filas


def medir_viaje_vs_cazador(semilla=31, ancho=40, alto=40, muestras=40) -> list:
    partida = _partida_con_mapa_completo(ancho, alto, semilla)
    salas = list(partida.cripta.salas())
    destino = salas[-1].id
    tiempos_viaje = []
    for i in range(muestras):
        partida.jugador.sala_id = salas[(i * 37) % len(salas)].id
        inicio = time.perf_counter()
        partida.ruta_conocida(destino)
        tiempos_viaje.append((time.perf_counter() - inicio) * 1000)
    buscador = BuscadorConocido(partida.cripta, partida.mapa)
    objetivo = partida.cripta.sala(destino)
    tiempos_cazador = []
    for i in range(muestras):
        origen = salas[(i * 37) % len(salas)]
        inicio = time.perf_counter()
        buscador.primer_paso(origen, objetivo)
        tiempos_cazador.append((time.perf_counter() - inicio) * 1000)
    return [{'escenario': 'viaje_paso', 'semilla': semilla, 'salas': len(salas),
             'ms_media': round(sum(tiempos_viaje) / len(tiempos_viaje), 3)},
            {'escenario': 'buscador_aislado', 'semilla': semilla, 'salas': len(salas),
             'ms_media': round(sum(tiempos_cazador) / len(tiempos_cazador), 3)}]


def medir_determinismo(semilla=31, ancho=12, alto=12) -> list:
    primera = _partida_con_mapa_completo(ancho, alto, semilla)
    segunda = _partida_con_mapa_completo(ancho, alto, semilla)
    mismo_mapa = (list(primera.mapa.estado) == list(segunda.mapa.estado) and
                  list(primera.mapa.puertas) == list(segunda.mapa.puertas))
    destino = list(primera.cripta.salas())[-1].id
    mismas = True
    for sala in list(primera.cripta.salas())[::7]:
        primera.jugador.sala_id = sala.id
        segunda.jugador.sala_id = sala.id
        if primera.ruta_conocida(destino) != segunda.ruta_conocida(destino):
            mismas = False
            break
    return [{'escenario': 'determinismo_mapa', 'semilla': semilla, 'salas': ancho * alto,
             'mismo_mapa': 'si' if mismo_mapa else 'no',
             'mismas_rutas': 'si' if mismas else 'no'}]


def ejecutar_mapa(rapido: bool = False) -> dict:
    tamanos = ((10, 10), (20, 20)) if rapido else ((10, 10), (20, 20), (40, 40))
    consultas = 20000 if rapido else 200000
    lado = 20 if rapido else 40
    return {'mapa_consultas': medir_consultas(tamanos=tamanos, consultas=consultas),
            'mapa_exploracion': medir_exploracion(),
            'viaje_paso': medir_paso_de_viaje(ancho=lado, alto=lado) if rapido else medir_paso_referencia_y_estres(),
            'viaje_vs_cazador': medir_viaje_vs_cazador(ancho=lado, alto=lado),
            'mapa_determinismo': medir_determinismo()}
