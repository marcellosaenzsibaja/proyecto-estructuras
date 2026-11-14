from src.estructuras_datos.tabla_hash import TablaHash
from src.modelos.direcciones import LETRAS, OPUESTA
from src.modelos.errores import ErrorDatos

class EstadisticasJugador:

    def __init__(self, vida_max, ataque, defensa, velocidad):
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad

class DatosCripta:

    def __init__(self, id_cripta, version, salas_total, sala_inicial, sala_salida, llave_salida, presupuesto, inventario_max, jugador):
        self.id = id_cripta
        self.version = version
        self.salas_total = salas_total
        self.sala_inicial = sala_inicial
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.presupuesto = presupuesto
        self.inventario_max = inventario_max
        self.jugador = jugador

class Cripta:

    def __init__(self, datos: DatosCripta):
        self.datos = datos
        self._salas = TablaHash()

    def agregar_sala(self, sala):
        if not self._salas.contiene(sala.id):
            sala.indice = len(self._salas)
        self._salas.poner(sala.id, sala)

    def sala(self, id_sala):
        sala = self._salas.obtener(id_sala)
        if sala is None:
            raise ErrorDatos(f'La sala {id_sala} no existe en la cripta')
        return sala

    def existe(self, id_sala) -> bool:
        return self._salas.contiene(id_sala)

    def salas(self):
        return self._salas.valores()

    def __len__(self):
        return len(self._salas)

    def enlazar_puertas(self):
        for sala in self.salas():
            for direccion in range(4):
                salida = sala.salidas[direccion]
                if salida is None:
                    continue
                destino = self.sala(salida.destino)
                salida.sala_destino = destino
                contraria = destino.salidas[OPUESTA[direccion]]
                if contraria is None or contraria.destino != sala.id or contraria.puerta is salida.puerta:
                    continue
                propia, otra = (salida.puerta, contraria.puerta)
                propia.costo = _costo_fusionado(propia, otra, sala.id, direccion, destino.id)
                propia.cerrada = propia.cerrada or otra.cerrada
                if propia.llave is None:
                    propia.llave = otra.llave
                if propia.cierre_automatico is None:
                    propia.cierre_automatico = otra.cierre_automatico
                contraria.puerta = propia


def _costo_fusionado(propia, otra, id_sala, direccion, id_destino) -> int:
    """Costo único de una conexión a partir de lo que declara cada lado (FR-002, research R4).

    Ninguno declara: 100. Uno solo declara: ese valor. Ambos con valores
    distintos: error de datos con las salas y las direcciones.
    """
    if propia.costo_declarado and otra.costo_declarado:
        if propia.costo != otra.costo:
            raise ErrorDatos(f'Costo asimétrico: sala {id_sala} salida {LETRAS[direccion]} declara {propia.costo} '
                             f'y sala {id_destino} salida {LETRAS[OPUESTA[direccion]]} declara {otra.costo}')
        return propia.costo
    if propia.costo_declarado:
        return propia.costo
    if otra.costo_declarado:
        propia.costo_declarado = True
        return otra.costo
    return 100
