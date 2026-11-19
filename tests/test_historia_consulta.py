"""Consulta de la historia: los casos del Apéndice B y los rechazos (spec 004)."""
import unittest

from src.modelos.acciones import ACEPTADA, Accion, ESPERAR, MOVER, RECOGER, USAR
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import NORTE
from src.modelos.partida import EN_CURSO
from src.modelos.resumen_historia import formatear
from tests.utilidades import construir, enemigo, pergamino


def _actuar(p, tipo, argumento=None):
    return p.ejecutar(Accion(tipo, argumento))


def _pasillo(largo=6):
    return [(i, 'N', i + 1, {}) for i in range(1, largo)]


def _iniciada(k=3, conexiones=None, contenidos=None, fichas=(), semilla=7):
    partida = construir(conexiones or _pasillo(), contenidos=contenidos, fichas=fichas, semilla=semilla)
    partida.linea.k = k
    partida.iniciar()
    return partida


class TestRechazos(unittest.TestCase):

    def test_instante_futuro_se_rechaza_004_FR008(self):
        partida = _iniciada()
        _actuar(partida, ESPERAR)
        resumen, error = partida.historia_en(partida.reloj.tiempo_virtual + 1)
        self.assertIsNone(resumen)
        self.assertIn('todavía no ha ocurrido', error)

    def test_instante_negativo_se_rechaza_004_FR009(self):
        partida = _iniciada()
        resumen, error = partida.historia_en(-1)
        self.assertIsNone(resumen)
        self.assertIsNotNone(error)

    def test_accion_fuera_de_rango_se_rechaza_004_FR009(self):
        partida = _iniciada()
        _actuar(partida, ESPERAR)
        self.assertIsNone(partida.historia_antes_de(0)[0])
        self.assertIsNone(partida.historia_antes_de(partida.acciones_jugador + 2)[0])
        self.assertIsNotNone(partida.historia_antes_de(partida.acciones_jugador + 1)[0])

    def test_argumento_no_entero_se_rechaza_004_FR009(self):
        partida = _iniciada()
        self.assertIsNone(partida.historia_en('x')[0])
        self.assertIsNone(partida.historia_antes_de(None)[0])

    def test_un_rechazo_no_consume_tiempo_004_FR010(self):
        partida = _iniciada()
        _actuar(partida, ESPERAR)
        reloj = partida.reloj.tiempo_virtual
        acciones = partida.acciones_jugador
        partida.historia_en(reloj + 500)
        self.assertEqual(partida.reloj.tiempo_virtual, reloj)
        self.assertEqual(partida.acciones_jugador, acciones)


class TestConsulta(unittest.TestCase):

    def test_instante_cero_es_el_estado_inicial_004_FR003(self):
        partida = _iniciada()
        for _ in range(4):
            _actuar(partida, MOVER, NORTE)
        resumen, error = partida.historia_en(0)
        self.assertIsNone(error)
        self.assertEqual(resumen.sala_id, 1)
        self.assertEqual(resumen.accion_numero, 0)

    def test_primera_accion_es_el_estado_inicial_004_FR003(self):
        partida = _iniciada()
        _actuar(partida, MOVER, NORTE)
        resumen, _ = partida.historia_antes_de(1)
        self.assertEqual(resumen.sala_id, 1)
        self.assertEqual(resumen.tiempo, 0)

    def test_el_resumen_trae_los_campos_minimos_004_FR006(self):
        malo = enemigo(comportamiento='guardian')
        partida = _iniciada(contenidos={2: ContenidoSala(enemigos=[('e-1', malo, None)])}, fichas=[malo])
        _actuar(partida, MOVER, NORTE)
        resumen, _ = partida.historia_en(partida.reloj.tiempo_virtual)
        self.assertEqual(resumen.sala_id, 2)
        self.assertEqual(resumen.vida_max, 30)
        self.assertIsInstance(resumen.inventario, list)
        self.assertIsInstance(resumen.efectos, list)
        self.assertEqual(len(resumen.enemigos), 1)
        self.assertGreaterEqual(resumen.exploradas, 2)
        self.assertEqual(resumen.estado, EN_CURSO)
        lineas = formatear(resumen)
        self.assertTrue(any('Sala:' in l for l in lineas))
        self.assertTrue(any('Mapa conocido' in l for l in lineas))

    def test_el_estado_en_t_incluye_todos_los_eventos_de_t_004_FR001_ApendiceB(self):
        partida = _iniciada(k=50)
        rapido = enemigo(velocidad=100, comportamiento='guardian')
        partida = _iniciada(k=50, contenidos={1: ContenidoSala(enemigos=[('e-1', rapido, None), ('e-2', rapido, None)])},
                            fichas=[rapido])
        for _ in range(3):
            _actuar(partida, ESPERAR)
        t = partida.reloj.tiempo_virtual
        resumen, error = partida.historia_en(t)
        self.assertIsNone(error)
        self.assertEqual(resumen.tiempo, t)
        reconstruido = [(nombre, vida) for nombre, _, vida, _ in resumen.enemigos]
        actual = [(e.nombre, e.vida) for e in partida.cripta.sala(1).enemigos]
        self.assertEqual(sorted(reconstruido), sorted(actual))

    def test_dos_consultas_al_mismo_instante_coinciden_004_FR012(self):
        partida = _iniciada()
        for _ in range(5):
            _actuar(partida, ESPERAR)
        t = partida.reloj.tiempo_virtual // 2
        primera = formatear(partida.historia_en(t)[0])
        segunda = formatear(partida.historia_en(t)[0])
        self.assertEqual(primera, segunda)

    def test_la_consulta_no_altera_la_partida_004_FR007_SC008_ApendiceB(self):
        partida = _iniciada(contenidos={1: ContenidoSala(objetos=[pergamino()])}, fichas=[pergamino()])
        _actuar(partida, RECOGER, 0)
        _actuar(partida, ESPERAR)
        reloj = partida.reloj.tiempo_virtual
        acciones = partida.acciones_jugador
        pergaminos = partida.pergaminos_disponibles
        mensajes = list(partida.mensajes.elementos())
        mapa = list(partida.mapa.estado)
        entradas = partida.linea.tamano()
        for t in range(0, reloj + 1, 20):
            partida.historia_en(t)
        self.assertEqual(partida.reloj.tiempo_virtual, reloj)
        self.assertEqual(partida.acciones_jugador, acciones)
        self.assertEqual(partida.pergaminos_disponibles, pergaminos)
        self.assertEqual(list(partida.mensajes.elementos()), mensajes)
        self.assertEqual(list(partida.mapa.estado), mapa)
        self.assertEqual(partida.linea.tamano(), entradas)


class TestPergaminoYLinea(unittest.TestCase):

    def _con_pergamino(self):
        ficha = pergamino()
        partida = _iniciada(k=50, contenidos={1: ContenidoSala(objetos=[ficha, pergamino('itm_p2')])},
                            fichas=[ficha, pergamino('itm_p2')])
        _actuar(partida, RECOGER, 0)
        return partida

    def test_la_historia_no_muestra_lo_revertido_004_FR013_ApendiceB(self):
        partida = self._con_pergamino()
        _actuar(partida, MOVER, NORTE)
        reloj_antes = partida.reloj.tiempo_virtual
        acciones_antes = partida.acciones_jugador
        resultado = _actuar(partida, USAR)
        self.assertEqual(resultado.estado, ACEPTADA)
        self.assertLess(partida.acciones_jugador, acciones_antes)
        self.assertLess(partida.reloj.tiempo_virtual, reloj_antes)
        self.assertEqual(partida.linea.acciones, partida.acciones_jugador)
        for entrada in partida.linea.entradas:
            self.assertLessEqual(entrada.numero, partida.acciones_jugador)

    def test_un_instante_posterior_al_retroceso_se_rechaza_004_FR014_ApendiceB(self):
        partida = self._con_pergamino()
        _actuar(partida, MOVER, NORTE)
        futuro = partida.reloj.tiempo_virtual
        _actuar(partida, USAR)
        self.assertLess(partida.reloj.tiempo_virtual, futuro)
        resumen, error = partida.historia_en(futuro)
        self.assertIsNone(resumen)
        self.assertIn('todavía no ha ocurrido', error)

    def test_las_acciones_nuevas_ocupan_el_lugar_004_FR016(self):
        partida = self._con_pergamino()
        _actuar(partida, MOVER, NORTE)
        _actuar(partida, USAR)
        self.assertEqual(partida.jugador.sala_id, 1)
        _actuar(partida, ESPERAR)
        ultimas = [e.tipo for e in partida.linea.entradas if e.numero > 0]
        self.assertEqual(ultimas[-1], ESPERAR)
        resumen, error = partida.historia_en(partida.reloj.tiempo_virtual)
        self.assertIsNone(error)
        self.assertEqual(resumen.sala_id, 1)


class TestEquivalenciaConResimulacion(unittest.TestCase):

    def test_coincide_con_resimular_desde_el_inicio_004_SC002(self):
        guion = [(ESPERAR, None), (MOVER, NORTE), (ESPERAR, None), (MOVER, NORTE),
                 (ESPERAR, None), (MOVER, NORTE), (ESPERAR, None), (ESPERAR, None)]
        partida = _iniciada(k=3, semilla=11)
        instantes = []
        for tipo, arg in guion:
            _actuar(partida, tipo, arg)
            instantes.append(partida.reloj.tiempo_virtual)
        for corte, t in enumerate(instantes, start=1):
            consultado = formatear(partida.historia_antes_de(corte)[0])
            referencia = _iniciada(k=3, semilla=11)
            for tipo, arg in guion[:corte - 1]:
                _actuar(referencia, tipo, arg)
            from src.modelos.resumen_historia import construir as construir_resumen
            esperado = formatear(construir_resumen(referencia))
            self.assertEqual(consultado, esperado, f'corte {corte}')


if __name__ == '__main__':
    unittest.main()
