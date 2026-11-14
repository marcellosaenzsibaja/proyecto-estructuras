from src.estructuras_datos.inventario import Inventario

class Objeto:
    __slots__ = ('uid', 'ficha')

    def __init__(self, uid, ficha):
        self.uid = uid
        self.ficha = ficha

class Trampa:
    __slots__ = ('instancia', 'ficha', 'armada', 'evento_rearme')

    def __init__(self, instancia, ficha):
        self.instancia = instancia
        self.ficha = ficha
        self.armada = True
        self.evento_rearme = None

class Puerta:
    __slots__ = ('cerrada', 'llave', 'cierre_automatico', 'evento_cierre', 'abierta_por_jugador')

    def __init__(self, cerrada=False, llave=None, cierre_automatico=None):
        self.cerrada = cerrada
        self.llave = llave
        self.cierre_automatico = cierre_automatico
        self.evento_cierre = None
        self.abierta_por_jugador = False

class Salida:
    __slots__ = ('destino', 'puerta')

    def __init__(self, destino, puerta):
        self.destino = destino
        self.puerta = puerta

class Sala:

    def __init__(self, id_sala: int, nombre: str):
        self.id = id_sala
        self.nombre = nombre
        self.salidas = [None, None, None, None]
        self.enemigos = []
        self.dormidos = []
        self.objetos = []
        self.trampas = []
        self.rastro = None
        self.contenido_incorporado = False

class Efecto:
    __slots__ = ('tipo', 'objetivo', 'valor', 'fin', 'evento')

    def __init__(self, tipo, objetivo, valor=0, fin=None):
        self.tipo = tipo
        self.objetivo = objetivo
        self.valor = valor
        self.fin = fin
        self.evento = None

class Actor:

    def __init__(self, id_actor, nombre, vida_max, ataque, defensa, velocidad, vida=None):
        self.id_actor = id_actor
        self.nombre = nombre
        self.vida_max = vida_max
        self.vida = vida_max if vida is None else max(0, min(vida, vida_max))
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.sala_id = None
        self.evento = None

    @property
    def tiempo_siguiente(self):
        return None if self.evento is None else self.evento.tiempo

    @property
    def vivo(self):
        return self.vida > 0

class Enemigo(Actor):

    def __init__(self, instancia, ficha, vida=None):
        super().__init__(instancia, ficha.nombre, ficha.vida_max, ficha.ataque, ficha.defensa, ficha.velocidad, vida)
        self.ficha = ficha
        self.activo = False
        self.regeneracion = None

    @property
    def comportamiento(self):
        return self.ficha.comportamiento

class Jugador(Actor):

    def __init__(self, vida_max, ataque, defensa, velocidad, inventario_max):
        super().__init__('jugador', 'Jugador', vida_max, ataque, defensa, velocidad)
        self.velocidad_base = velocidad
        self.inventario = Inventario(inventario_max)
        self.arma = None
        self.armadura = None
        self.veneno = None
        self.efecto_velocidad = None
        self.antorcha = None

    @property
    def ataque_total(self):
        bonus = self.arma.ficha.ataque_bonus if self.arma is not None else 0
        return self.ataque + bonus

    @property
    def defensa_total(self):
        bonus = self.armadura.ficha.defensa_bonus if self.armadura is not None else 0
        return self.defensa + bonus
