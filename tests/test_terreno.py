"""Terreno con costo (specs/001-terreno-cazador): carga del costo (T008).

Las pruebas de movimiento de la US1 (T016-T019) se agregan en la fase 3.
"""
import unittest

from src.modelos.errores import ErrorDatos
from src.servicios.generador_criptas import cargar_cripta_sintetica, fuente_sintetica, texto_sala
from tests.utilidades_cripta import conexion, cripta_desde_conexiones, textos_desde_conexiones

N, S, E, O = 0, 1, 2, 3


def _cargar(textos):
    return cargar_cripta_sintetica(fuente_sintetica(textos))


class TestCargaDelCosto(unittest.TestCase):
    """T008: lectura y validación del costo de las salidas."""

    def test_costo_ausente_vale_100_FR001(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2)])
        self.assertEqual(cripta.sala(1).salidas[N].puerta.costo, 100)
        self.assertEqual(cripta.sala(2).salidas[S].puerta.costo, 100)

    def test_costo_declarado_entero_FR001(self):
        cripta = cripta_desde_conexiones([conexion(1, 'E', 2, 250), conexion(2, 'E', 3, 1)])
        self.assertEqual(cripta.sala(1).salidas[E].puerta.costo, 250)
        self.assertEqual(cripta.sala(3).salidas[O].puerta.costo, 1)

    def test_costo_simetrico_misma_puerta_FR002(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 300)])
        self.assertIs(cripta.sala(1).salidas[N].puerta, cripta.sala(2).salidas[S].puerta)

    def test_un_solo_lado_declara_vale_para_ambos_FR002(self):
        textos = [texto_sala(1, [(N, 2, 250, False, None)]), texto_sala(2, [(S, 1, None, False, None)])]
        cripta = _cargar(textos)
        self.assertEqual(cripta.sala(1).salidas[N].puerta.costo, 250)
        self.assertEqual(cripta.sala(2).salidas[S].puerta.costo, 250)

    def test_ambos_lados_distintos_es_error_FR002(self):
        textos = [texto_sala(1, [(N, 2, 250, False, None)]), texto_sala(2, [(S, 1, 300, False, None)])]
        with self.assertRaises(ErrorDatos) as contexto:
            _cargar(textos)
        mensaje = str(contexto.exception)
        self.assertIn('1', mensaje)
        self.assertIn('2', mensaje)
        self.assertIn('N', mensaje)
        self.assertIn('S', mensaje)

    def test_costo_menor_que_uno_es_error_FR008(self):
        textos = textos_desde_conexiones([conexion(1, 'E', 2, 0)])
        with self.assertRaises(ErrorDatos) as contexto:
            _cargar(textos)
        self.assertIn('Sala 1', str(contexto.exception))
        self.assertIn('E', str(contexto.exception))

    def test_costo_no_entero_es_error_FR008(self):
        for valor in (2.5, 'caro', True):
            textos = [texto_sala(1, [(E, 2, valor, False, None)]), texto_sala(2, [(O, 1, valor, False, None)])]
            with self.subTest(valor=valor), self.assertRaises(ErrorDatos):
                _cargar(textos)

    def test_misma_cantidad_de_solicitudes_FR025(self):
        con_costo = fuente_sintetica(textos_desde_conexiones([conexion(1, 'N', 2, 250), conexion(2, 'E', 3, 7)]))
        sin_costo = fuente_sintetica(textos_desde_conexiones([conexion(1, 'N', 2), conexion(2, 'E', 3)]))
        cargar_cripta_sintetica(con_costo)
        cargar_cripta_sintetica(sin_costo)
        self.assertEqual(con_costo.solicitudes_realizadas, sin_costo.solicitudes_realizadas)


class TestIndiceYEnlace(unittest.TestCase):
    """Índice compacto y enlace directo (research R2, R3)."""

    def test_indice_compacto_en_orden_de_carga_FR030(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2), conexion(2, 'N', 3)])
        self.assertEqual([cripta.sala(i).indice for i in (1, 2, 3)], [0, 1, 2])

    def test_sala_destino_es_la_sala_vecina_FR011(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 40)])
        self.assertIs(cripta.sala(1).salidas[N].sala_destino, cripta.sala(2))
        self.assertIs(cripta.sala(2).salidas[S].sala_destino, cripta.sala(1))


if __name__ == '__main__':
    unittest.main()
