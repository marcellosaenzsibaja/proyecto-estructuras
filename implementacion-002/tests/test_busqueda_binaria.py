"""Búsqueda binaria propia (spec 002, FR-010 y FR-027)."""
import unittest

from src.estructuras_datos.busqueda_binaria import buscar


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


if __name__ == '__main__':
    unittest.main()
