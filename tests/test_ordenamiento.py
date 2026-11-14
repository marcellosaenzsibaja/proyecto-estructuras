import random
import unittest
from src.estructuras_datos.ordenamiento import UMBRAL_DESORDEN, UMBRAL_TAMANO, _proporcion_de_desorden, insercion, mezcla, ordenar

class PruebasOrdenamiento(unittest.TestCase):

    def test_insercion_ordena(self):
        datos = [5, 3, 8, 1, 9, 2]
        self.assertEqual(insercion(datos), [1, 2, 3, 5, 8, 9])
        self.assertEqual(datos, [5, 3, 8, 1, 9, 2])

    def test_mezcla_ordena(self):
        datos = [5, 3, 8, 1, 9, 2]
        self.assertEqual(mezcla(datos), [1, 2, 3, 5, 8, 9])
        self.assertEqual(datos, [5, 3, 8, 1, 9, 2])

    def test_estables_con_clave(self):
        datos = [('b', 1), ('a', 1), ('a', 2), ('c', 1)]
        esperado = [('a', 1), ('a', 2), ('b', 1), ('c', 1)]
        self.assertEqual(insercion(datos, clave=lambda t: t[0]), esperado)
        self.assertEqual(mezcla(datos, clave=lambda t: t[0]), esperado)

    def test_contra_referencia_aleatoria(self):
        azar = random.Random(7)
        for _ in range(30):
            datos = [azar.randint(-50, 50) for _ in range(azar.randint(0, 40))]
            referencia = _referencia(datos)
            self.assertEqual(insercion(datos), referencia)
            self.assertEqual(mezcla(datos), referencia)
            self.assertEqual(ordenar(datos), referencia)

    def test_ordenar_elige_insercion_en_listas_pequenas(self):
        datos = list(range(UMBRAL_TAMANO, 0, -1))
        self.assertLessEqual(len(datos), UMBRAL_TAMANO)
        self.assertEqual(ordenar(datos), insercion(datos))

    def test_ordenar_elige_insercion_si_esta_casi_ordenada(self):
        datos = list(range(200))
        datos[150], datos[151] = (datos[151], datos[150])
        self.assertLess(_proporcion_de_desorden(datos, None), UMBRAL_DESORDEN)
        self.assertEqual(ordenar(datos), mezcla(datos))

    def test_ordenar_elige_mezcla_con_datos_grandes_y_desordenados(self):
        azar = random.Random(11)
        datos = list(range(200))
        azar.shuffle(datos)
        self.assertGreater(_proporcion_de_desorden(datos, None), UMBRAL_DESORDEN)
        self.assertEqual(ordenar(datos), mezcla(datos))

    def test_listas_vacia_y_de_un_elemento(self):
        self.assertEqual(insercion([]), [])
        self.assertEqual(mezcla([]), [])
        self.assertEqual(ordenar([]), [])
        self.assertEqual(ordenar([7]), [7])

def _referencia(datos):
    copia = list(datos)
    for i in range(1, len(copia)):
        j = i
        while j > 0 and copia[j - 1] > copia[j]:
            copia[j - 1], copia[j] = (copia[j], copia[j - 1])
            j -= 1
    return copia
if __name__ == '__main__':
    unittest.main()
