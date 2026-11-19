import tempfile
import unittest
from src.adaptadores.fuente_datos import FuenteDatos
from src.controladores.controlador_juego import ControladorJuego
from src.estructuras_datos.cache_fichas import CacheFichas
from src.modelos.direcciones import ESTE, NORTE
from src.modelos.errores import ErrorDatos
from src.modelos.fichas import GUARDIAN, RASTREADOR, FichaEnemigo, FichaObjeto, FichaTrampa
from src.modelos.partida import VICTORIA, Partida
from src.servicios.cargador_cripta import cargar_datos, cargar_esqueleto
from src.servicios.fabrica_fichas import ficha_desde_dict
from src.servicios.proveedor_red import ProveedorRed
CATALOGO = {'ent_rata_gigante': {'id': 'ent_rata_gigante', 'clase': 'enemigo', 'nombre': 'Rata gigante', 'vida_max': 12, 'ataque': 5, 'defensa': 1, 'velocidad': 150, 'comportamiento': 'rastreador', 'suelta': ['itm_pocion_menor']}, 'itm_pocion_menor': {'id': 'itm_pocion_menor', 'clase': 'pocion', 'nombre': 'Poción menor', 'peso': 1, 'valor': 10, 'cura': 8}, 'itm_daga_oxidada': {'id': 'itm_daga_oxidada', 'clase': 'arma', 'nombre': 'Daga oxidada', 'peso': 2, 'valor': 15, 'ataque_bonus': 3}, 'itm_antorcha': {'id': 'itm_antorcha', 'clase': 'antorcha', 'nombre': 'Antorcha', 'peso': 1, 'valor': 5, 'duracion': 2000}, 'itm_llave_negra': {'id': 'itm_llave_negra', 'clase': 'llave', 'nombre': 'Llave negra', 'peso': 1, 'valor': 1, 'abre': 'x'}, 'trp_dardos': {'id': 'trp_dardos', 'clase': 'trampa', 'nombre': 'Dardos', 'daño': 4, 'rearme': 300}}

class FuenteFalsa(FuenteDatos):

    def __init__(self, salas=25, por_pagina=10):
        self.salas = salas
        self.por_pagina = por_pagina
        self.llamadas = []

    def obtener_criptas(self):
        self.llamadas.append('criptas')
        return {'criptas': []}

    def obtener_llaves(self, cripta_id):
        self.llamadas.append('llaves')
        return {'llaves': []}

    def obtener_datos_cripta(self, cripta_id):
        self.llamadas.append('datos')
        return {'id': cripta_id, 'version': 'v1', 'salas_total': self.salas, 'paginas': 1, 'salas_por_pagina': self.por_pagina, 'sala_inicial': 1, 'sala_salida': self.salas, 'llave_salida': 'itm_llave_negra', 'presupuesto_solicitudes': 20, 'inventario_max': 10, 'jugador': {'vida_max': 30, 'ataque': 6, 'defensa': 2, 'velocidad': 100}}

    def obtener_esqueleto(self, cripta_id, pagina=1):
        self.llamadas.append(('esqueleto', pagina))
        total = -(-self.salas // self.por_pagina)
        inicio = (pagina - 1) * self.por_pagina + 1
        salas = []
        for i in range(inicio, min(inicio + self.por_pagina, self.salas + 1)):
            salidas = {}
            if i > 1:
                salidas['S'] = {'sala': i - 1}
            if i < self.salas:
                salidas['N'] = {'sala': i + 1}
                if i == self.salas - 1:
                    salidas['N'] = {'sala': i + 1, 'cerrada': True, 'llave': 'itm_llave_negra'}
            salas.append({'id': i, 'nombre': f'Sala {i}', 'salidas': salidas})
        return {'pagina': pagina, 'total_paginas': total, 'salas': salas}

    def obtener_contenido_lote(self, cripta_id, ids_salas):
        self.llamadas.append(('contenido', tuple(ids_salas)))
        assert 1 <= len(ids_salas) <= 10
        contenido = []
        for i in ids_salas:
            c = {'sala': i, 'enemigos': [], 'objetos': [], 'trampas': []}
            if i % 3 == 0:
                c['enemigos'].append({'instancia': f'e-{i}', 'tipo': 'ent_rata_gigante', 'vida': 12})
            if i % 2 == 0:
                c['objetos'].append('itm_daga_oxidada')
            if i == 5:
                c['objetos'].append('itm_llave_negra')
                c['trampas'].append({'instancia': 't-5', 'tipo': 'trp_dardos'})
            if i == 1:
                c['objetos'].append('itm_antorcha')
            contenido.append(c)
        return {'contenido': contenido}

    def obtener_catalogo_lote(self, ids_entidades):
        self.llamadas.append(('catalogo', tuple(ids_entidades)))
        assert 1 <= len(ids_entidades) <= 10
        return {'entidades': [CATALOGO[i] for i in ids_entidades if i in CATALOGO]}

    def obtener_version_cripta(self, cripta_id):
        return {'id': cripta_id, 'version': 'v1'}

    def obtener_version_catalogo(self):
        return {'version': 'cat'}

class PruebasFabricaFichas(unittest.TestCase):

    def test_enemigo(self):
        f = ficha_desde_dict(CATALOGO['ent_rata_gigante'])
        self.assertIsInstance(f, FichaEnemigo)
        self.assertEqual(f.comportamiento, RASTREADOR)
        self.assertEqual(f.suelta, ('itm_pocion_menor',))

    def test_comportamiento_con_acento(self):
        d = dict(CATALOGO['ent_rata_gigante'], comportamiento='Guardián')
        self.assertEqual(ficha_desde_dict(d).comportamiento, GUARDIAN)

    def test_comportamiento_desconocido(self):
        d = dict(CATALOGO['ent_rata_gigante'], comportamiento='volador')
        with self.assertRaises(ErrorDatos):
            ficha_desde_dict(d)

    def test_objetos_y_trampa(self):
        self.assertIsInstance(ficha_desde_dict(CATALOGO['itm_daga_oxidada']), FichaObjeto)
        trampa = ficha_desde_dict(CATALOGO['trp_dardos'])
        self.assertIsInstance(trampa, FichaTrampa)
        self.assertEqual((trampa.dano, trampa.rearme), (4, 300))

    def test_errores_con_contexto(self):
        with self.assertRaises(ErrorDatos) as ctx:
            ficha_desde_dict({'id': 'itm_x', 'clase': 'arma', 'nombre': 'X', 'peso': 1, 'valor': 1})
        self.assertIn('itm_x', str(ctx.exception))
        with self.assertRaises(ErrorDatos):
            ficha_desde_dict({'id': 'itm_p', 'clase': 'pocion', 'nombre': 'P', 'peso': 1, 'valor': 1})
        with self.assertRaises(ErrorDatos):
            ficha_desde_dict({'id': 'itm_z', 'clase': 'raro', 'nombre': 'Z', 'peso': 1, 'valor': 1})
        with self.assertRaises(ErrorDatos):
            ficha_desde_dict(dict(CATALOGO['ent_rata_gigante'], velocidad=0))

class PruebasCargador(unittest.TestCase):

    def test_datos_sin_valores_por_defecto(self):
        fuente = FuenteFalsa()
        datos = cargar_datos(fuente, 'c')
        self.assertEqual((datos.sala_inicial, datos.sala_salida, datos.inventario_max), (1, 25, 10))
        self.assertEqual(datos.jugador.vida_max, 30)
        original = fuente.obtener_datos_cripta
        fuente.obtener_datos_cripta = lambda i: {k: v for k, v in original(i).items() if k != 'sala_inicial'}
        with self.assertRaises(ErrorDatos) as ctx:
            cargar_datos(fuente, 'c')
        self.assertIn('sala_inicial', str(ctx.exception))

    def test_esqueleto_paginado_y_puertas(self):
        fuente = FuenteFalsa()
        cripta = cargar_esqueleto(fuente, cargar_datos(fuente, 'c'))
        self.assertEqual(len(cripta), 25)
        paginas = [l for l in fuente.llamadas if isinstance(l, tuple) and l[0] == 'esqueleto']
        self.assertEqual(len(paginas), 3)
        puerta_ida = cripta.sala(24).salidas[NORTE].puerta
        puerta_vuelta = cripta.sala(25).salidas[1].puerta
        self.assertIs(puerta_ida, puerta_vuelta)
        self.assertTrue(puerta_ida.cerrada)
        self.assertEqual(puerta_ida.llave, 'itm_llave_negra')

    def test_precarga_anticipada_por_lotes_sin_repetir(self):
        fuente = FuenteFalsa()
        cripta = cargar_esqueleto(fuente, cargar_datos(fuente, 'c'))
        proveedor = ProveedorRed(fuente, cripta, CacheFichas(25))
        antes = len(fuente.llamadas)
        proveedor.asegurar_disponible(1)
        nuevas = fuente.llamadas[antes:]
        contenido = [l for l in nuevas if l[0] == 'contenido']
        catalogo = [l for l in nuevas if l[0] == 'catalogo']
        self.assertEqual(len(contenido), 1)
        self.assertEqual(len(contenido[0][1]), 10)
        self.assertTrue(proveedor.contenido_disponible(1))
        self.assertTrue(proveedor.contenido_disponible(10))
        self.assertFalse(proveedor.contenido_disponible(11))
        pedidos = [i for l in catalogo for i in l[1]]
        self.assertEqual(len(pedidos), len(set(pedidos)))
        self.assertNotIn('itm_pocion_menor', pedidos)
        sala5 = proveedor.obtener_contenido(5)
        self.assertEqual([o.id for o in sala5.objetos], ['itm_llave_negra'])
        self.assertEqual(len(sala5.trampas), 1)
        antes2 = len(fuente.llamadas)
        proveedor.asegurar_disponible(1)
        self.assertEqual(len(fuente.llamadas), antes2)
        antes3 = len(fuente.llamadas)
        self.assertEqual(proveedor.ficha('itm_pocion_menor').clase, 'pocion')
        self.assertEqual(len(fuente.llamadas) - antes3, 1)
        proveedor.ficha('itm_pocion_menor')
        self.assertEqual(len(fuente.llamadas) - antes3, 1)

    def test_avanzar_mas_alla_del_horizonte_pide_otro_lote(self):
        fuente = FuenteFalsa()
        cripta = cargar_esqueleto(fuente, cargar_datos(fuente, 'c'))
        proveedor = ProveedorRed(fuente, cripta, CacheFichas(25))
        proveedor.asegurar_disponible(1)
        self.assertFalse(proveedor.contenido_disponible(15))
        proveedor.asegurar_disponible(15)
        self.assertTrue(proveedor.contenido_disponible(15))

    def test_catalogo_incompleto_se_reporta(self):
        fuente = FuenteFalsa()
        fuente.obtener_catalogo_lote = lambda ids: {'entidades': []}
        cripta = cargar_esqueleto(fuente, cargar_datos(fuente, 'c'))
        with self.assertRaises(ErrorDatos):
            ProveedorRed(fuente, cripta, CacheFichas(25)).asegurar_disponible(1)

    def test_fijar_y_liberar_delegan_en_la_cache(self):
        fuente = FuenteFalsa()
        cripta = cargar_esqueleto(fuente, cargar_datos(fuente, 'c'))
        cache = CacheFichas(25)
        proveedor = ProveedorRed(fuente, cripta, cache)
        proveedor.asegurar_disponible(1)
        proveedor.fijar('itm_antorcha')
        self.assertTrue(cache.en_uso('itm_antorcha'))
        proveedor.liberar('itm_antorcha')
        self.assertFalse(cache.en_uso('itm_antorcha'))

class VistaGuionada:

    def __init__(self, comandos):
        self.comandos = list(comandos)
        self.finales = []

    def mostrar_inicio(self, partida):
        pass

    def mostrar_estado(self, partida):
        pass

    def mostrar_ayuda(self):
        pass

    def mostrar_mensaje(self, texto):
        pass

    def mostrar_inventario_ordenado(self, partida):
        pass

    def mostrar_puntajes(self, tabla):
        pass

    def pedir_comando(self):
        return self.comandos.pop(0) if self.comandos else ('salir', None)

    def mostrar_final(self, partida, abandonada):
        self.finales.append((partida.estado, abandonada))

class PruebasControlador(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def armar(self, comandos, salas=7):
        fuente = FuenteFalsa(salas=salas)
        cripta = cargar_esqueleto(fuente, cargar_datos(fuente, 'c'))
        proveedor = ProveedorRed(fuente, cripta, CacheFichas(25))
        vista = VistaGuionada(comandos)
        partida = Partida(cripta, proveedor, 11)
        ruta_puntajes = f'{self._tmp.name}/puntajes.json'
        controlador = ControladorJuego(partida, vista, ruta_puntajes=ruta_puntajes)
        return (controlador, vista, partida)

    def test_atacar_por_numero_de_la_lista(self):
        controlador, vista, partida = self.armar([('m', 'N'), ('m', 'N'), ('a', '1'), ('salir', None)])
        controlador.ejecutar()
        self.assertEqual(partida.jugador.sala_id, 3)
        enemigos = partida.cripta.sala(3).enemigos
        self.assertTrue(not enemigos or enemigos[0].vida < 12)
        self.assertEqual(partida.acciones_jugador, 3)

    def test_salir_abandona(self):
        controlador, vista, partida = self.armar([('ayuda', None), ('', None), ('salir', None)])
        controlador.ejecutar()
        self.assertEqual(vista.finales, [('en_curso', True)])

    def test_comandos_invalidos_no_rompen(self):
        controlador, vista, partida = self.armar([('m', 'X'), ('a', '5'), ('r', 'z'), ('volar', None), ('sig', None), ('ant', None), ('m', None), ('salir', None)])
        controlador.ejecutar()
        self.assertEqual(partida.reloj.tiempo_virtual, 0)

    def test_inventario_y_navegacion(self):
        controlador, vista, partida = self.armar([('r', '1'), ('m', 'N'), ('salir', None)])
        controlador.ejecutar()
        self.assertEqual(len(partida.jugador.inventario), 1)
        self.assertEqual(partida.jugador.sala_id, 2)
if __name__ == '__main__':
    unittest.main()
