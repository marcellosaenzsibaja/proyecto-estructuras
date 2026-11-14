"""T007: registro de búsqueda en listas indexadas con marca de generación (research R2, R9).

Requisito: FR-030.
"""
import unittest

from src.estructuras_datos.registro_busqueda import RegistroBusqueda


class TestGeneracion(unittest.TestCase):

    def test_nueva_busqueda_invalida_sin_limpiar_FR030(self):
        r = RegistroBusqueda(5)
        r.nueva_busqueda()
        r.registrar(2, 40)
        r.asentar(2)
        self.assertTrue(r.tiene(2))
        self.assertTrue(r.asentada(2))
        listas_antes = r.marca
        r.nueva_busqueda()
        self.assertIs(r.marca, listas_antes)  # no se recrean ni se recorren
        for i in range(5):
            self.assertFalse(r.tiene(i))
            self.assertFalse(r.asentada(i))

    def test_valores_viejos_no_se_leen_FR030(self):
        r = RegistroBusqueda(3)
        r.nueva_busqueda()
        r.registrar(1, 99)
        r.nueva_busqueda()
        self.assertFalse(r.tiene(1))


class TestExaminadas(unittest.TestCase):

    def test_cuenta_cada_sala_una_vez_FR030(self):
        r = RegistroBusqueda(4)
        r.nueva_busqueda()
        r.registrar(0, 10)
        r.registrar(0, 5)   # mejora de la misma sala: no vuelve a contar
        r.registrar(3, 900)  # sala de borde
        r.asentar(0)
        r.registrar(3, 800)  # la de borde mejora y luego se asienta
        r.asentar(3)
        self.assertEqual(r.examinadas, 2)

    def test_se_reinicia_por_busqueda_FR030(self):
        r = RegistroBusqueda(4)
        r.nueva_busqueda()
        r.registrar(1, 1)
        r.nueva_busqueda()
        self.assertEqual(r.examinadas, 0)


if __name__ == '__main__':
    unittest.main()
