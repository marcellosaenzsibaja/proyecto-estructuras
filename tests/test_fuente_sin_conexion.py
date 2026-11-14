import json
import os
import tempfile
import unittest
from src.adaptadores.errores import ErrorCliente
from src.adaptadores.fuente_sin_conexion import FuenteSinConexion

def _escribir(ruta, datos):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo)

class PruebasFuenteSinConexion(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def _bundle_minimo(self):
        _escribir(os.path.join(self.carpeta, 'criptas.json'), {'criptas': [{'id': 'c1', 'nombre': 'Cripta 1'}]})
        _escribir(os.path.join(self.carpeta, 'c1', 'datos_generales.json'), {'id': 'c1', 'presupuesto_solicitudes': 9})
        _escribir(os.path.join(self.carpeta, 'c1', 'version.json'), {'version': 'v1'})
        _escribir(os.path.join(self.carpeta, 'c1', 'esqueleto', 'pagina_1.json'), {'total_paginas': 1, 'salas': [{'id': 1}]})
        _escribir(os.path.join(self.carpeta, 'c1', 'salas', '1.json'), {'sala': 1, 'enemigos': [], 'objetos': ['itm_daga'], 'trampas': []})
        _escribir(os.path.join(self.carpeta, 'catalogo', 'entidades', 'itm_daga.json'), {'id': 'itm_daga', 'clase': 'arma', 'nombre': 'Daga'})
        _escribir(os.path.join(self.carpeta, 'catalogo', 'version.json'), {'version': 'k1'})

    def test_carpeta_inexistente_falla_al_construir(self):
        with self.assertRaises(ErrorCliente):
            FuenteSinConexion(os.path.join(self.carpeta, 'no_existe'))

    def test_contrato_completo_igual_que_la_api(self):
        self._bundle_minimo()
        fuente = FuenteSinConexion(self.carpeta)
        self.assertEqual(fuente.obtener_criptas()['criptas'][0]['id'], 'c1')
        datos = fuente.obtener_datos_cripta('c1')
        self.assertEqual(datos['presupuesto_solicitudes'], 9)
        self.assertEqual(fuente.presupuesto, 9)
        esqueleto = fuente.obtener_esqueleto('c1', 1)
        self.assertEqual(esqueleto['salas'][0]['id'], 1)
        contenido = fuente.obtener_contenido_lote('c1', [1])
        self.assertEqual(contenido['contenido'][0]['objetos'], ['itm_daga'])
        catalogo = fuente.obtener_catalogo_lote(['itm_daga'])
        self.assertEqual(catalogo['entidades'][0]['nombre'], 'Daga')
        self.assertEqual(fuente.obtener_version_cripta('c1')['version'], 'v1')
        self.assertEqual(fuente.obtener_version_catalogo()['version'], 'k1')

    def test_archivo_faltante_reporta_con_contexto(self):
        self._bundle_minimo()
        fuente = FuenteSinConexion(self.carpeta)
        with self.assertRaises(ErrorCliente):
            fuente.obtener_contenido_lote('c1', [99])

    def test_limites_de_lote(self):
        self._bundle_minimo()
        fuente = FuenteSinConexion(self.carpeta)
        with self.assertRaises(ValueError):
            fuente.obtener_contenido_lote('c1', [])
        with self.assertRaises(ValueError):
            fuente.obtener_contenido_lote('c1', list(range(11)))
        with self.assertRaises(ValueError):
            fuente.obtener_catalogo_lote([])

    def test_cuenta_lecturas_como_solicitudes(self):
        self._bundle_minimo()
        fuente = FuenteSinConexion(self.carpeta)
        fuente.obtener_datos_cripta('c1')
        fuente.obtener_esqueleto('c1', 1)
        self.assertEqual(fuente.solicitudes_realizadas, 2)
if __name__ == '__main__':
    unittest.main()
