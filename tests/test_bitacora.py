import os
import tempfile
import unittest
from src.modelos.acciones import ACEPTADA, Accion, ESPERAR, MOVER, RECOGER
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import NORTE
from src.modelos.errores import ErrorDatos
from src.servicios.bitacora import Bitacora, leer, reproducir, verificar_version
from tests.utilidades import arma, construir, llave

def _construir_cripta():
    return construir([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[arma(), llave()])}, [arma(), llave()])

class PruebasBitacora(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, 'partida.log')

    def test_grabar_y_leer(self):
        p = _construir_cripta()
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar(p.cripta.datos.id, p.cripta.datos.version, p.semilla)
            bitacora.registrar(Accion(RECOGER, 0))
            bitacora.registrar(Accion(MOVER, NORTE))
        encabezado, acciones = leer(self.ruta)
        self.assertEqual(encabezado['cripta_id'], p.cripta.datos.id)
        self.assertEqual(encabezado['semilla'], p.semilla)
        self.assertEqual([a.tipo for a in acciones], [RECOGER, MOVER])
        self.assertEqual(acciones[1].argumento, NORTE)

    def test_es_append_only(self):
        p = _construir_cripta()
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar(p.cripta.datos.id, p.cripta.datos.version, p.semilla)
            bitacora.registrar(Accion(ESPERAR))
        with Bitacora(self.ruta) as bitacora:
            bitacora.registrar(Accion(ESPERAR))
        _, acciones = leer(self.ruta)
        self.assertEqual(len(acciones), 2)

    def test_reproducir_llega_al_mismo_estado(self):
        p = _construir_cripta()
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar(p.cripta.datos.id, p.cripta.datos.version, p.semilla)
            p.iniciar()
            for accion in (Accion(RECOGER, 0), Accion(RECOGER, 0), Accion(MOVER, NORTE)):
                resultado = p.ejecutar(accion)
                self.assertEqual(resultado.estado, ACEPTADA)
                bitacora.registrar(accion)
        p2 = _construir_cripta()
        reproducida = reproducir(self.ruta, p2.cripta, p2.proveedor)
        self.assertEqual(reproducida.jugador.sala_id, p.jugador.sala_id)
        self.assertEqual(len(reproducida.jugador.inventario), len(p.jugador.inventario))
        self.assertEqual(reproducida.reloj.tiempo_virtual, p.reloj.tiempo_virtual)
        self.assertEqual(reproducida.acciones_jugador, p.acciones_jugador)

    def test_version_incompatible_se_rechaza(self):
        p = _construir_cripta()
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar('otra-cripta', 'v9', p.semilla)
        encabezado, _ = leer(self.ruta)
        with self.assertRaises(ErrorDatos):
            verificar_version(encabezado, p.cripta)
        with self.assertRaises(ErrorDatos):
            reproducir(self.ruta, p.cripta, p.proveedor)

    def test_archivo_sin_encabezado_falla(self):
        with open(self.ruta, 'w', encoding='utf-8') as archivo:
            archivo.write('{"tipo": "mover", "argumento": 0}\n')
        with self.assertRaises(ErrorDatos):
            leer(self.ruta)
if __name__ == '__main__':
    unittest.main()
