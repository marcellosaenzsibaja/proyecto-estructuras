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


class PruebasReplayConCazadores(unittest.TestCase):
    """T051: dos reproducciones del mismo log producen las mismas decisiones (FR-027, SC-005)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _construir(self):
        from src.modelos.fichas import CAZADOR, FichaEnemigo
        cazador = FichaEnemigo('ent_cazador', 'Cazador', 18, 1, 2, 130, CAZADOR, (), None, 2000)
        conexiones = [(1, 'N', 2, {'costo': 120}), (2, 'N', 3, {'costo': 80}), (3, 'E', 4, {'costo': 200}),
                      (4, 'S', 5, {'costo': 60}), (5, 'O', 2, {'costo': 300}), (4, 'N', 6, {'costo': 90})]
        return construir(conexiones, {1: ContenidoSala(enemigos=[('e-1', cazador, None), ('e-2', cazador, None)])}, [cazador], inicial=1)

    def _traza(self, partida):
        posiciones = []
        for sala in partida.cripta.salas():
            for e in sala.enemigos:
                posiciones.append((e.id_actor, e.sala_id, None if e.evento is None else e.evento.tiempo))
        posiciones.sort()
        return posiciones

    def test_replay_con_cazadores_FR027(self):
        from src.modelos.acciones import ESPERAR, MOVER
        from src.modelos.direcciones import ESTE, NORTE, OESTE, SUR
        ruta = os.path.join(self._tmp.name, 'partida.log')
        p = self._construir()
        acciones = [Accion(MOVER, NORTE), Accion(MOVER, NORTE), Accion(MOVER, ESTE), Accion(MOVER, NORTE), Accion(ESPERAR), Accion(ESPERAR), Accion(ESPERAR)]
        with Bitacora(ruta) as bitacora:
            bitacora.iniciar(p.cripta.datos.id, p.cripta.datos.version, p.semilla)
            p.iniciar()
            for accion in acciones:
                if p.estado != 'en_curso':
                    break
                p.ejecutar(accion)
                bitacora.registrar(accion)
        a = self._construir()
        b = self._construir()
        uno = reproducir(ruta, a.cripta, a.proveedor)
        dos = reproducir(ruta, b.cripta, b.proveedor)
        self.assertEqual(self._traza(uno), self._traza(dos))
        self.assertEqual(self._traza(uno), self._traza(p))
        self.assertEqual(uno.reloj.tiempo_virtual, p.reloj.tiempo_virtual)
        movidos = [t for t in self._traza(p) if t[1] != 1]
        self.assertTrue(movidos)  # los cazadores realmente persiguieron
