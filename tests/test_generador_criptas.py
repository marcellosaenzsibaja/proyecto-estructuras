"""T002: corrección y reproducibilidad del generador de criptas sintéticas.

Verifica las reglas G1-G5 de specs/001-terreno-cazador/tasks.md antes de usar
el generador en cualquier otra prueba. Requisitos: FR-001, FR-002, FR-030, FR-035.
"""
import json
import unittest

from src.servicios import generador_criptas as gc

CLAVES_SALA = ['id', 'nombre', 'salidas']
CLAVES_SALIDA = ['sala', 'costo', 'cerrada', 'llave', 'cierre_automatico']
ORDEN = ['N', 'S', 'E', 'O']
OPUESTA = ['S', 'N', 'O', 'E']


def _leer(fragmentos):
    return [json.loads(texto) for texto in fragmentos]


class TestReproducibilidad(unittest.TestCase):
    """G3 (FR-035): misma semilla, mismos textos."""

    def test_misma_semilla_mismos_textos_FR035(self):
        a = gc.cripta_sintetica(11, 8, 7, prob_cerrada=0.2, prob_sin_costo=0.3, prob_hueco=0.2)
        b = gc.cripta_sintetica(11, 8, 7, prob_cerrada=0.2, prob_sin_costo=0.3, prob_hueco=0.2)
        self.assertEqual(a, b)

    def test_semillas_distintas_textos_distintos_FR035(self):
        self.assertNotEqual(gc.cripta_sintetica(1, 8, 7), gc.cripta_sintetica(2, 8, 7))

    def test_paginas_barajadas_reproducibles_FR035(self):
        textos = gc.cripta_sintetica(5, 10, 10)
        self.assertEqual(gc.paginar(textos, 30, semilla=9), gc.paginar(textos, 30, semilla=9))
        self.assertNotEqual(gc.paginar(textos, 30, semilla=9), gc.paginar(textos, 30))


class TestEstructuraG1(unittest.TestCase):
    """G1 (FR-001): forma exacta del esqueleto del servicio."""

    def test_estructura_campo_por_campo_FR001(self):
        salas = _leer(gc.cripta_sintetica(3, 6, 5, prob_cerrada=0.3, prob_sin_costo=0.4, prob_hueco=0.2))
        self.assertEqual([s['id'] for s in salas], list(range(1, 31)))
        for sala in salas:
            self.assertEqual(list(sala.keys()), CLAVES_SALA)
            self.assertIsInstance(sala['id'], int)
            self.assertEqual(sala['nombre'], f"Sala sintética {sala['id']}")
            letras = list(sala['salidas'].keys())
            self.assertEqual(letras, [l for l in ORDEN if l in letras])
            for letra in letras:
                salida = sala['salidas'][letra]
                for clave in salida.keys():
                    self.assertIn(clave, CLAVES_SALIDA)
                self.assertIsInstance(salida['sala'], int)
                if 'costo' in salida:
                    self.assertIsInstance(salida['costo'], int)
                    self.assertTrue(1 <= salida['costo'] <= 300)
                if 'cerrada' in salida:
                    self.assertIs(salida['cerrada'], True)
                    self.assertTrue(salida['llave'].startswith('itm_llave_sint_'))
                else:
                    self.assertNotIn('llave', salida)

    def test_paginas_con_forma_del_servicio_FR001(self):
        paginas = [json.loads(t) for t in gc.paginar(gc.cripta_sintetica(4, 10, 12), 50)]
        self.assertEqual(len(paginas), 3)
        for numero, pagina in enumerate(paginas, 1):
            self.assertEqual(list(pagina.keys()), ['pagina', 'total_paginas', 'salas'])
            self.assertEqual(pagina['pagina'], numero)
            self.assertEqual(pagina['total_paginas'], 3)

    def test_se_carga_con_el_cargador_real_FR001(self):
        textos = gc.cripta_sintetica(8, 9, 9, prob_cerrada=0.2, prob_sin_costo=0.3)
        cripta = gc.cargar_cripta_sintetica(gc.fuente_sintetica(textos))
        self.assertEqual(len(cripta), 81)


class TestCoherenciaG2(unittest.TestCase):
    """G2 (FR-002): parejas opuestas simétricas."""

    def test_parejas_opuestas_simetricas_FR002(self):
        salas = _leer(gc.cripta_sintetica(21, 12, 9, prob_cerrada=0.3, prob_sin_costo=0.3, prob_hueco=0.3))
        n = len(salas)
        for sala in salas:
            for letra, salida in sala['salidas'].items():
                destino = salida['sala']
                self.assertTrue(1 <= destino <= n)
                vuelta = salas[destino - 1]['salidas'][OPUESTA[ORDEN.index(letra)]]
                self.assertEqual(vuelta['sala'], sala['id'])
                for clave in ('costo', 'cerrada', 'llave'):
                    self.assertEqual(vuelta.get(clave), salida.get(clave))


class TestPermutacionG4(unittest.TestCase):
    """G4 (FR-001): permutación sembrada de ids."""

    def test_inversa_exacta_FR001(self):
        g = gc.generar(17, 7, 6)
        for p in range(g.n):
            self.assertEqual(g.posicion_de_id[g.id_de_posicion[p]], p)
        self.assertEqual(sorted_list(g.id_de_posicion), list(range(1, g.n + 1)))

    def test_no_es_la_identidad_FR001(self):
        for semilla in (1, 2, 3):
            g = gc.generar(semilla, 6, 6)
            self.assertNotEqual(g.id_de_posicion, list(range(1, 37)))

    def test_valor_esperado_detecta_cambios_en_el_consumo_FR001(self):
        g = gc.generar(42, 4, 4)
        self.assertEqual(g.id_de_posicion, [8, 10, 6, 7, 15, 11, 13, 9, 2, 3, 14, 16, 5, 12, 1, 4])


def sorted_list(valores):
    """Ordena por inserción (no se usa sorted, P1 §4.9)."""
    resultado = list(valores)
    for i in range(1, len(resultado)):
        actual = resultado[i]
        j = i - 1
        while j >= 0 and resultado[j] > actual:
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = actual
    return resultado


def _alcanzables(salas, desde):
    """Recorrido con visitada indexada por id y pila en list (G5)."""
    visitada = [False] * (len(salas) + 1)
    visitada[desde] = True
    pila = [desde]
    total = 1
    while pila:
        actual = pila.pop()
        for salida in salas[actual - 1]['salidas'].values():
            if salida.get('cerrada'):
                continue
            v = salida['sala']
            if not visitada[v]:
                visitada[v] = True
                total += 1
                pila.append(v)
    return total


class TestConexidad(unittest.TestCase):
    """Árbol de expansión (FR-035)."""

    def test_conexa_todas_alcanzables_FR035(self):
        for semilla in range(5):
            salas = _leer(gc.cripta_sintetica(semilla, 15, 12, prob_hueco=0.7))
            self.assertEqual(_alcanzables(salas, 1), len(salas))

    def test_no_conexa_puede_tener_inalcanzables_FR035(self):
        alguna = False
        for semilla in range(10):
            salas = _leer(gc.cripta_sintetica(semilla, 12, 12, prob_hueco=0.8, conexa=False))
            if _alcanzables(salas, 1) < len(salas):
                alguna = True
                break
        self.assertTrue(alguna)

    def test_conexa_abierta_no_cierra_el_arbol_FR035(self):
        salas = _leer(gc.cripta_sintetica(6, 15, 15, prob_cerrada=0.9, conexa_abierta=True))
        self.assertEqual(_alcanzables(salas, 1), len(salas))


class TestProporciones(unittest.TestCase):
    """Proporciones pedidas dentro de ±5 puntos en 10 000 salas (FR-035)."""

    def test_proporciones_FR035(self):
        g = gc.generar(2026, 100, 100, prob_hueco=0.3, prob_sin_costo=0.25, prob_cerrada=0.2, conexa=False)
        numeros = []
        for p in range(g.n):
            if g.vecina(p, gc.ESTE) >= 0:
                numeros.append(2 * p)
            if g.vecina(p, gc.SUR) >= 0:
                numeros.append(2 * p + 1)
        existentes = [c for c in numeros if g.existe[c]]
        huecos = 1 - len(existentes) / len(numeros)
        sin_costo = sum(1 for c in existentes if not g.declara_costo[c]) / len(existentes)
        cerradas = sum(1 for c in existentes if g.cerrada[c]) / len(existentes)
        self.assertAlmostEqual(huecos, 0.3, delta=0.05)
        self.assertAlmostEqual(sin_costo, 0.25, delta=0.05)
        self.assertAlmostEqual(cerradas, 0.2, delta=0.05)


class TestAmpliadaX10(unittest.TestCase):
    """cripta_ampliada_x10 (FR-030, SC-004)."""

    def test_diez_veces_las_salas_FR030(self):
        base = gc.generar(3, 8, 8)
        jugador = base.id_sala(0)
        textos = gc.cripta_ampliada_x10(3, 8, 8, jugador, 150)
        self.assertEqual(len(textos), 640)
        cripta = gc.cargar_cripta_sintetica(gc.fuente_sintetica(textos))
        self.assertEqual(len(cripta), 640)

    @unittest.skip('Se activa con la referencia teórica de T025 (tests/referencia_cazador.py)')
    def test_region_en_rango_identica_FR030(self):
        pass


if __name__ == '__main__':
    unittest.main()
