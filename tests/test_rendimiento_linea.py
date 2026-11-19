"""Rendimiento y conteos de la línea de tiempo (spec 004, FR-022, FR-030, SC-003 a SC-005)."""
import gc
import time
import unittest

from src.modelos.linea_tiempo import K_POR_DEFECTO
from src.servicios.banco_linea_tiempo import LIMITE_CONSULTA_MS, _indices_muestra, jugar

ACCIONES = 5000


class TestRendimientoLinea(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.partida, cls.instantes = jugar(K_POR_DEFECTO, ACCIONES, 47)

    def test_la_consulta_queda_bajo_el_limite_004_FR030_SC003(self):
        indices = _indices_muestra(len(self.instantes), 25, 91)
        self.partida.historia_en(self.instantes[indices[0]])
        gc.collect()
        gc.disable()
        try:
            peor = 0.0
            for indice in indices:
                t = self.instantes[indice]
                inicio = time.perf_counter()
                resumen, error = self.partida.historia_en(t)
                transcurrido = (time.perf_counter() - inicio) * 1000
                self.assertIsNone(error)
                self.assertIsNotNone(resumen)
                peor = max(peor, transcurrido)
        finally:
            gc.enable()
        self.assertLess(peor, LIMITE_CONSULTA_MS, f'peor consulta {peor:.3f} ms')

    def test_nunca_reaplica_mas_de_k_004_FR022_SC004(self):
        for indice in _indices_muestra(len(self.instantes), 40, 7):
            t = self.instantes[indice]
            self.partida.historia_en(t)
            self.assertLessEqual(self.partida.linea.reaplicadas, K_POR_DEFECTO)

    def test_copias_no_pasan_de_n_sobre_k_mas_uno_004_SC005(self):
        esperado = self.partida.acciones_jugador // K_POR_DEFECTO + 1
        self.assertLessEqual(self.partida.linea.copias(), esperado)

    def test_la_memoria_no_crece_como_acciones_por_estado_004_FR024(self):
        pocas, _ = jugar(K_POR_DEFECTO, 200, 47)
        muchas, _ = jugar(K_POR_DEFECTO, 800, 47)
        self.assertEqual(muchas.acciones_jugador, 4 * pocas.acciones_jugador)
        copias_pocas = pocas.linea.copias()
        copias_muchas = muchas.linea.copias()
        self.assertLessEqual(copias_muchas, 4 * copias_pocas + 1)
        self.assertLess(copias_muchas, muchas.acciones_jugador)

    def test_k_mas_grande_usa_menos_copias_004_FR020(self):
        chica, _ = jugar(10, 600, 47)
        grande, _ = jugar(200, 600, 47)
        self.assertGreater(chica.linea.copias(), grande.linea.copias())

    def test_el_k_por_defecto_es_el_medido(self):
        self.assertEqual(K_POR_DEFECTO, 100)


if __name__ == '__main__':
    unittest.main()
