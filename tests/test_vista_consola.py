"""US4: ver el terreno y reconocer a los cazadores (T053; contrato interfaz-y-bench).

Requisitos: FR-023, FR-024.
"""
import io
import unittest
from contextlib import redirect_stdout

from src.modelos.contenido import ContenidoSala
from src.modelos.fichas import CAZADOR, FichaEnemigo
from src.vistas.vista_consola import VistaConsola
from tests.utilidades import construir, enemigo


def _texto_estado(partida):
    salida = io.StringIO()
    with redirect_stdout(salida):
        VistaConsola().mostrar_estado(partida)
    return salida.getvalue()


class TestVistaTerreno(unittest.TestCase):

    def test_US4_1_cada_salida_con_direccion_y_costo_FR023(self):
        p = construir([(1, 'N', 2, {'costo': 100}), (1, 'E', 3, {'costo': 250}), (1, 'O', 4, {})])
        p.iniciar()
        texto = _texto_estado(p)
        self.assertIn('[N] hacia sala 2: abierta, costo 100', texto)
        self.assertIn('[E] hacia sala 3: abierta, costo 250', texto)
        self.assertIn('[O] hacia sala 4: abierta, costo 100', texto)

    def test_salida_cerrada_muestra_costo_FR023(self):
        p = construir([(1, 'N', 2, {'costo': 70, 'cerrada': True, 'llave': 'itm_llave'})])
        p.iniciar()
        self.assertIn('[N] hacia sala 2: cerrada (llave itm_llave), costo 70', _texto_estado(p))

    def test_US4_2_cazador_marcado_y_distinto_de_otro_enemigo_FR024(self):
        cazador = FichaEnemigo('ent_sabueso', 'Sabueso óseo', 18, 6, 2, 120, CAZADOR, (), None, 600)
        rata = enemigo(id_ficha='ent_rata', comportamiento='errante', nombre='Rata')
        p = construir([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', cazador, None), ('e-2', rata, None)])}, [cazador, rata])
        p.iniciar()
        lineas = _texto_estado(p).splitlines()
        linea_cazador = [l for l in lineas if 'Sabueso óseo' in l][0]
        linea_rata = [l for l in lineas if 'Rata (' in l][0]
        self.assertIn('[cazador]', linea_cazador)
        self.assertNotIn('[cazador]', linea_rata)

    def test_no_muestra_distancias_ni_rutas_FR024(self):
        cazador = FichaEnemigo('ent_sabueso', 'Sabueso óseo', 18, 6, 2, 120, CAZADOR, (), None, 600)
        p = construir([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', cazador, None)])}, [cazador])
        p.iniciar()
        texto = _texto_estado(p).lower()
        for palabra in ('distancia', 'ruta', 'rango'):
            self.assertNotIn(palabra, texto)


if __name__ == '__main__':
    unittest.main()
