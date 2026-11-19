"""T005: prohibición automática de estructuras de conveniencia (constitución, Principio I).

Recorre con ast los módulos de la capacidad 001 y falla si encuentra
importaciones prohibidas, literales o constructores de diccionario o conjunto,
comprensiones de diccionario o conjunto, o llamadas a sorted/.sort. No hay
excepciones: el generador escribe texto JSON (G1) y solo se leen los
diccionarios que devuelve json.loads. Requisitos: FR-021, FR-030.
"""
import ast
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Se amplía en cada tarea que crea un módulo nuevo de la capacidad.
ARCHIVOS_VIGILADOS = [
    'src/estructuras_datos/monticulo.py',
    'src/estructuras_datos/registro_busqueda.py',
    'src/modelos/rutas.py',
    'src/modelos/cazador.py',
    'src/servicios/generador_criptas.py',
    'src/adaptadores/fuente_memoria.py',
    'tests/referencia_cazador.py',
    'tests/test_generador_criptas.py',
    'tests/utilidades_cripta.py',
    'src/estructuras_datos/busqueda_binaria.py',
    'src/modelos/resolubilidad.py',
    'src/servicios/verificador_servicio.py',
    'tests/test_busqueda_binaria.py',
    'tests/test_resolubilidad.py',
    'tests/test_resolubilidad_irresoluble.py',
    'tests/test_bench_resolubilidad.py',
    'tests/test_monticulo_llaves.py',
    'src/modelos/mapa_conocido.py',
    'src/modelos/linea_tiempo.py',
    'src/modelos/resumen_historia.py',
    'src/modelos/viaje.py',
    'tests/referencia_conocido.py',
]

MODULOS_PROHIBIDOS = ['heapq', 'bisect', 'collections', 'queue', 'networkx', 'igraph', 'graphlib', 'sortedcontainers']
NOMBRES_PROHIBIDOS_DE_FUNCTOOLS = ['lru_cache', 'cache']
CONSTRUCTORES_PROHIBIDOS = ['dict', 'set', 'frozenset', 'sorted']


def _raiz_modulo(nombre: str) -> str:
    return nombre.split('.')[0] if nombre else ''


def problemas_en(codigo: str, nombre_archivo: str) -> list:
    """Devuelve una lista de (línea, descripción) con cada construcción prohibida."""
    arbol = ast.parse(codigo, filename=nombre_archivo)
    problemas = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if _raiz_modulo(alias.name) in MODULOS_PROHIBIDOS:
                    problemas.append((nodo.lineno, f'import {alias.name}'))
        elif isinstance(nodo, ast.ImportFrom):
            raiz = _raiz_modulo(nodo.module or '')
            if raiz in MODULOS_PROHIBIDOS:
                problemas.append((nodo.lineno, f'from {nodo.module} import ...'))
            if raiz == 'functools':
                for alias in nodo.names:
                    if alias.name in NOMBRES_PROHIBIDOS_DE_FUNCTOOLS:
                        problemas.append((nodo.lineno, f'from functools import {alias.name}'))
        elif isinstance(nodo, ast.Attribute) and isinstance(nodo.value, ast.Name) and nodo.value.id == 'functools':
            if nodo.attr in NOMBRES_PROHIBIDOS_DE_FUNCTOOLS:
                problemas.append((nodo.lineno, f'functools.{nodo.attr}'))
        elif isinstance(nodo, ast.Dict):
            problemas.append((nodo.lineno, 'literal de diccionario'))
        elif isinstance(nodo, ast.Set):
            problemas.append((nodo.lineno, 'literal de conjunto'))
        elif isinstance(nodo, ast.DictComp):
            problemas.append((nodo.lineno, 'comprensión de diccionario'))
        elif isinstance(nodo, ast.SetComp):
            problemas.append((nodo.lineno, 'comprensión de conjunto'))
        elif isinstance(nodo, ast.Call):
            funcion = nodo.func
            if isinstance(funcion, ast.Name) and funcion.id in CONSTRUCTORES_PROHIBIDOS:
                problemas.append((nodo.lineno, f'{funcion.id}(...)'))
            elif isinstance(funcion, ast.Attribute) and funcion.attr == 'sort':
                problemas.append((nodo.lineno, '.sort(...)'))
    return problemas


class TestDetector(unittest.TestCase):
    """El detector reconoce cada construcción prohibida (FR-021)."""

    def test_detecta_construcciones_prohibidas_FR021(self):
        codigo = '\n'.join([
            'import heapq',
            'from collections import deque',
            'from functools import lru_cache',
            'a = {}',
            'b = {1: 2}',
            'c = {1, 2}',
            'd = dict()',
            'e = set()',
            'f = frozenset()',
            'g = {k: k for k in range(3)}',
            'h = {k for k in range(3)}',
            'i = sorted([3, 1])',
            '[3, 1].sort()',
        ])
        self.assertEqual(len(problemas_en(codigo, '<prueba>')), 13)

    def test_permite_listas_y_lectura_de_json_FR021(self):
        codigo = '\n'.join([
            'import json',
            'datos = json.loads(texto)',
            'x = datos["salidas"]',
            'lista = [0] * 10',
            'tupla = (1, 2)',
            'texto = "{\\"id\\": 1}"',
        ])
        self.assertEqual(problemas_en(codigo, '<prueba>'), [])


class TestArchivosVigilados(unittest.TestCase):
    """Los módulos de la capacidad no usan estructuras de conveniencia (FR-021, FR-030)."""

    def test_sin_estructuras_de_conveniencia_FR021(self):
        for relativo in ARCHIVOS_VIGILADOS:
            ruta = os.path.join(RAIZ, relativo)
            with self.subTest(archivo=relativo):
                if not os.path.isfile(ruta):
                    self.skipTest(f'{relativo} todavía no existe')
                with open(ruta, encoding='utf-8') as archivo:
                    problemas = problemas_en(archivo.read(), relativo)
                mensaje = '\n'.join(f'{relativo}:{linea}: {descripcion}' for linea, descripcion in problemas)
                self.assertEqual(problemas, [], f'Construcciones prohibidas:\n{mensaje}')


if __name__ == '__main__':
    unittest.main()
