"""Selección de la llave de menor id con el montículo propio (spec 002, FR-010)."""
import random
import unittest

from src.estructuras_datos.monticulo import MonticuloMin


class TestMonticuloDeLlaves(unittest.TestCase):

    def test_extrae_los_indices_en_orden_creciente_002_FR010(self):
        indices = list(range(40))
        random.Random(3).shuffle(indices)
        monticulo = MonticuloMin()
        for j in indices:
            monticulo.insertar(j, j)
        extraidos = []
        while len(monticulo) > 0:
            extraidos.append(monticulo.extraer_minimo()[1])
        self.assertEqual(extraidos, list(range(40)))

    def test_inserciones_intercaladas_conservan_el_minimo_002_FR010(self):
        monticulo = MonticuloMin()
        monticulo.insertar(5, 5)
        monticulo.insertar(2, 2)
        self.assertEqual(monticulo.extraer_minimo()[1], 2)
        monticulo.insertar(1, 1)
        self.assertEqual(monticulo.extraer_minimo()[1], 1)
        self.assertEqual(monticulo.extraer_minimo()[1], 5)


if __name__ == '__main__':
    unittest.main()
