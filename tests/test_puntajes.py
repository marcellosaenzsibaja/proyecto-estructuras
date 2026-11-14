import os
import tempfile
import unittest
from src.servicios.puntajes import calcular_puntaje, cargar, mejores, registrar

class _PartidaFalsa:

    def __init__(self, cripta_id, semilla, estado, acciones, enemigos, tiempo):
        self.cripta = type('C', (), {'datos': type('D', (), {'id': cripta_id})()})()
        self.semilla = semilla
        self.estado = estado
        self.acciones_jugador = acciones
        self.enemigos_derrotados = enemigos
        self.reloj = type('R', (), {'tiempo_virtual': tiempo})()

class PruebasPuntajes(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, 'puntajes.json')

    def test_sin_archivo_devuelve_lista_vacia(self):
        self.assertEqual(cargar(self.ruta), [])
        self.assertEqual(mejores(self.ruta), [])

    def test_registrar_y_ordenar_por_puntaje(self):
        peor = _PartidaFalsa('c1', 1, 'derrota', 2, 1, 500)
        mejor = _PartidaFalsa('c1', 2, 'victoria', 10, 5, 300)
        registrar(peor, self.ruta)
        registrar(mejor, self.ruta)
        tabla = mejores(self.ruta)
        self.assertEqual(len(tabla), 2)
        self.assertEqual(tabla[0]['semilla'], 2)
        self.assertGreaterEqual(tabla[0]['puntaje'], tabla[1]['puntaje'])

    def test_victoria_puntua_mas_que_derrota_en_igualdad_de_condiciones(self):
        derrota = _PartidaFalsa('c1', 1, 'derrota', 5, 3, 100)
        victoria = _PartidaFalsa('c1', 2, 'victoria', 5, 3, 100)
        self.assertGreater(calcular_puntaje(victoria), calcular_puntaje(derrota))

    def test_mejores_respeta_la_cantidad(self):
        for i in range(5):
            registrar(_PartidaFalsa('c1', i, 'derrota', i, i, 50), self.ruta)
        self.assertEqual(len(mejores(self.ruta, cantidad=3)), 3)
if __name__ == '__main__':
    unittest.main()
