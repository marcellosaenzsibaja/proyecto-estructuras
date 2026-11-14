from src.estructuras_datos.tabla_hash import TablaHash
from src.modelos.contenido import ContenidoSala, ProveedorContenido
from src.modelos.cripta import Cripta, DatosCripta, EstadisticasJugador
from src.modelos.direcciones import OPUESTA, indice_direccion
from src.modelos.entidades import Puerta, Sala, Salida
from src.modelos.fichas import ANTIDOTO, ANTORCHA, ARMA, ARMADURA, LLAVE, PERGAMINO, POCION, FichaEnemigo, FichaObjeto, FichaTrampa
from src.modelos.partida import Partida

class ProveedorMemoria(ProveedorContenido):

    def __init__(self, contenidos, fichas):
        self.contenidos = contenidos
        self.fichas = {f.id: f for f in fichas}
        self.bloqueadas = set()

    def contenido_disponible(self, id_sala):
        return id_sala not in self.bloqueadas

    def obtener_contenido(self, id_sala):
        return self.contenidos.get(id_sala, ContenidoSala())

    def ficha(self, id_ficha):
        return self.fichas[id_ficha]

def enemigo(id_ficha='ent_rata', vida_max=12, ataque=5, defensa=1, velocidad=150, comportamiento='guardian', suelta=(), regeneracion=None, nombre='Rata'):
    return FichaEnemigo(id_ficha, nombre, vida_max, ataque, defensa, velocidad, comportamiento, suelta, regeneracion)

def arma(id_ficha='itm_daga', bonus=3):
    return FichaObjeto(id_ficha, ARMA, 'Daga', 2, 15, ataque_bonus=bonus)

def armadura(id_ficha='itm_cota', bonus=2):
    return FichaObjeto(id_ficha, ARMADURA, 'Cota', 5, 30, defensa_bonus=bonus)

def llave(id_ficha='itm_llave'):
    return FichaObjeto(id_ficha, LLAVE, 'Llave', 1, 1)

def pocion_cura(id_ficha='itm_pocion', cura=10):
    return FichaObjeto(id_ficha, POCION, 'Poción', 1, 5, cura=cura)

def pocion_velocidad(id_ficha='itm_veloz', modificador=50, duracion=1000):
    return FichaObjeto(id_ficha, POCION, 'Poción veloz', 1, 5, modificador_velocidad=modificador, duracion=duracion)

def antidoto(id_ficha='itm_antidoto'):
    return FichaObjeto(id_ficha, ANTIDOTO, 'Antídoto', 1, 5)

def antorcha(id_ficha='itm_antorcha', duracion=2000):
    return FichaObjeto(id_ficha, ANTORCHA, 'Antorcha', 1, 5, duracion=duracion)

def trampa(id_ficha='trp_dardos', dano=4, rearme=300):
    return FichaTrampa(id_ficha, 'Dardos', dano, rearme)

def pergamino(id_ficha='itm_pergamino'):
    return FichaObjeto(id_ficha, PERGAMINO, 'Pergamino de retroceso', 1, 1)

def construir(conexiones, contenidos=None, fichas=(), semilla=1, inicial=1, salida=99, llave_salida='itm_llave', inventario_max=5, vida_max=30, ataque=6, defensa=2, velocidad=100):
    datos = DatosCripta('t', 'v1', 0, inicial, salida, llave_salida, 100, inventario_max, EstadisticasJugador(vida_max, ataque, defensa, velocidad))
    cripta = Cripta(datos)
    ids = {inicial}
    for a, _, b, _ in conexiones:
        ids.add(a)
        ids.add(b)
    for i in sorted(ids):
        cripta.agregar_sala(Sala(i, f'Sala {i}'))
    for a, letra, b, extra in conexiones:
        d = indice_direccion(letra)
        cripta.sala(a).salidas[d] = Salida(b, Puerta(**extra))
        cripta.sala(b).salidas[OPUESTA[d]] = Salida(a, Puerta(**extra))
    cripta.enlazar_puertas()
    proveedor = ProveedorMemoria(contenidos or {}, fichas)
    partida = Partida(cripta, proveedor, semilla)
    return partida
