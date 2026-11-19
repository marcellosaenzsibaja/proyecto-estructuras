import unicodedata
from src.estructuras_datos.monticulo import MonticuloMin
from src.estructuras_datos.registro_busqueda import RegistroBusqueda
from src.modelos.acciones import ACEPTADA, Accion, MOVER
from src.modelos.mapa_conocido import EXPLORADA, RECORDADA_ABIERTA

LLEGADA = 'llegada'
ENEMIGOS = 'enemigos'
DANO = 'dano'
SIN_RUTA = 'sin_ruta'
FIN_PARTIDA = 'fin_partida'


class Viaje:

    __slots__ = ('destino', 'motivo', 'pasos')

    def __init__(self, destino: int):
        self.destino = destino
        self.motivo = SIN_RUTA
        self.pasos = 0


class BuscadorConocido:

    def __init__(self, cripta, mapa):
        n = len(cripta)
        self.registro = RegistroBusqueda(n)
        self.monticulo = MonticuloMin()
        self.salas = [None] * n
        for sala in cripta.salas():
            self.salas[sala.indice] = sala
        self.mapa = mapa

    def _transitable(self, sala, direccion):
        if not self.mapa.recordada_abierta(sala, direccion):
            return None
        salida = sala.salidas[direccion]
        if salida is None:
            return None
        vecina = salida.sala_destino
        if vecina is None or self.mapa.estado_de(vecina) != EXPLORADA:
            return None
        return (vecina, salida.puerta.costo)

    def primer_paso(self, origen, objetivo):
        if origen is objetivo:
            return (0, None)
        if self.mapa.estado_de(origen) != EXPLORADA or self.mapa.estado_de(objetivo) != EXPLORADA:
            return None
        registro = self.registro
        monticulo = self.monticulo
        salas = self.salas
        distancia = registro.distancia
        primer_paso = registro.primer_paso
        marca = registro.marca
        marca_asentada = registro.marca_asentada
        estado_salas = self.mapa.estado
        puertas_recordadas = self.mapa.puertas
        insertar = monticulo.insertar
        registro.nueva_busqueda()
        monticulo.vaciar()
        generacion = registro.generacion
        objetivo_i = objetivo.indice
        origen_i = origen.indice
        registro.registrar(origen_i, 0)
        insertar(0, origen_i)
        while not monticulo.esta_vacio():
            costo, i = monticulo.minimo()
            monticulo.extraer_minimo()
            if marca_asentada[i] == generacion or costo != distancia[i]:
                continue
            marca_asentada[i] = generacion
            if i == objetivo_i:
                return (costo, primer_paso[i])
            sala = salas[i]
            salidas = sala.salidas
            base = i * 4
            etiqueta_heredada = primer_paso[i]
            for direccion in range(4):
                if puertas_recordadas[base + direccion] != RECORDADA_ABIERTA:
                    continue
                salida = salidas[direccion]
                vecina_sala = salida.sala_destino
                vecina = vecina_sala.indice
                if estado_salas[vecina] != EXPLORADA or marca_asentada[vecina] == generacion:
                    continue
                etiqueta = vecina_sala.id if i == origen_i else etiqueta_heredada
                nuevo = costo + salida.puerta.costo
                if marca[vecina] != generacion:
                    marca[vecina] = generacion
                    registro.examinadas += 1
                    distancia[vecina] = nuevo
                    primer_paso[vecina] = etiqueta
                    insertar(nuevo, vecina)
                elif nuevo < distancia[vecina]:
                    distancia[vecina] = nuevo
                    primer_paso[vecina] = etiqueta
                    insertar(nuevo, vecina)
                elif nuevo == distancia[vecina] and etiqueta < primer_paso[vecina]:
                    primer_paso[vecina] = etiqueta
        return None

    def direccion_hacia(self, sala, id_vecina: int):
        mejor_direccion = None
        mejor_costo = None
        for direccion in range(4):
            paso = self._transitable(sala, direccion)
            if paso is None:
                continue
            vecina_sala, costo_salida = paso
            if vecina_sala.id != id_vecina:
                continue
            if mejor_costo is None or costo_salida < mejor_costo:
                mejor_costo = costo_salida
                mejor_direccion = direccion
        return mejor_direccion

    @property
    def examinadas(self) -> int:
        return self.registro.examinadas


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize('NFD', texto)
    letras = [c for c in sin_tildes if unicodedata.category(c) != 'Mn']
    return ''.join(letras).strip().lower()


def resolver_destino(partida, texto):
    if texto is None:
        return (None, 'No hay ninguna sala conocida con ese nombre o id.')
    limpio = texto.strip()
    if not limpio:
        return (None, 'No hay ninguna sala conocida con ese nombre o id.')
    if limpio.lstrip('-').isdigit():
        id_sala = int(limpio)
        if not partida.cripta.existe(id_sala):
            return (None, 'No hay ninguna sala conocida con ese nombre o id.')
        sala = partida.cripta.sala(id_sala)
        if not partida.mapa.explorada(sala):
            return (None, 'No conoces esa sala todavía.')
        return (id_sala, None)
    buscado = normalizar(limpio)
    encontradas = []
    for id_sala in partida.mapa.salas_exploradas():
        sala = partida.cripta.sala(id_sala)
        if normalizar(sala.nombre) == buscado:
            encontradas.append(id_sala)
    if not encontradas:
        return (None, 'No hay ninguna sala conocida con ese nombre o id.')
    if len(encontradas) > 1:
        lista = ', '.join(str(i) for i in encontradas)
        return (None, f'Hay varias salas conocidas con ese nombre; usa el id ({lista}).')
    return (encontradas[0], None)


def validar_destino(partida, id_sala):
    if id_sala == partida.jugador.sala_id:
        return 'Ya estás en esa sala.'
    if partida.siguiente_paso_viaje(id_sala) is None:
        return 'No conoces ninguna ruta hasta esa sala.'
    return None


def ejecutar_viaje(partida, id_destino: int, antes_de_paso=None) -> Viaje:
    from src.modelos.partida import EN_CURSO
    viaje = Viaje(id_destino)
    while True:
        if partida.estado != EN_CURSO:
            viaje.motivo = FIN_PARTIDA
            return viaje
        direccion = partida.siguiente_paso_viaje(id_destino)
        if direccion is None:
            viaje.motivo = SIN_RUTA
            return viaje
        vida_antes = partida.jugador.vida
        accion = Accion(MOVER, direccion)
        if antes_de_paso is not None:
            antes_de_paso(accion)
        resultado = partida.ejecutar(accion)
        if resultado.estado != ACEPTADA:
            viaje.motivo = SIN_RUTA
            return viaje
        viaje.pasos += 1
        if partida.estado != EN_CURSO:
            viaje.motivo = FIN_PARTIDA
            return viaje
        if partida.jugador.sala_id == id_destino:
            viaje.motivo = LLEGADA
            return viaje
        if partida.jugador.vida < vida_antes:
            viaje.motivo = DANO
            return viaje
        sala = partida.sala_actual
        if sala.enemigos or sala.dormidos:
            viaje.motivo = ENEMIGOS
            return viaje


def mensaje_fin(partida, viaje: Viaje) -> str:
    sala = partida.cripta.sala(partida.jugador.sala_id)
    if viaje.motivo == LLEGADA:
        return f'Llegas a {sala.nombre} ({viaje.pasos} pasos).'
    if viaje.motivo == ENEMIGOS:
        return f'El viaje se detiene en {sala.nombre}: hay enemigos en la sala ({viaje.pasos} pasos).'
    if viaje.motivo == DANO:
        return f'El viaje se detiene en {sala.nombre}: has recibido daño ({viaje.pasos} pasos).'
    if viaje.motivo == SIN_RUTA:
        return (f'El viaje se detiene en {sala.nombre}: ya no conoces una ruta hasta el destino '
                f'({viaje.pasos} pasos).')
    return ''
