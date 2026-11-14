"""T006: montículo binario de mínimos con eliminación perezosa (research R1, tasks T010).

Requisitos: FR-014 (orden determinista), FR-030 (memoria acotada por la región).
"""
import random
import unittest

from src.estructuras_datos.monticulo import MonticuloMin


class TestOrden(unittest.TestCase):

    def test_orden_por_costo_y_luego_indice_FR014(self):
        m = MonticuloMin()
        for par in [(30, 4), (10, 9), (30, 2), (10, 3), (20, 1)]:
            m.insertar(*par)
        extraidos = [m.extraer_minimo() for _ in range(5)]
        self.assertEqual(extraidos, [(10, 3), (10, 9), (20, 1), (30, 2), (30, 4)])

    def test_minimo_no_extrae_FR030(self):
        m = MonticuloMin()
        m.insertar(5, 1)
        m.insertar(3, 2)
        self.assertEqual(m.minimo(), (3, 2))
        self.assertEqual(len(m), 2)
        self.assertEqual(m.extraer_minimo(), (3, 2))


class TestEliminacionPerezosa(unittest.TestCase):

    def test_entrada_obsoleta_queda_y_se_reconoce_FR014(self):
        """Insertar (50, 7) y después (30, 7): la de 30 sale primero; la de 50 sigue y es obsoleta."""
        m = MonticuloMin()
        distancia = [None] * 10
        asentada = [False] * 10
        m.insertar(50, 7)
        distancia[7] = 50
        m.insertar(30, 7)
        distancia[7] = 30
        self.assertEqual(len(m), 2)
        asentamientos = 0
        while not m.esta_vacio():
            costo, sala = m.extraer_minimo()
            if asentada[sala] or costo != distancia[sala]:
                continue  # obsoleta (regla de T010)
            asentada[sala] = True
            asentamientos += 1
        self.assertEqual(asentamientos, 1)

    def test_tamano_es_inserciones_menos_extracciones_FR030(self):
        m = MonticuloMin()
        for i in range(20):
            m.insertar(i % 5, i)
        for _ in range(7):
            m.extraer_minimo()
        self.assertEqual(len(m), 13)


class TestBordes(unittest.TestCase):

    def test_extraer_en_vacio_lanza_FR030(self):
        with self.assertRaises(IndexError):
            MonticuloMin().extraer_minimo()
        with self.assertRaises(IndexError):
            MonticuloMin().minimo()

    def test_vaciar_deja_reutilizable_FR030(self):
        m = MonticuloMin()
        m.insertar(1, 1)
        m.vaciar()
        self.assertTrue(m.esta_vacio())
        m.insertar(4, 2)
        self.assertEqual(m.extraer_minimo(), (4, 2))


class TestContraReferenciaLineal(unittest.TestCase):

    def test_diez_mil_operaciones_igual_que_lineal_FR014(self):
        rng = random.Random(123)
        m = MonticuloMin()
        lineal = []
        for _ in range(10000):
            if lineal and rng.random() < 0.45:
                mejor = 0
                for i in range(1, len(lineal)):
                    if lineal[i] < lineal[mejor]:
                        mejor = i
                esperado = lineal.pop(mejor)
                self.assertEqual(m.extraer_minimo(), esperado)
            else:
                par = (rng.randint(0, 500), rng.randint(0, 50))
                m.insertar(*par)
                lineal.append(par)
        self.assertEqual(len(m), len(lineal))


if __name__ == '__main__':
    unittest.main()
