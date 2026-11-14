import unittest
from src.estructuras_datos.cache_fichas import CacheFichas
from src.modelos.fichas import ARMA, FichaObjeto

def _ficha(id_ficha):
    return FichaObjeto(id_ficha, ARMA, id_ficha, 1, 1, ataque_bonus=1)

class PruebasCacheFichas(unittest.TestCase):

    def test_capacidad_invalida(self):
        with self.assertRaises(ValueError):
            CacheFichas(0)
        with self.assertRaises(ValueError):
            CacheFichas(-1)
        with self.assertRaises(ValueError):
            CacheFichas(True)

    def test_poner_y_obtener(self):
        cache = CacheFichas(3)
        cache.poner('a', _ficha('a'))
        self.assertIn('a', cache)
        self.assertEqual(cache.obtener('a').id, 'a')
        self.assertEqual(cache.aciertos, 1)
        self.assertIsNone(cache.obtener('b'))
        self.assertEqual(cache.fallos, 1)

    def test_desaloja_el_menos_usado_recientemente(self):
        cache = CacheFichas(2)
        cache.poner('a', _ficha('a'))
        cache.poner('b', _ficha('b'))
        cache.poner('c', _ficha('c'))
        self.assertNotIn('a', cache)
        self.assertIn('b', cache)
        self.assertIn('c', cache)
        self.assertEqual(cache.desalojos, 1)

    def test_obtener_refresca_la_posicion(self):
        cache = CacheFichas(2)
        cache.poner('a', _ficha('a'))
        cache.poner('b', _ficha('b'))
        cache.obtener('a')
        cache.poner('c', _ficha('c'))
        self.assertNotIn('b', cache)
        self.assertIn('a', cache)
        self.assertIn('c', cache)

    def test_actualizar_una_clave_existente_no_crece_la_cache(self):
        cache = CacheFichas(2)
        cache.poner('a', _ficha('a'))
        cache.poner('a', _ficha('a-v2'))
        self.assertEqual(len(cache), 1)
        self.assertEqual(cache.obtener('a').nombre, 'a-v2')

    def test_fichas_en_uso_no_se_desalojan(self):
        cache = CacheFichas(2)
        cache.poner('a', _ficha('a'))
        cache.fijar('a')
        cache.poner('b', _ficha('b'))
        cache.poner('c', _ficha('c'))
        self.assertIn('a', cache)
        self.assertTrue(cache.en_uso('a'))
        self.assertNotIn('b', cache)
        self.assertIn('c', cache)
        self.assertEqual(len(cache), 2)
        self.assertEqual(cache.desalojos, 1)

    def test_liberar_permite_desalojar_de_nuevo(self):
        cache = CacheFichas(2)
        cache.poner('a', _ficha('a'))
        cache.fijar('a')
        cache.poner('b', _ficha('b'))
        cache.poner('c', _ficha('c'))
        cache.liberar('a')
        cache.poner('d', _ficha('d'))
        self.assertNotIn('a', cache)

    def test_fijar_cuenta_referencias(self):
        cache = CacheFichas(5)
        cache.poner('a', _ficha('a'))
        cache.fijar('a')
        cache.fijar('a')
        cache.liberar('a')
        self.assertTrue(cache.en_uso('a'))
        cache.liberar('a')
        self.assertFalse(cache.en_uso('a'))

    def test_todas_en_uso_no_desaloja_ninguna(self):
        cache = CacheFichas(2)
        cache.fijar('a')
        cache.poner('a', _ficha('a'))
        cache.fijar('b')
        cache.poner('b', _ficha('b'))
        cache.fijar('c')
        cache.poner('c', _ficha('c'))
        self.assertEqual(cache.desalojos, 0)
        self.assertEqual(len(cache), 3)

    def test_entradas_en_orden_de_uso(self):
        cache = CacheFichas(3)
        cache.poner('a', _ficha('a'))
        cache.poner('b', _ficha('b'))
        cache.poner('c', _ficha('c'))
        cache.obtener('a')
        ids = [id_ficha for id_ficha, _ in cache.entradas_en_orden_de_uso()]
        self.assertEqual(ids, ['a', 'c', 'b'])
if __name__ == '__main__':
    unittest.main()
