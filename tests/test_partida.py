import random
import unittest
from src.modelos.acciones import ABRIR, ACEPTADA, ATACAR, EQUIPAR, ESPERAR, MOVER, PENDIENTE, RECHAZADA, RECOGER, SOLTAR, USAR, Accion
from src.modelos.contenido import ContenidoSala
from src.modelos.direcciones import ESTE, NORTE, OESTE, SUR
from src.modelos.errores import EstadoInvalido
from src.modelos.fichas import LLAVE
from src.modelos.partida import DERROTA, EN_CURSO, VICTORIA
from tests.utilidades import antidoto, antorcha, arma, armadura, construir, enemigo, llave, pergamino, pocion_cura, pocion_velocidad, trampa

def actuar(p, tipo, argumento=None):
    return p.ejecutar(Accion(tipo, argumento))

def iniciada(*args, **kwargs):
    p = construir(*args, **kwargs)
    p.iniciar()
    return p

def esperar_hasta(p, tiempo):
    while p.estado == EN_CURSO and p.reloj.tiempo_virtual < tiempo:
        actuar(p, ESPERAR)

class PruebasCostos(unittest.TestCase):

    def test_costos_de_acciones(self):
        daga, cota = (arma(), armadura())
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[daga, cota, pocion_cura(), llave()])}, [daga, cota])
        self.assertEqual(p.reloj.tiempo_virtual, 0)
        esperado = 0
        for tipo, arg, costo in [(RECOGER, 0, 25), (RECOGER, 0, 25), (RECOGER, 0, 25), (EQUIPAR, None, 50), (SOLTAR, None, 25), (MOVER, NORTE, 100), (ESPERAR, None, 100)]:
            if tipo == EQUIPAR:
                p.jugador.inventario.avanzar()
            resultado = actuar(p, tipo, arg)
            self.assertEqual(resultado.estado, ACEPTADA)
            esperado += costo
            self.assertEqual(p.reloj.tiempo_virtual, esperado)

    def test_usar_y_abrir_cuestan_50(self):
        p = iniciada([(1, 'N', 2, {'cerrada': True, 'llave': 'itm_llave'})], {1: ContenidoSala(objetos=[pocion_cura(), llave()])})
        actuar(p, RECOGER, 0)
        actuar(p, RECOGER, 0)
        self.assertEqual(p.reloj.tiempo_virtual, 50)
        actuar(p, ABRIR, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, 100)
        p.jugador.inventario.ir_al_inicio()
        actuar(p, USAR)
        self.assertEqual(p.reloj.tiempo_virtual, 150)

    def test_rechazos_no_consumen_tiempo(self):
        p = iniciada([(1, 'N', 2, {'cerrada': True, 'llave': 'itm_llave'})])
        for tipo, arg in [(MOVER, SUR), (MOVER, NORTE), (ABRIR, NORTE), (ABRIR, ESTE), (ATACAR, 'e-1'), (RECOGER, 0), (USAR, None), (EQUIPAR, None), (SOLTAR, None), (MOVER, 9)]:
            self.assertEqual(actuar(p, tipo, arg).estado, RECHAZADA)
        self.assertEqual(p.reloj.tiempo_virtual, 0)
        self.assertEqual(p.acciones_jugador, 0)
        self.assertTrue(p.esperando_jugador)

    def test_inventario_lleno_rechaza_recoger(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[arma(), armadura()])}, inventario_max=1)
        self.assertEqual(actuar(p, RECOGER, 0).estado, ACEPTADA)
        antes = p.reloj.tiempo_virtual
        self.assertEqual(actuar(p, RECOGER, 0).estado, RECHAZADA)
        self.assertEqual(p.reloj.tiempo_virtual, antes)
        actuar(p, SOLTAR)
        self.assertEqual(actuar(p, RECOGER, 0).estado, ACEPTADA)

class PruebasEnemigos(unittest.TestCase):

    def test_secuencia_del_enunciado(self):
        rata = enemigo(velocidad=150, ataque=5)
        daga = arma()
        p = iniciada([(1, 'N', 2, {})], {2: ContenidoSala(enemigos=[('e-1', rata, None)], objetos=[daga])}, [daga])
        azar = random.Random(1)
        actuar(p, MOVER, NORTE)
        e = p.cripta.sala(2).enemigos[0]
        self.assertEqual(p.reloj.tiempo_virtual, 100)
        self.assertEqual(e.evento.tiempo, 132)
        d1 = max(1, 5 + azar.randint(0, 4) - 2)
        self.assertEqual(p.jugador.vida, 30 - d1)
        actuar(p, RECOGER, 0)
        self.assertEqual(p.reloj.tiempo_virtual, 125)
        actuar(p, EQUIPAR)
        self.assertEqual(p.reloj.tiempo_virtual, 175)
        d2 = max(1, 5 + azar.randint(0, 4) - 2)
        self.assertEqual(p.jugador.vida, 30 - d1 - d2)

    def test_empate_el_enemigo_activado_actua_antes(self):
        rata = enemigo(velocidad=100, ataque=5)
        p = iniciada([(1, 'N', 2, {})], {2: ContenidoSala(enemigos=[('e-1', rata, None)])})
        actuar(p, MOVER, NORTE)
        self.assertEqual(p.reloj.tiempo_virtual, 100)
        self.assertLess(p.jugador.vida, 30)

    def test_activacion_en_orden_de_instancia(self):
        rata = enemigo(velocidad=150)
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-10', rata, None), ('e-2', rata, None)])})
        enemigos = p.cripta.sala(1).enemigos
        self.assertEqual([e.id_actor for e in enemigos], ['e-2', 'e-10'])
        self.assertEqual(enemigos[0].evento.tiempo, 66)
        self.assertLess(enemigos[0].evento.secuencia, enemigos[1].evento.secuencia)

    def test_enemigos_dormidos_no_actuan_hasta_la_entrada(self):
        rata = enemigo(velocidad=150)
        p = iniciada([(1, 'N', 2, {}), (2, 'N', 3, {})], {3: ContenidoSala(enemigos=[('e-1', rata, None)])})
        actuar(p, MOVER, NORTE)
        self.assertEqual(len(p.reloj.agenda), 0)
        self.assertFalse(p.cripta.sala(3).contenido_incorporado)

    def test_dano_con_arma_y_azar_reproducible(self):
        rata = enemigo(vida_max=100, ataque=0, velocidad=100, defensa=1)
        daga = arma(bonus=3)
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', rata, None)], objetos=[daga])}, [daga], semilla=7)
        actuar(p, RECOGER, 0)
        actuar(p, EQUIPAR)
        self.assertEqual(p.jugador.ataque_total, 9)
        e = p.cripta.sala(1).enemigos[0]
        azar = random.Random(7)
        esperado = max(1, 9 + azar.randint(0, 4) - 1)
        actuar(p, ATACAR, 'e-1')
        self.assertEqual(e.vida, 100 - esperado)

    def test_muerte_cancela_eventos_y_suelta_objetos(self):
        pocion = pocion_cura()
        rata = enemigo(vida_max=5, velocidad=150, suelta=('itm_pocion',), regeneracion=2)
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', rata, 1)])}, [pocion])
        self.assertEqual(len(p.reloj.agenda), 2)
        actuar(p, ATACAR, 'e-1')
        self.assertEqual(p.enemigos_derrotados, 1)
        self.assertEqual(p.cripta.sala(1).enemigos, [])
        self.assertEqual([o.ficha.id for o in p.cripta.sala(1).objetos], ['itm_pocion'])
        self.assertEqual(len(p.reloj.agenda), 0)
        self.assertEqual(p.jugador.vida, 30)

    def test_derrota(self):
        rata = enemigo(ataque=100, velocidad=150)
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', rata, None)])})
        actuar(p, ESPERAR)
        self.assertEqual(p.estado, DERROTA)
        self.assertEqual(p.jugador.vida, 0)
        with self.assertRaises(EstadoInvalido):
            actuar(p, ESPERAR)

    def test_regeneracion_con_tope(self):
        rata = enemigo(vida_max=12, ataque=0, regeneracion=3, comportamiento='guardian')
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', rata, 5)])})
        actuar(p, MOVER, NORTE)
        e = p.cripta.sala(1).enemigos[0]
        esperar_hasta(p, 250)
        self.assertEqual(e.vida, 8)
        esperar_hasta(p, 650)
        self.assertEqual(e.vida, 12)

    def test_guardian_errante_y_rastreador(self):
        conexiones = [(3, 'N', 2, {}), (3, 'S', 4, {}), (3, 'E', 5, {})]
        rata = enemigo(comportamiento='errante')
        p = construir(conexiones, {3: ContenidoSala(enemigos=[('e-1', rata, None)])}, inicial=3)
        p.iniciar()
        e = p.cripta.sala(3).enemigos[0]
        esperado = [2, 4, 5][random.Random(1).randrange(3)]
        p.jugador.sala_id = 2
        p._turno_enemigo(e)
        self.assertEqual(e.sala_id, esperado)
        p2 = construir([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', rata, None)])})
        p2.iniciar()
        e2 = p2.cripta.sala(1).enemigos[0]
        p2.cripta.sala(1).salidas[NORTE].puerta.cerrada = True
        p2.jugador.sala_id = 2
        p2._turno_enemigo(e2)
        self.assertEqual(e2.sala_id, 1)
        self.assertEqual(e2.evento.tiempo, p2.reloj.tiempo_virtual + 66)
        guardian = enemigo(comportamiento='guardian')
        p3 = construir([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', guardian, None)])})
        p3.iniciar()
        e3 = p3.cripta.sala(1).enemigos[0]
        p3.jugador.sala_id = 2
        p3._turno_enemigo(e3)
        self.assertEqual(e3.sala_id, 1)

    def test_rastro_fresco(self):
        conexiones = [(3, 'N', 2, {}), (3, 'S', 4, {}), (3, 'E', 5, {})]
        p = construir(conexiones, inicial=3)
        p.iniciar()
        sala3 = p.cripta.sala(3)
        p.cripta.sala(2).rastro = 100
        p.cripta.sala(4).rastro = 100
        p.cripta.sala(5).rastro = 50
        p.reloj.tiempo_virtual = 200
        self.assertEqual(p._vecino_con_rastro_fresco(sala3), 2)
        p.cripta.sala(4).rastro = 150
        self.assertEqual(p._vecino_con_rastro_fresco(sala3), 4)
        p.cripta.sala(4).rastro = 10
        p.cripta.sala(2).rastro = 0
        p.cripta.sala(5).rastro = 0
        p.reloj.tiempo_virtual = 400
        self.assertEqual(p._vecino_con_rastro_fresco(sala3), 4)
        p.cripta.sala(4).rastro = 0
        self.assertIsNone(p._vecino_con_rastro_fresco(sala3))
        p.cripta.sala(4).rastro = 300
        sala3.salidas[SUR].puerta.cerrada = True
        self.assertIsNone(p._vecino_con_rastro_fresco(sala3))

    def test_rastro_se_refresca_con_cada_accion(self):
        p = iniciada([(1, 'N', 2, {})])
        self.assertEqual(p.cripta.sala(1).rastro, 0)
        actuar(p, ESPERAR)
        self.assertEqual(p.cripta.sala(1).rastro, 0)
        actuar(p, MOVER, NORTE)
        self.assertEqual(p.cripta.sala(2).rastro, 100)
        actuar(p, ESPERAR)
        self.assertEqual(p.cripta.sala(2).rastro, 200)

class PruebasPuertasYVictoria(unittest.TestCase):

    def test_abrir_cruzar_y_cierre_automatico(self):
        p = iniciada([(1, 'E', 2, {'cerrada': True, 'llave': 'itm_llave', 'cierre_automatico': 200})], {1: ContenidoSala(objetos=[llave()])})
        self.assertEqual(actuar(p, MOVER, ESTE).estado, RECHAZADA)
        self.assertEqual(actuar(p, ABRIR, ESTE).estado, RECHAZADA)
        actuar(p, RECOGER, 0)
        self.assertEqual(actuar(p, ABRIR, ESTE).estado, ACEPTADA)
        self.assertEqual(len(p.jugador.inventario), 1)
        self.assertEqual(actuar(p, MOVER, ESTE).estado, ACEPTADA)
        self.assertEqual(p.jugador.sala_id, 2)
        esperar_hasta(p, 300)
        self.assertEqual(p.jugador.sala_id, 2)
        self.assertEqual(actuar(p, MOVER, OESTE).estado, RECHAZADA)
        self.assertEqual(actuar(p, ABRIR, OESTE).estado, ACEPTADA)
        self.assertEqual(actuar(p, MOVER, OESTE).estado, ACEPTADA)

    def test_victoria_exige_abrir_con_la_llave(self):
        p = iniciada([(1, 'N', 99, {'cerrada': True, 'llave': 'itm_llave'})], {1: ContenidoSala(objetos=[llave()])})
        self.assertEqual(actuar(p, MOVER, NORTE).estado, RECHAZADA)
        actuar(p, RECOGER, 0)
        actuar(p, ABRIR, NORTE)
        self.assertEqual(p.estado, EN_CURSO)
        actuar(p, MOVER, NORTE)
        self.assertEqual(p.estado, VICTORIA)
        self.assertEqual(p.acciones_jugador, 3)

    def test_contenido_pendiente_no_confirma_el_movimiento(self):
        p = iniciada([(1, 'N', 2, {})])
        p.proveedor.bloqueadas.add(2)
        resultado = actuar(p, MOVER, NORTE)
        self.assertEqual(resultado.estado, PENDIENTE)
        self.assertEqual(p.jugador.sala_id, 1)
        self.assertEqual(p.reloj.tiempo_virtual, 0)
        self.assertEqual(p.acciones_jugador, 0)
        self.assertTrue(p.esperando_jugador)
        p.proveedor.bloqueadas.clear()
        self.assertEqual(actuar(p, MOVER, NORTE).estado, ACEPTADA)
        self.assertEqual(p.jugador.sala_id, 2)

class PruebasObjetos(unittest.TestCase):

    def test_equipar_mueve_al_frente_y_soltar_desequipa(self):
        daga, cota = (arma(), armadura())
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[daga, cota])}, [daga, cota])
        actuar(p, RECOGER, 0)
        actuar(p, RECOGER, 0)
        inv = p.jugador.inventario
        inv.avanzar()
        actuar(p, EQUIPAR)
        self.assertEqual([o.ficha.id for o in inv], ['itm_cota', 'itm_daga'])
        self.assertEqual(p.jugador.defensa_total, 4)
        actuar(p, SOLTAR)
        self.assertEqual(p.jugador.defensa_total, 2)
        self.assertIsNone(p.jugador.armadura)
        self.assertEqual(len(p.sala_actual.objetos), 1)

    def test_equipar_otra_arma_sustituye_y_conserva(self):
        a1, a2 = (arma('itm_a1', 3), arma('itm_a2', 5))
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[a1, a2])}, [a1, a2])
        actuar(p, RECOGER, 0)
        actuar(p, RECOGER, 0)
        actuar(p, EQUIPAR)
        inv = p.jugador.inventario
        inv.avanzar()
        actuar(p, EQUIPAR)
        self.assertEqual(p.jugador.ataque_total, 6 + 5)
        self.assertEqual(len(inv), 2)

    def test_pocion_de_cura_respeta_vida_max(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[pocion_cura(cura=10)])})
        p.jugador.vida = 25
        actuar(p, RECOGER, 0)
        actuar(p, USAR)
        self.assertEqual(p.jugador.vida, 30)
        self.assertEqual(len(p.jugador.inventario), 0)

    def test_antorcha_se_enciende_y_se_apaga(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[antorcha(duracion=500)])})
        actuar(p, RECOGER, 0)
        actuar(p, USAR)
        self.assertEqual(p.jugador.antorcha.fin, 25 + 500)
        esperar_hasta(p, 600)
        self.assertIsNone(p.jugador.antorcha)

    def test_pergamino_no_disponible_todavia(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[pergamino()])})
        self.assertEqual(p.pergaminos_disponibles, 0)
        self.assertEqual(actuar(p, USAR).estado, RECHAZADA)

class PruebasPergamino(unittest.TestCase):

    def test_deshace_el_ultimo_movimiento(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[pergamino()]), 2: ContenidoSala()})
        actuar(p, RECOGER, 0)
        actuar(p, MOVER, NORTE)
        self.assertEqual(p.jugador.sala_id, 2)
        self.assertEqual(p.pergaminos_disponibles, 2)
        resultado = actuar(p, USAR)
        self.assertEqual(resultado.estado, ACEPTADA)
        self.assertEqual(p.jugador.sala_id, 1)
        self.assertEqual(p.pergaminos_disponibles, 1)
        self.assertEqual(len(p.jugador.inventario), 0)

    def test_deshace_soltar_en_su_posicion_exacta(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[llave(), pergamino()])})
        actuar(p, RECOGER, 0)
        actuar(p, RECOGER, 0)
        inv = p.jugador.inventario
        inv.ir_al_inicio()
        actuar(p, SOLTAR)
        self.assertEqual(len(inv), 1)
        self.assertEqual(len(p.sala_actual.objetos), 1)
        inv.ir_al_inicio()
        self.assertEqual(actuar(p, USAR).estado, ACEPTADA)
        self.assertEqual(len(inv), 1)
        self.assertEqual(len(p.sala_actual.objetos), 0)
        self.assertEqual(inv.actual().ficha.clase, LLAVE)

    def test_no_recupera_un_pergamino_ya_recogido(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[pergamino('itm_perg1'), pergamino('itm_perg2')])})
        actuar(p, RECOGER, 0)
        self.assertEqual(p.pergaminos_disponibles, 1)
        actuar(p, RECOGER, 0)
        self.assertEqual(len(p.jugador.inventario), 2)
        self.assertEqual(p.pergaminos_disponibles, 2)
        self.assertEqual(actuar(p, USAR).estado, ACEPTADA)
        self.assertEqual(len(p.jugador.inventario), 1)

    def test_se_agota_tras_usarlo(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[pergamino()])})
        actuar(p, RECOGER, 0)
        self.assertEqual(p.pergaminos_disponibles, 1)
        self.assertEqual(actuar(p, USAR).estado, ACEPTADA)
        self.assertEqual(p.pergaminos_disponibles, 0)
        self.assertEqual(len(p.jugador.inventario), 0)
        self.assertEqual(actuar(p, USAR).estado, RECHAZADA)

    def test_historial_limitado_a_cinco_intervalos(self):
        p = iniciada([(1, 'N', 2, {})])
        for _ in range(8):
            actuar(p, ESPERAR)
        self.assertEqual(p.pergaminos_disponibles, 5)

class PruebasEfectos(unittest.TestCase):

    def test_veneno_cinco_pulsos(self):
        p = iniciada([(1, 'N', 2, {})])
        p._aplicar_veneno(2)
        esperar_hasta(p, 500)
        self.assertEqual(p.jugador.vida, 30 - 5 * 2)
        self.assertIsNone(p.jugador.veneno)

    def test_antidoto_cancela_pulsos_futuros(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[antidoto()])})
        p._aplicar_veneno(2)
        actuar(p, RECOGER, 0)
        actuar(p, USAR)
        esperar_hasta(p, 600)
        self.assertEqual(p.jugador.vida, 30)
        self.assertIsNone(p.jugador.veneno)

    def test_veneno_mata(self):
        p = iniciada([(1, 'N', 2, {})], vida_max=3)
        p._aplicar_veneno(2)
        esperar_hasta(p, 500)
        self.assertEqual(p.estado, DERROTA)

    def test_pocion_de_velocidad(self):
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(objetos=[pocion_velocidad()])})
        actuar(p, RECOGER, 0)
        actuar(p, USAR)
        self.assertEqual(p.jugador.velocidad, 150)
        self.assertEqual(p.reloj.tiempo_virtual, 25 + 50 * 100 // 150)
        esperar_hasta(p, 1200)
        self.assertEqual(p.jugador.velocidad, 100)
        self.assertIsNone(p.jugador.efecto_velocidad)

    def test_reescalado_del_tiempo_restante(self):
        rata = enemigo(velocidad=150)
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', rata, None)])})
        e = p.cripta.sala(1).enemigos[0]
        e.evento.tiempo = 132
        p.reloj.tiempo_virtual = 100
        antes = e.evento.secuencia
        p._cambiar_velocidad(e, 300)
        self.assertEqual(e.evento.tiempo, 100 + 32 * 150 // 300)
        self.assertGreater(e.evento.secuencia, antes)
        p._cambiar_velocidad(e, 75)
        self.assertEqual(e.evento.tiempo, 100 + 16 * 300 // 75)

    def test_reescalado_minimo_uno(self):
        rata = enemigo(velocidad=150)
        p = iniciada([(1, 'N', 2, {})], {1: ContenidoSala(enemigos=[('e-1', rata, None)])})
        e = p.cripta.sala(1).enemigos[0]
        e.evento.tiempo = 101
        p.reloj.tiempo_virtual = 100
        p._cambiar_velocidad(e, 1000)
        self.assertEqual(e.evento.tiempo, 101)

    def test_trampa_dano_y_rearme(self):
        t = trampa(dano=4, rearme=300)
        p = iniciada([(1, 'N', 2, {})], {2: ContenidoSala(trampas=[('t-1', t)])})
        actuar(p, MOVER, NORTE)
        self.assertEqual(p.jugador.vida, 26)
        self.assertFalse(p.cripta.sala(2).trampas[0].armada)
        actuar(p, MOVER, SUR)
        actuar(p, MOVER, NORTE)
        self.assertEqual(p.jugador.vida, 26)
        actuar(p, MOVER, SUR)
        self.assertEqual(p.reloj.tiempo_virtual, 400)
        self.assertTrue(p.cripta.sala(2).trampas[0].armada)
        actuar(p, MOVER, NORTE)
        self.assertEqual(p.jugador.vida, 22)

class PruebasDeterminismo(unittest.TestCase):

    def jugar(self, semilla):
        rata = enemigo(velocidad=130, comportamiento='errante', ataque=3)
        rastreadora = enemigo('ent_r', velocidad=110, comportamiento='rastreador', ataque=2, nombre='Sombra')
        p = iniciada([(1, 'N', 2, {}), (2, 'N', 3, {}), (2, 'E', 4, {}), (3, 'E', 4, {})], {2: ContenidoSala(enemigos=[('e-1', rata, None)]), 3: ContenidoSala(enemigos=[('e-2', rastreadora, None)])}, semilla=semilla, vida_max=500)
        guion = [(MOVER, NORTE), (ESPERAR, None), (MOVER, NORTE), (ESPERAR, None), (MOVER, ESTE), (MOVER, OESTE), (ESPERAR, None), (MOVER, SUR), (ESPERAR, None), (ESPERAR, None)]
        for tipo, arg in guion:
            if p.estado != EN_CURSO:
                break
            actuar(p, tipo, arg)
        return (p.mensajes.elementos(), p.jugador.vida, p.reloj.tiempo_virtual)

    def test_misma_semilla_misma_partida(self):
        self.assertEqual(self.jugar(5), self.jugar(5))
        self.assertEqual(self.jugar(99), self.jugar(99))

    def test_bitacora_limitada_a_20(self):
        mensajes, _, _ = self.jugar(3)
        self.assertLessEqual(len(mensajes), 20)
if __name__ == '__main__':
    unittest.main()
