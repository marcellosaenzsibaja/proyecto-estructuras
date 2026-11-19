"""Comandos --verificar y --forzar y arranque de partida (spec 002, US1; Apéndice B caso 4).

Los identificadores FR-NNN de estas pruebas son los de specs/002-verificacion-resolubilidad/spec.md.
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import main


def _escribir(ruta, datos):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo)


def _construir(carpeta, resoluble=True, con_llaves=True):
    _escribir(os.path.join(carpeta, 'criptas.json'), {'criptas': [{'id': 'demo'}]})
    _escribir(os.path.join(carpeta, 'demo', 'datos_generales.json'), {'id': 'demo', 'version': 'v1', 'salas_total': 3, 'sala_inicial': 1, 'sala_salida': 3, 'llave_salida': 'k_s', 'presupuesto_solicitudes': 20, 'inventario_max': 10, 'jugador': {'vida_max': 30, 'ataque': 6, 'defensa': 2, 'velocidad': 100}})
    _escribir(os.path.join(carpeta, 'demo', 'version.json'), {'version': 'v1'})
    _escribir(os.path.join(carpeta, 'demo', 'esqueleto', 'pagina_1.json'), {'total_paginas': 1, 'salas': [
        {'id': 1, 'nombre': 'Entrada', 'salidas': {'E': {'sala': 2}}},
        {'id': 2, 'nombre': 'Pasillo', 'salidas': {'O': {'sala': 1}, 'E': {'sala': 3, 'cerrada': True, 'llave': 'k_s'}}},
        {'id': 3, 'nombre': 'Salida', 'salidas': {'O': {'sala': 2, 'cerrada': True, 'llave': 'k_s'}}}]})
    for sala in (1, 2, 3):
        _escribir(os.path.join(carpeta, 'demo', 'salas', f'{sala}.json'), {'sala': sala, 'enemigos': [], 'objetos': [], 'trampas': []})
    _escribir(os.path.join(carpeta, 'catalogo', 'version.json'), {'version': 'k1'})
    if con_llaves:
        sala_llave = 2 if resoluble else 3
        _escribir(os.path.join(carpeta, 'demo', 'llaves.json'), {'llaves': [{'id': 'k_s', 'sala': sala_llave}]})


class PruebasCli(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.carpeta = self._tmp.name

    def _ruta(self, nombre):
        return os.path.join(self.carpeta, nombre)

    def _argv(self, *extra):
        return ['--offline', self.carpeta, '--cripta', 'demo', '--semilla', '1', '--bitacora', self._ruta('bitacora.log'),
                '--puntajes-ruta', self._ruta('puntajes.json'), '--cache-ruta', self._ruta('cache.json'), *extra]

    def _ejecutar(self, argv, comandos=()):
        salida = io.StringIO()
        entradas = iter(comandos)
        with patch('builtins.input', lambda *_: next(entradas)), contextlib.redirect_stdout(salida):
            codigo = main.main(argv)
        return codigo, salida.getvalue()

    def test_cripta_resoluble_imprime_el_reporte_e_inicia_sin_pausa_002_FR017(self):
        _construir(self.carpeta, resoluble=True)
        codigo, texto = self._ejecutar(self._argv(), ['salir'])
        self.assertEqual(codigo, 0)
        self.assertIn('es resoluble', texto)
        self.assertTrue(os.path.isfile(self._ruta('bitacora.log')))

    def test_no_resoluble_sin_forzar_no_inicia_y_muestra_el_reporte_002_FR018(self):
        _construir(self.carpeta, resoluble=False)
        codigo, texto = self._ejecutar(self._argv())
        self.assertEqual(codigo, 1)
        self.assertIn('NO es resoluble', texto)
        self.assertIn('[k_s -> k_s]', texto)
        self.assertFalse(os.path.exists(self._ruta('bitacora.log')))

    def test_no_resoluble_con_forzar_muestra_el_reporte_y_juega_002_FR019(self):
        _construir(self.carpeta, resoluble=False)
        codigo, texto = self._ejecutar(self._argv('--forzar'), ['salir'])
        self.assertEqual(codigo, 0)
        self.assertIn('NO es resoluble', texto)
        self.assertTrue(os.path.isfile(self._ruta('bitacora.log')))

    def test_verificar_resoluble_devuelve_0_sin_vista_002_FR020(self):
        _construir(self.carpeta, resoluble=True)
        with patch('main.VistaConsola', side_effect=AssertionError('no debe instanciar la vista')):
            codigo, texto = self._ejecutar(['--verificar', 'demo', '--offline', self.carpeta, '--cache-ruta', self._ruta('cache.json')])
        self.assertEqual(codigo, 0)
        self.assertIn('es resoluble', texto)

    def test_verificar_no_resoluble_devuelve_1_002_FR020(self):
        _construir(self.carpeta, resoluble=False)
        codigo, texto = self._ejecutar(['--verificar', 'demo', '--offline', self.carpeta, '--cache-ruta', self._ruta('cache.json')])
        self.assertEqual(codigo, 1)
        self.assertIn('NO es resoluble', texto)

    def test_verificar_con_error_tecnico_devuelve_2_002_FR020(self):
        _construir(self.carpeta, con_llaves=False)
        with contextlib.redirect_stderr(io.StringIO()):
            codigo, _ = self._ejecutar(['--verificar', 'demo', '--offline', self.carpeta, '--cache-ruta', self._ruta('cache.json')])
        self.assertEqual(codigo, 2)

    def test_verificar_no_crea_bitacora_ni_partida_002_FR020(self):
        _construir(self.carpeta, resoluble=True)
        self._ejecutar(['--verificar', 'demo', '--offline', self.carpeta, '--bitacora', self._ruta('bitacora.log'), '--cache-ruta', self._ruta('cache.json')])
        self.assertFalse(os.path.exists(self._ruta('bitacora.log')))

    def test_bench_no_instancia_la_vista_002_FR031(self):
        with patch('main.VistaConsola', side_effect=AssertionError('no debe instanciar la vista')):
            with patch('main.banco_pruebas.ejecutar_todo', return_value=[]):
                with patch('main.banco_pruebas.formatear', return_value=''):
                    codigo, _ = self._ejecutar(['--bench'])
        self.assertEqual(codigo, 0)


if __name__ == '__main__':
    unittest.main()
