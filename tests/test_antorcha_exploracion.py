"""Efecto de la antorcha sobre el mapa conocido y su reversión (spec 003, US3 y Apéndice B)."""
import unittest

from src.modelos.acciones import Accion, MOVER, RECOGER, USAR
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import ESTE, NORTE, OESTE, SUR
from src.modelos.mapa_conocido import AVISTADA, EXPLORADA, RECORDADA_ABIERTA, SIN_OBSERVAR
from tests.utilidades import antorcha, construir, enemigo, pergamino, trampa


def _actuar(p, tipo, argumento=None):
    return p.ejecutar(Accion(tipo, argumento))


CRUZ = [(1, 'N', 2, {}), (2, 'N', 3, {}), (2, 'E', 4, {'cerrada': True, 'llave': 'itm_x'}),
        (2, 'O', 5, {}), (3, 'N', 6, {})]


def _con_antorcha(contenidos=None, extras=()):
    tea = antorcha(duracion=5000)
    objetos = [tea] + list(extras)
    base = {1: ContenidoSala(objetos=objetos)}
    if contenidos:
        base.update(contenidos)
    fichas = [tea] + list(extras)
    for contenido in (contenidos or {}).values():
        for instancia in contenido.enemigos:
            fichas.append(instancia[1])
        for t in contenido.trampas:
            fichas.append(t[1])
    partida = construir(CRUZ, contenidos=base, fichas=fichas, semilla=3)
    partida.iniciar()
    _actuar(partida, RECOGER, 0)
    return partida


def _encender(partida):
    for nodo in partida.jugador.inventario.nodos():
        if nodo.valor.ficha.clase == 'antorcha':
            partida.jugador.inventario.fijar_cursor(nodo)
            break
    _actuar(partida, USAR)


class TestAntorcha(unittest.TestCase):

    def test_sin_antorcha_las_vecinas_quedan_avistadas_003_FR005(self):
        partida = _con_antorcha()
        _actuar(partida, MOVER, NORTE)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(3)), AVISTADA)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(4)), AVISTADA)

    def test_con_antorcha_las_vecinas_quedan_exploradas_003_FR014_ApendiceB(self):
        partida = _con_antorcha()
        _encender(partida)
        self.assertIsNotNone(partida.jugador.antorcha)
        _actuar(partida, MOVER, NORTE)
        for id_sala in (3, 4, 5):
            self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(id_sala)), EXPLORADA, id_sala)

    def test_explora_tambien_por_salidas_cerradas_003_FR014_ApendiceB(self):
        partida = _con_antorcha()
        _encender(partida)
        _actuar(partida, MOVER, NORTE)
        self.assertTrue(partida.cripta.sala(2).salidas[ESTE].puerta.cerrada)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(4)), EXPLORADA)

    def test_revela_salidas_y_avista_lo_que_sigue_003_FR015(self):
        partida = _con_antorcha()
        _encender(partida)
        _actuar(partida, MOVER, NORTE)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(6)), AVISTADA)

    def test_no_observa_las_puertas_lejanas_de_la_vecina_003_FR017(self):
        partida = _con_antorcha()
        _encender(partida)
        _actuar(partida, MOVER, NORTE)
        sala3 = partida.cripta.sala(3)
        self.assertEqual(partida.mapa.puerta_recordada(sala3, NORTE), SIN_OBSERVAR)
        self.assertEqual(partida.mapa.puerta_recordada(sala3, SUR), RECORDADA_ABIERTA)

    def test_no_activa_enemigos_ni_trampas_003_FR016_ApendiceB(self):
        bestia = enemigo(comportamiento='guardian')
        dardos = trampa(dano=5)
        contenidos = {3: ContenidoSala(enemigos=[('e-1', bestia, None)], trampas=[('t-1', dardos)])}
        partida = _con_antorcha(contenidos)
        _encender(partida)
        vida_antes = partida.jugador.vida
        _actuar(partida, MOVER, NORTE)
        sala3 = partida.cripta.sala(3)
        self.assertEqual(partida.mapa.estado_de(sala3), EXPLORADA)
        self.assertEqual(partida.jugador.vida, vida_antes)
        self.assertEqual(sala3.enemigos, [])
        self.assertFalse(sala3.contenido_incorporado)

    def test_entrar_despues_si_activa_todo_003_FR018(self):
        bestia = enemigo(comportamiento='guardian')
        dardos = trampa(dano=5)
        contenidos = {3: ContenidoSala(enemigos=[('e-1', bestia, None)], trampas=[('t-1', dardos)])}
        partida = _con_antorcha(contenidos)
        _encender(partida)
        _actuar(partida, MOVER, NORTE)
        vida_antes = partida.jugador.vida
        _actuar(partida, MOVER, NORTE)
        sala3 = partida.cripta.sala(3)
        self.assertTrue(sala3.contenido_incorporado)
        self.assertEqual(len(sala3.enemigos), 1)
        self.assertLess(partida.jugador.vida, vida_antes)

    def test_apagarse_no_cambia_el_mapa_003_FR019(self):
        partida = _con_antorcha()
        _encender(partida)
        _actuar(partida, MOVER, NORTE)
        estado = list(partida.mapa.estado)
        partida.jugador.antorcha = None
        self.assertEqual(list(partida.mapa.estado), estado)


class TestReversionDeLaAntorcha(unittest.TestCase):

    def test_un_pergamino_revierte_la_exploracion_003_FR048_ApendiceB(self):
        perg = pergamino()
        partida = _con_antorcha(extras=[perg])
        _actuar(partida, RECOGER, 0)
        _encender(partida)
        estado_antes = list(partida.mapa.estado)
        exploradas_antes = list(partida.mapa.exploradas)
        puertas_antes = list(partida.mapa.puertas)
        sala_antes = partida.jugador.sala_id
        _actuar(partida, MOVER, NORTE)
        self.assertGreater(len(partida.mapa.exploradas), len(exploradas_antes) + 1)
        for nodo in partida.jugador.inventario.nodos():
            if nodo.valor.ficha.clase == 'pergamino':
                partida.jugador.inventario.fijar_cursor(nodo)
                break
        _actuar(partida, USAR)
        self.assertEqual(partida.jugador.sala_id, sala_antes)
        self.assertEqual(list(partida.mapa.estado), estado_antes)
        self.assertEqual(list(partida.mapa.exploradas), exploradas_antes)
        self.assertEqual(list(partida.mapa.puertas), puertas_antes)


if __name__ == '__main__':
    unittest.main()
