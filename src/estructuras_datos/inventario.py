from src.estructuras_datos.lista_doble import ListaDoble

class InventarioLleno(Exception):
    pass

class Inventario:

    def __init__(self, capacidad: int):
        if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
            raise ValueError('La capacidad del inventario debe ser un entero positivo')
        self.capacidad = capacidad
        self._lista = ListaDoble()
        self._cursor = None

    def __len__(self):
        return len(self._lista)

    def esta_vacio(self) -> bool:
        return self._lista.esta_vacia()

    def esta_lleno(self) -> bool:
        return len(self._lista) >= self.capacidad

    def agregar(self, objeto):
        if self.esta_lleno():
            raise InventarioLleno('El inventario está lleno')
        nodo = self._lista.agregar_al_final(objeto)
        if self._cursor is None:
            self._cursor = nodo
        return nodo

    def nodo_actual(self):
        return self._cursor

    def actual(self):
        if self._cursor is None:
            return None
        return self._cursor.valor

    def avanzar(self) -> bool:
        if self._cursor is None or self._cursor.siguiente is None:
            return False
        self._cursor = self._cursor.siguiente
        return True

    def retroceder(self) -> bool:
        if self._cursor is None or self._cursor.anterior is None:
            return False
        self._cursor = self._cursor.anterior
        return True

    def ir_al_inicio(self):
        self._cursor = self._lista.cabeza

    def soltar_actual(self):
        if self._cursor is None:
            return None
        return self.remover_nodo(self._cursor)

    def remover_nodo(self, nodo):
        if self._cursor is nodo:
            self._cursor = nodo.siguiente or nodo.anterior
        return self._lista.remover_nodo(nodo)

    def mover_al_frente(self, nodo):
        self._lista.mover_al_frente(nodo)

    def insertar_despues(self, referencia, nodo):
        self._lista.insertar_despues(referencia, nodo)

    def fijar_cursor(self, nodo):
        self._cursor = nodo

    def mover_actual_al_frente(self):
        if self._cursor is not None:
            self._lista.mover_al_frente(self._cursor)

    def __iter__(self):
        return iter(self._lista)

    def nodos(self):
        return self._lista.nodos()
