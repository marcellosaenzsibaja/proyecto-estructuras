ARMA = 'arma'
ARMADURA = 'armadura'
POCION = 'pocion'
ANTIDOTO = 'antidoto'
LLAVE = 'llave'
ANTORCHA = 'antorcha'
PERGAMINO = 'pergamino_retroceso'
GUARDIAN = 'guardian'
ERRANTE = 'errante'
RASTREADOR = 'rastreador'

class Ficha:

    def __init__(self, id_ficha: str, clase: str, nombre: str):
        self.id = id_ficha
        self.clase = clase
        self.nombre = nombre

class FichaEnemigo(Ficha):

    def __init__(self, id_ficha, nombre, vida_max, ataque, defensa, velocidad, comportamiento, suelta=(), regeneracion=None):
        super().__init__(id_ficha, 'enemigo', nombre)
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.comportamiento = comportamiento
        self.suelta = tuple(suelta)
        self.regeneracion = regeneracion

class FichaObjeto(Ficha):

    def __init__(self, id_ficha, clase, nombre, peso, valor, ataque_bonus=0, defensa_bonus=0, cura=None, modificador_velocidad=None, duracion=None):
        super().__init__(id_ficha, clase, nombre)
        self.peso = peso
        self.valor = valor
        self.ataque_bonus = ataque_bonus
        self.defensa_bonus = defensa_bonus
        self.cura = cura
        self.modificador_velocidad = modificador_velocidad
        self.duracion = duracion

class FichaTrampa(Ficha):

    def __init__(self, id_ficha, nombre, dano, rearme=None):
        super().__init__(id_ficha, 'trampa', nombre)
        self.dano = dano
        self.rearme = rearme
