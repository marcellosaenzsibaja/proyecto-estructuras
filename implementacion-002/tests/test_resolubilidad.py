"""Verificación de resolubilidad de criptas resolubles (spec 002, US2; Apéndice B casos 2 y 3).

Los identificadores FR-NNN de estas pruebas son los de specs/002-verificacion-resolubilidad/spec.md.
"""
import unittest

from src.modelos.resolubilidad import LlaveInfo, verificar
from tests.utilidades_cripta import conexion, cripta_con_llaves


def _verificar(conexiones, llaves, **datos):
    cripta, _ = cripta_con_llaves(conexiones, llaves, **datos)
    informacion = []
    for llave in llaves:
        informacion.append(LlaveInfo(llave[0], llave[1], llave[2] if len(llave) > 2 else None))
    return verificar(cripta, informacion)


class TestCadenaLineal(unittest.TestCase):

    def test_cadena_de_llaves_obligatoria_002_FR007_FR008(self):
        conexiones = [conexion(1, 'E', 2), conexion(2, 'E', 3, cerrada=True, llave='k_a'), conexion(3, 'E', 4, cerrada=True, llave='k_b')]
        reporte = _verificar(conexiones, [('k_b', 3), ('k_a', 1)], sala_salida=4, llave_salida='k_b')
        self.assertTrue(reporte.resoluble)
        self.assertEqual(reporte.orden_llaves, ['k_a', 'k_b'])

    def test_cada_llave_despues_de_las_necesarias_002_FR008(self):
        conexiones = [conexion(1, 'E', 2, cerrada=True, llave='k_c'), conexion(2, 'E', 3, cerrada=True, llave='k_b'),
                      conexion(3, 'E', 4, cerrada=True, llave='k_a')]
        reporte = _verificar(conexiones, [('k_c', 1), ('k_b', 2), ('k_a', 3)], sala_salida=4, llave_salida='k_a')
        self.assertTrue(reporte.resoluble)
        self.assertEqual(reporte.orden_llaves, ['k_c', 'k_b', 'k_a'])

    def test_sin_llaves_y_sin_puerta_de_salida_no_es_resoluble_002_FR007(self):
        conexiones = [conexion(1, 'E', 2)]
        reporte = _verificar(conexiones, [], sala_salida=2)
        self.assertFalse(reporte.resoluble)

    def test_llegar_a_la_salida_sin_puerta_que_requiera_la_llave_no_basta_002_FR007(self):
        conexiones = [conexion(1, 'E', 2)]
        reporte = _verificar(conexiones, [('k_x', 1)], sala_salida=2, llave_salida='k_x')
        self.assertFalse(reporte.resoluble)


class TestDeterminismo(unittest.TestCase):

    def test_varios_ordenes_validos_producen_el_mismo_orden_002_FR009_FR010(self):
        conexiones = [conexion(1, 'E', 2, cerrada=True, llave='k_c')]
        llaves = [('k_c', 1), ('k_a', 1), ('k_b', 1)]
        primero = _verificar(conexiones, llaves, sala_salida=2, llave_salida='k_c')
        segundo = _verificar(conexiones, llaves, sala_salida=2, llave_salida='k_c')
        self.assertEqual(primero.orden_llaves, ['k_a', 'k_b', 'k_c'])
        self.assertEqual(primero.orden_llaves, segundo.orden_llaves)

    def test_el_orden_de_entrada_de_las_llaves_no_altera_el_resultado_002_FR009(self):
        conexiones = [conexion(1, 'E', 2, cerrada=True, llave='k_z'), conexion(2, 'E', 3)]
        a = _verificar(conexiones, [('k_z', 1), ('k_m', 2), ('k_a', 1)], sala_salida=3, llave_salida='k_z')
        b = _verificar(conexiones, [('k_a', 1), ('k_z', 1), ('k_m', 2)], sala_salida=3, llave_salida='k_z')
        self.assertEqual(a.orden_llaves, b.orden_llaves)
        self.assertEqual(a.orden_llaves, ['k_a', 'k_z', 'k_m'])

    def test_desempate_lexicografico_no_numerico_002_FR010(self):
        conexiones = [conexion(1, 'E', 2)]
        reporte = _verificar(conexiones, [('k_2', 1), ('k_10', 1)], sala_salida=2, llave_salida='k_2')
        self.assertEqual(reporte.orden_llaves, ['k_10', 'k_2'])


class TestUbicacionDeLlaves(unittest.TestCase):

    def test_llave_de_enemigo_se_ubica_en_su_sala_inicial_002_FR006(self):
        conexiones = [conexion(1, 'E', 2), conexion(2, 'E', 3, cerrada=True, llave='k_e')]
        reporte = _verificar(conexiones, [('k_e', 2, 'e-1203')], sala_salida=3, llave_salida='k_e')
        self.assertTrue(reporte.resoluble)
        self.assertEqual(reporte.orden_llaves, ['k_e'])

    def test_llave_de_enemigo_en_sala_inalcanzable_no_se_obtiene_002_FR006(self):
        conexiones = [conexion(1, 'E', 2), conexion(2, 'E', 3, cerrada=True, llave='k_e')]
        reporte = _verificar(conexiones, [('k_e', 3, 'e-77')], sala_salida=3, llave_salida='k_e')
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.llaves_no_obtenibles[0].enemigo, 'e-77')
        self.assertEqual(reporte.llaves_no_obtenibles[0].sala, 3)

    def test_llave_libre_en_sala_alcanzable_002_FR005(self):
        conexiones = [conexion(1, 'E', 2), conexion(2, 'E', 3, cerrada=True, llave='k_s')]
        reporte = _verificar(conexiones, [('k_s', 2)], sala_salida=3, llave_salida='k_s')
        self.assertTrue(reporte.resoluble)


class TestSupuestos(unittest.TestCase):

    def test_las_llaves_no_se_consumen_002_FR003(self):
        conexiones = [conexion(1, 'E', 2, cerrada=True, llave='k_a'), conexion(2, 'E', 3, cerrada=True, llave='k_a'),
                      conexion(3, 'E', 4, cerrada=True, llave='k_a')]
        reporte = _verificar(conexiones, [('k_a', 1)], sala_salida=4, llave_salida='k_a')
        self.assertTrue(reporte.resoluble)

    def test_cierre_automatico_no_bloquea_002_FR004(self):
        cripta, _ = cripta_con_llaves([conexion(1, 'E', 2, cerrada=True, llave='k_a'), conexion(2, 'E', 3)], [('k_a', 1)],
                                      sala_salida=2, llave_salida='k_a')
        for salida in cripta.sala(1).salidas:
            if salida is not None:
                salida.puerta.cierre_automatico = 500
        reporte = verificar(cripta, [LlaveInfo('k_a', 1)])
        self.assertTrue(reporte.resoluble)

    def test_llave_duplicada_es_error_de_datos_002_FR001(self):
        from src.modelos.errores import ErrorDatos
        cripta, _ = cripta_con_llaves([conexion(1, 'E', 2)], [])
        with self.assertRaises(ErrorDatos):
            verificar(cripta, [LlaveInfo('k_a', 1), LlaveInfo('k_a', 2)])

    def test_llave_en_sala_inexistente_es_error_de_datos_002_FR001(self):
        from src.modelos.errores import ErrorDatos
        cripta, _ = cripta_con_llaves([conexion(1, 'E', 2)], [])
        with self.assertRaises(ErrorDatos):
            verificar(cripta, [LlaveInfo('k_a', 99)])


if __name__ == '__main__':
    unittest.main()
