"""T034: determinismo total de las decisiones del cazador.

- Misma cripta, semilla y acciones: misma traza, elemento por elemento.
- D5: cargar las salas en otro orden de páginas produce exactamente la misma traza.
- Los modos compartido e individual producen la misma traza.
- Solo enteros (D1).
Requisitos: FR-014, FR-019, FR-022, FR-027.
"""
import random
import unittest

from src.modelos.cazador import COMPARTIDO, INDIVIDUAL, MOVER, DecisorCazadores
from src.servicios import generador_criptas as gc

RANGOS = (150, 400, 900, 10 ** 9)


def _cripta(semilla, semilla_paginas=None):
    textos = gc.cripta_sintetica(semilla, 9, 8, costo_min=1, costo_max=250, prob_cerrada=0.15, prob_hueco=0.15)
    return gc.cargar_cripta_sintetica(gc.fuente_sintetica(textos, tam_pagina=17, semilla_paginas=semilla_paginas))


def traza(semilla, modo=COMPARTIDO, semilla_paginas=None, pasos=60, cazadores=8):
    """Simula persecuciones sembradas y devuelve la traza de decisiones.

    Todo se elige por id de sala y dirección (nunca por índice compacto), así que
    la simulación no depende del orden de carga.
    """
    cripta = _cripta(semilla, semilla_paginas)
    n = len(cripta)
    rng = random.Random(semilla * 7 + 1)
    decisor = DecisorCazadores(cripta, modo)
    posiciones = [rng.randint(1, n) for _ in range(cazadores)]
    rangos = [RANGOS[rng.randrange(len(RANGOS))] for _ in range(cazadores)]
    jugador = rng.randint(1, n)
    resultado = []
    for paso in range(pasos):
        # Cambia una puerta elegida por (id de sala, dirección).
        sala = cripta.sala(rng.randint(1, n))
        direccion = rng.randrange(4)
        if sala.salidas[direccion] is not None:
            puerta = sala.salidas[direccion].puerta
            puerta.cerrada = not puerta.cerrada
        for k in range(cazadores):
            decision = decisor.decidir(cripta.sala(posiciones[k]), rangos[k], cripta.sala(jugador))
            resultado.append((paso, k) + decision.como_tupla())
            if decision.accion == MOVER:
                posiciones[k] = decision.id_vecina
        # El jugador se mueve a una vecina abierta elegida por dirección.
        abiertas = []
        for d in range(4):
            salida = cripta.sala(jugador).salidas[d]
            if salida is not None and not salida.puerta.cerrada:
                abiertas.append(salida.destino)
        if abiertas:
            jugador = abiertas[rng.randrange(len(abiertas))]
    return resultado


class TestDeterminismo(unittest.TestCase):

    def test_misma_semilla_misma_traza_FR027(self):
        for semilla in (1, 2, 3):
            a = traza(semilla)
            b = traza(semilla)
            self.assertEqual(len(a), len(b))
            for x, y in zip(a, b):
                self.assertEqual(x, y)

    def test_orden_de_carga_no_cambia_la_traza_D5_FR014(self):
        for semilla in (4, 5):
            base = traza(semilla)
            self.assertEqual(traza(semilla, semilla_paginas=99), base)
            self.assertEqual(traza(semilla, semilla_paginas=12345), base)

    def test_modos_producen_la_misma_traza_FR022(self):
        for semilla in (6, 7, 8):
            self.assertEqual(traza(semilla, INDIVIDUAL), traza(semilla, COMPARTIDO))

    def test_las_decisiones_mueven_alguna_vez_FR019(self):
        movimientos = sum(1 for t in traza(9) if t[2] == MOVER)
        self.assertGreater(movimientos, 0)

    def test_distancias_enteras_D1(self):
        cripta = _cripta(10)
        decisor = DecisorCazadores(cripta, COMPARTIDO)
        decisor.decidir(cripta.sala(1), 10 ** 9, cripta.sala(len(cripta)))
        registro = decisor.buscador.registro
        for i in range(registro.n):
            if registro.asentada(i):
                self.assertIs(type(registro.distancia[i]), int)


if __name__ == '__main__':
    unittest.main()
