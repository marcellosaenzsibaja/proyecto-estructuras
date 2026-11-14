import os
import tempfile
import unittest
from src.modelos.acciones import Accion, MOVER, RECOGER
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import NORTE
from src.modelos.errores import ErrorDatos
from src.servicios.guardado import cargar_binario, cargar_json, guardar_binario, guardar_json, leer_sala_binaria, restaurar_partida, tomar_snapshot, version_compatible
from tests.utilidades import arma, construir, enemigo, llave, trampa

def _partida_en_curso():
    p = construir([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[arma(), llave(), enemigo(), trampa()], trampas=[('t-1', trampa())]), 2: ContenidoSala(enemigos=[('e-1', enemigo(), None)])}, [arma(), llave(), enemigo(), trampa()])
    p.iniciar()
    p.ejecutar(Accion(RECOGER, 0))
    p.ejecutar(Accion(RECOGER, 0))
    p.ejecutar(Accion(MOVER, NORTE))
    return p

class PruebasGuardado(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _ruta(self, nombre):
        return os.path.join(self._tmp.name, nombre)

    def _normalizado(self, snapshot):
        copia = dict(snapshot)
        copia['salas'] = sorted(snapshot['salas'], key=lambda s: s['id'])
        return copia

    def test_binario_e_json_producen_el_mismo_snapshot(self):
        p = _partida_en_curso()
        snap = tomar_snapshot(p)
        esperado = self._normalizado(snap)
        ruta_bin = self._ruta('partida.bin')
        guardar_binario(snap, ruta_bin)
        self.assertEqual(self._normalizado(cargar_binario(ruta_bin)), esperado)
        ruta_json = self._ruta('partida.json')
        guardar_json(snap, ruta_json)
        self.assertEqual(self._normalizado(cargar_json(ruta_json)), esperado)

    def test_acceso_aleatorio_a_una_sola_sala(self):
        p = _partida_en_curso()
        snap = tomar_snapshot(p)
        ruta = self._ruta('partida.bin')
        guardar_binario(snap, ruta)
        esperado_sala2 = next((s for s in snap['salas'] if s['id'] == 2))
        self.assertEqual(leer_sala_binaria(ruta, 2), esperado_sala2)
        self.assertIsNone(leer_sala_binaria(ruta, 999))

    def test_restaurar_reconstruye_una_partida_jugable(self):
        p1 = _partida_en_curso()
        snap = tomar_snapshot(p1)
        p2_base = construir([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[arma(), llave(), enemigo(), trampa()], trampas=[('t-1', trampa())]), 2: ContenidoSala(enemigos=[('e-1', enemigo(), None)])}, [arma(), llave(), enemigo(), trampa()])
        restaurada = restaurar_partida(snap, p2_base.cripta, p2_base.proveedor)
        self.assertEqual(restaurada.jugador.sala_id, p1.jugador.sala_id)
        self.assertEqual(restaurada.jugador.vida, p1.jugador.vida)
        self.assertEqual(len(restaurada.jugador.inventario), len(p1.jugador.inventario))
        self.assertEqual(restaurada.acciones_jugador, p1.acciones_jugador)
        self.assertEqual(restaurada.reloj.tiempo_virtual, p1.reloj.tiempo_virtual)
        self.assertTrue(restaurada.esperando_jugador)
        sala2 = restaurada.cripta.sala(2)
        self.assertEqual(len(sala2.enemigos), 1)
        self.assertTrue(sala2.enemigos[0].activo)
        from src.modelos.acciones import ESPERAR
        resultado = restaurada.ejecutar(Accion(ESPERAR))
        self.assertEqual(resultado.estado, 'aceptada')

    def test_version_incompatible_se_rechaza(self):
        p1 = _partida_en_curso()
        snap = tomar_snapshot(p1)
        p2_base = construir([(1, 'N', 2, {})])
        self.assertTrue(version_compatible(snap, p1.cripta))
        p2_base.cripta.datos.version = 'otra-version'
        self.assertFalse(version_compatible(snap, p2_base.cripta))
        with self.assertRaises(ErrorDatos):
            restaurar_partida(snap, p2_base.cripta, p2_base.proveedor)

    def test_binario_es_mas_compacto_que_json(self):
        p = _partida_en_curso()
        snap = tomar_snapshot(p)
        ruta_bin = self._ruta('partida.bin')
        ruta_json = self._ruta('partida.json')
        guardar_binario(snap, ruta_bin)
        guardar_json(snap, ruta_json)
        self.assertLess(os.path.getsize(ruta_bin), os.path.getsize(ruta_json))
if __name__ == '__main__':
    unittest.main()
