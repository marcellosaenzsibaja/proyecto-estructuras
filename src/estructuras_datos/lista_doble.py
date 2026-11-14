class NodoLista:
    __slots__ = ('valor', 'anterior', 'siguiente', 'lista')

    def __init__(self, valor):
        self.valor = valor
        self.anterior = None
        self.siguiente = None
        self.lista = None

class ListaDoble:

    def __init__(self):
        self.cabeza = None
        self.cola = None
        self._tamano = 0

    def __len__(self):
        return self._tamano

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def agregar_al_final(self, valor) -> NodoLista:
        nodo = NodoLista(valor)
        self._enlazar_al_final(nodo)
        return nodo

    def agregar_al_frente(self, valor) -> NodoLista:
        nodo = NodoLista(valor)
        self._enlazar_al_frente(nodo)
        return nodo

    def remover_nodo(self, nodo: NodoLista):
        self._verificar(nodo)
        self._desenlazar(nodo)
        return nodo.valor

    def mover_al_frente(self, nodo: NodoLista):
        self._verificar(nodo)
        if nodo is self.cabeza:
            return
        self._desenlazar(nodo)
        self._enlazar_al_frente(nodo)

    def insertar_despues(self, referencia, nodo: NodoLista):
        nodo.lista = self
        if referencia is None:
            nodo.anterior = None
            nodo.siguiente = self.cabeza
            if self.cabeza is None:
                self.cola = nodo
            else:
                self.cabeza.anterior = nodo
            self.cabeza = nodo
        else:
            self._verificar(referencia)
            nodo.anterior = referencia
            nodo.siguiente = referencia.siguiente
            if referencia.siguiente is None:
                self.cola = nodo
            else:
                referencia.siguiente.anterior = nodo
            referencia.siguiente = nodo
        self._tamano += 1

    def nodos(self):
        actual = self.cabeza
        while actual is not None:
            yield actual
            actual = actual.siguiente

    def nodos_inversos(self):
        actual = self.cola
        while actual is not None:
            yield actual
            actual = actual.anterior

    def __iter__(self):
        for nodo in self.nodos():
            yield nodo.valor

    def _verificar(self, nodo):
        if nodo.lista is not self:
            raise ValueError('El nodo no pertenece a esta lista')

    def _enlazar_al_final(self, nodo):
        nodo.lista = self
        nodo.siguiente = None
        nodo.anterior = self.cola
        if self.cola is None:
            self.cabeza = nodo
        else:
            self.cola.siguiente = nodo
        self.cola = nodo
        self._tamano += 1

    def _enlazar_al_frente(self, nodo):
        nodo.lista = self
        nodo.anterior = None
        nodo.siguiente = self.cabeza
        if self.cabeza is None:
            self.cola = nodo
        else:
            self.cabeza.anterior = nodo
        self.cabeza = nodo
        self._tamano += 1

    def _desenlazar(self, nodo):
        if nodo.anterior is None:
            self.cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente
        if nodo.siguiente is None:
            self.cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior
        nodo.anterior = None
        nodo.siguiente = None
        nodo.lista = None
        self._tamano -= 1
