"""US3: las decisiones siguen siendo correctas cuando el mapa cambia (T042, T045, T046).

Requisitos: FR-019, FR-020, FR-021, FR-022, FR-028.
"""
import random
import unittest

from src.modelos.acciones import MOVER as ACCION_MOVER, RECOGER, USAR, Accion
from src.modelos.cazador import COMPARTIDO, INDIVIDUAL, MOVER, DecisorCazadores
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import NORTE
from src.modelos.fichas import CAZADOR, FichaEnemigo
from src.servicios import generador_criptas as gc
from tests.referencia_cazador import decision_desde_distancias_al_jugador, decision_referencia, distancias_desde_referencia
from tests.utilidades import construir, pergamino
from tests.utilidades_cripta import conexion, cripta_desde_conexiones

SIN_LIMITE = 10 ** 9


def _cripta_dos_rutas():
    # Ruta corta 1-2-3 (200) y ruta larga 1-4-5-3 (600).
    return cripta_desde_conexiones([
        conexion(1, 'N', 2, 100), conexion(2, 'N', 3, 100),
        conexion(1, 'E', 4, 200), conexion(4, 'N', 5, 200), conexion(5, 'O', 3, 200)])


def _cambiar(decisor, puerta, cerrada):
    puerta.cerrada = cerrada
    decisor.notificar_puerta(puerta)


class TestCambiosEntreTurnos(unittest.TestCase):
    """T042: US3-1 (Apéndice B), US3-2 y US3-3."""

    def test_US3_1_puerta_de_la_ruta_se_cierra_FR019_FR020(self):
        cripta = _cripta_dos_rutas()
        decisor = DecisorCazadores(cripta)
        u, jugador = cripta.sala(1), cripta.sala(3)
        self.assertEqual(decisor.decidir(u, SIN_LIMITE, jugador).id_vecina, 2)
        busquedas = decisor.busquedas
        _cambiar(decisor, cripta.sala(2).salidas[NORTE].puerta, True)
        decision = decisor.decidir(u, SIN_LIMITE, jugador)
        self.assertEqual(decision.como_tupla(), decision_referencia(cripta, 1, SIN_LIMITE, 3))
        self.assertEqual(decision.id_vecina, 4)
        self.assertEqual(decisor.busquedas, busquedas + 1)

    def test_US3_2_se_abre_un_atajo_FR020(self):
        cripta = _cripta_dos_rutas()
        puerta = cripta.sala(2).salidas[NORTE].puerta
        puerta.cerrada = True
        decisor = DecisorCazadores(cripta)
        u, jugador = cripta.sala(1), cripta.sala(3)
        self.assertEqual(decisor.decidir(u, SIN_LIMITE, jugador).id_vecina, 4)
        busquedas = decisor.busquedas
        _cambiar(decisor, puerta, False)
        decision = decisor.decidir(u, SIN_LIMITE, jugador)
        self.assertEqual(decision.como_tupla(), decision_referencia(cripta, 1, SIN_LIMITE, 3))
        self.assertEqual(decision.id_vecina, 2)
        self.assertEqual(decisor.busquedas, busquedas + 1)

    def test_US3_3_el_jugador_cambia_de_sala_FR020(self):
        cripta = _cripta_dos_rutas()
        decisor = DecisorCazadores(cripta)
        decisor.decidir(cripta.sala(1), SIN_LIMITE, cripta.sala(3))
        busquedas = decisor.busquedas
        decision = decisor.decidir(cripta.sala(1), SIN_LIMITE, cripta.sala(5))
        self.assertEqual(decision.como_tupla(), decision_referencia(cripta, 1, SIN_LIMITE, 5))
        self.assertEqual(decisor.busquedas, busquedas + 1)


def _ficha_cazador(rango):
    return FichaEnemigo('ent_cazador', 'Cazador', 18, 6, 2, 100, CAZADOR, (), None, rango)


class TestMuchosCazadoresYRetroceso(unittest.TestCase):
    """T045: US3-5 (30 cazadores, orden distinto) y US3-6 (retroceso con pergamino)."""

    def test_US3_5_orden_de_calculo_no_cambia_decisiones_FR022(self):
        textos = gc.cripta_sintetica(31, 12, 12, costo_min=1, costo_max=200, prob_cerrada=0.1)
        cripta = gc.cargar_cripta_sintetica(gc.fuente_sintetica(textos))
        rng = random.Random(5)
        cazadores = [(rng.randint(1, 144), (100, 300, 700, SIN_LIMITE)[rng.randrange(4)]) for _ in range(30)]
        jugador = cripta.sala(72)
        adelante = DecisorCazadores(cripta)
        atras = DecisorCazadores(cripta)
        en_orden = [adelante.decidir(cripta.sala(s), r, jugador).como_tupla() for s, r in cazadores]
        al_reves = [atras.decidir(cripta.sala(s), r, jugador).como_tupla() for s, r in reversed(cazadores)]
        al_reves.reverse()
        self.assertEqual(en_orden, al_reves)
        for (s, r), obtenida in zip(cazadores, en_orden):
            self.assertEqual(obtenida, decision_referencia(cripta, s, r, 72))

    def test_US3_6_retroceso_decide_segun_el_estado_restaurado_FR028(self):
        cazador = _ficha_cazador(SIN_LIMITE)
        rollo = pergamino()
        p = construir([(1, 'N', 2, {}), (2, 'N', 3, {}), (3, 'N', 4, {}), (4, 'N', 5, {})],
                      {1: ContenidoSala(objetos=[rollo]), 5: ContenidoSala(enemigos=[('e-1', cazador, None)])},
                      [cazador, rollo])
        p.iniciar()
        sala5 = p.cripta.sala(5)
        p._incorporar_contenido(sala5)
        p._activar_enemigos(sala5)
        e = sala5.enemigos[0]
        p.ejecutar(Accion(RECOGER, 0))
        p.ejecutar(Accion(ACCION_MOVER, NORTE))
        p.ejecutar(Accion(ACCION_MOVER, NORTE))
        self.assertEqual(p.ejecutar(Accion(USAR)).estado, 'aceptada')
        restaurada = p.decisor_cazadores.decidir(p.cripta.sala(e.sala_id), SIN_LIMITE, p.sala_actual)
        self.assertEqual(restaurada.como_tupla(), decision_referencia(p.cripta, e.sala_id, SIN_LIMITE, p.jugador.sala_id))


class TestAleatorioLargo(unittest.TestCase):
    """T046: >= 10 000 decisiones con puertas inestables y reutilización activada (SC-002)."""

    def test_diez_mil_decisiones_sin_diferencias_FR019_FR020_FR021_FR022(self):
        total = 0
        diferencias = 0
        reutilizaciones = 0
        busquedas = 0
        for modo in (COMPARTIDO, INDIVIDUAL):
            for semilla in range(4):
                textos = gc.cripta_sintetica(100 + semilla, 10, 9, costo_min=1, costo_max=250, prob_cerrada=0.2, prob_hueco=0.1)
                cripta = gc.cargar_cripta_sintetica(gc.fuente_sintetica(textos))
                n = len(cripta)
                rng = random.Random(semilla)
                decisor = DecisorCazadores(cripta, modo)
                posiciones = [rng.randint(1, n) for _ in range(10)]
                rangos = [(120, 350, 800, SIN_LIMITE)[rng.randrange(4)] for _ in range(10)]
                jugador = rng.randint(1, n)
                for _ in range(130):
                    for _ in range(rng.randint(0, 3)):
                        sala = cripta.sala(rng.randint(1, n))
                        salida = sala.salidas[rng.randrange(4)]
                        if salida is not None:
                            _cambiar(decisor, salida.puerta, not salida.puerta.cerrada)
                    dist = distancias_desde_referencia(cripta, jugador, n)
                    for k in range(10):
                        esperado = decision_desde_distancias_al_jugador(cripta, dist, posiciones[k], rangos[k], jugador)
                        obtenida = decisor.decidir(cripta.sala(posiciones[k]), rangos[k], cripta.sala(jugador)).como_tupla()
                        total += 1
                        if obtenida != esperado:
                            diferencias += 1
                        if obtenida[0] == MOVER:
                            posiciones[k] = obtenida[1]
                    if rng.random() < 0.6:
                        abiertas = [s.destino for s in cripta.sala(jugador).salidas if s is not None and not s.puerta.cerrada]
                        if abiertas:
                            jugador = abiertas[rng.randrange(len(abiertas))]
                reutilizaciones += decisor.reutilizaciones
                busquedas += decisor.busquedas
        self.assertGreaterEqual(total, 10000)
        self.assertEqual(diferencias, 0)
        self.assertGreater(reutilizaciones, 0)  # la reutilización ocurrió de verdad
        print(f'\n[T046] decisiones={total} busquedas={busquedas} reutilizaciones={reutilizaciones}')


if __name__ == '__main__':
    unittest.main()
