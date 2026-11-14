MOVER = 'mover'
ABRIR = 'abrir'
ATACAR = 'atacar'
ESPERAR = 'esperar'
RECOGER = 'recoger'
USAR = 'usar'
EQUIPAR = 'equipar'
SOLTAR = 'soltar'
ACEPTADA = 'aceptada'
RECHAZADA = 'rechazada'
PENDIENTE = 'pendiente'

class Accion:
    __slots__ = ('tipo', 'argumento')

    def __init__(self, tipo, argumento=None):
        self.tipo = tipo
        self.argumento = argumento

class Resultado:
    __slots__ = ('estado', 'mensaje', 'costo')

    def __init__(self, estado, mensaje='', costo=0):
        self.estado = estado
        self.mensaje = mensaje
        self.costo = costo
