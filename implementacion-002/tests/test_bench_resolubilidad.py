"""Bench de resolubilidad y equivalencia con la alternativa ingenua (spec 002, US5).

Los identificadores FR-NNN de estas pruebas son los de specs/002-verificacion-resolubilidad/spec.md.
"""
import unittest

from src.modelos.resolubilidad import verificar
from src.servicios import banco_resolubilidad as br
from src.servicios.banco_pruebas import formatear


class TestEquivalenciaConLaAlternativaIngenua(unittest.TestCase):

    def test_cadenas_mismo_orden_y_veredicto_002_FR030(self):
        for cantidad in (1, 5, 30):
            cripta, llaves = br.cripta_cadena(3, 150, cantidad)
            reporte = verificar(cripta, llaves)
            orden, resoluble = br.verificar_ingenuo(cripta, llaves)
            self.assertTrue(reporte.resoluble)
            self.assertEqual(reporte.orden_llaves, orden)
            self.assertEqual(reporte.resoluble, resoluble)
            self.assertEqual(len(orden), cantidad)

    def test_cuadriculas_sembradas_mismo_orden_y_veredicto_002_FR030(self):
        for semilla in range(1, 13):
            cripta, llaves = br.cripta_cuadricula(semilla, 9, 9, prob_cerrada=0.25)
            reporte = verificar(cripta, llaves)
            orden, resoluble = br.verificar_ingenuo(cripta, llaves)
            self.assertEqual(reporte.orden_llaves, orden, f'semilla {semilla}')
            self.assertEqual(reporte.resoluble, resoluble, f'semilla {semilla}')


class TestBench(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.resultados = br.ejecutar_resolubilidad(rapido=True)

    def test_incluye_cadenas_y_cuadricula_002_FR030(self):
        filas = self.resultados['resolubilidad']
        self.assertGreaterEqual(len(filas), 4)
        for fila in filas:
            self.assertEqual(fila['mismo_orden'], 'si')
            self.assertIn('ms_ingenuo', fila)

    def test_cripta_sintetica_es_determinista_por_semilla_002_FR030(self):
        a = br.cripta_cadena(5, 80, 10)[1]
        b = br.cripta_cadena(5, 80, 10)[1]
        self.assertEqual([(l.id, l.sala) for l in a], [(l.id, l.sala) for l in b])
        c = br.cripta_cadena(6, 80, 10)[1]
        self.assertNotEqual([l.sala for l in a], [l.sala for l in c])

    def test_determinismo_del_orden_002_FR009(self):
        fila = self.resultados['resolubilidad_determinismo'][0]
        self.assertEqual(fila['mismo_orden'], 'si')

    def test_formato_del_bench_002_FR030(self):
        texto = formatear(self.resultados)
        self.assertIn('[resolubilidad]', texto)
        self.assertIn('ms_reactivo=', texto)
        self.assertIn('ms_ingenuo=', texto)

    def test_mil_salas_se_verifican_en_menos_de_200_ms_002_FR026(self):
        cripta, llaves = br.cripta_cadena(2026, br.SALAS_REFERENCIA, 100)
        ms, _ = br._tiempo(lambda: verificar(cripta, llaves), 3)
        self.assertLess(ms, br.LIMITE_MS)

    def test_cadena_invalida_002_FR030(self):
        with self.assertRaises(ValueError):
            br.cripta_cadena(1, 10, 0)
        with self.assertRaises(ValueError):
            br.cripta_cadena(1, 10, 9)


if __name__ == '__main__':
    unittest.main()
