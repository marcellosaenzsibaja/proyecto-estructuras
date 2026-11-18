"""Diagnóstico de criptas no resolubles (spec 002, US3; Apéndice B caso 1).

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


def _ids(llaves):
    return [llave.id for llave in llaves]


class TestCicloDirecto(unittest.TestCase):

    def _reporte(self):
        conexiones = [conexion(1, 'E', 2), conexion(2, 'E', 3, cerrada=True, llave='k_s')]
        return _verificar(conexiones, [('k_s', 3)], sala_salida=3, llave_salida='k_s')

    def test_llave_de_salida_tras_su_propia_puerta_no_es_resoluble_y_senala_el_ciclo_002_FR011_FR015_FR016(self):
        reporte = self._reporte()
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.ciclos, [['k_s', 'k_s']])

    def test_reporta_llaves_no_obtenibles_002_FR012(self):
        self.assertEqual(_ids(self._reporte().llaves_no_obtenibles), ['k_s'])

    def test_reporta_frontera_con_llave_y_sala_de_la_llave_002_FR013_FR014(self):
        frontera = self._reporte().frontera
        self.assertEqual(len(frontera), 1)
        puerta = frontera[0]
        self.assertEqual((puerta.sala_origen, puerta.sala_destino, puerta.llave, puerta.sala_llave), (2, 3, 'k_s', 3))

    def test_el_texto_del_reporte_incluye_el_ciclo_002_FR015(self):
        texto = self._reporte().texto()
        self.assertIn('NO es resoluble', texto)
        self.assertIn('[k_s -> k_s]', texto)
        self.assertIn('sala 2 E -> sala 3 requiere k_s', texto)


class TestCicloIndirecto(unittest.TestCase):

    def _conexiones(self):
        return [conexion(1, 'E', 2, cerrada=True, llave='k_b'), conexion(2, 'E', 3, cerrada=True, llave='k_c'),
                conexion(3, 'E', 4, cerrada=True, llave='k_a')]

    def test_ciclo_de_tres_llaves_inicia_en_la_menor_002_FR015_FR016(self):
        reporte = _verificar(self._conexiones(), [('k_a', 2), ('k_b', 3), ('k_c', 4)], sala_salida=4, llave_salida='k_a')
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.ciclos, [['k_a', 'k_b', 'k_c', 'k_a']])

    def test_el_ciclo_no_depende_del_orden_de_entrada_002_FR016(self):
        a = _verificar(self._conexiones(), [('k_a', 2), ('k_b', 3), ('k_c', 4)], sala_salida=4, llave_salida='k_a')
        b = _verificar(self._conexiones(), [('k_c', 4), ('k_b', 3), ('k_a', 2)], sala_salida=4, llave_salida='k_a')
        self.assertEqual(a.ciclos, b.ciclos)

    def test_solo_la_primera_puerta_es_frontera_002_FR013(self):
        reporte = _verificar(self._conexiones(), [('k_a', 2), ('k_b', 3), ('k_c', 4)], sala_salida=4, llave_salida='k_a')
        self.assertEqual(len(reporte.frontera), 1)
        self.assertEqual(reporte.frontera[0].llave, 'k_b')
        self.assertEqual(_ids(reporte.llaves_no_obtenibles), ['k_a', 'k_b', 'k_c'])


class TestSinCiclo(unittest.TestCase):

    def test_puerta_sin_llave_ubicada_no_forma_ciclo_002_FR012_FR014(self):
        conexiones = [conexion(1, 'E', 2, cerrada=True, llave='k_x'), conexion(2, 'E', 3)]
        reporte = _verificar(conexiones, [('k_x', 1)], sala_salida=3, llave_salida='k_x')
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.ciclos, [])

    def test_llave_de_la_puerta_ausente_del_servicio_002_FR012_FR014(self):
        conexiones = [conexion(1, 'E', 2, cerrada=True, llave='k_fantasma')]
        reporte = _verificar(conexiones, [], sala_salida=2, llave_salida='k_fantasma')
        self.assertFalse(reporte.resoluble)
        self.assertEqual(reporte.frontera[0].llave, 'k_fantasma')
        self.assertIsNone(reporte.frontera[0].sala_llave)
        self.assertIn('sin ubicación', reporte.texto())

    def test_frontera_ordenada_por_sala_y_direccion_002_FR013(self):
        conexiones = [conexion(1, 'E', 3, cerrada=True, llave='k_p'), conexion(1, 'N', 2, cerrada=True, llave='k_q'),
                      conexion(1, 'S', 4, cerrada=True, llave='k_r')]
        reporte = _verificar(conexiones, [('k_p', 3), ('k_q', 2), ('k_r', 4)], sala_salida=4, llave_salida='k_r')
        self.assertEqual([p.llave for p in reporte.frontera], ['k_q', 'k_r', 'k_p'])


class TestRobustezIterativa(unittest.TestCase):

    def test_cadena_profunda_no_desborda_la_recursion_002_FR015_FR016(self):
        n = 1500
        conexiones = []
        llaves = []
        for j in range(1, n + 1):
            siguiente = j + 1 if j < n else 1
            conexiones.append(conexion(j, 'E', j + 1, cerrada=True, llave=f'k_{siguiente:04d}'))
            llaves.append((f'k_{j:04d}', j + 1))
        reporte = _verificar(conexiones, llaves, sala_salida=n + 1, llave_salida='k_0001')
        self.assertFalse(reporte.resoluble)
        self.assertEqual(len(reporte.ciclos), 1)
        ciclo = reporte.ciclos[0]
        self.assertEqual(len(ciclo), n + 1)
        self.assertEqual(ciclo[0], 'k_0001')
        self.assertEqual(ciclo[-1], 'k_0001')


class TestReporteResoluble(unittest.TestCase):

    def test_texto_de_cripta_resoluble_lista_el_orden_002_FR008(self):
        conexiones = [conexion(1, 'E', 2, cerrada=True, llave='k_a')]
        reporte = _verificar(conexiones, [('k_a', 1)], sala_salida=2, llave_salida='k_a')
        texto = reporte.texto()
        self.assertIn('es resoluble', texto)
        self.assertIn('1. k_a', texto)


if __name__ == '__main__':
    unittest.main()
