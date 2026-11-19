import json
import random
import time
from src.modelos.acciones import Accion, ESPERAR, MOVER
from src.modelos.contenido import ContenidoSala, ProveedorContenido
from src.modelos.cripta import Cripta, DatosCripta, EstadisticasJugador
from src.modelos.direcciones import OPUESTA
from src.modelos.entidades import Puerta, Sala, Salida
from src.modelos.linea_tiempo import asegurar_puntos
from src.modelos.partida import EN_CURSO, Partida
from src.servicios.guardado import tomar_snapshot

LIMITE_CONSULTA_MS = 50
ACCIONES_REFERENCIA = 5000
VALORES_K = (1, 25, 100, 200)


class _ProveedorVacio(ProveedorContenido):

    def contenido_disponible(self, id_sala):
        return True

    def obtener_contenido(self, id_sala):
        return ContenidoSala()

    def ficha(self, id_ficha):
        raise KeyError(id_ficha)


def cripta_anillo(salas: int, semilla: int) -> Cripta:
    datos = DatosCripta('bench-linea', 'v1', salas, 1, salas + 1, None, 10 ** 9, 20,
                        EstadisticasJugador(10 ** 7, 6, 2, 100))
    cripta = Cripta(datos)
    for i in range(1, salas + 1):
        cripta.agregar_sala(Sala(i, f'Sala {i}'))
    for i in range(1, salas + 1):
        vecina = i + 1 if i < salas else 1
        costo = 100 + (i * 37 + semilla) % 150
        puerta = Puerta(costo=costo, costo_declarado=True)
        cripta.sala(i).salidas[0] = Salida(vecina, puerta)
        cripta.sala(vecina).salidas[OPUESTA[0]] = Salida(i, puerta)
    cripta.enlazar_puertas()
    return cripta


def _guion(acciones: int):
    pasos = []
    for i in range(acciones):
        pasos.append(Accion(MOVER, 0) if i % 3 != 2 else Accion(ESPERAR))
    return pasos


def jugar(k: int, acciones: int, semilla: int, salas: int = 40):
    cripta = cripta_anillo(salas, semilla)
    partida = Partida(cripta, _ProveedorVacio(), semilla, k)
    partida.iniciar()
    instantes = []
    for accion in _guion(acciones):
        if partida.estado != EN_CURSO:
            break
        partida.ejecutar(accion)
        instantes.append(partida.reloj.tiempo_virtual)
    return (partida, instantes)


def _bytes_linea(partida) -> int:
    entradas = [[e.numero, e.tiempo, e.tipo, e.argumento] for e in partida.linea.entradas]
    total = len(json.dumps(entradas))
    for punto in partida.linea.puntos:
        total += len(json.dumps(punto.snapshot))
        total += len(json.dumps([punto.estado_azar[0], list(punto.estado_azar[1]), punto.estado_azar[2]]))
    return total


def _indices_muestra(total: int, muestras: int, semilla: int):
    azar = random.Random(semilla)
    if total <= muestras:
        return list(range(total))
    return [azar.randrange(total) for _ in range(muestras)]


def _consultar(partida, instantes, muestras: int = 40, semilla: int = 91):
    tiempos = []
    reaplicadas = 0
    for indice in _indices_muestra(len(instantes), muestras, semilla):
        t = instantes[indice]
        inicio = time.perf_counter()
        resumen, error = partida.historia_en(t)
        tiempos.append((time.perf_counter() - inicio) * 1000)
        if error is None:
            reaplicadas = max(reaplicadas, partida.linea.reaplicadas)
    media = sum(tiempos) / len(tiempos) if tiempos else 0.0
    return (media, max(tiempos) if tiempos else 0.0, reaplicadas)


def _fila(escenario, semilla, acciones, k, partida, media, maximo, reaplicadas, limite=True, nota=None):
    fila = {'escenario': escenario, 'semilla': semilla, 'acciones': acciones, 'k': k,
            'copias': partida.linea.copias(), 'bytes_linea': _bytes_linea(partida),
            'reaplicadas_max': reaplicadas,
            'ms_consulta_media': round(media, 3), 'ms_consulta_max': round(maximo, 3)}
    if limite:
        fila['limite_ms'] = LIMITE_CONSULTA_MS
        fila['resultado'] = 'CUMPLE' if maximo < LIMITE_CONSULTA_MS else 'NO CUMPLE'
    if nota is not None:
        fila['nota'] = nota
    return fila


def medir_valores_de_k(semilla=47, acciones=ACCIONES_REFERENCIA, valores=VALORES_K) -> list:
    filas = []
    for k in valores:
        partida, instantes = jugar(k, acciones, semilla)
        media, maximo, reaplicadas = _consultar(partida, instantes)
        nota = 'alternativa_descartada_copia_por_accion' if k == 1 else None
        filas.append(_fila(f'linea_k{k}_{acciones}_acciones', semilla, acciones, k, partida,
                           media, maximo, reaplicadas, nota=nota))
    return filas


def medir_sin_puntos_de_control(semilla=47, acciones=600) -> list:
    partida, instantes = jugar(acciones + 10, acciones, semilla)
    media, maximo, reaplicadas = _consultar(partida, instantes, muestras=12)
    fila = _fila(f'linea_sin_puntos_control_{acciones}_acciones', semilla, acciones, acciones + 10,
                 partida, media, maximo, reaplicadas, nota='alternativa_descartada_sin_puntos')
    return [fila]


def medir_determinismo(semilla=47, acciones=300, k=25) -> list:
    primera, instantes = jugar(k, acciones, semilla)
    segunda, _ = jugar(k, acciones, semilla)
    misma_historia = ([(e.numero, e.tiempo, e.tipo, e.argumento) for e in primera.linea.entradas] ==
                      [(e.numero, e.tiempo, e.tipo, e.argumento) for e in segunda.linea.entradas])
    mismos = True
    for t in instantes[::37]:
        uno = primera.historia_en(t)[0]
        otro = segunda.historia_en(t)[0]
        if uno is None or otro is None or uno.sala_id != otro.sala_id or uno.vida != otro.vida:
            mismos = False
            break
    return [{'escenario': 'determinismo_linea', 'semilla': semilla, 'acciones': acciones, 'k': k,
             'misma_historia': 'si' if misma_historia else 'no',
             'mismos_resumenes': 'si' if mismos else 'no'}]


def medir_reconstruccion_al_cargar(semilla=47, acciones=400, k=25) -> list:
    partida, instantes = jugar(k, acciones, semilla)
    snapshot = tomar_snapshot(partida)
    from src.servicios.guardado import restaurar_partida
    cripta = cripta_anillo(40, semilla)
    cargada = restaurar_partida(snapshot, cripta, _ProveedorVacio(), k_checkpoint=k)
    inicio = time.perf_counter()
    asegurar_puntos(cargada)
    ms_reconstruccion = (time.perf_counter() - inicio) * 1000
    media, maximo, reaplicadas = _consultar(cargada, instantes, muestras=12)
    return [{'escenario': 'reconstruccion_al_cargar', 'semilla': semilla, 'acciones': acciones,
             'k': k, 'copias': cargada.linea.copias(),
             'ms_reconstruir_puntos': round(ms_reconstruccion, 3),
             'ms_consulta_media': round(media, 3), 'ms_consulta_max': round(maximo, 3),
             'reaplicadas_max': reaplicadas, 'limite_ms': LIMITE_CONSULTA_MS,
             'resultado': 'CUMPLE' if maximo < LIMITE_CONSULTA_MS else 'NO CUMPLE'}]


def ejecutar_linea_tiempo(rapido: bool = False) -> dict:
    acciones = 600 if rapido else ACCIONES_REFERENCIA
    filas = medir_valores_de_k(acciones=acciones)
    filas.extend(medir_sin_puntos_de_control())
    filas.extend(medir_reconstruccion_al_cargar())
    return {'linea_tiempo': filas, 'linea_determinismo': medir_determinismo()}
