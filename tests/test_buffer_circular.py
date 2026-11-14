import unittest
from src.estructuras_datos.buffer_circular import BufferCircular

class PruebasBufferCircular(unittest.TestCase):

    def test_menos_que_capacidad(self):
        b = BufferCircular(20)
        for i in range(5):
            b.agregar(i)
        self.assertEqual(b.elementos(), [0, 1, 2, 3, 4])
        self.assertEqual(len(b), 5)

    def test_conserva_solo_los_ultimos(self):
        b = BufferCircular(20)
        for i in range(1000):
            b.agregar(i)
        self.assertEqual(b.elementos(), list(range(980, 1000)))
        self.assertEqual(len(b), 20)

    def test_memoria_constante(self):
        b = BufferCircular(20)
        for i in range(100000):
            b.agregar(i)
        self.assertEqual(len(b._datos), 20)

    def test_capacidad_invalida(self):
        for c in (0, -3, None):
            with self.assertRaises(ValueError):
                BufferCircular(c)
if __name__ == '__main__':
    unittest.main()
