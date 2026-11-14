"""Decisión del cazador (P2 §3.2; research R5, R6; tasks T038, T039).

Modo «compartido» (preliminar, research R5): una búsqueda desde la sala del
jugador que se expande, para cada cazador que decide, solo hasta su rango
(extender_hasta) y queda en pausa; un cazador de rango mayor la retoma sin
repetir trabajo. Modo «individual»: una búsqueda desde cada cazador, acotada por
su rango, que propaga el primer paso. Ambos producen exactamente la misma
decisión que un cálculo desde cero (FR-019, FR-022).

La información de cálculo es infraestructura: no se guarda ni se revierte
(FR-021). No usa diccionarios, conjuntos ni estructuras de biblioteca.
"""
from src.modelos.rutas import BuscadorRutas

ATACAR = 'atacar'
ESPERAR = 'esperar'
MOVER = 'mover'
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COMPARTIDO = 'compartido'
INDIVIDUAL = 'individual'


class Decision:
    __slots__ = ('accion', 'salida', 'direccion', 'id_vecina', 'costo')

    def __init__(self, accion, salida=None, direccion=None, id_vecina=None, costo=COSTO_ESPERAR):
        self.accion = accion
        self.salida = salida
        self.direccion = direccion
        self.id_vecina = id_vecina
        self.costo = costo

    def como_tupla(self):
        """Tupla comparable con la referencia: (accion, id_vecina, direccion, costo)."""
        return (self.accion, self.id_vecina, self.direccion, self.costo)


_ESPERAR = Decision(ESPERAR, costo=COSTO_ESPERAR)
_ATACAR = Decision(ATACAR, costo=COSTO_ATACAR)


def regla_local(sala, rango: int, distancia_de) -> Decision:
    """Regla común a ambos modos (T038).

    Recorre las salidas de sala en orden N, S, E, O, descarta puertas cerradas y
    vecinas sin distancia asentada, y elige la menor clave D4:
    (costo(s) + dist(v), id(v), costo(s), dirección). Espera si no hay candidata
    o si su total supera el rango (FR-012 a FR-015).
    """
    mejor = None
    mejor_salida = None
    for direccion in range(4):
        salida = sala.salidas[direccion]
        if salida is None or salida.puerta.cerrada:
            continue
        dv = distancia_de(salida.sala_destino)
        if dv is None:
            continue
        costo = salida.puerta.costo
        clave = (costo + dv, salida.destino, costo, direccion)
        if mejor is None or clave < mejor:
            mejor = clave
            mejor_salida = salida
    if mejor is None or mejor[0] > rango:
        return _ESPERAR
    return Decision(MOVER, mejor_salida, mejor[3], mejor[1], mejor[2])


def _salida_hacia(sala, id_vecina: int):
    """Salida abierta más barata hacia id_vecina; empate por orden N, S, E, O (FR-015)."""
    mejor = None
    mejor_direccion = None
    for direccion in range(4):
        salida = sala.salidas[direccion]
        if salida is None or salida.puerta.cerrada or salida.destino != id_vecina:
            continue
        if mejor is None or salida.puerta.costo < mejor.puerta.costo:
            mejor = salida
            mejor_direccion = direccion
    return mejor, mejor_direccion


class DecisorCazadores:

    def __init__(self, cripta, modo: str = COMPARTIDO):
        if modo not in (COMPARTIDO, INDIVIDUAL):
            raise ValueError(f'Modo de decisión desconocido: {modo!r}')
        self.cripta = cripta
        self.modo = modo
        self.buscador = BuscadorRutas(cripta)
        self.busquedas = 0
        self.reutilizaciones = 0
        self.salas_examinadas_total = 0

    def decidir(self, sala_cazador, rango: int, sala_jugador) -> Decision:
        """Decisión del cazador que está en sala_cazador frente al jugador en sala_jugador."""
        if sala_cazador is sala_jugador:
            return _ATACAR
        if self.modo == COMPARTIDO:
            return self._decidir_compartido(sala_cazador, rango, sala_jugador)
        return self._decidir_individual(sala_cazador, rango, sala_jugador)

    def _decidir_compartido(self, sala_cazador, rango, sala_jugador):
        buscador = self.buscador
        buscador.distancias_desde(sala_jugador, rango)
        self.busquedas += 1
        self.salas_examinadas_total += buscador.examinadas
        return regla_local(sala_cazador, rango, buscador.distancia)

    def _decidir_individual(self, sala_cazador, rango, sala_jugador):
        buscador = self.buscador
        resultado = buscador.primer_paso_desde(sala_cazador, sala_jugador, rango)
        self.busquedas += 1
        self.salas_examinadas_total += buscador.examinadas
        if resultado is None:
            return _ESPERAR
        _, id_vecina = resultado
        salida, direccion = _salida_hacia(sala_cazador, id_vecina)
        return Decision(MOVER, salida, direccion, id_vecina, salida.puerta.costo)
