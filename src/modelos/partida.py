import random
from src.estructuras_datos.buffer_circular import BufferCircular
from src.modelos.acciones import ABRIR, ACEPTADA, ATACAR, EQUIPAR, ESPERAR, MOVER, PENDIENTE, RECHAZADA, RECOGER, SOLTAR, USAR, Resultado
from src.modelos.direcciones import LETRAS
from src.modelos.entidades import Efecto, Enemigo, Jugador, Objeto, Trampa
from src.modelos.errores import ContenidoNoDisponible, EstadoInvalido
from src.modelos.cazador import MOVER as DECISION_MOVER, DecisorCazadores
from src.modelos.fichas import ANTIDOTO, ANTORCHA, ARMA, ARMADURA, CAZADOR, ERRANTE, GUARDIAN, LLAVE, PERGAMINO, POCION, RASTREADOR
from src.modelos.linea_tiempo import CURSOR_ANT, CURSOR_SIG, K_POR_DEFECTO, LineaTiempo, reconstruir_antes_de, reconstruir_en
from src.modelos.mapa_conocido import MapaConocido
from src.modelos.reloj import MotorReloj
from src.modelos.resumen_historia import construir as construir_resumen
EN_CURSO = 'en_curso'
VICTORIA = 'victoria'
DERROTA = 'derrota'
MENSAJES_VISIBLES = 20
COSTO_MOVER = 100
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR = 50
COSTO_EQUIPAR = 50
COSTO_RECOGER = 25
COSTO_SOLTAR = 25
COSTO_ABRIR = 50
INTERVALO_VENENO = 80
DURACION_VENENO = 400
INTERVALO_REGENERACION = 200
REARME_POR_DEFECTO = 300
ANTIGUEDAD_MAXIMA_RASTRO = 400
MAXIMO_HISTORIAL = 5
EV_JUGADOR = 'jugador'
EV_ENEMIGO = 'enemigo'
EV_VENENO = 'veneno'
EV_FIN_VELOCIDAD = 'fin_velocidad'
EV_FIN_ANTORCHA = 'fin_antorcha'
EV_REGENERACION = 'regeneracion'
EV_REARME = 'rearme'
EV_CIERRE = 'cierre_puerta'
EFECTO_VENENO = 'veneno'
EFECTO_VELOCIDAD = 'velocidad'
EFECTO_ANTORCHA = 'antorcha'
EFECTO_REGENERACION = 'regeneracion'

def clave_instancia(texto: str):
    i = len(texto)
    while i > 0 and '0' <= texto[i - 1] <= '9':
        i -= 1
    numero = int(texto[i:]) if i < len(texto) else -1
    return (texto[:i], numero)

def _insertar_por_instancia(lista, enemigo):
    clave = clave_instancia(enemigo.id_actor)
    i = len(lista)
    while i > 0 and clave < clave_instancia(lista[i - 1].id_actor):
        i -= 1
    lista.insert(i, enemigo)

def _rechazo(mensaje):
    return Resultado(RECHAZADA, mensaje, 0)

def _aceptada(mensaje, costo):
    return Resultado(ACEPTADA, mensaje, costo)

class Partida:

    def __init__(self, cripta, proveedor, semilla: int, k_checkpoint: int = K_POR_DEFECTO):
        self.cripta = cripta
        self.proveedor = proveedor
        self.semilla = semilla
        self.azar = random.Random(semilla)
        self.mapa = MapaConocido(len(cripta))
        self.linea = LineaTiempo(k_checkpoint)
        self.registra_linea = True
        self.limite_tiempo = None
        self._accion_actual = None
        self._buscador_conocido = None
        self.reloj = MotorReloj()
        self.mensajes = BufferCircular(MENSAJES_VISIBLES)
        self.estado = EN_CURSO
        self.acciones_jugador = 0
        self.enemigos_derrotados = 0
        self._esperando_jugador = False
        self._iniciada = False
        self._siguiente_uid = 0
        self._historial = []
        self._intervalo_actual = []
        self._grabando = False
        # Infraestructura de cálculo del cazador: no se guarda ni se revierte (FR-021).
        self._decisor = None
        # Contador monotónico de cambios de puertas (infraestructura, research R6).
        self.version_puertas = 0
        estadisticas = cripta.datos.jugador
        self.jugador = Jugador(estadisticas.vida_max, estadisticas.ataque, estadisticas.defensa, estadisticas.velocidad, cripta.datos.inventario_max)

    @property
    def esperando_jugador(self) -> bool:
        return self._esperando_jugador

    @property
    def iniciada(self) -> bool:
        return self._iniciada

    @property
    def sala_actual(self):
        return self.cripta.sala(self.jugador.sala_id)

    @property
    def pergaminos_disponibles(self) -> int:
        return len(self._historial)

    def iniciar(self):
        if self._iniciada:
            raise EstadoInvalido('La partida ya fue iniciada')
        inicial = self.cripta.sala(self.cripta.datos.sala_inicial)
        self.proveedor.asegurar_disponible(inicial.id)
        if not self.proveedor.contenido_disponible(inicial.id):
            raise ContenidoNoDisponible(f'El contenido de la sala inicial {inicial.id} no está disponible')
        self._iniciada = True
        self._incorporar_contenido(inicial)
        self.jugador.sala_id = inicial.id
        inicial.rastro = 0
        self.mapa.observar_puertas(inicial)
        self.mapa.explorar(inicial)
        self.jugador.evento = self.reloj.programar_evento(0, EV_JUGADOR, self.jugador)
        self._activar_enemigos(inicial)
        self._mensaje(f'Comienza la partida en {inicial.nombre}.')
        self._grabando = True
        self._avanzar()
        if self.registra_linea:
            self.linea.tomar_punto(self)

    def ejecutar(self, accion) -> Resultado:
        if self.estado != EN_CURSO or not self._esperando_jugador:
            raise EstadoInvalido('La partida no espera una acción del jugador')
        tipo = accion.tipo
        argumento = accion.argumento
        self._accion_actual = accion
        if tipo == USAR and self._pergamino_seleccionado():
            return self._usar_pergamino()
        if tipo == MOVER:
            resultado = self._mover(argumento)
        elif tipo == ABRIR:
            resultado = self._abrir(argumento)
        elif tipo == ATACAR:
            resultado = self._atacar(argumento)
        elif tipo == ESPERAR:
            resultado = self._esperar()
        elif tipo == RECOGER:
            resultado = self._recoger(argumento)
        elif tipo == USAR:
            resultado = self._usar()
        elif tipo == EQUIPAR:
            resultado = self._equipar()
        elif tipo == SOLTAR:
            resultado = self._soltar()
        else:
            raise ValueError(f'Acción desconocida: {tipo}')
        if resultado.estado == RECHAZADA:
            self._mensaje(resultado.mensaje)
            return resultado
        if resultado.estado == ACEPTADA:
            self._cerrar_accion(resultado.costo)
        return resultado

    def _mensaje(self, texto: str):
        self.mensajes.agregar(f'[{self.reloj.tiempo_virtual}] {texto}')

    def _registrar(self, deshacer):
        if self._grabando:
            self._intervalo_actual.append(deshacer)

    def _set_atributo(self, objetivo, atributo, nuevo):
        anterior = getattr(objetivo, atributo)
        setattr(objetivo, atributo, nuevo)

        def deshacer():
            setattr(objetivo, atributo, anterior)
        self._registrar(deshacer)

    def _lista_append(self, lista, item):
        lista.append(item)

        def deshacer():
            lista.remove(item)
        self._registrar(deshacer)

    def _lista_remove(self, lista, item):
        lista.remove(item)

        def deshacer():
            lista.append(item)
        self._registrar(deshacer)

    def _lista_pop(self, lista, indice):
        item = lista.pop(indice)

        def deshacer():
            lista.insert(indice, item)
        self._registrar(deshacer)
        return item

    def _programar_en(self, objetivo, atributo, intervalo, tipo, carga=None):
        anterior = getattr(objetivo, atributo)
        evento = self.reloj.programar_evento(intervalo, tipo, carga)
        setattr(objetivo, atributo, evento)

        def deshacer(ev=evento, obj=objetivo, attr=atributo, prev=anterior):
            self.reloj.agenda.cancelar(ev)
            setattr(obj, attr, prev)
        self._registrar(deshacer)
        return evento

    def _cancelar_en(self, objetivo, atributo) -> bool:
        evento = getattr(objetivo, atributo)
        if evento is None:
            return False
        cancelado = self.reloj.cancelar_evento(evento)
        setattr(objetivo, atributo, None)
        if cancelado:

            def deshacer(ev=evento, obj=objetivo, attr=atributo):
                self.reloj.agenda.insertar(ev)
                setattr(obj, attr, ev)
            self._registrar(deshacer)
        return cancelado

    def _reprogramar(self, evento, nuevo_tiempo):
        tiempo_anterior = evento.tiempo
        secuencia_anterior = evento.secuencia
        self.reloj.reprogramar_evento(evento, nuevo_tiempo)

        def deshacer():
            self.reloj.agenda.reprogramar(evento, tiempo_anterior, secuencia_anterior)
        self._registrar(deshacer)

    def _confirmar_intervalo(self):
        if self._intervalo_actual:
            self._historial.append(self._intervalo_actual)
            if len(self._historial) > MAXIMO_HISTORIAL:
                self._historial.pop(0)
        self._intervalo_actual = []

    def _pergamino_seleccionado(self) -> bool:
        objeto = self.jugador.inventario.actual()
        return objeto is not None and objeto.ficha.clase == PERGAMINO

    def _usar_pergamino(self) -> Resultado:
        if not self._historial:
            mensaje = 'No hay ninguna acción que deshacer.'
            self._mensaje(mensaje)
            return _rechazo(mensaje)
        nodo = self.jugador.inventario.nodo_actual()
        intervalo = self._historial.pop()
        self._grabando = False
        try:
            for deshacer in reversed(intervalo):
                deshacer()
        finally:
            self._grabando = True
        self.jugador.inventario.remover_nodo(nodo)
        if self.registra_linea:
            self.linea.recortar(self.acciones_jugador, self.reloj.tiempo_virtual)
        self._mensaje('Usas el pergamino de retroceso. El tiempo retrocede.')
        return Resultado(ACEPTADA, '', 0)

    def _cerrar_accion(self, costo: int):
        self._esperando_jugador = False
        numero = self.acciones_jugador + 1
        if self.registra_linea and self._accion_actual is not None:
            self.linea.registrar_accion(numero, self.reloj.tiempo_virtual,
                                        self._accion_actual.tipo, self._accion_actual.argumento)
        self._set_atributo(self, 'acciones_jugador', numero)
        self._set_atributo(self.sala_actual, 'rastro', self.reloj.tiempo_virtual)
        if self.estado == EN_CURSO:
            self._programar_accion(self.jugador, costo)
            self._avanzar()
        self._confirmar_intervalo()
        if self.registra_linea and self.linea.debe_tomar_punto(self.acciones_jugador):
            self.linea.tomar_punto(self)

    def _programar_accion(self, actor, costo: int):
        intervalo = max(1, costo * 100 // actor.velocidad)
        tipo = EV_JUGADOR if actor is self.jugador else EV_ENEMIGO
        self._programar_en(actor, 'evento', intervalo, tipo, actor)

    def _avanzar(self):
        while self.estado == EN_CURSO and (not self._esperando_jugador):
            if self.limite_tiempo is not None:
                if self.reloj.agenda.esta_vacio() or self.reloj.agenda.minimo().tiempo > self.limite_tiempo:
                    self.reloj.tiempo_virtual = self.limite_tiempo
                    return
            anterior_tiempo = self.reloj.tiempo_virtual
            evento = self.reloj.siguiente_evento()
            if evento is None:
                raise EstadoInvalido('La agenda quedó vacía con la partida en curso')

            def deshacer(t=anterior_tiempo):
                self.reloj.tiempo_virtual = t
            self._registrar(deshacer)
            self._despachar(evento)

    def _despachar(self, evento):
        tipo = evento.tipo
        if tipo == EV_JUGADOR:
            self.jugador.evento = None
            self._esperando_jugador = True
        elif tipo == EV_ENEMIGO:
            self._turno_enemigo(evento.carga)
        elif tipo == EV_VENENO:
            self._pulso_veneno(evento.carga)
        elif tipo == EV_FIN_VELOCIDAD:
            self._fin_velocidad(evento.carga)
        elif tipo == EV_FIN_ANTORCHA:
            self._fin_antorcha(evento.carga)
        elif tipo == EV_REGENERACION:
            self._pulso_regeneracion(evento.carga)
        elif tipo == EV_REARME:
            self._rearmar(evento.carga)
        elif tipo == EV_CIERRE:
            self._cerrar_puerta(evento.carga)

    def _nuevo_objeto(self, ficha):
        self._siguiente_uid += 1
        return Objeto(self._siguiente_uid, ficha)

    def _incorporar_contenido(self, sala):
        contenido = self.proveedor.obtener_contenido(sala.id)
        for instancia, ficha, vida in contenido.enemigos:
            enemigo = Enemigo(instancia, ficha, vida)
            enemigo.sala_id = sala.id
            _insertar_por_instancia(sala.dormidos, enemigo)
            self.proveedor.fijar(ficha.id)
        for ficha in contenido.objetos:
            sala.objetos.append(self._nuevo_objeto(ficha))
            self.proveedor.fijar(ficha.id)
        for instancia, ficha in contenido.trampas:
            sala.trampas.append(Trampa(instancia, ficha))
            self.proveedor.fijar(ficha.id)
        sala.contenido_incorporado = True

    def _liberar_suelo_sala(self, sala):
        for objeto in sala.objetos:
            self.proveedor.liberar(objeto.ficha.id)
        for trampa in sala.trampas:
            self.proveedor.liberar(trampa.ficha.id)

    def _activar_enemigos(self, sala):
        if not sala.dormidos:
            return
        anteriores_dormidos = sala.dormidos
        anteriores_enemigos = list(sala.enemigos)
        for enemigo in sala.dormidos:
            enemigo.activo = True
            sala.enemigos.append(enemigo)
            self._programar_accion(enemigo, 100)
            if enemigo.ficha.regeneracion:
                efecto = Efecto(EFECTO_REGENERACION, enemigo, enemigo.ficha.regeneracion)
                self._programar_en(efecto, 'evento', INTERVALO_REGENERACION, EV_REGENERACION, efecto)
                enemigo.regeneracion = efecto
        sala.dormidos = []

        def deshacer():
            for enemigo in anteriores_dormidos:
                enemigo.activo = False
            sala.enemigos[:] = anteriores_enemigos
            sala.dormidos = anteriores_dormidos
        self._registrar(deshacer)

    def _nombre(self, enemigo) -> str:
        return f'{enemigo.nombre} ({enemigo.id_actor})'

    def _calcular_dano(self, ataque: int, defensa: int) -> int:
        return max(1, ataque + self.azar.randint(0, 4) - defensa)

    def _restar_vida(self, actor, cantidad: int):
        self._set_atributo(actor, 'vida', max(0, actor.vida - cantidad))

    def _danar_jugador(self, cantidad: int, causa: str):
        self._restar_vida(self.jugador, cantidad)
        self._mensaje(f'{causa} te causa {cantidad} de daño (vida {self.jugador.vida}/{self.jugador.vida_max}).')
        if self.jugador.vida == 0:
            self._derrota()

    def _derrota(self):
        self._set_atributo(self, 'estado', DERROTA)
        self._mensaje('Has sido derrotado.')

    def _victoria(self):
        self._set_atributo(self, 'estado', VICTORIA)
        self._mensaje('Has escapado de la cripta.')

    def _mover(self, direccion):
        if not isinstance(direccion, int) or not 0 <= direccion < 4:
            return _rechazo('Dirección inválida.')
        sala = self.sala_actual
        salida = sala.salidas[direccion]
        if salida is None:
            return _rechazo(f'No hay salida hacia {LETRAS[direccion]}.')
        if salida.puerta.cerrada:
            return _rechazo(f'La puerta hacia {LETRAS[direccion]} está cerrada.')
        destino = self.cripta.sala(salida.destino)
        if not destino.contenido_incorporado:
            self.proveedor.asegurar_disponible(destino.id)
            if not self.proveedor.contenido_disponible(destino.id):
                return Resultado(PENDIENTE, f'El contenido de {destino.nombre} aún no está disponible.', 0)
            self._incorporar_contenido(destino)
        self._liberar_suelo_sala(sala)
        self._set_atributo(self.jugador, 'sala_id', destino.id)
        self._mensaje(f'Te mueves a {destino.nombre}.')
        self.mapa.observar_puertas(destino, self._registrar)
        self.mapa.explorar(destino, self._registrar)
        if self.jugador.antorcha is not None:
            for direccion_vecina in range(4):
                salida_vecina = destino.salidas[direccion_vecina]
                if salida_vecina is not None and salida_vecina.sala_destino is not None:
                    self.mapa.explorar(salida_vecina.sala_destino, self._registrar)
        self._activar_enemigos(destino)
        self._activar_trampas(destino)
        if self.estado == EN_CURSO and destino.id == self.cripta.datos.sala_salida and salida.puerta.abierta_por_jugador and (salida.puerta.llave == self.cripta.datos.llave_salida):
            self._victoria()
        # El costo base del movimiento es el costo de la salida (FR-003).
        return _aceptada('', salida.puerta.costo)

    def _activar_trampas(self, sala):
        for trampa in sala.trampas:
            if not trampa.armada:
                continue
            self._set_atributo(trampa, 'armada', False)
            self._mensaje(f'Se activa la trampa {trampa.ficha.nombre}.')
            rearme = trampa.ficha.rearme
            if rearme is None:
                rearme = REARME_POR_DEFECTO
            self._programar_en(trampa, 'evento_rearme', rearme, EV_REARME, trampa)
            self._danar_jugador(trampa.ficha.dano, trampa.ficha.nombre)
            if self.estado != EN_CURSO:
                return

    def _rearmar(self, trampa):
        self._set_atributo(trampa, 'evento_rearme', None)
        self._set_atributo(trampa, 'armada', True)

    def _tiene_llave(self, id_llave: str) -> bool:
        for objeto in self.jugador.inventario:
            if objeto.ficha.clase == LLAVE and objeto.ficha.id == id_llave:
                return True
        return False

    def _abrir(self, direccion):
        if not isinstance(direccion, int) or not 0 <= direccion < 4:
            return _rechazo('Dirección inválida.')
        salida = self.sala_actual.salidas[direccion]
        if salida is None:
            return _rechazo(f'No hay salida hacia {LETRAS[direccion]}.')
        puerta = salida.puerta
        if not puerta.cerrada:
            return _rechazo('La puerta ya está abierta.')
        if puerta.llave is None:
            return _rechazo('Esta puerta no se puede abrir con una llave.')
        if not self._tiene_llave(puerta.llave):
            return _rechazo('No tienes la llave correcta.')
        self._poner_cerrada(puerta, False)
        self.mapa.observar_puerta(self.sala_actual, direccion, False, self._registrar)
        self._set_atributo(puerta, 'abierta_por_jugador', True)
        if puerta.cierre_automatico:
            self._programar_en(puerta, 'evento_cierre', puerta.cierre_automatico, EV_CIERRE, puerta)
        self._mensaje(f'Abres la puerta hacia {LETRAS[direccion]}.')
        return _aceptada('', COSTO_ABRIR)

    def _cerrar_puerta(self, puerta):
        self._set_atributo(puerta, 'evento_cierre', None)
        self._poner_cerrada(puerta, True)

    def _poner_cerrada(self, puerta, cerrada: bool):
        """Único punto de cambio de Puerta.cerrada (abrir, cierre automático y deshacer; T047)."""
        anterior = puerta.cerrada
        puerta.cerrada = cerrada
        self._notificar_puerta(puerta)

        def deshacer():
            puerta.cerrada = anterior
            self._notificar_puerta(puerta)
        self._registrar(deshacer)

    def _notificar_puerta(self, puerta):
        # No se revierte: deshacer también es un cambio y vuelve a incrementar.
        self.version_puertas += 1
        if self._decisor is not None:
            self._decisor.notificar_puerta(puerta)
        self._observar_si_presente(puerta)

    def _observar_si_presente(self, puerta):
        """El jugador observa una puerta cuando está en cualquiera de sus dos salas (003 FR-008)."""
        if self.jugador.sala_id is None:
            return
        sala = self.cripta.sala(self.jugador.sala_id)
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is not None and salida.puerta is puerta:
                self.mapa.observar_puerta(sala, direccion, puerta.cerrada, self._registrar)

    def _atacar(self, instancia):
        objetivo = None
        for enemigo in self.sala_actual.enemigos:
            if enemigo.id_actor == instancia:
                objetivo = enemigo
                break
        if objetivo is None:
            return _rechazo('Ese enemigo no está en la sala.')
        dano = self._calcular_dano(self.jugador.ataque_total, objetivo.defensa)
        self._restar_vida(objetivo, dano)
        self._mensaje(f'Atacas a {self._nombre(objetivo)} y le causas {dano} de daño.')
        if not objetivo.vivo:
            self._matar_enemigo(objetivo)
        return _aceptada('', COSTO_ATACAR)

    def _matar_enemigo(self, enemigo):
        self._cancelar_en(enemigo, 'evento')
        if enemigo.regeneracion is not None:
            self._cancelar_en(enemigo.regeneracion, 'evento')
            self._set_atributo(enemigo, 'regeneracion', None)
        sala = self.cripta.sala(enemigo.sala_id)
        self._lista_remove(sala.enemigos, enemigo)
        self.proveedor.liberar(enemigo.ficha.id)
        for id_objeto in enemigo.ficha.suelta:
            ficha_objeto = self.proveedor.ficha(id_objeto)
            self._lista_append(sala.objetos, self._nuevo_objeto(ficha_objeto))
            self.proveedor.fijar(ficha_objeto.id)
        self._set_atributo(self, 'enemigos_derrotados', self.enemigos_derrotados + 1)
        self._mensaje(f'{self._nombre(enemigo)} ha muerto.')

    def _esperar(self):
        self._mensaje('Esperas.')
        return _aceptada('', COSTO_ESPERAR)

    def _recoger(self, indice):
        sala = self.sala_actual
        if not isinstance(indice, int) or not 0 <= indice < len(sala.objetos):
            return _rechazo('No existe ese objeto en el suelo.')
        inventario = self.jugador.inventario
        if inventario.esta_lleno():
            return _rechazo('El inventario está lleno; suelta un objeto primero.')
        objeto = sala.objetos[indice]
        es_pergamino = objeto.ficha.clase == PERGAMINO
        if es_pergamino:
            sala.objetos.pop(indice)
            inventario.agregar(objeto)
        else:
            objeto = self._lista_pop(sala.objetos, indice)
            nodo = inventario.agregar(objeto)

            def deshacer():
                inventario.remover_nodo(nodo)
            self._registrar(deshacer)
        self._mensaje(f'Recoges {objeto.ficha.nombre}.')
        return _aceptada('', COSTO_RECOGER)

    def _soltar(self):
        inventario = self.jugador.inventario
        nodo = inventario.nodo_actual()
        if nodo is None:
            return _rechazo('No hay ningún objeto seleccionado.')
        objeto = nodo.valor
        es_pergamino = objeto.ficha.clase == PERGAMINO
        anterior_vecino = nodo.anterior
        inventario.soltar_actual()
        if self.jugador.arma is objeto:
            self._set_atributo(self.jugador, 'arma', None)
        if self.jugador.armadura is objeto:
            self._set_atributo(self.jugador, 'armadura', None)
        sala = self.sala_actual
        sala.objetos.append(objeto)
        if not es_pergamino:

            def deshacer():
                sala.objetos.remove(objeto)
                inventario.insertar_despues(anterior_vecino, nodo)
                inventario.fijar_cursor(nodo)
            self._registrar(deshacer)
        self._mensaje(f'Sueltas {objeto.ficha.nombre}.')
        return _aceptada('', COSTO_SOLTAR)

    def _equipar(self):
        inventario = self.jugador.inventario
        nodo = inventario.nodo_actual()
        if nodo is None:
            return _rechazo('No hay ningún objeto seleccionado.')
        objeto = nodo.valor
        clase = objeto.ficha.clase
        if clase == ARMA:
            self._set_atributo(self.jugador, 'arma', objeto)
        elif clase == ARMADURA:
            self._set_atributo(self.jugador, 'armadura', objeto)
        else:
            return _rechazo(f'{objeto.ficha.nombre} no se puede equipar.')
        anterior_vecino = nodo.anterior
        inventario.mover_al_frente(nodo)

        def deshacer():
            inventario.remover_nodo(nodo)
            inventario.insertar_despues(anterior_vecino, nodo)
            inventario.fijar_cursor(nodo)
        self._registrar(deshacer)
        self._mensaje(f'Equipas {objeto.ficha.nombre}.')
        return _aceptada('', COSTO_EQUIPAR)

    def _usar(self):
        inventario = self.jugador.inventario
        objeto = inventario.actual()
        if objeto is None:
            return _rechazo('No hay ningún objeto seleccionado.')
        ficha = objeto.ficha
        clase = ficha.clase
        if clase not in (POCION, ANTIDOTO, ANTORCHA):
            return _rechazo(f'{ficha.nombre} no se puede usar.')
        nodo = inventario.nodo_actual()
        anterior_vecino = nodo.anterior
        inventario.soltar_actual()
        self.proveedor.liberar(ficha.id)

        def deshacer():
            inventario.insertar_despues(anterior_vecino, nodo)
            inventario.fijar_cursor(nodo)
        self._registrar(deshacer)
        self._mensaje(f'Usas {ficha.nombre}.')
        if clase == POCION:
            if ficha.cura is not None:
                self._curar(ficha.cura)
            if ficha.modificador_velocidad is not None:
                self._aplicar_velocidad(self.jugador, ficha.modificador_velocidad, ficha.duracion)
        elif clase == ANTIDOTO:
            self._cancelar_veneno()
        elif clase == ANTORCHA:
            self._encender_antorcha(ficha.duracion)
        return _aceptada('', COSTO_USAR)

    def _curar(self, cantidad: int):
        jugador = self.jugador
        self._set_atributo(jugador, 'vida', min(jugador.vida_max, jugador.vida + cantidad))
        self._mensaje(f'Recuperas vida ({jugador.vida}/{jugador.vida_max}).')

    def _aplicar_veneno(self, dano: int):
        jugador = self.jugador
        self._cancelar_veneno()
        efecto = Efecto(EFECTO_VENENO, jugador, dano, self.reloj.tiempo_virtual + DURACION_VENENO)
        self._programar_en(efecto, 'evento', INTERVALO_VENENO, EV_VENENO, efecto)
        self._set_atributo(jugador, 'veneno', efecto)
        self._mensaje('Has sido envenenado.')

    def _cancelar_veneno(self):
        veneno = self.jugador.veneno
        if veneno is None:
            return
        self._cancelar_en(veneno, 'evento')
        self._set_atributo(self.jugador, 'veneno', None)
        self._mensaje('El veneno desaparece.')

    def _pulso_veneno(self, efecto):
        self._set_atributo(efecto, 'evento', None)
        self._danar_jugador(efecto.valor, 'El veneno')
        if self.estado != EN_CURSO:
            return
        if self.reloj.tiempo_virtual + INTERVALO_VENENO <= efecto.fin:
            self._programar_en(efecto, 'evento', INTERVALO_VENENO, EV_VENENO, efecto)
        else:
            self._set_atributo(self.jugador, 'veneno', None)
            self._mensaje('El veneno se agota.')

    def _cambiar_velocidad(self, actor, nueva: int):
        anterior = actor.velocidad
        if nueva == anterior:
            return
        self._set_atributo(actor, 'velocidad', nueva)
        evento = actor.evento
        if evento is not None:
            ahora = self.reloj.tiempo_virtual
            restante = max(1, (evento.tiempo - ahora) * anterior // nueva)
            self._reprogramar(evento, ahora + restante)

    def _aplicar_velocidad(self, actor, modificador: int, duracion: int):
        previo = actor.efecto_velocidad
        if previo is not None:
            self._cancelar_en(previo, 'evento')
        efecto = Efecto(EFECTO_VELOCIDAD, actor, modificador, self.reloj.tiempo_virtual + duracion)
        self._set_atributo(actor, 'efecto_velocidad', efecto)
        self._cambiar_velocidad(actor, max(1, actor.velocidad_base + modificador))
        self._programar_en(efecto, 'evento', duracion, EV_FIN_VELOCIDAD, efecto)
        self._mensaje(f'Tu velocidad cambia a {actor.velocidad}.')

    def _fin_velocidad(self, efecto):
        actor = efecto.objetivo
        self._set_atributo(efecto, 'evento', None)
        self._set_atributo(actor, 'efecto_velocidad', None)
        self._cambiar_velocidad(actor, actor.velocidad_base)
        self._mensaje(f'Tu velocidad vuelve a {actor.velocidad}.')

    def _encender_antorcha(self, duracion: int):
        jugador = self.jugador
        previa = jugador.antorcha
        if previa is not None:
            self._cancelar_en(previa, 'evento')
        efecto = Efecto(EFECTO_ANTORCHA, jugador, 0, self.reloj.tiempo_virtual + duracion)
        self._programar_en(efecto, 'evento', duracion, EV_FIN_ANTORCHA, efecto)
        self._set_atributo(jugador, 'antorcha', efecto)
        self._mensaje('Enciendes una antorcha.')

    def _fin_antorcha(self, efecto):
        self._set_atributo(efecto, 'evento', None)
        self._set_atributo(self.jugador, 'antorcha', None)
        self._mensaje('La antorcha se apaga.')

    def _pulso_regeneracion(self, efecto):
        enemigo = efecto.objetivo
        self._set_atributo(efecto, 'evento', None)
        if not enemigo.vivo:
            return
        self._set_atributo(enemigo, 'vida', min(enemigo.vida_max, enemigo.vida + efecto.valor))
        self._programar_en(efecto, 'evento', INTERVALO_REGENERACION, EV_REGENERACION, efecto)

    def _turno_enemigo(self, enemigo):
        self._set_atributo(enemigo, 'evento', None)
        if enemigo.sala_id == self.jugador.sala_id:
            self._ataque_enemigo(enemigo)
            costo = COSTO_ATACAR
        else:
            costo = self._comportamiento(enemigo)
        if self.estado == EN_CURSO and enemigo.vivo:
            # Atacar y esperar cuestan 100; moverse, el costo de la salida (FR-003, FR-005, research R8).
            self._programar_accion(enemigo, costo)

    def _ataque_enemigo(self, enemigo):
        dano = self._calcular_dano(enemigo.ataque, self.jugador.defensa_total)
        self._danar_jugador(dano, self._nombre(enemigo))

    def _comportamiento(self, enemigo) -> int:
        """Aplica el comportamiento del enemigo y devuelve el costo base de la acción realizada."""
        comportamiento = enemigo.comportamiento
        if comportamiento == GUARDIAN:
            return COSTO_ESPERAR
        sala = self.cripta.sala(enemigo.sala_id)
        if comportamiento == ERRANTE:
            opciones = []
            for direccion in range(4):
                salida = sala.salidas[direccion]
                if salida is not None and (not salida.puerta.cerrada):
                    opciones.append(salida)
            if opciones:
                salida = opciones[self.azar.randrange(len(opciones))]
                self._mover_enemigo(enemigo, salida.destino)
                return salida.puerta.costo
        elif comportamiento == RASTREADOR:
            destino = self._vecino_con_rastro_fresco(sala)
            if destino is not None:
                self._mover_enemigo(enemigo, destino)
                return self._costo_hacia(sala, destino)
        elif comportamiento == CAZADOR:
            decision = self.decisor_cazadores.decidir(sala, enemigo.ficha.rango, self.sala_actual)
            if decision.accion == DECISION_MOVER:
                self._mover_enemigo(enemigo, decision.salida.destino)
            return decision.costo
        return COSTO_ESPERAR

    @property
    def decisor_cazadores(self) -> DecisorCazadores:
        """Decisor de los cazadores, creado al primer uso (infraestructura, FR-021)."""
        if self._decisor is None:
            self._decisor = DecisorCazadores(self.cripta)
        return self._decisor

    def _costo_hacia(self, sala, id_destino: int) -> int:
        """Costo de la salida abierta más barata hacia id_destino; empate por orden N, S, E, O (FR-015)."""
        mejor = None
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is not None and salida.destino == id_destino and not salida.puerta.cerrada:
                if mejor is None or salida.puerta.costo < mejor:
                    mejor = salida.puerta.costo
        return COSTO_MOVER if mejor is None else mejor

    def _vecino_con_rastro_fresco(self, sala):
        ahora = self.reloj.tiempo_virtual
        mejor = None
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None or salida.puerta.cerrada:
                continue
            vecina = self.cripta.sala(salida.destino)
            rastro = vecina.rastro
            if rastro is None or ahora - rastro >= ANTIGUEDAD_MAXIMA_RASTRO:
                continue
            if mejor is None or rastro > mejor.rastro or (rastro == mejor.rastro and vecina.id < mejor.id):
                mejor = vecina
        return None if mejor is None else mejor.id

    def _mover_enemigo(self, enemigo, id_destino: int):
        origen = self.cripta.sala(enemigo.sala_id)
        destino = self.cripta.sala(id_destino)
        self._lista_remove(origen.enemigos, enemigo)
        self._lista_append(destino.enemigos, enemigo)
        self._set_atributo(enemigo, 'sala_id', id_destino)
        jugador_en = self.jugador.sala_id
        if origen.id == jugador_en:
            self._mensaje(f'{self._nombre(enemigo)} se aleja de la sala.')
        elif destino.id == jugador_en:
            self._mensaje(f'{self._nombre(enemigo)} entra a la sala.')

    @property
    def buscador_conocido(self):
        if self._buscador_conocido is None:
            from src.modelos.viaje import BuscadorConocido
            self._buscador_conocido = BuscadorConocido(self.cripta, self.mapa)
        return self._buscador_conocido

    def ruta_conocida(self, id_destino: int):
        if not self.cripta.existe(id_destino):
            return None
        origen = self.cripta.sala(self.jugador.sala_id)
        objetivo = self.cripta.sala(id_destino)
        return self.buscador_conocido.primer_paso(origen, objetivo)

    def ruta_conocida_existe(self, id_destino: int) -> bool:
        return self.ruta_conocida(id_destino) is not None

    def siguiente_paso_viaje(self, id_destino: int):
        resultado = self.ruta_conocida(id_destino)
        if resultado is None:
            return None
        _, id_vecina = resultado
        if id_vecina is None:
            return None
        origen = self.cripta.sala(self.jugador.sala_id)
        return self.buscador_conocido.direccion_hacia(origen, id_vecina)

    def destino_valido(self, id_destino: int) -> bool:
        if not self.cripta.existe(id_destino):
            return False
        return self.mapa.explorada(self.cripta.sala(id_destino))

    def mover_cursor(self, sentido: int) -> bool:
        inventario = self.jugador.inventario
        movido = inventario.avanzar() if sentido > 0 else inventario.retroceder()
        if movido and self.registra_linea:
            self.linea.registrar_cursor(self.reloj.tiempo_virtual,
                                        CURSOR_SIG if sentido > 0 else CURSOR_ANT)
        return movido

    def avanzar_hasta(self, tiempo: int):
        if self.estado != EN_CURSO:
            return
        anterior_limite = self.limite_tiempo
        esperando = self._esperando_jugador
        self.limite_tiempo = tiempo
        self._esperando_jugador = False
        try:
            self._avanzar()
        finally:
            self.limite_tiempo = anterior_limite
            self._esperando_jugador = esperando if self.estado == EN_CURSO else False
        if self.estado == EN_CURSO and self.reloj.tiempo_virtual < tiempo:
            self.reloj.tiempo_virtual = tiempo

    def historia_en(self, tiempo):
        if not isinstance(tiempo, int) or isinstance(tiempo, bool):
            return (None, "Usa 'historia <t>' con un instante, o 'historia #k' con el número de una acción.")
        if tiempo < 0:
            return (None, f'El instante debe estar entre 0 y {self.reloj.tiempo_virtual}.')
        if tiempo > self.reloj.tiempo_virtual:
            return (None, f'Ese instante todavía no ha ocurrido (el reloj va en {self.reloj.tiempo_virtual}).')
        reconstruida = reconstruir_en(self, tiempo)
        if reconstruida is None:
            return (None, 'No hay información suficiente para reconstruir ese instante.')
        return (construir_resumen(reconstruida), None)

    def historia_antes_de(self, numero):
        if not isinstance(numero, int) or isinstance(numero, bool):
            return (None, "Usa 'historia <t>' con un instante, o 'historia #k' con el número de una acción.")
        if numero < 1 or numero > self.acciones_jugador + 1:
            return (None, f'Solo hay {self.acciones_jugador} acciones del jugador; '
                          f'usa #1 a #{self.acciones_jugador + 1}.')
        reconstruida = reconstruir_antes_de(self, numero)
        if reconstruida is None:
            return (None, 'No hay información suficiente para reconstruir esa acción.')
        return (construir_resumen(reconstruida), None)
