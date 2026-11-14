import unittest
from unittest.mock import patch
import requests
from src.adaptadores.api_client import ApiClient
from src.adaptadores.errores import ErrorCliente, PresupuestoAgotado

class RespuestaFalsa:

    def __init__(self, status_code, cuerpo=None, texto=''):
        self.status_code = status_code
        self._cuerpo = cuerpo
        self.text = texto

    def json(self):
        if self._cuerpo is None:
            raise ValueError('sin cuerpo')
        return self._cuerpo
RUTA_GET = 'src.adaptadores.api_client.requests.get'

class PruebasApiClient(unittest.TestCase):

    def setUp(self):
        self.esperas = []
        self.cliente = ApiClient(esperar=self.esperas.append)

    def test_identificador_unico_por_ejecucion(self):
        with patch(RUTA_GET, return_value=RespuestaFalsa(200, {})) as get:
            self.cliente.obtener_criptas()
            self.cliente.obtener_version_catalogo()
        ids = {c.kwargs['headers']['X-Cripta-Client-Id'] for c in get.call_args_list}
        self.assertEqual(len(ids), 1)
        self.assertEqual(self.cliente.solicitudes_realizadas, 2)

    def test_429_espera_lo_indicado_y_cuenta_el_reintento(self):
        respuestas = [RespuestaFalsa(429, {'error': 'x', 'reintentar_en': 12}), RespuestaFalsa(200, {'criptas': []})]
        with patch(RUTA_GET, side_effect=respuestas):
            datos = self.cliente.obtener_criptas()
        self.assertEqual(datos, {'criptas': []})
        self.assertEqual(self.esperas, [12])
        self.assertEqual(self.cliente.solicitudes_realizadas, 2)

    def test_429_sin_reintentar_en_reporta_con_contexto(self):
        with patch(RUTA_GET, return_value=RespuestaFalsa(429, {'error': 'x'})):
            with self.assertRaises(ErrorCliente) as ctx:
                self.cliente.obtener_criptas()
        self.assertIn('listar criptas', str(ctx.exception))

    def test_presupuesto_se_toma_de_los_datos_generales(self):
        datos = {'id': 'c', 'presupuesto_solicitudes': 3}
        with patch(RUTA_GET, return_value=RespuestaFalsa(200, datos)):
            self.cliente.obtener_datos_cripta('c')
            self.assertEqual(self.cliente.presupuesto, 3)
            self.assertEqual(self.cliente.solicitudes_restantes, 2)

    def test_no_se_excede_el_presupuesto(self):
        self.cliente.establecer_presupuesto(2)
        with patch(RUTA_GET, return_value=RespuestaFalsa(200, {})) as get:
            self.cliente.obtener_criptas()
            self.cliente.obtener_criptas()
            with self.assertRaises(PresupuestoAgotado):
                self.cliente.obtener_criptas()
        self.assertEqual(get.call_count, 2)

    def test_reintento_429_no_excede_el_presupuesto(self):
        self.cliente.establecer_presupuesto(1)
        respuestas = [RespuestaFalsa(429, {'reintentar_en': 1}), RespuestaFalsa(200, {})]
        with patch(RUTA_GET, side_effect=respuestas) as get:
            with self.assertRaises(PresupuestoAgotado):
                self.cliente.obtener_criptas()
        self.assertEqual(get.call_count, 1)

    def test_error_http_incluye_operacion(self):
        with patch(RUTA_GET, return_value=RespuestaFalsa(404, None, 'no existe')):
            with self.assertRaises(ErrorCliente) as ctx:
                self.cliente.obtener_datos_cripta('cripta-99')
        mensaje = str(ctx.exception)
        self.assertIn('404', mensaje)
        self.assertIn('cripta-99', mensaje)

    def test_excepcion_de_red_se_reporta_con_contexto(self):
        with patch(RUTA_GET, side_effect=requests.ConnectionError('caído')):
            with self.assertRaises(ErrorCliente) as ctx:
                self.cliente.obtener_esqueleto('cripta-01', 2)
        self.assertIn('esqueleto de cripta-01 página 2', str(ctx.exception))

    def test_limites_de_lote(self):
        with self.assertRaises(ValueError):
            self.cliente.obtener_contenido_lote('c', list(range(11)))
        with self.assertRaises(ValueError):
            self.cliente.obtener_contenido_lote('c', [])
        with self.assertRaises(ValueError):
            self.cliente.obtener_catalogo_lote([f'id{i}' for i in range(11)])
        self.assertEqual(self.cliente.solicitudes_realizadas, 0)

    def test_parametros_de_lote(self):
        with patch(RUTA_GET, return_value=RespuestaFalsa(200, {})) as get:
            self.cliente.obtener_contenido_lote('c', [1, 2, 3])
            self.cliente.obtener_catalogo_lote(['a', 'b'])
        self.assertEqual(get.call_args_list[0].kwargs['params'], {'salas': '1,2,3'})
        self.assertEqual(get.call_args_list[1].kwargs['params'], {'ids': 'a,b'})
if __name__ == '__main__':
    unittest.main()
