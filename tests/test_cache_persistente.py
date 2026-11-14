import os
import tempfile
import unittest
from src.estructuras_datos.cache_fichas import CacheFichas
from src.modelos.fichas import ARMA, ARMADURA, ERRANTE, FichaEnemigo, FichaObjeto, FichaTrampa
from src.servicios.cache_persistente import cargar_cache, guardar_cache

class PruebasCachePersistente(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, 'cache.json')

    def test_guardar_y_cargar_conserva_las_fichas(self):
        cache = CacheFichas(10)
        cache.poner('itm_daga', FichaObjeto('itm_daga', ARMA, 'Daga', 2, 15, ataque_bonus=3))
        cache.poner('itm_cota', FichaObjeto('itm_cota', ARMADURA, 'Cota', 5, 30, defensa_bonus=2))
        cache.poner('ent_rata', FichaEnemigo('ent_rata', 'Rata', 12, 5, 1, 150, ERRANTE, suelta=['itm_daga']))
        cache.poner('trp_dardos', FichaTrampa('trp_dardos', 'Dardos', 4, 300))
        guardar_cache(cache, self.ruta, version_catalogo='k1')
        restaurada = cargar_cache(self.ruta, version_catalogo='k1', capacidad=10)
        self.assertEqual(len(restaurada), 4)
        self.assertEqual(restaurada.obtener('itm_daga').ataque_bonus, 3)
        self.assertEqual(restaurada.obtener('ent_rata').suelta, ('itm_daga',))
        self.assertEqual(restaurada.obtener('trp_dardos').rearme, 300)

    def test_version_distinta_descarta_la_cache_guardada(self):
        cache = CacheFichas(5)
        cache.poner('itm_daga', FichaObjeto('itm_daga', ARMA, 'Daga', 2, 15, ataque_bonus=3))
        guardar_cache(cache, self.ruta, version_catalogo='k1')
        restaurada = cargar_cache(self.ruta, version_catalogo='k2', capacidad=5)
        self.assertEqual(len(restaurada), 0)

    def test_archivo_inexistente_devuelve_cache_vacia(self):
        restaurada = cargar_cache(self.ruta, version_catalogo='k1', capacidad=5)
        self.assertEqual(len(restaurada), 0)

    def test_archivo_corrupto_devuelve_cache_vacia(self):
        with open(self.ruta, 'w', encoding='utf-8') as archivo:
            archivo.write('{esto no es json valido')
        restaurada = cargar_cache(self.ruta, version_catalogo='k1', capacidad=5)
        self.assertEqual(len(restaurada), 0)

    def test_conserva_el_orden_de_uso_reciente(self):
        cache = CacheFichas(10)
        cache.poner('a', FichaObjeto('a', ARMA, 'A', 1, 1, ataque_bonus=1))
        cache.poner('b', FichaObjeto('b', ARMA, 'B', 1, 1, ataque_bonus=1))
        cache.obtener('a')
        guardar_cache(cache, self.ruta, version_catalogo='k1')
        restaurada = cargar_cache(self.ruta, version_catalogo='k1', capacidad=1)
        self.assertEqual(len(restaurada), 1)
        self.assertIn('a', restaurada)
        self.assertNotIn('b', restaurada)
if __name__ == '__main__':
    unittest.main()
