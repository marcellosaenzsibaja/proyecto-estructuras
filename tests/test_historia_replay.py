"""Consulta sin interacción: --hasta, cursor en la bitácora y comentarios (spec 004)."""
import os
import tempfile
import unittest

from src.modelos.acciones import Accion, ESPERAR, MOVER, USAR
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import NORTE
from src.modelos.linea_tiempo import CURSOR_ANT, CURSOR_SIG
from src.modelos.resumen_historia import construir as construir_resumen
from src.modelos.resumen_historia import formatear
from src.servicios.bitacora import Bitacora, leer, reproducir
from tests.utilidades import construir, pocion_cura


def _conexiones(largo=6):
    return [(i, 'N', i + 1, {}) for i in range(1, largo)]


def _cripta(contenidos=None, fichas=()):
    return construir(_conexiones(), contenidos=contenidos, fichas=fichas, semilla=5)


class TestReplayHasta(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, 'partida.log')

    def _grabar(self, acciones):
        base = _cripta()
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar(base.cripta.datos.id, base.cripta.datos.version, base.semilla)
            for accion in acciones:
                bitacora.registrar(accion)
        return base

    def test_hasta_da_el_mismo_resumen_que_historia_004_FR017(self):
        acciones = [Accion(MOVER, NORTE), Accion(ESPERAR), Accion(MOVER, NORTE), Accion(ESPERAR)]
        self._grabar(acciones)
        vivo = _cripta()
        vivo.linea.k = 2
        vivo.iniciar()
        instantes = []
        for accion in acciones:
            vivo.ejecutar(accion)
            instantes.append(vivo.reloj.tiempo_virtual)
        for t in instantes:
            reproducida = reproducir(self.ruta, _cripta().cripta, _cripta().proveedor, hasta=t, k_checkpoint=2)
            if reproducida.reloj.tiempo_virtual < t:
                reproducida.avanzar_hasta(t)
            esperado = formatear(vivo.historia_en(t)[0])
            obtenido = formatear(construir_resumen(reproducida, t))
            self.assertEqual(obtenido, esperado, f't={t}')

    def test_hasta_posterior_al_final_indica_que_termino_antes_004_FR018_ApendiceB(self):
        self._grabar([Accion(ESPERAR), Accion(ESPERAR)])
        base = _cripta()
        reproducida = reproducir(self.ruta, base.cripta, base.proveedor, hasta=10 ** 6)
        final = reproducida.reloj.tiempo_virtual
        resumen = construir_resumen(reproducida, 10 ** 6)
        self.assertTrue(resumen.trunco)
        lineas = formatear(resumen)
        self.assertTrue(any('terminó en el instante' in l for l in lineas))
        self.assertEqual(resumen.tiempo_final, final)

    def test_sin_hasta_reproduce_toda_la_bitacora_004_FR019(self):
        acciones = [Accion(ESPERAR)] * 4
        self._grabar(acciones)
        base = _cripta()
        reproducida = reproducir(self.ruta, base.cripta, base.proveedor)
        self.assertEqual(reproducida.acciones_jugador, 4)


class TestCursorEnBitacora(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, 'partida.log')

    def test_el_cursor_se_graba_y_se_reproduce_004_R5(self):
        primera, segunda = pocion_cura('itm_p1', cura=5), pocion_cura('itm_p2', cura=20)
        contenidos = {1: ContenidoSala(objetos=[primera, segunda])}
        fichas = [primera, segunda]
        base = construir(_conexiones(), contenidos=contenidos, fichas=fichas, semilla=5)
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar(base.cripta.datos.id, base.cripta.datos.version, base.semilla)
            bitacora.registrar(Accion('recoger', 0))
            bitacora.registrar(Accion('recoger', 0))
            bitacora.registrar_cursor(CURSOR_SIG)
            bitacora.registrar(Accion(USAR))
        _, acciones = leer(self.ruta)
        self.assertIn(CURSOR_SIG, [a.tipo for a in acciones])
        otra = construir(_conexiones(), contenidos=contenidos, fichas=fichas, semilla=5)
        reproducida = reproducir(self.ruta, otra.cripta, otra.proveedor)
        self.assertEqual(reproducida.acciones_jugador, 3)
        restantes = [o.ficha.id for o in reproducida.jugador.inventario]
        self.assertEqual(len(restantes), 1)

    def test_el_comentario_no_es_una_accion_003_FR044(self):
        base = _cripta()
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar(base.cripta.datos.id, base.cripta.datos.version, base.semilla)
            bitacora.registrar_comentario('ir a 4')
            bitacora.registrar(Accion(MOVER, NORTE))
            bitacora.registrar(Accion(MOVER, NORTE))
        _, acciones = leer(self.ruta)
        self.assertEqual([a.tipo for a in acciones], [MOVER, MOVER])
        otra = _cripta()
        reproducida = reproducir(self.ruta, otra.cripta, otra.proveedor)
        self.assertEqual(reproducida.acciones_jugador, 2)

    def test_una_bitacora_sin_cursor_sigue_leyendose_004_R5(self):
        base = _cripta()
        with Bitacora(self.ruta) as bitacora:
            bitacora.iniciar(base.cripta.datos.id, base.cripta.datos.version, base.semilla)
            bitacora.registrar(Accion(ESPERAR))
        otra = _cripta()
        reproducida = reproducir(self.ruta, otra.cripta, otra.proveedor)
        self.assertEqual(reproducida.acciones_jugador, 1)


if __name__ == '__main__':
    unittest.main()
