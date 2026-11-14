"""US3: reutilización demostrada (T043, T044; research R6).

Región asentada: salas asentadas en la generación del cálculo guardado.
Puerta alejada: sus dos salas están fuera de la región asentada.
Requisitos: FR-020, FR-021, FR-022.
"""
import unittest

from src.modelos.cazador import UMBRAL_PUERTAS, DecisorCazadores
from src.modelos.contenido import ContenidoSala
from src.modelos.fichas import CAZADOR, FichaEnemigo
from src.servicios import generador_criptas as gc
from tests.referencia_cazador import decision_desde_distancias_al_jugador, distancias_desde_referencia
from tests.utilidades import construir, enemigo

RANGO = 300


def _cripta_grande():
    """Cripta de 2000 salas (50 x 40), conexa, sin puertas cerradas."""
    g = gc.generar(77, 50, 40, costo_min=50, costo_max=150)
    cripta = gc.cargar_cripta_sintetica(gc.fuente_sintetica(gc.fragmentos(g)))
    return cripta, g.id_sala(0)


def _puertas_lejanas(cripta, dist, minimo, cantidad):
    """Puertas (vistas hacia E o S) cuyas dos salas están a distancia > minimo del jugador."""
    elegidas = []
    for id_sala in range(1, len(cripta) + 1):
        sala = cripta.sala(id_sala)
        for direccion in (1, 2):  # S, E: cada puerta se ve una sola vez
            salida = sala.salidas[direccion]
            if salida is None:
                continue
            if dist[id_sala] > minimo and dist[salida.destino] > minimo:
                elegidas.append(salida.puerta)
                if len(elegidas) == cantidad:
                    return elegidas
    return elegidas


def _cambiar(decisor, puerta):
    puerta.cerrada = not puerta.cerrada
    decisor.notificar_puerta(puerta)


class TestNoRecalculoPuertasAlejadas(unittest.TestCase):
    """T043: US3-4, cambios de puertas alejadas no provocan ningún recálculo.

    Demostración (research R6): la búsqueda solo usó salidas de salas asentadas.
    Una puerta con ambos extremos sin asentar no participó en ninguna distancia
    asentada; abrirla no puede crear un camino de costo <= la cota alcanzada,
    porque para usarla habría que alcanzar un extremo con costo <= esa cota y
    ese extremo estaría asentado; cerrarla no quita ningún camino usado.
    """

    def test_cien_puertas_alejadas_sin_recalculo_FR020_FR021(self):
        cripta, id_jugador = _cripta_grande()
        jugador = cripta.sala(id_jugador)
        dist = distancias_desde_referencia(cripta, id_jugador, len(cripta))
        cazadores = [i for i in range(1, len(cripta) + 1) if 0 < dist[i] <= 200][:5]
        self.assertGreaterEqual(len(cazadores), 2)
        decisor = DecisorCazadores(cripta)
        for c in cazadores:
            decisor.decidir(cripta.sala(c), RANGO, jugador)
        busquedas = decisor.busquedas
        examinadas = decisor.salas_examinadas_total
        self.assertEqual(busquedas, 1)
        puertas = _puertas_lejanas(cripta, dist, 3 * RANGO, 100)
        self.assertEqual(len(puertas), 100)
        for numero, puerta in enumerate(puertas, 1):
            _cambiar(decisor, puerta)
            for c in cazadores:
                reutilizaciones = decisor.reutilizaciones
                decision = decisor.decidir(cripta.sala(c), RANGO, jugador)
                self.assertEqual(decisor.reutilizaciones, reutilizaciones + 1)
                if numero in (1, 50, 100):
                    dist_actual = distancias_desde_referencia(cripta, id_jugador, len(cripta))
                    self.assertEqual(decision.como_tupla(), decision_desde_distancias_al_jugador(cripta, dist_actual, c, RANGO, id_jugador))
        self.assertEqual(decisor.busquedas, busquedas)               # no cambia
        self.assertEqual(decisor.salas_examinadas_total, examinadas)  # no cambia

    def test_cierre_automatico_lejano_no_recalcula_FR020(self):
        cazador = FichaEnemigo('ent_cazador', 'Cazador', 18, 6, 2, 100, CAZADOR, (), None, 150)
        conexiones = [(i, 'N', i + 1, {}) for i in range(1, 8)]
        conexiones[0] = (1, 'N', 2, {'cierre_automatico': 500})
        p = construir(conexiones, {7: ContenidoSala(enemigos=[('e-1', cazador, None)])}, [cazador], inicial=8)
        p.iniciar()
        decisor = p.decisor_cazadores
        decisor.decidir(p.cripta.sala(7), 150, p.sala_actual)
        busquedas = decisor.busquedas
        version = p.version_puertas
        puerta = p.cripta.sala(1).salidas[0].puerta  # entre las salas 1 y 2, lejos del jugador (8)
        p._cerrar_puerta(puerta)                      # el manejador del evento de cierre automático
        self.assertEqual(p.version_puertas, version + 1)
        decisor.decidir(p.cripta.sala(7), 150, p.sala_actual)
        self.assertEqual(decisor.busquedas, busquedas)
        self.assertEqual(decisor.reutilizaciones, 1)


class TestCasosLimite(unittest.TestCase):
    """T044: qué recalcula y qué no."""

    def setUp(self):
        self.cripta, self.id_jugador = _cripta_grande()
        self.jugador = self.cripta.sala(self.id_jugador)
        self.dist = distancias_desde_referencia(self.cripta, self.id_jugador, len(self.cripta))
        self.cazador = self.cripta.sala([i for i in range(1, len(self.cripta) + 1) if 0 < self.dist[i] <= 200][0])
        self.decisor = DecisorCazadores(self.cripta)
        self.decisor.decidir(self.cazador, RANGO, self.jugador)

    def test_puerta_con_una_sala_en_la_region_recalcula_FR020(self):
        salida = None
        for s in self.jugador.salidas:
            if s is not None:
                salida = s
                break
        _cambiar(self.decisor, salida.puerta)
        self.decisor.decidir(self.cazador, RANGO, self.jugador)
        self.assertEqual(self.decisor.busquedas, 2)

    def test_puerta_entre_borde_y_sala_sin_asentar_no_recalcula_FR021(self):
        registro = self.decisor.buscador.registro
        puerta = None
        for sala in self.cripta.salas():
            i = sala.indice
            if registro.tiene(i) and not registro.asentada(i):  # sala de borde
                for s in sala.salidas:
                    if s is not None and not registro.asentada(s.sala_destino.indice):
                        puerta = s.puerta
                        break
            if puerta is not None:
                break
        self.assertIsNotNone(puerta)
        _cambiar(self.decisor, puerta)
        self.decisor.decidir(self.cazador, RANGO, self.jugador)
        self.assertEqual(self.decisor.busquedas, 1)

    def test_mas_cambios_que_el_umbral_recalcula_FR020(self):
        for puerta in _puertas_lejanas(self.cripta, self.dist, 3 * RANGO, UMBRAL_PUERTAS + 1):
            _cambiar(self.decisor, puerta)
        self.decisor.decidir(self.cazador, RANGO, self.jugador)
        self.assertEqual(self.decisor.busquedas, 2)

    def test_rango_mayor_extiende_y_menor_no_trabaja_FR022(self):
        examinadas = self.decisor.salas_examinadas_total
        self.decisor.decidir(self.cazador, RANGO * 3, self.jugador)
        self.assertEqual(self.decisor.busquedas, 1)
        self.assertGreater(self.decisor.salas_examinadas_total, examinadas)
        examinadas = self.decisor.salas_examinadas_total
        self.decisor.decidir(self.cazador, RANGO, self.jugador)
        self.assertEqual(self.decisor.busquedas, 1)
        self.assertEqual(self.decisor.salas_examinadas_total, examinadas)

    def test_otros_actores_y_velocidad_no_cambian_puertas_FR020(self):
        cazador = FichaEnemigo('ent_cazador', 'Cazador', 18, 6, 2, 100, CAZADOR, (), None, 500)
        guardia = enemigo(id_ficha='ent_guardia', comportamiento='errante', vida_max=1)
        p = construir([(1, 'N', 2, {}), (2, 'N', 3, {}), (3, 'N', 4, {})],
                      {1: ContenidoSala(enemigos=[('e-1', cazador, None), ('e-2', guardia, None)])}, [cazador, guardia])
        p.iniciar()
        decisor = p.decisor_cazadores
        version = p.version_puertas
        e1, e2 = p.cripta.sala(1).enemigos[0], p.cripta.sala(1).enemigos[1]
        p._mover_enemigo(e2, 2)
        p._cambiar_velocidad(e1, 250)
        p._matar_enemigo(e2)
        self.assertEqual(p.version_puertas, version)
        self.assertEqual(decisor.busquedas, 0)



class TestInfraestructuraFueraDelEstado(unittest.TestCase):
    """T050: decisor, registro, contadores y version_puertas no son estado del juego (FR-021, FR-028, FR-029)."""

    def test_no_se_guardan_ni_se_revierten_FR021_FR028(self):
        from src.modelos.acciones import ABRIR, RECOGER, USAR, Accion
        from src.servicios.guardado import tomar_snapshot
        from tests.utilidades import llave, pergamino
        rollo, llave_ = pergamino(), llave()
        cazador = FichaEnemigo('ent_cazador', 'Cazador', 18, 6, 2, 100, CAZADOR, (), None, 500)
        p = construir([(1, 'N', 2, {'cerrada': True, 'llave': 'itm_llave'}), (2, 'N', 3, {})],
                      {1: ContenidoSala(objetos=[rollo, llave_]), 3: ContenidoSala(enemigos=[('e-1', cazador, None)])},
                      [cazador, rollo, llave_])
        p.iniciar()
        decisor = p.decisor_cazadores
        p.ejecutar(Accion(RECOGER, 0))
        p.ejecutar(Accion(RECOGER, 0))
        p.ejecutar(Accion(ABRIR, 0))
        version = p.version_puertas
        self.assertEqual(version, 1)
        p.jugador.inventario.ir_al_inicio()
        while p.jugador.inventario.actual().ficha.id != rollo.id:
            p.jugador.inventario.avanzar()
        self.assertEqual(p.ejecutar(Accion(USAR)).estado, 'aceptada')
        self.assertTrue(p.cripta.sala(1).salidas[0].puerta.cerrada)   # la puerta sí se revirtió
        self.assertEqual(p.version_puertas, version + 1)               # el contador no se revierte
        self.assertIs(p.decisor_cazadores, decisor)                     # el decisor sigue siendo el mismo
        snapshot = tomar_snapshot(p)
        texto = repr(snapshot)
        for nombre in ('version_puertas', 'decisor', 'busquedas', 'reutilizaciones', 'generacion'):
            self.assertNotIn(nombre, texto)


if __name__ == '__main__':
    unittest.main()
