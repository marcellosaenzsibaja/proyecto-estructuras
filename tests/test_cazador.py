"""Enemigo cazador (specs/001-terreno-cazador): ficha de catálogo (T009).

Las pruebas de decisión de la US2 (T026-T035) se agregan en la fase 4.
"""
import json
import unittest

from src.modelos.errores import ErrorDatos
from src.modelos.fichas import CAZADOR, FichaEnemigo
from src.servicios.fabrica_fichas import ficha_desde_dict
from src.servicios.generador_criptas import ficha_cazador


class TestFichaCazador(unittest.TestCase):
    """T009: comportamiento cazador con rango entero >= 0."""

    def test_ficha_cazador_con_rango_FR009(self):
        ficha = ficha_desde_dict(json.loads(ficha_cazador('ent_sabueso', 600, velocidad=120)))
        self.assertIsInstance(ficha, FichaEnemigo)
        self.assertEqual(ficha.comportamiento, CAZADOR)
        self.assertEqual(ficha.rango, 600)
        self.assertEqual(ficha.velocidad, 120)

    def test_rango_cero_es_valido_FR009(self):
        self.assertEqual(ficha_desde_dict(json.loads(ficha_cazador('ent_quieto', 0))).rango, 0)

    def test_cazador_sin_rango_es_error_con_id_FR009(self):
        texto = ficha_cazador('ent_sin_rango', 5).replace(', "rango": 5', '')
        with self.assertRaises(ErrorDatos) as contexto:
            ficha_desde_dict(json.loads(texto))
        self.assertIn('ent_sin_rango', str(contexto.exception))

    def test_rango_invalido_es_error_FR009(self):
        for valor in ('-1', '2.5', '"lejos"', 'true', 'null'):
            texto = ficha_cazador('ent_malo', 5).replace('"rango": 5', '"rango": ' + valor)
            with self.subTest(valor=valor), self.assertRaises(ErrorDatos) as contexto:
                ficha_desde_dict(json.loads(texto))
            self.assertIn('ent_malo', str(contexto.exception))

    def test_otros_comportamientos_no_requieren_rango_FR009(self):
        texto = ficha_cazador('ent_guardia', 5).replace('"cazador", "rango": 5', '"guardian"')
        ficha = ficha_desde_dict(json.loads(texto))
        self.assertIsNone(ficha.rango)



# ---------------------------------------------------------------------------
# US2: el cazador persigue al jugador por la ruta más barata (T026-T035)
# ---------------------------------------------------------------------------
from src.modelos.acciones import ESPERAR as ACCION_ESPERAR, MOVER as ACCION_MOVER, Accion
from src.modelos.cazador import ATACAR, COMPARTIDO, ESPERAR, INDIVIDUAL, MOVER, DecisorCazadores
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import ESTE, NORTE, OESTE, SUR
from src.servicios import generador_criptas as gc
from tests.referencia_cazador import decision_desde_matriz, decision_referencia, matriz_referencia
from tests.utilidades import construir, enemigo
from tests.utilidades_cripta import conexion, cripta_desde_conexiones

SIN_LIMITE = 10 ** 9


def decidir(cripta, sala_cazador, rango, sala_jugador):
    """Decide en ambos modos, comprueba que coinciden con la referencia y devuelve la tupla."""
    esperado = decision_referencia(cripta, sala_cazador, rango, sala_jugador)
    for modo in (COMPARTIDO, INDIVIDUAL):
        obtenida = DecisorCazadores(cripta, modo).decidir(cripta.sala(sala_cazador), rango, cripta.sala(sala_jugador)).como_tupla()
        if obtenida != esperado:
            raise AssertionError(f'modo {modo}: {obtenida} != referencia {esperado}')
    return esperado


def ficha_cazador_obj(rango, velocidad=100, ataque=6, id_ficha='ent_cazador'):
    return FichaEnemigo(id_ficha, 'Cazador', 18, ataque, 2, velocidad, CAZADOR, (), None, rango)


def _actuar(p, tipo, argumento=None):
    return p.ejecutar(Accion(tipo, argumento))


class TestAtaque(unittest.TestCase):
    """T026: US2-1, misma sala: ataca con costo 100 y no se mueve."""

    def test_US2_1_misma_sala_ataca_FR010(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2)])
        self.assertEqual(decidir(cripta, 1, 500, 1), (ATACAR, None, None, 100))

    def test_US2_1_en_partida_ataca_y_no_se_mueve_FR010(self):
        cazador = ficha_cazador_obj(500, ataque=5)
        p = construir([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', cazador, None)])}, [cazador])
        p.iniciar()
        e = p.cripta.sala(1).enemigos[0]
        _actuar(p, ACCION_ESPERAR)
        self.assertLess(p.jugador.vida, 30)
        self.assertEqual(e.sala_id, 1)
        self.assertEqual(e.evento.tiempo, 200)


class TestSinRuta(unittest.TestCase):
    """T027: US2-2 / Apéndice B, sin ruta abierta: espera con costo 100."""

    def test_US2_2_sin_ruta_espera_FR011_FR012(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, cerrada=True), conexion(2, 'N', 3)])
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 3), (ESPERAR, None, None, 100))


class TestRango(unittest.TestCase):
    """T028: US2-3 / Apéndice B (d > rango) y US2-4 (d == rango)."""

    def setUp(self):
        self.cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 150), conexion(2, 'N', 3, 250)])

    def test_US2_3_ruta_mas_cara_que_el_rango_espera_FR012(self):
        self.assertEqual(decidir(self.cripta, 1, 399, 3), (ESPERAR, None, None, 100))

    def test_US2_4_ruta_igual_al_rango_se_mueve_FR013(self):
        self.assertEqual(decidir(self.cripta, 1, 400, 3), (MOVER, 2, NORTE, 150))


class TestRutaMasBarata(unittest.TestCase):
    """T029: US2-5 / Apéndice B, gana la ruta de menos costo aunque tenga más salas."""

    def test_US2_5_menos_costo_mas_salas_FR011_FR013(self):
        cripta = cripta_desde_conexiones([
            conexion(1, 'N', 2, 300), conexion(2, 'N', 3, 200),                            # 2 salidas, costo 500
            conexion(1, 'E', 4, 100), conexion(4, 'N', 5, 100), conexion(5, 'N', 6, 100),  # 4 salidas, costo 400
            conexion(6, 'O', 3, 100)])
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 3), (MOVER, 4, ESTE, 100))


class TestDesempate(unittest.TestCase):
    """T030: US2-6 / Apéndice B, dos vecinas con rutas mínimas: la de menor id."""

    def test_US2_6_dos_vecinas_menor_id_FR014(self):
        cripta = cripta_desde_conexiones([
            conexion(1, 'N', 7), conexion(7, 'E', 9),
            conexion(1, 'E', 5), conexion(5, 'N', 9)])
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 9), (MOVER, 5, ESTE, 100))

    def test_cuadricula_con_muchas_rutas_iguales_calculada_a_mano_FR014(self):
        # Cuadrícula 3x3 con ids por filas (1 2 3 / 4 5 6 / 7 8 9) y costo uniforme.
        conexiones = []
        for fila in range(3):
            for columna in range(3):
                i = fila * 3 + columna + 1
                if columna < 2:
                    conexiones.append(conexion(i, 'E', i + 1, 100))
                if fila < 2:
                    conexiones.append(conexion(i, 'S', i + 3, 100))
        cripta = cripta_desde_conexiones(conexiones)
        # Desde 1: vecinas 2 (E) y 4 (S) inician rutas de 400 -> menor id 2.
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 9), (MOVER, 2, ESTE, 100))
        # Desde 2: vecinas 3 (E) y 5 (S) inician rutas de 300 -> menor id 3.
        self.assertEqual(decidir(cripta, 2, SIN_LIMITE, 9), (MOVER, 3, ESTE, 100))
        # Desde 5: vecinas 6 (E) y 8 (S) -> menor id 6.
        self.assertEqual(decidir(cripta, 5, SIN_LIMITE, 9), (MOVER, 6, ESTE, 100))


class TestVariasSalidasMismaVecina(unittest.TestCase):
    """T031: US2-7, varias salidas hacia la misma vecina, y enemigos en la ruta."""

    def test_la_mas_barata_FR013_FR015(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 250), conexion(1, 'E', 2, 120), conexion(2, 'N', 3)])
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 3), (MOVER, 2, ESTE, 120))

    def test_empate_por_orden_N_S_E_O_FR015(self):
        cripta = cripta_desde_conexiones([conexion(1, 'E', 2, 150), conexion(1, 'N', 2, 150), conexion(2, 'N', 3)])
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 3), (MOVER, 2, NORTE, 150))

    def test_otro_enemigo_en_la_ruta_no_la_bloquea_FR017(self):
        cazador = ficha_cazador_obj(SIN_LIMITE)
        guardia = enemigo(id_ficha='ent_guardia', comportamiento='guardian')
        p = construir([(1, 'N', 2, {}), (2, 'N', 3, {}), (3, 'N', 4, {})],
                      {3: ContenidoSala(enemigos=[('e-1', cazador, None)]), 2: ContenidoSala(enemigos=[('e-2', guardia, None)])},
                      [cazador, guardia])
        p.iniciar()
        sala3 = p.cripta.sala(3)
        p._incorporar_contenido(sala3)
        p._activar_enemigos(sala3)
        e = sala3.enemigos[0]
        p._turno_enemigo(e)
        self.assertEqual(e.sala_id, 2)  # entra a la sala del guardián


class TestPuertasYContenido(unittest.TestCase):
    """T032: US2-8 (no abre puertas) y US2-9 (no depende del contenido descargado)."""

    def test_US2_8_no_atraviesa_puertas_cerradas_FR016(self):
        cripta = cripta_desde_conexiones([
            conexion(1, 'N', 2, 100, cerrada=True), conexion(2, 'N', 3, 100),   # atajo cerrado: 200
            conexion(1, 'E', 4, 300), conexion(4, 'N', 5, 300), conexion(5, 'O', 3, 300)])
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 3), (MOVER, 4, ESTE, 300))

    def test_US2_9_no_depende_del_contenido_FR017(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 80), conexion(2, 'E', 3, 90), conexion(1, 'E', 4, 50), conexion(4, 'N', 3, 200)])
        antes = decidir(cripta, 1, SIN_LIMITE, 3)
        for sala in cripta.salas():
            sala.contenido_incorporado = True
        self.assertEqual(decidir(cripta, 1, SIN_LIMITE, 3), antes)


class TestActivacion(unittest.TestCase):
    """T033: US2-10, dormido no actúa; se activa al entrar el jugador; rango 0 espera."""

    def test_US2_10_dormido_no_actua_y_se_activa_al_entrar_FR018(self):
        cazador = ficha_cazador_obj(SIN_LIMITE, velocidad=100)
        p = construir([(1, 'N', 2, {}), (2, 'N', 3, {})], {3: ContenidoSala(enemigos=[('e-1', cazador, None)])}, [cazador])
        p.iniciar()
        for _ in range(5):
            _actuar(p, ACCION_ESPERAR)
        self.assertEqual(len(p.cripta.sala(3).enemigos), 0)
        self.assertEqual(len(p.reloj.agenda), 0)
        _actuar(p, ACCION_MOVER, NORTE)
        _actuar(p, ACCION_MOVER, NORTE)
        e = p.cripta.sala(3).enemigos[0]
        self.assertTrue(e.activo)
        self.assertEqual(e.evento.tiempo, 700 + 100)

    def test_rango_cero_espera_FR012(self):
        cripta = cripta_desde_conexiones([conexion(1, 'N', 2, 1)])
        self.assertEqual(decidir(cripta, 1, 0, 2), (ESPERAR, None, None, 100))


class TestComparacionExhaustiva(unittest.TestCase):
    """T035: todos los pares en 50 criptas sembradas, 6 rangos, ambos modos, contra la referencia."""

    RANGOS = (0, 1, 100, 250, 600, SIN_LIMITE)

    def test_exhaustivo_contra_referencia_FR019_FR022(self):
        import random as _random
        rng = _random.Random(2026)
        diferencias = 0
        comparadas = 0
        for semilla in range(50):
            ancho = rng.randint(2, 7)
            alto = rng.randint(max(2, 10 // ancho), max(2, 40 // ancho))
            textos = gc.cripta_sintetica(semilla, ancho, alto, costo_min=1, costo_max=300,
                                         prob_cerrada=0.25, prob_hueco=0.2, conexa=False)
            cripta = gc.cargar_cripta_sintetica(gc.fuente_sintetica(textos))
            matriz = matriz_referencia(cripta)
            decisores = (DecisorCazadores(cripta, COMPARTIDO), DecisorCazadores(cripta, INDIVIDUAL))
            salas = list(cripta.salas())
            for u in salas:
                for jugador in salas:
                    for rango in self.RANGOS:
                        esperado = decision_desde_matriz(cripta, matriz, u.id, rango, jugador.id)
                        for decisor in decisores:
                            comparadas += 1
                            if decisor.decidir(u, rango, jugador).como_tupla() != esperado:
                                diferencias += 1
        self.assertGreater(comparadas, 50000)
        self.assertEqual(diferencias, 0)


if __name__ == '__main__':
    unittest.main()
