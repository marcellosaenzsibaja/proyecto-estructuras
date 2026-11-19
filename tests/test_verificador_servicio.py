"""Obtención y persistencia de la ubicación de llaves (spec 002, US4).

Los identificadores FR-NNN de estas pruebas son los de specs/002-verificacion-resolubilidad/spec.md.
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.adaptadores.api_client import ApiClient
from src.adaptadores.errores import ErrorCliente, PresupuestoAgotado
from src.adaptadores.fuente_sin_conexion import FuenteSinConexion
from src.modelos.errores import ErrorDatos
from src.servicios.verificador_servicio import cargar_llaves, interpretar_llaves, ruta_cache, verificar_cripta
from tests.utilidades_cripta import conexion, cripta_con_llaves

RUTA_GET = 'src.adaptadores.api_client.requests.get'


class RespuestaFalsa:

    def __init__(self, status_code, cuerpo):
        self.status_code = status_code
        self._cuerpo = cuerpo
        self.text = ''

    def json(self):
        return self._cuerpo


class TestInterpretacion(unittest.TestCase):

    def test_interpreta_llaves_con_y_sin_enemigo_002_FR021(self):
        crudo = json.loads('{"llaves": [{"id": "a", "sala": 4}, {"id": "b", "sala": 12, "enemigo": "e-1203"}]}')
        llaves = interpretar_llaves(crudo)
        self.assertEqual([(l.id, l.sala, l.enemigo) for l in llaves], [('a', 4, None), ('b', 12, 'e-1203')])

    def test_respuesta_sin_campo_llaves_es_error_de_datos_002_FR021(self):
        with self.assertRaises(ErrorDatos):
            interpretar_llaves(json.loads('{}'))

    def test_llave_sin_sala_es_error_de_datos_002_FR021(self):
        with self.assertRaises(ErrorDatos):
            interpretar_llaves(json.loads('{"llaves": [{"id": "a"}]}'))


class TestPersistencia(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.carpeta = self._tmp.name
        self.cripta, self.fuente = cripta_con_llaves([conexion(1, 'E', 2, cerrada=True, llave='k_a')], [('k_a', 1)],
                                                     sala_salida=2, llave_salida='k_a')

    def test_la_primera_consulta_cuesta_una_solicitud_y_se_persiste_002_FR022_FR023(self):
        antes = self.fuente.solicitudes_realizadas
        cargar_llaves(self.fuente, self.cripta.datos, self.carpeta)
        self.assertEqual(self.fuente.solicitudes_realizadas - antes, 1)
        self.assertTrue(os.path.isfile(ruta_cache(self.carpeta, self.cripta.datos.id)))

    def test_con_la_misma_version_no_hay_solicitudes_adicionales_002_FR024(self):
        cargar_llaves(self.fuente, self.cripta.datos, self.carpeta)
        antes = self.fuente.solicitudes_realizadas
        llaves = cargar_llaves(self.fuente, self.cripta.datos, self.carpeta)
        self.assertEqual(self.fuente.solicitudes_realizadas, antes)
        self.assertEqual([l.id for l in llaves], ['k_a'])

    def test_una_version_distinta_invalida_lo_persistido_002_FR023(self):
        cargar_llaves(self.fuente, self.cripta.datos, self.carpeta)
        self.cripta.datos.version = 'v-nueva'
        antes = self.fuente.solicitudes_realizadas
        cargar_llaves(self.fuente, self.cripta.datos, self.carpeta)
        self.assertEqual(self.fuente.solicitudes_realizadas - antes, 1)

    def test_archivo_corrupto_se_descarta_002_FR023(self):
        ruta = ruta_cache(self.carpeta, self.cripta.datos.id)
        with open(ruta, 'w', encoding='utf-8') as archivo:
            archivo.write('{no es json')
        llaves = cargar_llaves(self.fuente, self.cripta.datos, self.carpeta)
        self.assertEqual([l.id for l in llaves], ['k_a'])

    def test_verificar_cripta_integra_carga_y_verificacion_002_FR021(self):
        reporte = verificar_cripta(self.fuente, self.cripta, self.carpeta)
        self.assertTrue(reporte.resoluble)


class TestFuentes(unittest.TestCase):

    def test_fuente_sin_conexion_lee_llaves_json_002_FR024(self):
        with tempfile.TemporaryDirectory() as carpeta:
            os.makedirs(os.path.join(carpeta, 'c1'))
            with open(os.path.join(carpeta, 'c1', 'llaves.json'), 'w', encoding='utf-8') as archivo:
                archivo.write('{"llaves": [{"id": "a", "sala": 1}]}')
            fuente = FuenteSinConexion(carpeta)
            self.assertEqual(fuente.obtener_llaves('c1')['llaves'][0]['id'], 'a')

    def test_fuente_sin_conexion_sin_archivo_es_error_002_FR024(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with self.assertRaises(ErrorCliente):
                FuenteSinConexion(carpeta).obtener_llaves('c1')

    def test_api_client_cuenta_la_consulta_en_el_presupuesto_002_FR022(self):
        cliente = ApiClient(esperar=lambda segundos: None)
        with patch(RUTA_GET, return_value=RespuestaFalsa(200, {'llaves': []})) as get:
            cliente.obtener_llaves('cripta-01')
        self.assertTrue(get.call_args.args[0].endswith('/criptas/cripta-01/llaves'))
        self.assertEqual(cliente.solicitudes_realizadas, 1)

    def test_api_client_respeta_el_tiempo_del_429_y_cuenta_el_reintento_002_FR022(self):
        esperas = []
        cliente = ApiClient(esperar=esperas.append)
        respuestas = [RespuestaFalsa(429, {'reintentar_en': 7}), RespuestaFalsa(200, {'llaves': []})]
        with patch(RUTA_GET, side_effect=respuestas):
            cliente.obtener_llaves('cripta-01')
        self.assertEqual(esperas, [7])
        self.assertEqual(cliente.solicitudes_realizadas, 2)

    def test_api_client_sin_presupuesto_no_consulta_002_FR022(self):
        cliente = ApiClient(esperar=lambda segundos: None)
        cliente.establecer_presupuesto(0)
        with patch(RUTA_GET) as get:
            with self.assertRaises(PresupuestoAgotado):
                cliente.obtener_llaves('cripta-01')
        get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
