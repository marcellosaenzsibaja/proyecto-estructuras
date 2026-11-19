"""Persistencia de la línea de tiempo y del mapa conocido, y rechazo de formatos anteriores."""
import json
import os
import struct
import tempfile
import unittest

from src.modelos.acciones import Accion, ESPERAR, MOVER, RECOGER
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import NORTE
from src.modelos.errores import ErrorDatos
from src.modelos.resumen_historia import formatear
from src.servicios import guardado
from tests.utilidades import antorcha, construir, pocion_cura


def _conexiones(largo=6):
    return [(i, 'N', i + 1, {}) for i in range(1, largo)]


def _jugada(k=3, contenidos=None, fichas=()):
    partida = construir(_conexiones(), contenidos=contenidos, fichas=fichas, semilla=13)
    partida.linea.k = k
    partida.iniciar()
    for accion in [Accion(MOVER, NORTE), Accion(ESPERAR), Accion(MOVER, NORTE), Accion(ESPERAR)]:
        partida.ejecutar(accion)
    return partida


class TestPersistencia(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _ruta(self, nombre):
        return os.path.join(self._tmp.name, nombre)

    def _recargar(self, partida, nombre='p.bin', contenidos=None, fichas=()):
        ruta = self._ruta(nombre)
        snapshot = guardado.tomar_snapshot(partida)
        if nombre.endswith('.json'):
            guardado.guardar_json(snapshot, ruta)
            leido = guardado.cargar_json(ruta)
        else:
            guardado.guardar_binario(snapshot, ruta)
            leido = guardado.cargar_binario(ruta)
        limpia = construir(_conexiones(), contenidos=contenidos, fichas=fichas, semilla=13)
        return guardado.restaurar_partida(leido, limpia.cripta, limpia.proveedor)

    def test_conserva_la_linea_completa_004_FR028(self):
        partida = _jugada()
        cargada = self._recargar(partida)
        self.assertEqual(cargada.linea.tamano(), partida.linea.tamano())
        self.assertEqual([e.numero for e in cargada.linea.entradas],
                         [e.numero for e in partida.linea.entradas])
        self.assertEqual([e.tiempo for e in cargada.linea.entradas],
                         [e.tiempo for e in partida.linea.entradas])

    def test_las_consultas_dan_el_mismo_resumen_004_FR028_SC009(self):
        partida = _jugada()
        cargada = self._recargar(partida)
        for t in range(0, partida.reloj.tiempo_virtual + 1, 50):
            esperado = formatear(partida.historia_en(t)[0])
            obtenido = formatear(cargada.historia_en(t)[0])
            self.assertEqual(obtenido, esperado, f't={t}')

    def test_conserva_el_mapa_conocido_003_FR046(self):
        partida = _jugada()
        cargada = self._recargar(partida)
        self.assertEqual(list(cargada.mapa.estado), list(partida.mapa.estado))
        self.assertEqual(list(cargada.mapa.puertas), list(partida.mapa.puertas))
        self.assertEqual(cargada.mapa.exploradas, partida.mapa.exploradas)

    def test_conserva_el_mapa_en_json_003_FR046(self):
        partida = _jugada()
        cargada = self._recargar(partida, 'p.json')
        self.assertEqual(list(cargada.mapa.estado), list(partida.mapa.estado))
        self.assertEqual(cargada.linea.tamano(), partida.linea.tamano())

    def test_conserva_el_cursor_y_los_efectos_004_FR028(self):
        tea = antorcha(duracion=3000)
        pocion = pocion_cura('itm_p1')
        partida = construir(_conexiones(), contenidos={1: ContenidoSala(objetos=[tea, pocion])},
                            fichas=[tea, pocion], semilla=13)
        partida.iniciar()
        partida.ejecutar(Accion(RECOGER, 0))
        partida.ejecutar(Accion(RECOGER, 0))
        partida.ejecutar(Accion('usar'))
        self.assertIsNotNone(partida.jugador.antorcha)
        indice_antes = [n.valor.ficha.id for n in partida.jugador.inventario.nodos()].index(
            partida.jugador.inventario.actual().ficha.id)
        cargada = self._recargar(partida, contenidos={1: ContenidoSala(objetos=[tea, pocion])}, fichas=[tea, pocion])
        self.assertIsNotNone(cargada.jugador.antorcha)
        self.assertEqual(cargada.jugador.antorcha.fin, partida.jugador.antorcha.fin)
        indice_despues = [n.valor.ficha.id for n in cargada.jugador.inventario.nodos()].index(
            cargada.jugador.inventario.actual().ficha.id)
        self.assertEqual(indice_despues, indice_antes)


class TestIncompatibilidad(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_la_version_del_formato_es_tres_004_FR029(self):
        self.assertEqual(guardado.FORMATO_VERSION, 3)

    def test_un_archivo_de_version_anterior_se_rechaza_004_FR029_ApendiceB(self):
        partida = _jugada()
        ruta = os.path.join(self._tmp.name, 'vieja.bin')
        guardado.guardar_binario(guardado.tomar_snapshot(partida), ruta)
        with open(ruta, 'r+b') as archivo:
            archivo.seek(len(guardado.MAGIC))
            archivo.write(struct.pack('>H', 2))
        with self.assertRaises(ErrorDatos) as contexto:
            guardado.cargar_binario(ruta)
        self.assertIn('incompatible', str(contexto.exception))

    def test_un_archivo_de_la_primera_parte_se_rechaza_004_FR029_ApendiceB(self):
        partida = _jugada()
        ruta = os.path.join(self._tmp.name, 'p1.bin')
        guardado.guardar_binario(guardado.tomar_snapshot(partida), ruta)
        with open(ruta, 'r+b') as archivo:
            archivo.seek(len(guardado.MAGIC))
            archivo.write(struct.pack('>H', 1))
        with self.assertRaises(ErrorDatos):
            guardado.cargar_binario(ruta)


class TestPuntosNoSePersisten(unittest.TestCase):

    def test_el_snapshot_de_un_punto_no_lleva_la_linea_004_R2(self):
        partida = _jugada()
        completo = guardado.tomar_snapshot(partida, incluir_linea=True)
        punto = guardado.tomar_snapshot(partida, incluir_linea=False)
        self.assertIn('linea', completo['extra'])
        self.assertNotIn('linea', punto['extra'])

    def test_el_archivo_no_contiene_puntos_de_control_004_R2(self):
        partida = _jugada()
        snapshot = guardado.tomar_snapshot(partida)
        texto = json.dumps(snapshot)
        self.assertNotIn('estado_azar', texto)
        self.assertNotIn('indice_entrada', texto)


if __name__ == '__main__':
    unittest.main()
