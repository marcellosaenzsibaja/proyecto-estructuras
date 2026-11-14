from src.estructuras_datos.ordenamiento import ordenar
from src.modelos.direcciones import LETRAS
from src.modelos.fichas import ARMA, ARMADURA, CAZADOR
AYUDA = 'Comandos:\n  mover <N|S|E|O>     (m)\n  abrir <N|S|E|O>     (ab)\n  atacar <número>     (a)    número de la lista de enemigos\n  esperar             (e)\n  recoger <número>    (r)    número de la lista del suelo\n  usar                (u)    objeto seleccionado\n  equipar             (eq)   objeto seleccionado\n  soltar              (so)   objeto seleccionado\n  sig / ant           recorrer el inventario\n  ordenar             (ord)  ver el inventario en orden alfabético\n  pergamino           (perg) deshace tu última decisión, si tienes uno\n  guardar [archivo]   (gu)   guarda la partida (.bin o .json)\n  cargar [archivo]    (ca)   retoma una partida guardada\n  puntajes            (pts)  mejores puntajes registrados\n  ayuda               (?)\n  salir'

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
            estado = 'abierta'
            if salida.puerta.cerrada:
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
