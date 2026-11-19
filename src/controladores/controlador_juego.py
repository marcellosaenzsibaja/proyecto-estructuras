from src.modelos.acciones import ABRIR, ATACAR, ESPERAR, EQUIPAR, MOVER, PENDIENTE, RECOGER, SOLTAR, USAR, Accion
from src.modelos.direcciones import indice_direccion
from src.modelos.fichas import PERGAMINO
from src.modelos.linea_tiempo import CURSOR_ANT, CURSOR_SIG
from src.modelos.partida import EN_CURSO
from src.modelos.viaje import ejecutar_viaje, resolver_destino, validar_destino
from src.servicios import guardado, puntajes

AYUDA_HISTORIA = "Usa 'historia <t>' con un instante, o 'historia #k' con el número de una acción."

class ControladorJuego:

    def __init__(self, partida, vista, bitacora=None, ruta_puntajes=puntajes.RUTA_POR_DEFECTO):
        self.partida = partida
        self.vista = vista
        self.bitacora = bitacora
        self.ruta_puntajes = ruta_puntajes
        self.abandonada = False

    def ejecutar(self):
        if not self.partida.iniciada:
            self.partida.iniciar()
        self.vista.mostrar_inicio(self.partida)
        while self.partida.estado == EN_CURSO:
            self.vista.mostrar_estado(self.partida)
            nombre, argumento = self.vista.pedir_comando()
            if not self._atender(nombre, argumento):
                self.abandonada = True
                break
        self.vista.mostrar_final(self.partida, self.abandonada)
        if not self.abandonada:
            entrada = puntajes.registrar(self.partida, self.ruta_puntajes)
            self.vista.mostrar_mensaje(f"Puntaje de esta partida: {entrada['puntaje']}")
            self.vista.mostrar_puntajes(puntajes.mejores(self.ruta_puntajes))

    def _atender(self, nombre, argumento) -> bool:
        if nombre == 'salir':
            return False
        if nombre == '':
            return True
        if nombre in ('ayuda', '?'):
            self.vista.mostrar_ayuda()
        elif nombre in ('sig', 'ant'):
            movido = self.partida.mover_cursor(1 if nombre == 'sig' else -1)
            if movido and self.bitacora is not None:
                self.bitacora.registrar_cursor(CURSOR_SIG if nombre == 'sig' else CURSOR_ANT)
            if not movido:
                self.vista.mostrar_mensaje('No hay más objetos en esa dirección.')
        elif nombre in ('historia', 'hist'):
            self._historia(argumento)
        elif nombre in ('mapa', 'mp'):
            self.vista.mostrar_mapa_conocido(self.partida)
        elif nombre == 'ir':
            self._ir_a(argumento)
        elif nombre in ('ordenar', 'ord'):
            self.vista.mostrar_inventario_ordenado(self.partida)
        elif nombre in ('puntajes', 'pts'):
            self.vista.mostrar_puntajes(puntajes.mejores(self.ruta_puntajes))
        elif nombre in ('pergamino', 'perg'):
            self._usar_pergamino_seleccionandolo()
        elif nombre in ('guardar', 'gu'):
            self._guardar(argumento)
        elif nombre in ('cargar', 'ca'):
            self._cargar(argumento)
        else:
            accion = self._traducir(nombre, argumento)
            if accion is None:
                self.vista.mostrar_mensaje("Comando no reconocido. Escribe 'ayuda'.")
            else:
                self._ejecutar_accion(accion)
        return True

    def _usar_pergamino_seleccionandolo(self):
        inventario = self.partida.jugador.inventario
        for nodo in inventario.nodos():
            if nodo.valor.ficha.clase == PERGAMINO:
                inventario.fijar_cursor(nodo)
                self._ejecutar_accion(Accion(USAR))
                return
        self.vista.mostrar_mensaje('No tienes ningún pergamino de retroceso.')

    def _ir_a(self, argumento):
        texto = (argumento or '').strip()
        if texto.lower().startswith('a ') or texto.lower() == 'a':
            texto = texto[1:].strip()
        id_destino, error = resolver_destino(self.partida, texto)
        if error is not None:
            self.vista.mostrar_mensaje(error)
            return
        error = validar_destino(self.partida, id_destino)
        if error is not None:
            self.vista.mostrar_mensaje(error)
            return
        if self.bitacora is not None:
            self.bitacora.registrar_comentario(f'ir a {id_destino}')

        def _antes(accion):
            if self.bitacora is not None:
                self.bitacora.registrar(accion)
        viaje = ejecutar_viaje(self.partida, id_destino, antes_de_paso=_antes)
        self.vista.mostrar_fin_viaje(self.partida, viaje)

    def _historia(self, argumento):
        if argumento is None or not argumento.strip():
            self.vista.mostrar_mensaje(AYUDA_HISTORIA)
            return
        texto = argumento.strip()
        if texto.startswith('#'):
            resto = texto[1:]
            if not resto.isdigit():
                self.vista.mostrar_mensaje(AYUDA_HISTORIA)
                return
            resumen, error = self.partida.historia_antes_de(int(resto))
        elif texto.isdigit():
            resumen, error = self.partida.historia_en(int(texto))
        else:
            self.vista.mostrar_mensaje(AYUDA_HISTORIA)
            return
        if error is not None:
            self.vista.mostrar_mensaje(error)
            return
        self.vista.mostrar_resumen_historia(resumen)

    def _guardar(self, argumento):
        ruta = argumento or 'partida.bin'
        try:
            snapshot = guardado.tomar_snapshot(self.partida)
            if ruta.endswith('.json'):
                guardado.guardar_json(snapshot, ruta)
            else:
                guardado.guardar_binario(snapshot, ruta)
            self.vista.mostrar_mensaje(f"Partida guardada en '{ruta}'.")
        except OSError as error:
            self.vista.mostrar_mensaje(f'No se pudo guardar: {error}')

    def _cargar(self, argumento):
        ruta = argumento or 'partida.bin'
        try:
            cargador = guardado.cargar_json if ruta.endswith('.json') else guardado.cargar_binario
            snapshot = cargador(ruta)
            self.partida = guardado.restaurar_partida(snapshot, self.partida.cripta, self.partida.proveedor)
            self.vista.mostrar_mensaje(f"Partida cargada desde '{ruta}'.")
        except (OSError, ValueError) as error:
            self.vista.mostrar_mensaje(f'No se pudo cargar: {error}')

    def _ejecutar_accion(self, accion):
        if self.bitacora is not None:
            self.bitacora.registrar(accion)
        resultado = self.partida.ejecutar(accion)
        if resultado.estado == PENDIENTE:
            self.vista.mostrar_mensaje(resultado.mensaje)

    def _traducir(self, nombre, argumento):
        if nombre in ('mover', 'm', 'abrir', 'ab'):
            direccion = indice_direccion(argumento)
            if direccion is None:
                return None
            return Accion(MOVER if nombre in ('mover', 'm') else ABRIR, direccion)
        if nombre in ('atacar', 'a'):
            numero = self._numero(argumento)
            enemigos = self.partida.sala_actual.enemigos
            if numero is None or not 1 <= numero <= len(enemigos):
                return None
            return Accion(ATACAR, enemigos[numero - 1].id_actor)
        if nombre in ('recoger', 'r'):
            numero = self._numero(argumento)
            if numero is None:
                return None
            return Accion(RECOGER, numero - 1)
        if nombre in ('esperar', 'e'):
            return Accion(ESPERAR)
        if nombre in ('usar', 'u'):
            return Accion(USAR)
        if nombre in ('equipar', 'eq'):
            return Accion(EQUIPAR)
        if nombre in ('soltar', 'so'):
            return Accion(SOLTAR)
        return None

    def _numero(self, texto):
        if texto is not None and texto.isdigit():
            return int(texto)
        return None
