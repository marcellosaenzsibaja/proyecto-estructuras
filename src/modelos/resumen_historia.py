class ResumenHistoria:

    __slots__ = ('tiempo', 'accion_numero', 'sala_id', 'sala_nombre', 'vida', 'vida_max',
                 'ataque', 'defensa', 'velocidad', 'inventario', 'efectos', 'enemigos',
                 'exploradas', 'avistadas', 'estado', 'trunco', 'tiempo_final')

    def __init__(self):
        self.tiempo = 0
        self.accion_numero = 0
        self.sala_id = None
        self.sala_nombre = ''
        self.vida = 0
        self.vida_max = 0
        self.ataque = 0
        self.defensa = 0
        self.velocidad = 0
        self.inventario = []
        self.efectos = []
        self.enemigos = []
        self.exploradas = 0
        self.avistadas = 0
        self.estado = ''
        self.trunco = False
        self.tiempo_final = 0


def _efectos(partida):
    jugador = partida.jugador
    filas = []
    if jugador.veneno is not None:
        filas.append(('veneno', jugador.veneno.valor, jugador.veneno.fin))
    if jugador.efecto_velocidad is not None:
        filas.append(('velocidad', jugador.efecto_velocidad.valor, jugador.efecto_velocidad.fin))
    if jugador.antorcha is not None:
        filas.append(('antorcha', 0, jugador.antorcha.fin))
    return filas


def construir(partida, tiempo_pedido=None) -> ResumenHistoria:
    resumen = ResumenHistoria()
    jugador = partida.jugador
    sala = partida.cripta.sala(jugador.sala_id)
    resumen.tiempo = partida.reloj.tiempo_virtual
    resumen.accion_numero = partida.acciones_jugador
    resumen.sala_id = sala.id
    resumen.sala_nombre = sala.nombre
    resumen.vida = jugador.vida
    resumen.vida_max = jugador.vida_max
    resumen.ataque = jugador.ataque_total
    resumen.defensa = jugador.defensa_total
    resumen.velocidad = jugador.velocidad
    seleccionado = jugador.inventario.actual()
    for objeto in jugador.inventario:
        resumen.inventario.append((objeto.ficha.nombre, objeto is seleccionado))
    resumen.efectos = _efectos(partida)
    for enemigo in sala.enemigos:
        resumen.enemigos.append((enemigo.nombre, enemigo.id_actor, enemigo.vida, enemigo.vida_max))
    for enemigo in sala.dormidos:
        resumen.enemigos.append((enemigo.nombre, enemigo.id_actor, enemigo.vida, enemigo.vida_max))
    resumen.exploradas = partida.mapa.total_exploradas()
    resumen.avistadas = partida.mapa.total_avistadas()
    resumen.estado = partida.estado
    resumen.tiempo_final = partida.reloj.tiempo_virtual
    if tiempo_pedido is not None and tiempo_pedido > partida.reloj.tiempo_virtual:
        resumen.trunco = True
    return resumen


def formatear(resumen: ResumenHistoria, tiempo_pedido=None):
    lineas = []
    cabeza = f'Historia del instante {resumen.tiempo}'
    if resumen.accion_numero >= 0:
        cabeza += f' (antes de la acción #{resumen.accion_numero + 1})'
    lineas.append(cabeza)
    lineas.append(f'  Sala: [{resumen.sala_id}] {resumen.sala_nombre}')
    lineas.append(f'  Vida: {resumen.vida}/{resumen.vida_max}   ataque {resumen.ataque}  '
                  f'defensa {resumen.defensa}  velocidad {resumen.velocidad}')
    if resumen.inventario:
        partes = []
        for nombre, seleccionado in resumen.inventario:
            partes.append(f'*{nombre}' if seleccionado else nombre)
        lineas.append(f'  Inventario ({len(resumen.inventario)}): ' + ', '.join(partes))
    else:
        lineas.append('  Inventario: vacío')
    if resumen.efectos:
        partes = []
        for tipo, valor, fin in resumen.efectos:
            if valor:
                partes.append(f'{tipo} ({valor} por pulso, termina en {fin})')
            else:
                partes.append(f'{tipo} (termina en {fin})')
        lineas.append('  Efectos: ' + ', '.join(partes))
    else:
        lineas.append('  Efectos: ninguno')
    if resumen.enemigos:
        partes = []
        for nombre, instancia, vida, vida_max in resumen.enemigos:
            partes.append(f'{nombre} ({instancia}) {vida}/{vida_max}')
        lineas.append('  Enemigos aquí: ' + ', '.join(partes))
    else:
        lineas.append('  Enemigos aquí: ninguno')
    lineas.append(f'  Mapa conocido: {resumen.exploradas} exploradas, {resumen.avistadas} avistadas')
    if resumen.estado != 'en_curso':
        lineas.append(f'  Estado de la partida: {resumen.estado}')
    if resumen.trunco:
        lineas.append(f'  La partida terminó en el instante {resumen.tiempo_final}, '
                      f'antes del instante pedido.')
    return lineas
