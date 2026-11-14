"""T055: SC-004, el trabajo de decidir depende de la región dentro del rango, no del tamaño de la cripta.

Requisito: FR-030.
"""
import unittest

from src.modelos.cazador import COMPARTIDO, INDIVIDUAL, DecisorCazadores
from src.servicios import generador_criptas as gc
from tests.referencia_cazador import distancias_desde_referencia

RANGO = 300


def _criptas():
    base_g = gc.generar(4, 14, 14, costo_min=40, costo_max=160)
    jugador = base_g.id_sala((14 // 2) * 14 + 7)
    base = gc.cargar_cripta_sintetica(gc.fuente_sintetica(gc.fragmentos(base_g)))
    # Pasillo de la ampliación con costo > 2 * RANGO: tampoco alcanza la región de un cazador cercano.
    grande = gc.cargar_cripta_sintetica(gc.fuente_sintetica(
        gc.cripta_ampliada_x10(4, 14, 14, jugador, 2 * RANGO, costo_min=40, costo_max=160)))
    return base, grande, jugador


def _cazador_cercano(cripta, jugador):
    for salida in cripta.sala(jugador).salidas:
        if salida is not None:
            return salida.destino
    raise AssertionError('el jugador no tiene vecinas')


def _examinadas(cripta, modo, cazador, rango, jugador):
    decisor = DecisorCazadores(cripta, modo, reutilizar=False)
    decisor.decidir(cripta.sala(cazador), rango, cripta.sala(jugador))
    return decisor


class TestEscala(unittest.TestCase):

    def test_mismo_numero_de_salas_examinadas_x1_y_x10_FR030(self):
        base, grande, jugador = _criptas()
        self.assertEqual(len(grande), 10 * len(base))
        cazador = _cazador_cercano(base, jugador)
        for modo in (COMPARTIDO, INDIVIDUAL):
            with self.subTest(modo=modo):
                en_base = _examinadas(base, modo, cazador, RANGO, jugador).buscador.examinadas
                en_grande = _examinadas(grande, modo, cazador, RANGO, jugador).buscador.examinadas
                self.assertEqual(en_base, en_grande)
                self.assertLess(en_base, len(base))

    def test_ninguna_sala_examinada_mas_alla_del_rango_salvo_el_borde_FR030(self):
        base, grande, jugador = _criptas()
        cazador = _cazador_cercano(grande, jugador)
        for modo, origen in ((COMPARTIDO, jugador), (INDIVIDUAL, cazador)):
            with self.subTest(modo=modo):
                decisor = _examinadas(grande, modo, cazador, RANGO, jugador)
                registro = decisor.buscador.registro
                dist = distancias_desde_referencia(grande, origen, len(grande))
                for sala in grande.salas():
                    i = sala.indice
                    if registro.asentada(i):
                        self.assertLessEqual(dist[sala.id], RANGO)
                    elif registro.tiene(i):  # borde: vecina de una sala asentada
                        vecinas_asentadas = [s for s in sala.salidas if s is not None and registro.asentada(s.sala_destino.indice)]
                        self.assertTrue(vecinas_asentadas)

    def test_rangos_mezclados_el_pequeno_solo_paga_su_region_FR030(self):
        """Hallazgo H1: con un cazador de rango 100 junto a otro de rango 2000."""
        base, grande, jugador = _criptas()
        cazador = _cazador_cercano(grande, jugador)
        decisor = DecisorCazadores(grande, COMPARTIDO)
        decisor.decidir(grande.sala(cazador), 100, grande.sala(jugador))
        solo_pequeno = decisor.salas_examinadas_total
        registro = decisor.buscador.registro
        dist = distancias_desde_referencia(grande, jugador, len(grande))
        for sala in grande.salas():
            if registro.asentada(sala.indice):
                self.assertLessEqual(dist[sala.id], 100)
        decisor.decidir(grande.sala(cazador), 2000, grande.sala(jugador))
        self.assertGreater(decisor.salas_examinadas_total, solo_pequeno)  # el grande extiende y paga lo suyo
        self.assertEqual(decisor.busquedas, 1)


if __name__ == '__main__':
    unittest.main()
