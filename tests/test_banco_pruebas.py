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
        resultados = ejecutar_todo()
        texto = formatear(resultados)
        for subsistema in ('agenda', 'cache_fichas', 'inventario', 'historial', 'ordenamiento', 'guardado'):
            self.assertIn(subsistema, resultados)
            self.assertIn(f'[{subsistema}]', texto)
if __name__ == '__main__':
    unittest.main()
