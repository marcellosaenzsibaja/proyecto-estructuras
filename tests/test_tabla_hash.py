import random
import unittest
from src.estructuras_datos.tabla_hash import TablaHash, codigo_hash

class PruebasTablaHash(unittest.TestCase):

    def test_poner_obtener_actualizar(self):
        t = TablaHash()
        t.poner('a', 1)
        t.poner(7, 'siete')
        t.poner('a', 2)
        self.assertEqual(t.obtener('a'), 2)
        self.assertEqual(t.obtener(7), 'siete')
        self.assertEqual(len(t), 2)

    def test_ausentes(self):
        t = TablaHash()
        self.assertIsNone(t.obtener('x'))
        self.assertEqual(t.obtener('x', 5), 5)
        self.assertFalse('x' in t)
        with self.assertRaises(KeyError):
            t['x']
        with self.assertRaises(KeyError):
            t.eliminar('x')

    def test_claves_int_y_str_no_se_confunden(self):
        t = TablaHash()
        t.poner(1, 'int')
        t.poner('1', 'str')
        self.assertEqual(t.obtener(1), 'int')
        self.assertEqual(t.obtener('1'), 'str')

    def test_tipos_no_soportados(self):
        t = TablaHash()
        for clave in (1.5, None, (1, 2), True):
            with self.assertRaises(TypeError):
                t.poner(clave, 1)

    def test_eliminar(self):
        t = TablaHash()
        for i in range(100):
            t.poner(i, i * 2)
        self.assertEqual(t.eliminar(40), 80)
        self.assertFalse(40 in t)
        self.assertEqual(len(t), 99)

    def test_crecimiento_conserva_datos(self):
        t = TablaHash()
        for i in range(5000):
            t.poner(f'k{i}', i)
        self.assertEqual(len(t), 5000)
        for i in range(5000):
            self.assertEqual(t.obtener(f'k{i}'), i)

    def test_contra_referencia_aleatoria(self):
        azar = random.Random(42)
        t = TablaHash()
        ref = {}
        for _ in range(20000):
            clave = azar.choice([azar.randint(-50, 300), f's{azar.randint(0, 300)}'])
            op = azar.random()
            if op < 0.6:
                valor = azar.randint(0, 10 ** 6)
                t.poner(clave, valor)
                ref[clave] = valor
            elif op < 0.8:
                if clave in ref:
                    self.assertEqual(t.eliminar(clave), ref.pop(clave))
                else:
                    self.assertFalse(clave in t)
            else:
                self.assertEqual(t.obtener(clave), ref.get(clave))
            self.assertEqual(len(t), len(ref))
        self.assertEqual(sorted(map(str, t.claves())), sorted(map(str, ref)))

    def test_iteracion_determinista(self):

        def construir():
            t = TablaHash()
            for i in range(200):
                t.poner(f'id_{i}', i)
                t.poner(i, i)
            return list(t.items())
        self.assertEqual(construir(), construir())

    def test_codigo_hash_estable(self):
        self.assertEqual(codigo_hash('ent_rata_gigante'), codigo_hash('ent_rata_gigante'))
        self.assertEqual(codigo_hash(-1), codigo_hash(-1))
if __name__ == '__main__':
    unittest.main()
