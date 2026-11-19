from src.estructuras_datos.ordenamiento import ordenar
from src.modelos.direcciones import LETRAS
from src.modelos.fichas import ARMA, ARMADURA, CAZADOR
from src.modelos.mapa_conocido import NOMBRE_PUERTA, RECORDADA_CERRADA
from src.modelos.resumen_historia import formatear as formatear_historia
from src.modelos.viaje import mensaje_fin as mensaje_fin_viaje
AYUDA = 'Comandos:\n  mover <N|S|E|O>     (m)\n  abrir <N|S|E|O>     (ab)\n  atacar <número>     (a)    número de la lista de enemigos\n  esperar             (e)\n  recoger <número>    (r)    número de la lista del suelo\n  usar                (u)    objeto seleccionado\n  equipar             (eq)   objeto seleccionado\n  soltar              (so)   objeto seleccionado\n  sig / ant           recorrer el inventario\n  ordenar             (ord)  ver el inventario en orden alfabético\n  pergamino           (perg) deshace tu última decisión, si tienes uno\n  mapa                (mp)   ver el mapa que conoces\n  ir a <sala>         viajar a una sala explorada por la ruta que conoces\n  historia <t>        (hist) estado de la partida en un instante pasado\n  historia #k         (hist) estado justo antes de tu acción número k\n  guardar [archivo]   (gu)   guarda la partida (.bin o .json)\n  cargar [archivo]    (ca)   retoma una partida guardada\n  puntajes            (pts)  mejores puntajes registrados\n  ayuda               (?)\n  salir'

class VistaConsola:

    def seleccionar_cripta(self, criptas) -> str:
        print('Criptas disponibles:')
        for i, c in enumerate(criptas, start=1):
            print(f"  {i}. {c['id']} - {c.get('nombre', '')} ({c.get('salas', '?')} salas, dificultad {c.get('dificultad', '?')})")
        while True:
            texto = input('Elige una cripta (número): ').strip()
            if texto.isdigit() and 1 <= int(texto) <= len(criptas):
                return criptas[int(texto) - 1]['id']
            print('Opción inválida.')

    def mostrar_inicio(self, partida):
        print(f'\nCRIPTA - {partida.cripta.datos.id} (semilla {partida.semilla})')
        print(AYUDA)

    def mostrar_ayuda(self):
        print(AYUDA)

    def mostrar_mensaje(self, texto: str):
        print(texto)

    def mostrar_resumen_historia(self, resumen):
        for linea in formatear_historia(resumen):
            print(linea)

    def mostrar_fin_viaje(self, partida, viaje):
        mensaje = mensaje_fin_viaje(partida, viaje)
        if mensaje:
            print(mensaje)

    def mostrar_mapa_conocido(self, partida):
        mapa = partida.mapa
        cripta = partida.cripta
        print(f'\nMapa conocido ({mapa.total_exploradas()} salas exploradas, '
              f'{mapa.total_avistadas()} avistadas)')
        for id_sala in mapa.salas_exploradas():
            sala = cripta.sala(id_sala)
            marca = ' <- estás aquí' if id_sala == partida.jugador.sala_id else ''
            print(f'  [{sala.id}] {sala.nombre}{marca}')
            for direccion in range(4):
                salida = sala.salidas[direccion]
                if salida is None:
                    print(f'    {LETRAS[direccion]} -> (sin salida)')
                    continue
                estado = NOMBRE_PUERTA[mapa.puerta_recordada(sala, direccion)]
                destino = salida.sala_destino
                if destino is not None and mapa.explorada(destino):
                    etiqueta = f'sala {destino.id} ({destino.nombre})'
                else:
                    etiqueta = f'sala {salida.destino} (sin explorar)'
                print(f'    {LETRAS[direccion]} -> {etiqueta}: {estado}, costo {salida.puerta.costo}')
        avistadas = mapa.ids_avistadas(cripta)
        if avistadas:
            print('  Salas avistadas: ' + ', '.join(str(i) for i in avistadas))
        else:
            print('  Salas avistadas: ninguna')

    def mostrar_estado(self, partida):
        jugador = partida.jugador
        sala = partida.sala_actual
        print('\n' + '=' * 64)
        print(f'Tiempo virtual: {partida.reloj.tiempo_virtual}')
        print(f'Vida {jugador.vida}/{jugador.vida_max} | Ataque {jugador.ataque_total} | Defensa {jugador.defensa_total} | Velocidad {jugador.velocidad}')
        efectos = []
        if jugador.veneno is not None:
            efectos.append(f'veneno hasta {jugador.veneno.fin}')
        if jugador.efecto_velocidad is not None:
            efectos.append(f'velocidad alterada hasta {jugador.efecto_velocidad.fin}')
        if jugador.antorcha is not None:
            efectos.append(f'antorcha encendida hasta {jugador.antorcha.fin}')
        print('Efectos: ' + (', '.join(efectos) if efectos else 'ninguno'))
        print(f'\nSala: {sala.nombre} (#{sala.id})')
        print('Salidas:')
        salidas = 0
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None:
                continue
            salidas += 1
            # La vista deriva el estado del conocimiento del jugador, no de la
            # realidad (003 FR-021, FR-025). Estando en la sala, ambos coinciden.
            recordada = partida.mapa.puerta_recordada(sala, direccion)
            estado = NOMBRE_PUERTA[recordada]
            if recordada == RECORDADA_CERRADA:
                estado = f'cerrada (llave {salida.puerta.llave})'
            # El costo de tránsito de cada salida de la sala actual (FR-023).
            print(f'  [{LETRAS[direccion]}] hacia sala {salida.destino}: {estado}, costo {salida.puerta.costo}')
        if salidas == 0:
            print('  ninguna')
        print('Enemigos:')
        if not sala.enemigos:
            print('  ninguno')
        for i, e in enumerate(sala.enemigos, start=1):
            # Los cazadores se distinguen de los demás enemigos (FR-024).
            marca = ' [cazador]' if e.comportamiento == CAZADOR else ''
            print(f'  {i}. {e.nombre} ({e.id_actor}){marca} vida {e.vida}/{e.vida_max}')
        print('Suelo:')
        if not sala.objetos:
            print('  vacío')
        for i, o in enumerate(sala.objetos, start=1):
            print(f'  {i}. {o.ficha.nombre}')
        if sala.trampas:
            print('Trampas:')
            for t in sala.trampas:
                print(f"  {t.ficha.nombre}: {('armada' if t.armada else 'desarmada')}")
        self._mostrar_inventario(partida)
        print('\nMensajes:')
        for mensaje in partida.mensajes:
            print(f'  {mensaje}')

    def _mostrar_inventario(self, partida):
        inventario = partida.jugador.inventario
        jugador = partida.jugador
        print(f'Inventario ({len(inventario)}/{inventario.capacidad}):')
        if inventario.esta_vacio():
            print('  vacío')
        actual = inventario.nodo_actual()
        for nodo in inventario.nodos():
            objeto = nodo.valor
            marca = '>' if nodo is actual else ' '
            equipo = ''
            if objeto is jugador.arma or objeto is jugador.armadura:
                equipo = ' [equipado]'
            clase = objeto.ficha.clase
            detalle = ''
            if clase == ARMA:
                detalle = f' (+{objeto.ficha.ataque_bonus} ataque)'
            elif clase == ARMADURA:
                detalle = f' (+{objeto.ficha.defensa_bonus} defensa)'
            print(f' {marca} {objeto.ficha.nombre}{detalle}{equipo}')

    def mostrar_inventario_ordenado(self, partida):
        items = ordenar(list(partida.jugador.inventario), clave=lambda o: o.ficha.nombre)
        print('Inventario (orden alfabético):')
        if not items:
            print('  vacío')
        for objeto in items:
            print(f'  - {objeto.ficha.nombre}')

    def mostrar_puntajes(self, tabla):
        print('Mejores puntajes:')
        if not tabla:
            print('  (ninguno todavía)')
        for i, entrada in enumerate(tabla, start=1):
            print(f"  {i}. {entrada['cripta_id']} - {entrada['puntaje']} puntos ({entrada['resultado']}, semilla {entrada['semilla']})")

    def pedir_comando(self):
        try:
            texto = input('\n> ').strip()
        except EOFError:
            return ('salir', None)
        partes = texto.split(maxsplit=1)
        if not partes:
            return ('', None)
        return (partes[0].lower(), partes[1].strip() if len(partes) > 1 else None)

    def mostrar_final(self, partida, abandonada: bool):
        print('\n' + '=' * 64)
        if abandonada:
            print('Partida abandonada.')
        elif partida.estado == 'victoria':
            print('VICTORIA')
        else:
            print('DERROTA')
        print(f'Acciones: {partida.acciones_jugador} | Enemigos derrotados: {partida.enemigos_derrotados} | Tiempo virtual: {partida.reloj.tiempo_virtual}')
