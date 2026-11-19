"""«ir a» en partida.log: un movimiento por paso más un comentario (spec 003, FR-043 y FR-044)."""
import os
import tempfile
import unittest

from src.modelos.acciones import Accion, MOVER
from src.modelos.direcciones import NORTE, SUR
from src.controladores.controlador_juego import ControladorJuego
from src.servicios.bitacora import Bitacora, leer, reproducir
from tests.utilidades import construir


class VistaMuda:

    def __init__(self, comandos):
        self.comandos = list(comandos)
        self.mensajes = []
        self.finales = []

    def mostrar_inicio(self, partida):
        pass

    def mostrar_estado(self, partida):
        pass

    def mostrar_ayuda(self):
        pass

    def mostrar_mensaje(self, texto):
        self.mensajes.append(texto)

    def mostrar_inventario_ordenado(self, partida):
        pass

    def mostrar_puntajes(self, tabla):
        pass

    def mostrar_mapa_conocido(self, partida):
        self.mensajes.append('MAPA')

    def mostrar_fin_viaje(self, partida, viaje):
        self.mensajes.append(f'FIN {viaje.motivo} {viaje.pasos}')

    def mostrar_resumen_historia(self, resumen):
        self.mensajes.append('HISTORIA')

    def pedir_comando(self):
        return self.comandos.pop(0) if self.comandos else ('salir', None)

    def mostrar_final(self, partida, abandonada):
        self.finales.append((partida.estado, abandonada))


def _pasillo(largo=5):
    return [(i, 'N', i + 1, {'costo': 100}) for i in range(1, largo)]


class TestViajeEnBitacora(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, 'partida.log')

    def _armar(self, comandos):
        partida = construir(_pasillo(), semilla=3)
        partida.iniciar()
        bitacora = Bitacora(self.ruta)
        bitacora.iniciar(partida.cripta.datos.id, partida.cripta.datos.version, partida.semilla)
        vista = VistaMuda(comandos)
        controlador = ControladorJuego(partida, vista, bitacora=bitacora,
                                       ruta_puntajes=os.path.join(self._tmp.name, 'p.json'))
        return (controlador, vista, partida, bitacora)

    def test_cada_paso_se_graba_como_un_movimiento_003_FR043(self):
        comandos = [('mover', 'N'), ('mover', 'N'), ('mover', 'N'), ('ir', 'a 1'), ('salir', None)]
        controlador, vista, partida, bitacora = self._armar(comandos)
        controlador.ejecutar()
        bitacora.cerrar()
        with open(self.ruta, encoding='utf-8') as archivo:
            lineas = [l for l in archivo if l.strip()]
        self.assertIn('"comentario"', ''.join(lineas))
        _, acciones = leer(self.ruta)
        self.assertEqual([a.tipo for a in acciones], [MOVER] * 6)
        self.assertEqual(partida.jugador.sala_id, 1)
        self.assertTrue(any(m.startswith('FIN llegada 3') for m in vista.mensajes))

    def test_el_comentario_no_se_ejecuta_al_reproducir_003_FR044(self):
        comandos = [('mover', 'N'), ('mover', 'N'), ('ir', 'a 1'), ('salir', None)]
        controlador, _, partida, bitacora = self._armar(comandos)
        controlador.ejecutar()
        bitacora.cerrar()
        otra = construir(_pasillo(), semilla=3)
        reproducida = reproducir(self.ruta, otra.cripta, otra.proveedor)
        self.assertEqual(reproducida.jugador.sala_id, partida.jugador.sala_id)
        self.assertEqual(reproducida.acciones_jugador, partida.acciones_jugador)
        self.assertEqual(list(reproducida.mapa.estado), list(partida.mapa.estado))

    def test_el_comando_mapa_no_consume_tiempo_ni_se_graba_003_FR026(self):
        comandos = [('mover', 'N'), ('mapa', None), ('salir', None)]
        controlador, vista, partida, bitacora = self._armar(comandos)
        controlador.ejecutar()
        bitacora.cerrar()
        _, acciones = leer(self.ruta)
        self.assertEqual([a.tipo for a in acciones], [MOVER])
        self.assertIn('MAPA', vista.mensajes)
        self.assertEqual(partida.reloj.tiempo_virtual, 100)

    def test_un_destino_no_explorado_no_graba_nada_003_FR029(self):
        comandos = [('ir', 'a 4'), ('salir', None)]
        controlador, vista, partida, bitacora = self._armar(comandos)
        controlador.ejecutar()
        bitacora.cerrar()
        _, acciones = leer(self.ruta)
        self.assertEqual(acciones, [])
        self.assertEqual(partida.reloj.tiempo_virtual, 0)
        self.assertTrue(any('No conoces' in m for m in vista.mensajes))


if __name__ == '__main__':
    unittest.main()
