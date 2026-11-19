"""Línea de tiempo: entradas, puntos de control, recorte y conteos (spec 004)."""
import unittest

from src.modelos.acciones import Accion, ESPERAR, MOVER, USAR
from src.modelos.direcciones import indice_direccion
from src.modelos.linea_tiempo import CURSOR_SIG, LineaTiempo
from tests.utilidades import construir, pergamino


def _pasillo(largo=6, costos=None):
    conexiones = []
    for i in range(1, largo):
        extra = {} if costos is None else {'costo': costos[i - 1]}
        conexiones.append((i, 'N', i + 1, extra))
    return conexiones


def _partida(k=3, largo=6, contenidos=None, fichas=()):
    partida = construir(_pasillo(largo), contenidos=contenidos, fichas=fichas, semilla=7)
    partida.linea.k = k
    partida.iniciar()
    return partida


def _esperar(partida, veces):
    for _ in range(veces):
        partida.ejecutar(Accion(ESPERAR))


class TestLineaTiempo(unittest.TestCase):

    def test_k_menor_que_uno_se_rechaza_004_FR021(self):
        with self.assertRaises(ValueError):
            LineaTiempo(0)

    def test_registra_una_entrada_por_accion_004_FR023(self):
        partida = _partida()
        _esperar(partida, 5)
        self.assertEqual(partida.linea.tamano(), 5)
        self.assertEqual(partida.acciones_jugador, 5)

    def test_un_punto_de_control_cada_k_acciones_004_FR020(self):
        for k in (1, 3, 10):
            partida = _partida(k=k)
            _esperar(partida, 20)
            esperado = 20 // k + 1
            self.assertEqual(partida.linea.copias(), esperado, f'k={k}')

    def test_copias_no_pasan_de_n_sobre_k_mas_uno_004_SC005(self):
        partida = _partida(k=7)
        _esperar(partida, 50)
        self.assertLessEqual(partida.linea.copias(), 50 // 7 + 1)

    def test_punto_del_instante_cero_siempre_existe_004_FR026(self):
        partida = _partida(k=100)
        _esperar(partida, 3)
        punto = partida.linea.punto_en_o_antes(0)
        self.assertIsNotNone(punto)
        self.assertEqual(punto.tiempo, 0)
        self.assertEqual(punto.numero, 0)

    def test_nunca_reaplica_mas_de_k_acciones_004_FR022_SC004(self):
        for k in (1, 4, 9):
            partida = _partida(k=k)
            _esperar(partida, 30)
            for t in range(0, partida.reloj.tiempo_virtual + 1, 25):
                resumen, error = partida.historia_en(t)
                self.assertIsNone(error, (k, t))
                self.assertLessEqual(partida.linea.reaplicadas, k, (k, t))

    def test_el_punto_localizado_no_supera_el_instante_004_FR026(self):
        partida = _partida(k=4)
        _esperar(partida, 25)
        for t in range(0, partida.reloj.tiempo_virtual + 1, 10):
            punto = partida.linea.punto_en_o_antes(t)
            self.assertLessEqual(punto.tiempo, t)

    def test_registra_el_cursor_del_inventario_004_FR023(self):
        fichas = (pergamino(), pergamino('itm_perg2'))
        partida = _partida(contenidos=None, fichas=fichas)
        partida.jugador.inventario.agregar(type('O', (), {'uid': 1, 'ficha': fichas[0]})())
        partida.jugador.inventario.agregar(type('O', (), {'uid': 2, 'ficha': fichas[1]})())
        partida.jugador.inventario.ir_al_inicio()
        self.assertTrue(partida.mover_cursor(1))
        self.assertEqual(partida.linea.entradas[-1].tipo, CURSOR_SIG)
        self.assertEqual(partida.linea.entradas[-1].numero, 0)
        self.assertEqual(partida.acciones_jugador, 0)

    def test_recorte_quita_solo_lo_posterior_004_FR015(self):
        partida = _partida(k=2)
        _esperar(partida, 10)
        entradas_antes = partida.linea.tamano()
        copias_antes = partida.linea.copias()
        partida.linea.recortar(7, partida.linea.entradas[6].tiempo)
        self.assertEqual(partida.linea.tamano(), 7)
        self.assertLess(partida.linea.tamano(), entradas_antes)
        self.assertLessEqual(partida.linea.copias(), copias_antes)
        for punto in partida.linea.puntos:
            self.assertLessEqual(punto.numero, 7)

    def test_recorte_conserva_el_punto_que_sigue_valido_004_FR015(self):
        partida = _partida(k=5)
        _esperar(partida, 12)
        partida.linea.recortar(10, partida.linea.entradas[9].tiempo)
        numeros = list(partida.linea.numeros_punto)
        self.assertIn(0, numeros)
        self.assertIn(5, numeros)
        self.assertNotIn(15, numeros)


class TestLineaInerte(unittest.TestCase):

    def test_una_linea_inerte_no_registra_nada_004_FR007(self):
        partida = _partida()
        partida.linea.activa = False
        partida.registra_linea = False
        antes = partida.linea.tamano()
        _esperar(partida, 4)
        self.assertEqual(partida.linea.tamano(), antes)


if __name__ == '__main__':
    unittest.main()
