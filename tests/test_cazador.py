"""Enemigo cazador (specs/001-terreno-cazador): ficha de catálogo (T009).

Las pruebas de decisión de la US2 (T026-T035) se agregan en la fase 4.
"""
import json
import unittest

from src.modelos.errores import ErrorDatos
from src.modelos.fichas import CAZADOR, FichaEnemigo
from src.servicios.fabrica_fichas import ficha_desde_dict
from src.servicios.generador_criptas import ficha_cazador


class TestFichaCazador(unittest.TestCase):
    """T009: comportamiento cazador con rango entero >= 0."""

    def test_ficha_cazador_con_rango_FR009(self):
        ficha = ficha_desde_dict(json.loads(ficha_cazador('ent_sabueso', 600, velocidad=120)))
        self.assertIsInstance(ficha, FichaEnemigo)
        self.assertEqual(ficha.comportamiento, CAZADOR)
        self.assertEqual(ficha.rango, 600)
        self.assertEqual(ficha.velocidad, 120)

    def test_rango_cero_es_valido_FR009(self):
        self.assertEqual(ficha_desde_dict(json.loads(ficha_cazador('ent_quieto', 0))).rango, 0)

    def test_cazador_sin_rango_es_error_con_id_FR009(self):
        texto = ficha_cazador('ent_sin_rango', 5).replace(', "rango": 5', '')
        with self.assertRaises(ErrorDatos) as contexto:
            ficha_desde_dict(json.loads(texto))
        self.assertIn('ent_sin_rango', str(contexto.exception))

    def test_rango_invalido_es_error_FR009(self):
        for valor in ('-1', '2.5', '"lejos"', 'true', 'null'):
            texto = ficha_cazador('ent_malo', 5).replace('"rango": 5', '"rango": ' + valor)
            with self.subTest(valor=valor), self.assertRaises(ErrorDatos) as contexto:
                ficha_desde_dict(json.loads(texto))
            self.assertIn('ent_malo', str(contexto.exception))

    def test_otros_comportamientos_no_requieren_rango_FR009(self):
        texto = ficha_cazador('ent_guardia', 5).replace('"cazador", "rango": 5', '"guardian"')
        ficha = ficha_desde_dict(json.loads(texto))
        self.assertIsNone(ficha.rango)


if __name__ == '__main__':
    unittest.main()
