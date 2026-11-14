import json
import os
import struct
from src.estructuras_datos.ordenamiento import ordenar
from src.modelos.entidades import Objeto, Puerta, Salida, Enemigo, Trampa
from src.modelos.errores import ErrorDatos
from src.modelos.partida import EN_CURSO, EV_ENEMIGO, Partida
MAGIC = b'CRPT'
# Versión 2: agrega el costo de cada puerta (P2, FR-001). Un archivo de la
# versión 1 (primera parte) se rechaza como incompatible (FR-026).
FORMATO_VERSION = 2
_ESTADOS = ('en_curso', 'victoria', 'derrota')

def _estado_a_codigo(estado):
    return _ESTADOS.index(estado)

def _codigo_a_estado(codigo):
    return _ESTADOS[codigo]

def tomar_snapshot(partida) -> dict:
    jugador = partida.jugador
    inventario = []
    for nodo in jugador.inventario.nodos():
        objeto = nodo.valor
        inventario.append({'uid': objeto.uid, 'id_ficha': objeto.ficha.id, 'arma': jugador.arma is objeto, 'armadura': jugador.armadura is objeto})
    salas = []
    for sala in partida.cripta.salas():
        if not sala.contenido_incorporado:
            continue
        puertas = []
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None:
                puertas.append(None)
                continue
            puertas.append({'destino': salida.destino, 'cerrada': salida.puerta.cerrada, 'llave': salida.puerta.llave, 'abierta_por_jugador': salida.puerta.abierta_por_jugador, 'costo': salida.puerta.costo})
        salas.append({'id': sala.id, 'rastro': sala.rastro, 'puertas': puertas, 'objetos': [{'uid': o.uid, 'id_ficha': o.ficha.id} for o in sala.objetos], 'enemigos': [{'instancia': e.id_actor, 'id_ficha': e.ficha.id, 'vida': e.vida, 'activo': e.activo, 'tiempo_siguiente': -1 if e.evento is None else e.evento.tiempo} for e in sala.enemigos], 'trampas': [{'instancia': t.instancia, 'id_ficha': t.ficha.id, 'armada': t.armada} for t in sala.trampas]})
    return {'cripta_id': partida.cripta.datos.id, 'version_cripta': partida.cripta.datos.version, 'semilla': partida.semilla, 'tiempo_virtual': partida.reloj.tiempo_virtual, 'acciones_jugador': partida.acciones_jugador, 'enemigos_derrotados': partida.enemigos_derrotados, 'estado': partida.estado, 'siguiente_uid': partida._siguiente_uid, 'jugador': {'vida': jugador.vida, 'sala_id': jugador.sala_id, 'inventario': inventario}, 'salas': salas}

def version_compatible(snapshot: dict, cripta) -> bool:
    return snapshot.get('cripta_id') == cripta.datos.id and snapshot.get('version_cripta') == cripta.datos.version

def restaurar_partida(snapshot: dict, cripta, proveedor) -> Partida:
    if not version_compatible(snapshot, cripta):
        raise ErrorDatos(f"El guardado no es compatible con esta cripta (esperaba {cripta.datos.id}@{cripta.datos.version}, el guardado es de {snapshot.get('cripta_id')}@{snapshot.get('version_cripta')})")
    partida = Partida(cripta, proveedor, snapshot['semilla'])
    partida._iniciada = True
    partida.reloj.tiempo_virtual = snapshot['tiempo_virtual']
    partida.acciones_jugador = snapshot['acciones_jugador']
    partida.enemigos_derrotados = snapshot['enemigos_derrotados']
    partida.estado = snapshot['estado']
    partida._siguiente_uid = snapshot['siguiente_uid']
    for crudo in snapshot['salas']:
        sala = cripta.sala(crudo['id'])
        sala.contenido_incorporado = True
        sala.rastro = crudo['rastro']
        for direccion, info in enumerate(crudo['puertas']):
            if info is None:
                sala.salidas[direccion] = None
                continue
            puerta = Puerta(cerrada=info['cerrada'], llave=info['llave'], costo=info['costo'])
            puerta.abierta_por_jugador = info['abierta_por_jugador']
            sala.salidas[direccion] = Salida(info['destino'], puerta)
        sala.dormidos = []
        sala.objetos = []
        for o in crudo['objetos']:
            ficha = proveedor.ficha(o['id_ficha'])
            sala.objetos.append(Objeto(o['uid'], ficha))
            proveedor.fijar(ficha.id)
        sala.enemigos = []
        for e in crudo['enemigos']:
            ficha = proveedor.ficha(e['id_ficha'])
            enemigo = Enemigo(e['instancia'], ficha, e['vida'])
            enemigo.sala_id = sala.id
            enemigo.activo = e['activo']
            sala.enemigos.append(enemigo)
            proveedor.fijar(ficha.id)
            if enemigo.activo and enemigo.vivo:
                # Se restaura el instante exacto de su próximo turno para continuar
                # con las mismas decisiones (FR-029); sin dato, la regla de P1.
                siguiente = e.get('tiempo_siguiente', -1)
                if siguiente >= partida.reloj.tiempo_virtual:
                    enemigo.evento = partida.reloj.programar_evento(siguiente - partida.reloj.tiempo_virtual, EV_ENEMIGO, enemigo)
                else:
                    partida._programar_accion(enemigo, 100)
        sala.trampas = []
        for t in crudo['trampas']:
            ficha = proveedor.ficha(t['id_ficha'])
            trampa = Trampa(t['instancia'], ficha)
            trampa.armada = t['armada']
            sala.trampas.append(trampa)
            proveedor.fijar(ficha.id)
    jugador = partida.jugador
    jugador.vida = snapshot['jugador']['vida']
    jugador.sala_id = snapshot['jugador']['sala_id']
    for item in snapshot['jugador']['inventario']:
        ficha = proveedor.ficha(item['id_ficha'])
        objeto = Objeto(item['uid'], ficha)
        jugador.inventario.agregar(objeto)
        if item['arma']:
            jugador.arma = objeto
        if item['armadura']:
            jugador.armadura = objeto
        proveedor.fijar(ficha.id)
    # Vuelve a unir las puertas de ambos lados y a enlazar Salida.sala_destino (research R3).
    cripta.enlazar_puertas()
    jugador.evento = None
    partida._esperando_jugador = partida.estado == EN_CURSO
    partida._grabando = True
    return partida

def guardar_json(snapshot: dict, ruta: str):
    _asegurar_carpeta(ruta)
    temporal = f'{ruta}.tmp'
    with open(temporal, 'w', encoding='utf-8') as archivo:
        json.dump(snapshot, archivo, ensure_ascii=False)
    os.replace(temporal, ruta)

def cargar_json(ruta: str) -> dict:
    with open(ruta, 'r', encoding='utf-8') as archivo:
        return json.load(archivo)

def _empacar_str(texto: str) -> bytes:
    datos = texto.encode('utf-8')
    return struct.pack('>H', len(datos)) + datos

def _desempacar_str(buf, pos):
    n, = struct.unpack_from('>H', buf, pos)
    pos += 2
    return (buf[pos:pos + n].decode('utf-8'), pos + n)

def _empacar_str_opcional(texto) -> bytes:
    if texto is None:
        return struct.pack('>B', 0)
    return struct.pack('>B', 1) + _empacar_str(texto)

def _desempacar_str_opcional(buf, pos):
    bandera, = struct.unpack_from('>B', buf, pos)
    pos += 1
    if not bandera:
        return (None, pos)
    return _desempacar_str(buf, pos)

def _empacar_encabezado(snapshot: dict) -> bytes:
    partes = [_empacar_str(snapshot['cripta_id']), _empacar_str(snapshot['version_cripta']), struct.pack('>q', snapshot['semilla']), struct.pack('>q', snapshot['tiempo_virtual']), struct.pack('>I', snapshot['acciones_jugador']), struct.pack('>I', snapshot['enemigos_derrotados']), struct.pack('>B', _estado_a_codigo(snapshot['estado'])), struct.pack('>I', snapshot['siguiente_uid']), struct.pack('>i', snapshot['jugador']['sala_id']), struct.pack('>i', snapshot['jugador']['vida']), struct.pack('>H', len(snapshot['jugador']['inventario']))]
    for item in snapshot['jugador']['inventario']:
        partes.append(struct.pack('>i', item['uid']))
        partes.append(_empacar_str(item['id_ficha']))
        bandera = (1 if item['arma'] else 0) | (2 if item['armadura'] else 0)
        partes.append(struct.pack('>B', bandera))
    return b''.join(partes)

def _desempacar_encabezado(buf, pos):
    cripta_id, pos = _desempacar_str(buf, pos)
    version_cripta, pos = _desempacar_str(buf, pos)
    semilla, = struct.unpack_from('>q', buf, pos)
    pos += 8
    tiempo_virtual, = struct.unpack_from('>q', buf, pos)
    pos += 8
    acciones_jugador, = struct.unpack_from('>I', buf, pos)
    pos += 4
    enemigos_derrotados, = struct.unpack_from('>I', buf, pos)
    pos += 4
    codigo_estado, = struct.unpack_from('>B', buf, pos)
    pos += 1
    siguiente_uid, = struct.unpack_from('>I', buf, pos)
    pos += 4
    sala_id, = struct.unpack_from('>i', buf, pos)
    pos += 4
    vida, = struct.unpack_from('>i', buf, pos)
    pos += 4
    n_items, = struct.unpack_from('>H', buf, pos)
    pos += 2
    inventario = []
    for _ in range(n_items):
        uid, = struct.unpack_from('>i', buf, pos)
        pos += 4
        id_ficha, pos = _desempacar_str(buf, pos)
        bandera, = struct.unpack_from('>B', buf, pos)
        pos += 1
        inventario.append({'uid': uid, 'id_ficha': id_ficha, 'arma': bool(bandera & 1), 'armadura': bool(bandera & 2)})
    snapshot = {'cripta_id': cripta_id, 'version_cripta': version_cripta, 'semilla': semilla, 'tiempo_virtual': tiempo_virtual, 'acciones_jugador': acciones_jugador, 'enemigos_derrotados': enemigos_derrotados, 'estado': _codigo_a_estado(codigo_estado), 'siguiente_uid': siguiente_uid, 'jugador': {'sala_id': sala_id, 'vida': vida, 'inventario': inventario}}
    return (snapshot, pos)

def _empacar_sala(crudo: dict) -> bytes:
    partes = [struct.pack('>i', crudo['id'])]
    partes.append(struct.pack('>q', -1 if crudo['rastro'] is None else crudo['rastro']))
    for info in crudo['puertas']:
        if info is None:
            partes.append(struct.pack('>B', 0))
            continue
        partes.append(struct.pack('>B', 1))
        partes.append(struct.pack('>i', info['destino']))
        partes.append(struct.pack('>I', info['costo']))
        partes.append(struct.pack('>B', 1 if info['cerrada'] else 0))
        partes.append(_empacar_str_opcional(info['llave']))
        partes.append(struct.pack('>B', 1 if info['abierta_por_jugador'] else 0))
    partes.append(struct.pack('>H', len(crudo['objetos'])))
    for o in crudo['objetos']:
        partes.append(struct.pack('>i', o['uid']))
        partes.append(_empacar_str(o['id_ficha']))
    partes.append(struct.pack('>H', len(crudo['enemigos'])))
    for e in crudo['enemigos']:
        partes.append(_empacar_str(e['instancia']))
        partes.append(_empacar_str(e['id_ficha']))
        partes.append(struct.pack('>i', e['vida']))
        partes.append(struct.pack('>B', 1 if e['activo'] else 0))
        partes.append(struct.pack('>q', e['tiempo_siguiente']))
    partes.append(struct.pack('>H', len(crudo['trampas'])))
    for t in crudo['trampas']:
        partes.append(_empacar_str(t['instancia']))
        partes.append(_empacar_str(t['id_ficha']))
        partes.append(struct.pack('>B', 1 if t['armada'] else 0))
    return b''.join(partes)

def _desempacar_sala(buf, pos):
    id_sala, = struct.unpack_from('>i', buf, pos)
    pos += 4
    rastro, = struct.unpack_from('>q', buf, pos)
    pos += 8
    puertas = []
    for _ in range(4):
        hay, = struct.unpack_from('>B', buf, pos)
        pos += 1
        if not hay:
            puertas.append(None)
            continue
        destino, = struct.unpack_from('>i', buf, pos)
        pos += 4
        costo, = struct.unpack_from('>I', buf, pos)
        pos += 4
        cerrada, = struct.unpack_from('>B', buf, pos)
        pos += 1
        llave, pos = _desempacar_str_opcional(buf, pos)
        abierta, = struct.unpack_from('>B', buf, pos)
        pos += 1
        puertas.append({'destino': destino, 'cerrada': bool(cerrada), 'llave': llave, 'abierta_por_jugador': bool(abierta), 'costo': costo})
    n_objetos, = struct.unpack_from('>H', buf, pos)
    pos += 2
    objetos = []
    for _ in range(n_objetos):
        uid, = struct.unpack_from('>i', buf, pos)
        pos += 4
        id_ficha, pos = _desempacar_str(buf, pos)
        objetos.append({'uid': uid, 'id_ficha': id_ficha})
    n_enemigos, = struct.unpack_from('>H', buf, pos)
    pos += 2
    enemigos = []
    for _ in range(n_enemigos):
        instancia, pos = _desempacar_str(buf, pos)
        id_ficha, pos = _desempacar_str(buf, pos)
        vida, = struct.unpack_from('>i', buf, pos)
        pos += 4
        activo, = struct.unpack_from('>B', buf, pos)
        pos += 1
        tiempo_siguiente, = struct.unpack_from('>q', buf, pos)
        pos += 8
        enemigos.append({'instancia': instancia, 'id_ficha': id_ficha, 'vida': vida, 'activo': bool(activo), 'tiempo_siguiente': tiempo_siguiente})
    n_trampas, = struct.unpack_from('>H', buf, pos)
    pos += 2
    trampas = []
    for _ in range(n_trampas):
        instancia, pos = _desempacar_str(buf, pos)
        id_ficha, pos = _desempacar_str(buf, pos)
        armada, = struct.unpack_from('>B', buf, pos)
        pos += 1
        trampas.append({'instancia': instancia, 'id_ficha': id_ficha, 'armada': bool(armada)})
    crudo = {'id': id_sala, 'rastro': None if rastro == -1 else rastro, 'puertas': puertas, 'objetos': objetos, 'enemigos': enemigos, 'trampas': trampas}
    return (crudo, pos)
_PREAMBULO = struct.Struct('>4sBII')
_ENTRADA_INDICE = struct.Struct('>iII')

def _asegurar_carpeta(ruta):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

def guardar_binario(snapshot: dict, ruta: str):
    encabezado = _empacar_encabezado(snapshot)
    salas_ordenadas = ordenar(snapshot['salas'], clave=lambda s: s['id'])
    registros = [_empacar_sala(s) for s in salas_ordenadas]
    inicio_indice = _PREAMBULO.size + len(encabezado)
    inicio_registros = inicio_indice + len(registros) * _ENTRADA_INDICE.size
    indice = bytearray()
    desplazamiento = inicio_registros
    for sala, registro in zip(salas_ordenadas, registros):
        indice += _ENTRADA_INDICE.pack(sala['id'], desplazamiento, len(registro))
        desplazamiento += len(registro)
    preambulo = _PREAMBULO.pack(MAGIC, FORMATO_VERSION, len(encabezado), len(registros))
    _asegurar_carpeta(ruta)
    temporal = f'{ruta}.tmp'
    with open(temporal, 'wb') as archivo:
        archivo.write(preambulo)
        archivo.write(encabezado)
        archivo.write(bytes(indice))
        for registro in registros:
            archivo.write(registro)
    os.replace(temporal, ruta)

def _leer_preambulo_e_indice(archivo):
    archivo.seek(0)
    magic, version_formato, long_encabezado, num_salas = _PREAMBULO.unpack(archivo.read(_PREAMBULO.size))
    if magic != MAGIC:
        raise ErrorDatos('Archivo de guardado inválido: falta la firma CRPT')
    if version_formato != FORMATO_VERSION:
        raise ErrorDatos(f'Formato de guardado incompatible (versión {version_formato}, se esperaba {FORMATO_VERSION})')
    encabezado = archivo.read(long_encabezado)
    snapshot, _ = _desempacar_encabezado(encabezado, 0)
    indice = {}
    for _ in range(num_salas):
        id_sala, desplazamiento, longitud = _ENTRADA_INDICE.unpack(archivo.read(_ENTRADA_INDICE.size))
        indice[id_sala] = (desplazamiento, longitud)
    return (snapshot, indice)

def cargar_binario(ruta: str) -> dict:
    with open(ruta, 'rb') as archivo:
        snapshot, indice = _leer_preambulo_e_indice(archivo)
        salas = []
        for desplazamiento, longitud in ordenar(list(indice.values()), clave=lambda t: t[0]):
            archivo.seek(desplazamiento)
            crudo, _ = _desempacar_sala(archivo.read(longitud), 0)
            salas.append(crudo)
    snapshot['salas'] = salas
    return snapshot

def leer_sala_binaria(ruta: str, id_sala: int):
    with open(ruta, 'rb') as archivo:
        _, indice = _leer_preambulo_e_indice(archivo)
        if id_sala not in indice:
            return None
        desplazamiento, longitud = indice[id_sala]
        archivo.seek(desplazamiento)
        crudo, _ = _desempacar_sala(archivo.read(longitud), 0)
    return crudo
