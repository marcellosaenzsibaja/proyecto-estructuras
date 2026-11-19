"""Búsqueda binaria propia (spec 002, FR-010 y FR-027; spec 004, FR-026)."""
import unittest

from src.estructuras_datos.busqueda_binaria import buscar, ultimo_menor_o_igual


class TestBusquedaBinaria(unittest.TestCase):

    def test_encuentra_cada_elemento_002_FR010(self):
        lista = ['a', 'c', 'e', 'g', 'k', 'm']
        for i in range(len(lista)):
            self.assertEqual(buscar(lista, lista[i]), i)

    def test_elemento_ausente_002_FR010(self):
        lista = ['b', 'd', 'f']
        self.assertEqual(buscar(lista, 'a'), -1)
        self.assertEqual(buscar(lista, 'c'), -1)
        self.assertEqual(buscar(lista, 'z'), -1)

    def test_lista_vacia_y_unitaria_002_FR010(self):
        self.assertEqual(buscar([], 'a'), -1)
        self.assertEqual(buscar(['a'], 'a'), 0)
        self.assertEqual(buscar(['a'], 'b'), -1)

    def test_con_clave_002_FR027(self):
        lista = [(1, 'x'), (4, 'y'), (9, 'z')]
        self.assertEqual(buscar(lista, 4, lambda par: par[0]), 1)
        self.assertEqual(buscar(lista, 5, lambda par: par[0]), -1)

    def test_orden_textual_no_numerico_002_FR010(self):
        lista = ['k_10', 'k_2', 'k_3']
        self.assertEqual(buscar(lista, 'k_2'), 1)


class TestUltimoMenorOIgual(unittest.TestCase):

    def test_coincidencia_exacta_004_FR026(self):
        lista = [0, 100, 250, 600, 1000]
        for i in range(len(lista)):
            self.assertEqual(ultimo_menor_o_igual(lista, lista[i]), i)

    def test_valor_entre_dos_elementos_004_FR026(self):
        lista = [0, 100, 250, 600, 1000]
        self.assertEqual(ultimo_menor_o_igual(lista, 99), 0)
        self.assertEqual(ultimo_menor_o_igual(lista, 101), 1)
        self.assertEqual(ultimo_menor_o_igual(lista, 599), 2)
        self.assertEqual(ultimo_menor_o_igual(lista, 1500), 4)

    def test_menor_que_todos_devuelve_menos_uno_004_FR026(self):
        self.assertEqual(ultimo_menor_o_igual([10, 20, 30], 9), -1)

    def test_lista_vacia_y_unitaria_004_FR026(self):
        self.assertEqual(ultimo_menor_o_igual([], 5), -1)
        self.assertEqual(ultimo_menor_o_igual([5], 5), 0)
        self.assertEqual(ultimo_menor_o_igual([5], 4), -1)
        self.assertEqual(ultimo_menor_o_igual([5], 6), 0)

    def test_valores_repetidos_devuelve_el_ultimo_004_FR026(self):
        lista = [0, 100, 100, 100, 250]
        self.assertEqual(ultimo_menor_o_igual(lista, 100), 3)

    def test_con_clave_004_FR026(self):
        lista = [(0, 'a'), (100, 'b'), (250, 'c')]
        self.assertEqual(ultimo_menor_o_igual(lista, 200, lambda par: par[0]), 1)

    def test_coincide_con_una_busqueda_lineal_004_FR026(self):
        lista = [0, 3, 3, 7, 11, 11, 11, 20, 41]
        for valor in range(-2, 45):
            esperado = -1
            for i, actual in enumerate(lista):
                if actual <= valor:
                    esperado = i
            self.assertEqual(ultimo_menor_o_igual(lista, valor), esperado, valor)


if __name__ == '__main__':
    unittest.main()
