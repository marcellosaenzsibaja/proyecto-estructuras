"""Comando «ir a»: rutas, rechazos y paradas (spec 003, US4 y US5, y Apéndice B)."""
import unittest

from src.modelos.acciones import Accion, MOVER, RECOGER, USAR
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import ESTE, NORTE, OESTE, SUR
from src.modelos.viaje import DANO, ENEMIGOS, LLEGADA, SIN_RUTA, ejecutar_viaje, resolver_destino, validar_destino
from tests.referencia_conocido import mejor_primer_paso
from tests.utilidades import antorcha, construir, enemigo, llave, pergamino, trampa


def _actuar(p, tipo, argumento=None):
    return p.ejecutar(Accion(tipo, argumento))


def _iniciada(conexiones, contenidos=None, fichas=(), semilla=3):
    partida = construir(conexiones, contenidos=contenidos, fichas=fichas, semilla=semilla)
    partida.iniciar()
    return partida


def _explorar(partida, direcciones):
    for direccion in direcciones:
        _actuar(partida, MOVER, direccion)


class TestRechazos(unittest.TestCase):

    def test_destino_no_explorado_se_rechaza_sin_tiempo_003_FR029_ApendiceB(self):
        partida = _iniciada([(1, 'N', 2, {}), (2, 'N', 3, {})])
        reloj = partida.reloj.tiempo_virtual
        acciones = partida.acciones_jugador
        id_destino, error = resolver_destino(partida, '2')
        self.assertIsNone(id_destino)
        self.assertIn('No conoces esa sala', error)
        self.assertEqual(partida.reloj.tiempo_virtual, reloj)
        self.assertEqual(partida.acciones_jugador, acciones)

    def test_destino_inexistente_se_rechaza_003_FR029(self):
        partida = _iniciada([(1, 'N', 2, {})])
        self.assertIsNone(resolver_destino(partida, '77')[0])
        self.assertIsNone(resolver_destino(partida, 'Sala fantasma')[0])
        self.assertIsNone(resolver_destino(partida, '')[0])

    def test_destino_igual_a_la_sala_actual_se_rechaza_003_FR029(self):
        partida = _iniciada([(1, 'N', 2, {})])
        self.assertEqual(validar_destino(partida, 1), 'Ya estás en esa sala.')

    def test_sin_ruta_conocida_se_rechaza_003_FR029(self):
        conexiones = [(1, 'N', 2, {}), (2, 'N', 3, {'cerrada': True, 'llave': 'itm_x'})]
        partida = _iniciada(conexiones)
        _explorar(partida, [NORTE])
        self.assertIsNotNone(resolver_destino(partida, '2')[0])
        self.assertEqual(partida.mapa.explorada(partida.cripta.sala(3)), False)

    def test_nombre_ambiguo_se_rechaza_003_FR028(self):
        partida = _iniciada([(1, 'N', 2, {})])
        partida.cripta.sala(2).nombre = partida.cripta.sala(1).nombre
        _explorar(partida, [NORTE])
        id_destino, error = resolver_destino(partida, partida.cripta.sala(1).nombre)
        self.assertIsNone(id_destino)
        self.assertIn('varias salas', error)

    def test_resuelve_por_nombre_sin_tildes_ni_mayusculas_003_FR028(self):
        partida = _iniciada([(1, 'N', 2, {})])
        partida.cripta.sala(1).nombre = 'Galería Inundada'
        self.assertEqual(resolver_destino(partida, 'galeria inundada')[0], 1)


class TestRutas(unittest.TestCase):

    def test_sigue_la_ruta_mas_barata_no_la_mas_corta_003_FR031(self):
        conexiones = [(1, 'N', 2, {'costo': 250}), (2, 'N', 5, {'costo': 250}),
                      (1, 'E', 3, {'costo': 100}), (3, 'N', 4, {'costo': 100}),
                      (4, 'N', 5, {'costo': 100}), (5, 'E', 6, {'costo': 100})]
        partida = _iniciada(conexiones)
        _explorar(partida, [NORTE, NORTE, SUR, SUR, ESTE, NORTE, NORTE, SUR, SUR, OESTE])
        self.assertEqual(partida.jugador.sala_id, 1)
        for id_sala in (2, 3, 4, 5):
            self.assertTrue(partida.mapa.explorada(partida.cripta.sala(id_sala)), id_sala)
        self.assertEqual(partida.siguiente_paso_viaje(5), ESTE)

    def test_desempata_por_la_vecina_de_menor_id_003_FR032(self):
        conexiones = [(1, 'N', 2, {'costo': 100}), (1, 'E', 3, {'costo': 100}),
                      (2, 'E', 4, {'costo': 100}), (3, 'N', 4, {'costo': 100})]
        partida = _iniciada(conexiones)
        _explorar(partida, [NORTE, ESTE, OESTE, SUR, SUR, OESTE])
        self.assertEqual(partida.jugador.sala_id, 1)
        resultado = partida.ruta_conocida(4)
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado[1], 2)

    def test_no_usa_una_puerta_recordada_cerrada_aunque_tenga_llave_003_FR041(self):
        conexiones = [(1, 'N', 2, {'cerrada': True, 'llave': 'itm_llave'})]
        partida = _iniciada(conexiones, {1: ContenidoSala(objetos=[llave()])}, [llave()])
        _actuar(partida, RECOGER, 0)
        self.assertFalse(partida.mapa.recordada_abierta(partida.cripta.sala(1), NORTE))
        self.assertIsNone(partida.siguiente_paso_viaje(2))

    def test_coincide_con_la_referencia_teorica_003_SC005(self):
        conexiones = [(1, 'N', 2, {'costo': 120}), (1, 'E', 3, {'costo': 100}),
                      (2, 'E', 4, {'costo': 100}), (3, 'N', 4, {'costo': 130}),
                      (4, 'N', 5, {'costo': 100}), (2, 'N', 5, {'costo': 300})]
        partida = _iniciada(conexiones)
        _explorar(partida, [NORTE, ESTE, NORTE, SUR, OESTE, SUR, OESTE])
        for id_destino in (2, 3, 4, 5):
            sala = partida.cripta.sala(id_destino)
            if not partida.mapa.explorada(sala):
                continue
            esperado = mejor_primer_paso(partida, partida.jugador.sala_id, id_destino)
            obtenido = partida.ruta_conocida(id_destino)
            self.assertEqual(obtenido, esperado, f'destino {id_destino}')


class TestViaje(unittest.TestCase):

    def test_llega_al_destino_y_consume_tiempo_003_FR034_FR036(self):
        conexiones = [(i, 'N', i + 1, {'costo': 100}) for i in range(1, 5)]
        partida = _iniciada(conexiones)
        _explorar(partida, [NORTE, NORTE, NORTE])
        self.assertEqual(partida.jugador.sala_id, 4)
        reloj_antes = partida.reloj.tiempo_virtual
        acciones_antes = partida.acciones_jugador
        viaje = ejecutar_viaje(partida, 1)
        self.assertEqual(viaje.motivo, LLEGADA)
        self.assertEqual(viaje.pasos, 3)
        self.assertEqual(partida.jugador.sala_id, 1)
        self.assertEqual(partida.acciones_jugador, acciones_antes + 3)
        self.assertEqual(partida.reloj.tiempo_virtual, reloj_antes + 300)

    DIAMANTE = [(1, 'N', 2, {'costo': 100}), (2, 'E', 4, {'costo': 100}),
                (1, 'E', 3, {'costo': 300}), (3, 'N', 4, {'costo': 300})]

    def _diamante_con_antorcha(self, contenido_de_2):
        """Explora 2 y 4 solo con la antorcha, para que su contenido siga sin incorporar."""
        tea = antorcha(duracion=9000)
        contenidos = {1: ContenidoSala(objetos=[tea]), 2: contenido_de_2}
        fichas = [tea]
        for instancia in contenido_de_2.enemigos:
            fichas.append(instancia[1])
        for t in contenido_de_2.trampas:
            fichas.append(t[1])
        partida = _iniciada(self.DIAMANTE, contenidos, fichas)
        _actuar(partida, RECOGER, 0)
        _explorar(partida, [ESTE, NORTE, SUR, OESTE])
        _actuar(partida, USAR)
        _explorar(partida, [ESTE, OESTE])
        self.assertEqual(partida.jugador.sala_id, 1)
        for id_sala in (2, 3, 4):
            self.assertTrue(partida.mapa.explorada(partida.cripta.sala(id_sala)), id_sala)
        self.assertFalse(partida.cripta.sala(2).contenido_incorporado)
        return partida

    def test_se_detiene_ante_enemigos_dormidos_003_FR037_ApendiceB(self):
        bestia = enemigo(comportamiento='guardian', velocidad=1)
        partida = self._diamante_con_antorcha(ContenidoSala(enemigos=[('e-1', bestia, None)]))
        vida_antes = partida.jugador.vida
        viaje = ejecutar_viaje(partida, 4)
        self.assertEqual(partida.jugador.vida, vida_antes)
        self.assertEqual(viaje.motivo, ENEMIGOS)
        self.assertEqual(partida.jugador.sala_id, 2)
        self.assertEqual(len(partida.cripta.sala(2).enemigos), 1)
        self.assertEqual(partida.cripta.sala(2).dormidos, [])

    def test_se_detiene_al_recibir_dano_003_FR038(self):
        dardos = trampa(dano=6, rearme=100000)
        partida = self._diamante_con_antorcha(ContenidoSala(trampas=[('t-1', dardos)]))
        vida_antes = partida.jugador.vida
        viaje = ejecutar_viaje(partida, 4)
        self.assertEqual(viaje.motivo, DANO)
        self.assertEqual(partida.jugador.sala_id, 2)
        self.assertLess(partida.jugador.vida, vida_antes)

    def test_la_puerta_que_el_mapa_creia_abierta_detiene_el_viaje_003_FR039_ApendiceB(self):
        conexiones = [(1, 'N', 2, {}), (2, 'N', 3, {})]
        partida = _iniciada(conexiones)
        _explorar(partida, [NORTE, NORTE, SUR, SUR])
        self.assertEqual(partida.jugador.sala_id, 1)
        sala2 = partida.cripta.sala(2)
        self.assertTrue(partida.mapa.recordada_abierta(sala2, NORTE))
        sala2.salidas[NORTE].puerta.cerrada = True
        reloj_antes = partida.reloj.tiempo_virtual
        viaje = ejecutar_viaje(partida, 3)
        self.assertEqual(viaje.motivo, SIN_RUTA)
        self.assertEqual(viaje.pasos, 1)
        self.assertEqual(partida.jugador.sala_id, 2)
        self.assertEqual(partida.reloj.tiempo_virtual, reloj_antes + 100)
        self.assertFalse(partida.mapa.recordada_abierta(sala2, NORTE))

    def test_la_ruta_se_recalcula_y_el_viaje_sigue_si_hay_alternativa_003_FR035(self):
        conexiones = [(1, 'N', 2, {'costo': 100}), (2, 'N', 5, {'costo': 100}),
                      (2, 'E', 3, {'costo': 100}), (3, 'N', 4, {'costo': 100}),
                      (4, 'O', 5, {'costo': 100})]
        partida = _iniciada(conexiones)
        _explorar(partida, [NORTE, NORTE, SUR, ESTE, NORTE, OESTE, ESTE, SUR, OESTE, SUR])
        self.assertEqual(partida.jugador.sala_id, 1)
        for id_sala in (2, 3, 4, 5):
            self.assertTrue(partida.mapa.explorada(partida.cripta.sala(id_sala)), id_sala)
        partida.cripta.sala(2).salidas[NORTE].puerta.cerrada = True
        viaje = ejecutar_viaje(partida, 5)
        self.assertEqual(viaje.motivo, LLEGADA)
        self.assertEqual(partida.jugador.sala_id, 5)
        self.assertGreater(viaje.pasos, 2)


class TestPergaminoEnViaje(unittest.TestCase):

    def test_revierte_solo_el_ultimo_paso_003_FR045_ApendiceB(self):
        perg = pergamino()
        conexiones = [(i, 'N', i + 1, {'costo': 100}) for i in range(1, 5)]
        partida = _iniciada(conexiones, {1: ContenidoSala(objetos=[perg])}, [perg])
        _actuar(partida, RECOGER, 0)
        _explorar(partida, [NORTE, NORTE, NORTE])
        viaje = ejecutar_viaje(partida, 1)
        self.assertEqual(viaje.motivo, LLEGADA)
        self.assertEqual(partida.jugador.sala_id, 1)
        acciones_antes = partida.acciones_jugador
        for nodo in partida.jugador.inventario.nodos():
            if nodo.valor.ficha.clase == 'pergamino':
                partida.jugador.inventario.fijar_cursor(nodo)
                break
        _actuar(partida, USAR)
        self.assertEqual(partida.jugador.sala_id, 2)
        self.assertEqual(partida.acciones_jugador, acciones_antes - 1)


if __name__ == '__main__':
    unittest.main()
