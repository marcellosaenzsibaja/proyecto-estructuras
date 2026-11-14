"""Terreno con costo (specs/001-terreno-cazador): carga del costo (T008).

Las pruebas de movimiento de la US1 (T016-T019) se agregan en la fase 3.
"""
import unittest

from src.modelos.errores import ErrorDatos
from src.servicios.generador_criptas import cargar_cripta_sintetica, fuente_sintetica, texto_sala
from tests.utilidades_cripta import conexion, cripta_desde_conexiones, textos_desde_conexiones

N, S, E, O = 0, 1, 2, 3


def _cargar(textos):
    return cargar_cripta_sintetica(fuente_sintetica(textos))


class TestCargaDelCosto(unittest.TestCase):
    """T008: lectura y validación del costo de las salidas."""

    def test_costo_ausente_vale_100_FR001(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2)])
        self.assertEqual(cripta.sala(1).salidas[N].puerta.costo, 100)
        self.assertEqual(cripta.sala(2).salidas[S].puerta.costo, 100)

    def test_costo_declarado_entero_FR001(self):
        cripta = cripta_desde_conexiones([conexion(1, 'E', 2, 250), conexion(2, 'E', 3, 1)])
        self.assertEqual(cripta.sala(1).salidas[E].puerta.costo, 250)
        self.assertEqual(cripta.sala(3).salidas[O].puerta.costo, 1)

    def test_costo_simetrico_misma_puerta_FR002(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 300)])
        self.assertIs(cripta.sala(1).salidas[N].puerta, cripta.sala(2).salidas[S].puerta)

    def test_un_solo_lado_declara_vale_para_ambos_FR002(self):
        textos = [texto_sala(1, [(N, 2, 250, False, None)]), texto_sala(2, [(S, 1, None, False, None)])]
        cripta = _cargar(textos)
        self.assertEqual(cripta.sala(1).salidas[N].puerta.costo, 250)
        self.assertEqual(cripta.sala(2).salidas[S].puerta.costo, 250)

    def test_ambos_lados_distintos_es_error_FR002(self):
        textos = [texto_sala(1, [(N, 2, 250, False, None)]), texto_sala(2, [(S, 1, 300, False, None)])]
        with self.assertRaises(ErrorDatos) as contexto:
            _cargar(textos)
        mensaje = str(contexto.exception)
        self.assertIn('1', mensaje)
        self.assertIn('2', mensaje)
        self.assertIn('N', mensaje)
        self.assertIn('S', mensaje)

    def test_costo_menor_que_uno_es_error_FR008(self):
        textos = textos_desde_conexiones([conexion(1, 'E', 2, 0)])
        with self.assertRaises(ErrorDatos) as contexto:
            _cargar(textos)
        self.assertIn('Sala 1', str(contexto.exception))
        self.assertIn('E', str(contexto.exception))

    def test_costo_no_entero_es_error_FR008(self):
        for valor in (2.5, 'caro', True):
            textos = [texto_sala(1, [(E, 2, valor, False, None)]), texto_sala(2, [(O, 1, valor, False, None)])]
            with self.subTest(valor=valor), self.assertRaises(ErrorDatos):
                _cargar(textos)

    def test_misma_cantidad_de_solicitudes_FR025(self):
        con_costo = fuente_sintetica(textos_desde_conexiones([conexion(1, 'N', 2, 250), conexion(2, 'E', 3, 7)]))
        sin_costo = fuente_sintetica(textos_desde_conexiones([conexion(1, 'N', 2), conexion(2, 'E', 3)]))
        cargar_cripta_sintetica(con_costo)
        cargar_cripta_sintetica(sin_costo)
        self.assertEqual(con_costo.solicitudes_realizadas, sin_costo.solicitudes_realizadas)


class TestIndiceYEnlace(unittest.TestCase):
    """Índice compacto y enlace directo (research R2, R3)."""

    def test_indice_compacto_en_orden_de_carga_FR030(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2), conexion(2, 'N', 3)])
        self.assertEqual([cripta.sala(i).indice for i in (1, 2, 3)], [0, 1, 2])

    def test_sala_destino_es_la_sala_vecina_FR011(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 40)])
        self.assertIs(cripta.sala(1).salidas[N].sala_destino, cripta.sala(2))
        self.assertIs(cripta.sala(2).salidas[S].sala_destino, cripta.sala(1))



# ---------------------------------------------------------------------------
# US1: el terreno determina cuánto tarda moverse (T016-T019)
# ---------------------------------------------------------------------------
from src.modelos.acciones import ABRIR, ACEPTADA, ESPERAR, MOVER, RECOGER, Accion
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import ESTE, NORTE, OESTE, SUR
from tests.utilidades import construir, enemigo, llave


def _actuar(p, tipo, argumento=None):
    return p.ejecutar(Accion(tipo, argumento))


def _iniciada(*args, **kwargs):
    p = construir(*args, **kwargs)
    p.iniciar()
    return p


class TestMovimientoConCosto(unittest.TestCase):
    """T016: US1-1, US1-2 y US1-5."""

    def test_US1_1_costo_250_proxima_accion_en_250_FR003_FR004(self):
        p = _iniciada([(1, 'N', 2, {'costo': 250})])
        self.assertEqual(_actuar(p, MOVER, NORTE).estado, ACEPTADA)
        self.assertEqual(p.reloj.tiempo_virtual, 250)

    def test_US1_2_sin_costo_cuesta_100_FR003(self):
        p = _iniciada([(1, 'N', 2, {})])
        _actuar(p, MOVER, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, 100)

    def test_US1_5_mismo_costo_en_ambos_sentidos_FR002_FR003(self):
        p = _iniciada([(1, 'E', 2, {'costo': 300})])
        _actuar(p, MOVER, ESTE)
        self.assertEqual(p.reloj.tiempo_virtual, 300)
        _actuar(p, MOVER, OESTE)
        self.assertEqual(p.reloj.tiempo_virtual, 600)

    def test_intervalo_usa_la_velocidad_FR004(self):
        p = _iniciada([(1, 'N', 2, {'costo': 250})], velocidad=150)
        _actuar(p, MOVER, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, max(1, 250 * 100 // 150))


class TestIntervaloMinimo(unittest.TestCase):
    """T017: US1-3 / Apéndice B, actor rápido por una salida de costo 1."""

    def test_US1_3_velocidad_alta_costo_1_intervalo_al_menos_1_FR004(self):
        p = _iniciada([(1, 'N', 2, {'costo': 1}), (2, 'N', 3, {'costo': 1})], velocidad=1000)
        _actuar(p, MOVER, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, 1)
        _actuar(p, MOVER, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, 2)


class TestCambioDeVelocidad(unittest.TestCase):
    """T018: US1-4 / Apéndice B, el tiempo restante se escala según P1 §2.3."""

    def test_US1_4_cambio_de_velocidad_tras_salida_costosa_FR006(self):
        errante = enemigo(comportamiento='errante', velocidad=100)
        p = _iniciada([(1, 'N', 2, {}), (3, 'E', 4, {'costo': 400})],
                      {3: ContenidoSala(enemigos=[('e-1', errante, None)])})
        e = _enemigo_activo(p, 3)
        p.jugador.sala_id = 1
        p._turno_enemigo(e)
        ahora = p.reloj.tiempo_virtual
        self.assertEqual(e.sala_id, 4)
        self.assertEqual(e.evento.tiempo, ahora + 400)
        t = ahora + 100
        p.reloj.tiempo_virtual = t
        p._cambiar_velocidad(e, 200)
        self.assertEqual(e.evento.tiempo, t + max(1, (ahora + 400 - t) * 100 // 200))


def _enemigo_activo(p, id_sala):
    """Activa a mano los enemigos de una sala para probar su turno de forma aislada."""
    sala = p.cripta.sala(id_sala)
    if not sala.contenido_incorporado:
        p._incorporar_contenido(sala)
    p._activar_enemigos(sala)
    return sala.enemigos[0]


class TestOtrasAccionesSinCambios(unittest.TestCase):
    """T019: US1-6, las demás acciones y las decisiones de P1 no cambian."""

    def test_US1_6_costos_de_otras_acciones_FR005(self):
        p = _iniciada([(1, 'N', 2, {'costo': 250, 'cerrada': True, 'llave': 'itm_llave'})],
                      {1: ContenidoSala(objetos=[llave()])}, [llave()])
        _actuar(p, RECOGER, 0)
        self.assertEqual(p.reloj.tiempo_virtual, 25)
        _actuar(p, ESPERAR)
        self.assertEqual(p.reloj.tiempo_virtual, 125)
        _actuar(p, ABRIR, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, 175)
        _actuar(p, MOVER, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, 425)

    def test_US1_6_errante_decide_igual_y_tarda_el_costo_FR007(self):
        errante = enemigo(comportamiento='errante', velocidad=100)
        p = _iniciada([(1, 'N', 2, {}), (3, 'E', 4, {'costo': 250})],
                      {3: ContenidoSala(enemigos=[('e-1', errante, None)])})
        e = _enemigo_activo(p, 3)
        p.jugador.sala_id = 1
        p._turno_enemigo(e)
        self.assertEqual(e.sala_id, 4)
        self.assertEqual(e.evento.tiempo, p.reloj.tiempo_virtual + 250)

    def test_US1_6_errante_sin_salidas_espera_100_FR005_FR007(self):
        errante = enemigo(comportamiento='errante', velocidad=100)
        p = _iniciada([(1, 'N', 2, {}), (3, 'E', 4, {'costo': 250, 'cerrada': True})],
                      {3: ContenidoSala(enemigos=[('e-1', errante, None)])})
        e = _enemigo_activo(p, 3)
        p.jugador.sala_id = 1
        p._turno_enemigo(e)
        self.assertEqual(e.sala_id, 3)
        self.assertEqual(e.evento.tiempo, p.reloj.tiempo_virtual + 100)

    def test_US1_6_rastreador_sigue_el_rastro_y_tarda_el_costo_FR007(self):
        rastreador = enemigo(comportamiento='rastreador', velocidad=100)
        p = _iniciada([(1, 'N', 2, {}), (3, 'E', 4, {'costo': 180}), (3, 'N', 5, {'costo': 20})],
                      {3: ContenidoSala(enemigos=[('e-1', rastreador, None)])})
        e = _enemigo_activo(p, 3)
        p.cripta.sala(4).rastro = p.reloj.tiempo_virtual
        p.jugador.sala_id = 1
        p._turno_enemigo(e)
        self.assertEqual(e.sala_id, 4)
        self.assertEqual(e.evento.tiempo, p.reloj.tiempo_virtual + 180)


if __name__ == '__main__':
    unittest.main()
