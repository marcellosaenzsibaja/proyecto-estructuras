"""Rendimiento del mapa conocido y del paso de «ir a» (spec 003, FR-050 a FR-053)."""
import gc
import time
import unittest

from src.servicios.banco_mapa import LIMITE_PASO_MS, _partida_con_mapa_completo, medir_consultas, medir_exploracion


class TestPasoDeViaje(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.partida = _partida_con_mapa_completo(20, 20, 31)
        cls.salas = list(cls.partida.cripta.salas())

    def test_un_paso_queda_bajo_cinco_ms_003_FR053_SC003(self):
        """400 salas: la escala de la cripta de referencia (ver DECISIONES §P2 5.3)."""
        destino = self.salas[-1].id
        self.partida.jugador.sala_id = self.salas[0].id
        self.partida.ruta_conocida(destino)
        gc.collect()
        gc.disable()
        try:
            peor = 0.0
            for i in range(30):
                self.partida.jugador.sala_id = self.salas[(i * 53) % len(self.salas)].id
                inicio = time.perf_counter()
                self.partida.ruta_conocida(destino)
                peor = max(peor, (time.perf_counter() - inicio) * 1000)
        finally:
            gc.enable()
        self.assertLess(peor, LIMITE_PASO_MS, f'peor paso {peor:.3f} ms con 400 salas conocidas')

    def test_solo_examina_salas_conocidas_003_FR030(self):
        destino = self.salas[-1].id
        self.partida.jugador.sala_id = self.salas[0].id
        self.partida.ruta_conocida(destino)
        self.assertLessEqual(self.partida.buscador_conocido.examinadas,
                             self.partida.mapa.total_exploradas())


class TestConteos(unittest.TestCase):

    def test_la_consulta_no_se_encarece_con_el_mapa_003_FR050(self):
        filas = medir_consultas(tamanos=((10, 10), (40, 40)), consultas=40000)
        pequeno = filas[0]['ns_por_consulta']
        grande = filas[1]['ns_por_consulta']
        self.assertLess(grande, pequeno * 3, f'{pequeno} ns -> {grande} ns')

    def test_explorar_cuesta_lo_mismo_con_mapa_grande_003_FR051_SC004(self):
        filas = medir_exploracion()
        self.assertEqual(filas[0]['salas_tocadas'], filas[1]['salas_tocadas'])
        self.assertEqual(filas[0]['puertas_tocadas'], filas[1]['puertas_tocadas'])
        self.assertGreater(filas[1]['exploradas_antes'], filas[0]['exploradas_antes'] * 5)


if __name__ == '__main__':
    unittest.main()
