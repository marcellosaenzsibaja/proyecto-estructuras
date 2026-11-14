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

def _construir_bundle_offline(carpeta):
    _escribir(os.path.join(carpeta, 'criptas.json'), {'criptas': [{'id': 'demo'}]})
    _escribir(os.path.join(carpeta, 'demo', 'datos_generales.json'), {'id': 'demo', 'version': 'v1', 'salas_total': 2, 'sala_inicial': 1, 'sala_salida': 2, 'llave_salida': None, 'presupuesto_solicitudes': 20, 'inventario_max': 10, 'jugador': {'vida_max': 30, 'ataque': 6, 'defensa': 2, 'velocidad': 100}})
    _escribir(os.path.join(carpeta, 'demo', 'version.json'), {'version': 'v1'})
    _escribir(os.path.join(carpeta, 'demo', 'esqueleto', 'pagina_1.json'), {'total_paginas': 1, 'salas': [{'id': 1, 'nombre': 'Entrada', 'salidas': {'N': {'sala': 2}}}, {'id': 2, 'nombre': 'Salida', 'salidas': {'S': {'sala': 1}}}]})
    _escribir(os.path.join(carpeta, 'demo', 'salas', '1.json'), {'sala': 1, 'enemigos': [], 'objetos': ['itm_daga'], 'trampas': []})
    _escribir(os.path.join(carpeta, 'demo', 'salas', '2.json'), {'sala': 2, 'enemigos': [], 'objetos': [], 'trampas': []})
    _escribir(os.path.join(carpeta, 'catalogo', 'entidades', 'itm_daga.json'), {'id': 'itm_daga', 'clase': 'arma', 'nombre': 'Daga', 'peso': 1, 'valor': 1, 'ataque_bonus': 2})
    _escribir(os.path.join(carpeta, 'catalogo', 'version.json'), {'version': 'k1'})

class PruebasMain(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.carpeta = self._tmp.name
        _construir_bundle_offline(self.carpeta)

    def _ruta(self, nombre):
        return os.path.join(self.carpeta, nombre)

    def _argv(self, *extra):
        return ['--offline', self.carpeta, '--cripta', 'demo', '--semilla', '1', '--bitacora', self._ruta('bitacora.log'), '--puntajes-ruta', self._ruta('puntajes.json'), '--cache-ruta', self._ruta('cache.json'), *extra]

    def test_bench_no_requiere_ninguna_cripta(self):
        with patch('builtins.print'):
            self.assertEqual(main.main(['--bench']), 0)

    def test_partida_interactiva_guarda_bitacora_y_cache(self):
        comandos = iter(['r 1', 'm N', 'salir'])
        with patch('builtins.input', lambda *_: next(comandos)), patch('builtins.print'):
            codigo = main.main(self._argv())
        self.assertEqual(codigo, 0)
        self.assertTrue(os.path.isfile(self._ruta('bitacora.log')))
        self.assertTrue(os.path.isfile(self._ruta('cache.json')))
        with open(self._ruta('cache.json'), encoding='utf-8') as archivo:
            cache = json.load(archivo)
        self.assertEqual(cache['version_catalogo'], 'k1')
        self.assertTrue(any((f['id'] == 'itm_daga' for f in cache['fichas'])))

    def test_replay_reproduce_la_bitacora_grabada(self):
        comandos = iter(['r 1', 'm N', 'salir'])
        with patch('builtins.input', lambda *_: next(comandos)), patch('builtins.print'):
            main.main(self._argv())
        with patch('builtins.print') as impresion:
            codigo = main.main(['--offline', self.carpeta, '--replay', self._ruta('bitacora.log'), '--cache-ruta', self._ruta('cache.json')])
        self.assertEqual(codigo, 0)
        texto = '\n'.join((str(c.args[0]) if c.args else '' for c in impresion.call_args_list))
        self.assertIn('Partida abandonada', texto)

    def test_guardar_y_cargar_mediante_comandos(self):
        comandos = iter(['r 1', f"guardar {self._ruta('p.bin')}", 'salir'])
        with patch('builtins.input', lambda *_: next(comandos)), patch('builtins.print'):
            main.main(self._argv())
        self.assertTrue(os.path.isfile(self._ruta('p.bin')))
        comandos2 = iter([f"cargar {self._ruta('p.bin')}", 'salir'])
        with patch('builtins.input', lambda *_: next(comandos2)), patch('builtins.print'):
            codigo = main.main(self._argv(*['--bitacora', self._ruta('bitacora2.log')]))
        self.assertEqual(codigo, 0)
if __name__ == '__main__':
    unittest.main()
