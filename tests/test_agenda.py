import random
import unittest
from src.estructuras_datos.agenda import Agenda, Evento
from src.modelos.reloj import MotorReloj

def clave(e):
    return (e.tiempo, e.secuencia)

class PruebasAgenda(unittest.TestCase):

    def test_orden_por_tiempo_y_secuencia(self):
        a = Agenda()
        for t, s in [(5, 3), (5, 1), (2, 9), (5, 2), (1, 4)]:
            a.insertar(Evento(t, s, 'x'))
        salida = []
        while not a.esta_vacio():
            salida.append(clave(a.extraer_minimo()))
        self.assertEqual(salida, [(1, 4), (2, 9), (5, 1), (5, 2), (5, 3)])

    def test_cancelar_evita_ejecucion(self):
        a = Agenda()
        eventos = [Evento(i, i, 'x') for i in range(10)]
        for e in eventos:
            a.insertar(e)
        self.assertTrue(a.cancelar(eventos[0]))
        self.assertTrue(a.cancelar(eventos[5]))
        self.assertFalse(a.cancelar(eventos[5]))
        self.assertTrue(eventos[5].cancelado)
        tiempos = []
        while not a.esta_vacio():
            tiempos.append(a.extraer_minimo().tiempo)
        self.assertEqual(tiempos, [1, 2, 3, 4, 6, 7, 8, 9])

    def test_reprogramar_adelanta_y_atrasa(self):
        a = Agenda()
        e1, e2, e3 = (Evento(10, 1, 'a'), Evento(20, 2, 'b'), Evento(30, 3, 'c'))
        for e in (e1, e2, e3):
            a.insertar(e)
        a.reprogramar(e3, 5, 4)
        a.reprogramar(e1, 25, 5)
        orden = [a.extraer_minimo() for _ in range(3)]
        self.assertEqual([e.tipo for e in orden], ['c', 'b', 'a'])

    def test_reprogramar_empate_usa_nueva_secuencia(self):
        a = Agenda()
        e1, e2 = (Evento(10, 1, 'a'), Evento(10, 2, 'b'))
        a.insertar(e1)
        a.insertar(e2)
        a.reprogramar(e1, 10, 3)
        self.assertEqual(a.extraer_minimo().tipo, 'b')

    def test_reprogramar_evento_no_programado(self):
        a = Agenda()
        with self.assertRaises(ValueError):
            a.reprogramar(Evento(1, 1, 'x'), 2, 2)

    def test_insertar_dos_veces(self):
        a = Agenda()
        e = Evento(1, 1, 'x')
        a.insertar(e)
        with self.assertRaises(ValueError):
            a.insertar(e)

    def test_evento_extraido_puede_reinsertarse(self):
        a = Agenda()
        e = Evento(1, 1, 'x')
        a.insertar(e)
        a.extraer_minimo()
        e.tiempo, e.secuencia = (4, 2)
        a.insertar(e)
        self.assertEqual(clave(a.minimo()), (4, 2))

    def test_agenda_vacia(self):
        a = Agenda()
        with self.assertRaises(IndexError):
            a.extraer_minimo()
        with self.assertRaises(IndexError):
            a.minimo()

    def test_estres_contra_referencia(self):
        azar = random.Random(7)
        a = Agenda()
        vivos = []
        secuencia = 0
        for _ in range(30000):
            op = azar.random()
            if op < 0.45 or not vivos:
                secuencia += 1
                e = Evento(azar.randint(0, 200), secuencia, 'x')
                a.insertar(e)
                vivos.append(e)
            elif op < 0.65:
                e = vivos.pop(azar.randrange(len(vivos)))
                self.assertTrue(a.cancelar(e))
            elif op < 0.85:
                secuencia += 1
                e = azar.choice(vivos)
                a.reprogramar(e, azar.randint(0, 200), secuencia)
            else:
                esperado = min(vivos, key=clave)
                self.assertIs(a.extraer_minimo(), esperado)
                vivos.remove(esperado)
            self.assertEqual(len(a), len(vivos))
            if vivos:
                self.assertIs(a.minimo(), min(vivos, key=clave))

class PruebasMotorReloj(unittest.TestCase):

    def test_orden_y_reloj(self):
        reloj = MotorReloj()
        reloj.programar_evento(100, 'b')
        reloj.programar_evento(50, 'a')
        primero = reloj.siguiente_evento()
        self.assertEqual((primero.tipo, reloj.tiempo_virtual), ('a', 50))
        segundo = reloj.siguiente_evento()
        self.assertEqual((segundo.tipo, reloj.tiempo_virtual), ('b', 100))
        self.assertIsNone(reloj.siguiente_evento())

    def test_cancelado_no_aparece_ni_mueve_reloj(self):
        reloj = MotorReloj()
        e = reloj.programar_evento(10, 'x')
        reloj.programar_evento(30, 'y')
        reloj.cancelar_evento(e)
        self.assertEqual(reloj.siguiente_evento().tipo, 'y')
        self.assertEqual(reloj.tiempo_virtual, 30)

    def test_reprogramar_asigna_secuencia_nueva(self):
        reloj = MotorReloj()
        e1 = reloj.programar_evento(10, 'a')
        reloj.programar_evento(10, 'b')
        antes = e1.secuencia
        reloj.reprogramar_evento(e1, 10)
        self.assertGreater(e1.secuencia, antes)
        self.assertEqual(reloj.siguiente_evento().tipo, 'b')
if __name__ == '__main__':
    unittest.main()
