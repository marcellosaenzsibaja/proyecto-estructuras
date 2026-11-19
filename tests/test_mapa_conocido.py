"""Mapa conocido: tres estados y memoria de puertas (spec 003, US1 y US2)."""
import unittest

from src.modelos.acciones import Accion, ABRIR, ESPERAR, MOVER, RECOGER
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import NORTE, SUR
from src.modelos.mapa_conocido import AVISTADA, DESCONOCIDA, EXPLORADA, RECORDADA_ABIERTA, RECORDADA_CERRADA, SIN_OBSERVAR
from tests.utilidades import construir, llave


def _actuar(p, tipo, argumento=None):
    return p.ejecutar(Accion(tipo, argumento))


def _iniciada(conexiones, contenidos=None, fichas=()):
    partida = construir(conexiones, contenidos=contenidos, fichas=fichas, semilla=3)
    partida.iniciar()
    return partida


def _cadena(largo=4):
    return [(i, 'N', i + 1, {}) for i in range(1, largo)]


class TestEstadosDeSala(unittest.TestCase):

    def test_la_sala_inicial_esta_explorada_desde_el_instante_cero_003_FR002(self):
        partida = _iniciada(_cadena())
        self.assertEqual(partida.reloj.tiempo_virtual, 0)
        self.assertTrue(partida.mapa.explorada(partida.cripta.sala(1)))

    def test_las_vecinas_de_la_inicial_quedan_avistadas_003_FR007(self):
        partida = _iniciada(_cadena())
        self.assertTrue(partida.mapa.avistada(partida.cripta.sala(2)))

    def test_lo_demas_es_desconocido_003_FR006(self):
        partida = _iniciada(_cadena())
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(3)), DESCONOCIDA)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(4)), DESCONOCIDA)

    def test_entrar_explora_y_avista_a_las_siguientes_003_FR003_FR007(self):
        partida = _iniciada(_cadena())
        _actuar(partida, MOVER, NORTE)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(2)), EXPLORADA)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(3)), AVISTADA)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(4)), DESCONOCIDA)

    def test_una_sala_explorada_no_vuelve_a_avistada_003_FR003(self):
        partida = _iniciada(_cadena())
        _actuar(partida, MOVER, NORTE)
        _actuar(partida, MOVER, SUR)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(1)), EXPLORADA)
        self.assertEqual(partida.mapa.estado_de(partida.cripta.sala(2)), EXPLORADA)

    def test_los_tres_estados_son_exclusivos_003_FR001(self):
        partida = _iniciada(_cadena())
        _actuar(partida, MOVER, NORTE)
        for sala in partida.cripta.salas():
            cuantos = sum((partida.mapa.explorada(sala), partida.mapa.avistada(sala),
                           partida.mapa.estado_de(sala) == DESCONOCIDA))
            self.assertEqual(cuantos, 1, sala.id)

    def test_explorar_solo_toca_lo_revelado_003_FR051(self):
        partida = _iniciada(_cadena(12))
        partida.mapa.reiniciar_conteos()
        _actuar(partida, MOVER, NORTE)
        tocadas_pocas = partida.mapa.salas_tocadas
        grande = _iniciada(_cadena(120))
        for _ in range(6):
            _actuar(grande, MOVER, NORTE)
        grande.mapa.reiniciar_conteos()
        _actuar(grande, MOVER, NORTE)
        self.assertEqual(grande.mapa.salas_tocadas, tocadas_pocas)


class TestMemoriaDePuertas(unittest.TestCase):

    def test_al_llegar_se_observan_las_puertas_de_la_sala_003_FR009_FR012(self):
        partida = _iniciada(_cadena())
        sala = partida.cripta.sala(1)
        self.assertEqual(partida.mapa.puerta_recordada(sala, NORTE), RECORDADA_ABIERTA)

    def test_una_puerta_nunca_vista_queda_sin_observar_003_FR011(self):
        partida = _iniciada(_cadena())
        lejana = partida.cripta.sala(3)
        self.assertEqual(partida.mapa.puerta_recordada(lejana, NORTE), SIN_OBSERVAR)
        self.assertFalse(partida.mapa.recordada_abierta(lejana, NORTE))

    def test_se_observa_desde_cualquiera_de_los_dos_extremos_003_FR008(self):
        partida = _iniciada(_cadena())
        _actuar(partida, MOVER, NORTE)
        sala2 = partida.cripta.sala(2)
        self.assertEqual(partida.mapa.puerta_recordada(sala2, SUR), RECORDADA_ABIERTA)

    def test_una_puerta_cerrada_se_recuerda_cerrada_003_FR009(self):
        conexiones = [(1, 'N', 2, {'cerrada': True, 'llave': 'itm_llave'})]
        partida = _iniciada(conexiones)
        sala = partida.cripta.sala(1)
        self.assertEqual(partida.mapa.puerta_recordada(sala, NORTE), RECORDADA_CERRADA)

    def test_abrir_una_puerta_la_recuerda_abierta_003_FR013(self):
        conexiones = [(1, 'N', 2, {'cerrada': True, 'llave': 'itm_llave'})]
        partida = _iniciada(conexiones, {1: ContenidoSala(objetos=[llave()])}, [llave()])
        _actuar(partida, RECOGER, 0)
        _actuar(partida, ABRIR, NORTE)
        sala = partida.cripta.sala(1)
        self.assertEqual(partida.mapa.puerta_recordada(sala, NORTE), RECORDADA_ABIERTA)

    def test_el_mapa_recuerda_abierta_una_puerta_que_se_cerro_lejos_003_FR010(self):
        conexiones = [(1, 'N', 2, {}), (2, 'N', 3, {})]
        partida = _iniciada(conexiones)
        _actuar(partida, MOVER, NORTE)
        sala2 = partida.cripta.sala(2)
        self.assertEqual(partida.mapa.puerta_recordada(sala2, NORTE), RECORDADA_ABIERTA)
        _actuar(partida, MOVER, SUR)
        puerta = sala2.salidas[NORTE].puerta
        puerta.cerrada = True
        self.assertEqual(partida.mapa.puerta_recordada(sala2, NORTE), RECORDADA_ABIERTA)

    def test_al_volver_el_mapa_se_corrige_003_FR012(self):
        conexiones = [(1, 'N', 2, {}), (2, 'N', 3, {})]
        partida = _iniciada(conexiones)
        _actuar(partida, MOVER, NORTE)
        _actuar(partida, MOVER, SUR)
        sala2 = partida.cripta.sala(2)
        sala2.salidas[NORTE].puerta.cerrada = True
        _actuar(partida, MOVER, NORTE)
        self.assertEqual(partida.mapa.puerta_recordada(sala2, NORTE), RECORDADA_CERRADA)


class TestReversion(unittest.TestCase):

    def test_revertir_una_entrada_restaura_el_mapa_003_FR048(self):
        from tests.utilidades import pergamino
        ficha = pergamino()
        partida = _iniciada(_cadena(5), {1: ContenidoSala(objetos=[ficha])}, [ficha])
        _actuar(partida, RECOGER, 0)
        estado_antes = list(partida.mapa.estado)
        puertas_antes = list(partida.mapa.puertas)
        exploradas_antes = list(partida.mapa.exploradas)
        _actuar(partida, MOVER, NORTE)
        self.assertNotEqual(list(partida.mapa.estado), estado_antes)
        _actuar(partida, 'usar')
        self.assertEqual(list(partida.mapa.estado), estado_antes)
        self.assertEqual(list(partida.mapa.puertas), puertas_antes)
        self.assertEqual(list(partida.mapa.exploradas), exploradas_antes)


if __name__ == '__main__':
    unittest.main()
