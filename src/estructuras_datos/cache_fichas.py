from src.estructuras_datos.lista_doble import ListaDoble
from src.estructuras_datos.tabla_hash import TablaHash
CAPACIDAD_POR_DEFECTO = 25

class CacheFichas:

    def __init__(self, capacidad: int=CAPACIDAD_POR_DEFECTO):
        if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
            raise ValueError('La capacidad de la caché debe ser un entero positivo')
        self.capacidad = capacidad
        self._indice = TablaHash()
        self._orden = ListaDoble()
        self._referencias = TablaHash()
        self.aciertos = 0
        self.fallos = 0
        self.desalojos = 0

    def __len__(self):
        return len(self._indice)

    def __contains__(self, id_ficha):
        return self._indice.contiene(id_ficha)

    def obtener(self, id_ficha):
        nodo = self._indice.obtener(id_ficha)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        self._orden.mover_al_frente(nodo)
        return nodo.valor[1]

    def poner(self, id_ficha, ficha):
        nodo = self._indice.obtener(id_ficha)
        if nodo is not None:
            nodo.valor = (id_ficha, ficha)
            self._orden.mover_al_frente(nodo)
            return
        nuevo = self._orden.agregar_al_frente((id_ficha, ficha))
        self._indice.poner(id_ficha, nuevo)
        self._desalojar_si_hace_falta()

    def fijar(self, id_ficha):
        actuales = self._referencias.obtener(id_ficha, 0)
        self._referencias.poner(id_ficha, actuales + 1)

    def liberar(self, id_ficha):
        actuales = self._referencias.obtener(id_ficha, 0)
        if actuales <= 1:
            if id_ficha in self._referencias:
                self._referencias.eliminar(id_ficha)
        else:
            self._referencias.poner(id_ficha, actuales - 1)

    def en_uso(self, id_ficha) -> bool:
        return self._referencias.obtener(id_ficha, 0) > 0

    def entradas_en_orden_de_uso(self):
        for nodo in self._orden.nodos():
            yield nodo.valor

    def _desalojar_si_hace_falta(self):
        while len(self._indice) > self.capacidad:
            candidato = self._buscar_desalojable()
            if candidato is None:
                break
            id_ficha, nodo = candidato
            self._orden.remover_nodo(nodo)
            self._indice.eliminar(id_ficha)
            self.desalojos += 1

    def _buscar_desalojable(self):
        for nodo in self._orden.nodos_inversos():
            id_ficha, _ = nodo.valor
            if not self.en_uso(id_ficha):
                return (id_ficha, nodo)
        return None
