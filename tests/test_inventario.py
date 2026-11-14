import unittest
from src.estructuras_datos.inventario import Inventario, InventarioLleno
from src.estructuras_datos.lista_doble import ListaDoble

class PruebasListaDoble(unittest.TestCase):

    def test_recorridos_y_tamano(self):
        lista = ListaDoble()
        for v in 'abc':
            lista.agregar_al_final(v)
        lista.agregar_al_frente('z')
        self.assertEqual(list(lista), ['z', 'a', 'b', 'c'])
        self.assertEqual([n.valor for n in lista.nodos_inversos()], ['c', 'b', 'a', 'z'])
        self.assertEqual(len(lista), 4)

    def test_remover_nodo_en_cualquier_posicion(self):
        lista = ListaDoble()
        nodos = [lista.agregar_al_final(i) for i in range(5)]
        lista.remover_nodo(nodos[2])
        lista.remover_nodo(nodos[0])
        lista.remover_nodo(nodos[4])
        self.assertEqual(list(lista), [1, 3])
        self.assertEqual(len(lista), 2)
        with self.assertRaises(ValueError):
            lista.remover_nodo(nodos[2])

    def test_mover_al_frente_conserva_nodo(self):
        lista = ListaDoble()
        nodos = [lista.agregar_al_final(i) for i in range(4)]
        lista.mover_al_frente(nodos[3])
        lista.mover_al_frente(nodos[3])
        self.assertEqual(list(lista), [3, 0, 1, 2])
        self.assertIs(lista.cabeza, nodos[3])
        self.assertEqual(len(lista), 4)

    def test_vaciar_y_reutilizar(self):
        lista = ListaDoble()
        n = lista.agregar_al_final(1)
        lista.remover_nodo(n)
        self.assertTrue(lista.esta_vacia())
        self.assertIsNone(lista.cabeza)
        self.assertIsNone(lista.cola)
        lista.agregar_al_final(2)
        self.assertEqual(list(lista), [2])

class PruebasInventario(unittest.TestCase):

    def test_capacidad(self):
        inv = Inventario(2)
        inv.agregar('a')
        inv.agregar('b')
        self.assertTrue(inv.esta_lleno())
        with self.assertRaises(InventarioLleno):
            inv.agregar('c')
        inv.soltar_actual()
        self.assertFalse(inv.esta_lleno())
        inv.agregar('c')
        self.assertEqual(list(inv), ['b', 'c'])

    def test_capacidad_invalida(self):
        for c in (0, -1, None, True):
            with self.assertRaises(ValueError):
                Inventario(c)

    def test_recorrido_adelante_y_atras(self):
        inv = Inventario(5)
        for v in 'abc':
            inv.agregar(v)
        self.assertEqual(inv.actual(), 'a')
        self.assertFalse(inv.retroceder())
        self.assertTrue(inv.avanzar())
        self.assertTrue(inv.avanzar())
        self.assertEqual(inv.actual(), 'c')
        self.assertFalse(inv.avanzar())
        self.assertTrue(inv.retroceder())
        self.assertEqual(inv.actual(), 'b')

    def test_soltar_actual_en_cualquier_posicion(self):
        inv = Inventario(5)
        for v in 'abcd':
            inv.agregar(v)
        inv.avanzar()
        self.assertEqual(inv.soltar_actual(), 'b')
        self.assertEqual(inv.actual(), 'c')
        inv.avanzar()
        self.assertEqual(inv.soltar_actual(), 'd')
        self.assertEqual(inv.actual(), 'c')
        self.assertEqual(inv.soltar_actual(), 'c')
        self.assertEqual(inv.actual(), 'a')
        self.assertEqual(inv.soltar_actual(), 'a')
        self.assertIsNone(inv.actual())
        self.assertIsNone(inv.soltar_actual())
        self.assertTrue(inv.esta_vacio())

    def test_equipar_mueve_al_frente_sin_perder_cursor(self):
        inv = Inventario(5)
        for v in 'abc':
            inv.agregar(v)
        inv.avanzar()
        inv.avanzar()
        inv.mover_actual_al_frente()
        self.assertEqual(list(inv), ['c', 'a', 'b'])
        self.assertEqual(inv.actual(), 'c')
        self.assertFalse(inv.retroceder())

    def test_remover_nodo_ajusta_cursor(self):
        inv = Inventario(5)
        nodos = [inv.agregar(v) for v in 'abc']
        inv.remover_nodo(nodos[0])
        self.assertEqual(inv.actual(), 'b')
        inv.remover_nodo(nodos[2])
        self.assertEqual(inv.actual(), 'b')

    def test_agregar_tras_vaciar_reubica_cursor(self):
        inv = Inventario(3)
        inv.agregar('a')
        inv.soltar_actual()
        inv.agregar('b')
        self.assertEqual(inv.actual(), 'b')
if __name__ == '__main__':
    unittest.main()
