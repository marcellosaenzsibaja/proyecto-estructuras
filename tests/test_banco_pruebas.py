import unittest
from src.servicios.banco_pruebas import ejecutar_todo, formatear, medir_agenda, medir_cache_fichas, medir_guardado, medir_historial, medir_inventario, medir_ordenamiento

class PruebasBancoPruebas(unittest.TestCase):

    def test_medir_agenda(self):
        resultado = medir_agenda(n=50)
        self.assertEqual(resultado['n'], 50)
        self.assertGreaterEqual(resultado['segundos_insertar'], 0)
        self.assertGreaterEqual(resultado['segundos_extraer_en_orden'], 0)

    def test_medir_cache_fichas(self):
        resultado = medir_cache_fichas(n=60, capacidad=10)
        self.assertEqual(resultado['desalojos'], 50)

    def test_medir_inventario(self):
        resultado = medir_inventario(n=30)
        self.assertEqual(resultado['n'], 30)

    def test_medir_historial(self):
        resultado = medir_historial(n=20)
        self.assertLessEqual(resultado['pergaminos_acumulados'], 5)
        self.assertGreater(resultado['pergaminos_acumulados'], 0)

    def test_medir_ordenamiento(self):
        resultado = medir_ordenamiento(n=200)
        self.assertEqual(resultado['n'], 200)

    def test_medir_guardado(self):
        resultado = medir_guardado(acciones=10)
        self.assertLess(resultado['bytes_binario'], resultado['bytes_json'])

    def test_ejecutar_todo_y_formatear(self):
        resultados = ejecutar_todo(rapido=True)
        texto = formatear(resultados)
        for subsistema in ('agenda', 'cache_fichas', 'inventario', 'historial', 'ordenamiento', 'guardado'):
            self.assertIn(subsistema, resultados)
            self.assertIn(f'[{subsistema}]', texto)


class PruebasBenchCazador(unittest.TestCase):
    """T056: determinismo y secciones de --bench (FR-032 a FR-035, SC-006)."""

    @classmethod
    def setUpClass(cls):
        from src.servicios.banco_cazador import ejecutar_cazador
        cls.uno = ejecutar_cazador(rapido=True)
        cls.dos = ejecutar_cazador(rapido=True)

    def test_misma_semilla_mismos_resultados_deterministas_FR035(self):
        campos = ('escenario', 'semilla', 'salas', 'cazadores', 'examinadas_media', 'reutilizaciones', 'busquedas', 'huella')
        for seccion in self.uno:
            for a, b in zip(self.uno[seccion], self.dos[seccion]):
                for campo in campos:
                    self.assertEqual(a.get(campo), b.get(campo), seccion + '/' + a['escenario'] + '/' + campo)

    def test_cuatro_grupos_de_la_US5_en_la_salida_SC006(self):
        texto = formatear(self.uno)
        nombres = ('cazador_compartido_30_rango_pequeno', 'cazador_individual_30_rango_grande',
                   'reutilizacion_puertas_estables_reutilizar', 'reutilizacion_puertas_inestables_recalcular_siempre',
                   'revision_agenda_', 'revision_historial_', 'determinismo_criptas_sinteticas',
                   'ciclo_eventos_30_cazadores', 'escala_x10_')
        for nombre in nombres:
            self.assertIn(nombre, texto)
        self.assertIn('reproducible=si', texto)
        self.assertRegex(texto, 'resultado=(CUMPLE|NO CUMPLE)')

    def test_bench_no_instancia_la_vista_FR035(self):
        import io
        from contextlib import redirect_stdout
        from unittest import mock
        import main
        from src.servicios import banco_pruebas
        original = banco_pruebas.ejecutar_todo
        with mock.patch.object(main, 'VistaConsola', side_effect=AssertionError('--bench instanció la vista')):
            with mock.patch.object(banco_pruebas, 'ejecutar_todo', lambda: original(rapido=True)):
                salida = io.StringIO()
                with redirect_stdout(salida):
                    self.assertEqual(main.main(['--bench']), 0)
        self.assertIn('[ciclo_eventos]', salida.getvalue())


if __name__ == '__main__':
    unittest.main()
