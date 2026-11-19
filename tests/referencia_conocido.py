"""Referencia teórica del subgrafo conocido (spec 003, SC-005).

Calcula por fuerza bruta el costo mínimo y el primer paso correcto sobre el
mapa conocido, sin reutilizar nada de la implementación: enumera caminos
simples. Solo sirve para criptas pequeñas, que es donde se compara.
"""
from src.modelos.mapa_conocido import EXPLORADA


def _vecinas(partida, sala):
    salidas = []
    for direccion in range(4):
        salida = sala.salidas[direccion]
        if salida is None:
            continue
        if not partida.mapa.recordada_abierta(sala, direccion):
            continue
        vecina = salida.sala_destino
        if vecina is None or partida.mapa.estado_de(vecina) != EXPLORADA:
            continue
        salidas.append((vecina, salida.puerta.costo))
    return salidas


def costos_de_caminos(partida, origen, objetivo, visitadas):
    """Costos de todos los caminos simples de origen a objetivo, sin repetir salas."""
    if origen is objetivo:
        return [0]
    resultados = []
    visitadas = visitadas + [origen.id]
    for vecina, costo in _vecinas(partida, origen):
        if vecina.id in visitadas:
            continue
        for total in costos_de_caminos(partida, vecina, objetivo, visitadas):
            resultados.append(costo + total)
    return resultados


def mejor_primer_paso(partida, id_origen, id_objetivo):
    """Devuelve (costo minimo, id de la vecina de menor id entre las rutas minimas) o None."""
    origen = partida.cripta.sala(id_origen)
    objetivo = partida.cripta.sala(id_objetivo)
    if partida.mapa.estado_de(origen) != EXPLORADA or partida.mapa.estado_de(objetivo) != EXPLORADA:
        return None
    if origen is objetivo:
        return (0, None)
    opciones = []
    for vecina, costo in _vecinas(partida, origen):
        for total in costos_de_caminos(partida, vecina, objetivo, [origen.id]):
            opciones.append((costo + total, vecina.id))
    if not opciones:
        return None
    minimo = min(c for c, _ in opciones)
    mejor = min(v for c, v in opciones if c == minimo)
    return (minimo, mejor)
