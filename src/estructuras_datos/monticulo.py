"""Montículo binario de mínimos con eliminación perezosa (research R1).

Almacena pares (costo, indice) en una lista organizada como montículo binario
(hijo izquierdo 2i+1, derecho 2i+2, padre (i-1)//2) y los compara como tupla:
menor costo y, si empatan, menor índice (D3), de modo que la ejecución es
repetible.

Eliminación perezosa: el montículo no ofrece «disminuir clave» y no sabe nada
de salas. Cuando la búsqueda encuentra un costo menor para una sala, inserta
una entrada nueva y deja la anterior. Al extraer, el consumidor descarta como
obsoleta toda entrada cuya sala ya esté asentada o cuyo costo no coincida con
la distancia registrada. Así no hace falta llevar la posición de cada sala
dentro del montículo, a cambio de hasta 4 entradas por sala (una por salida):
el tamaño nunca supera 1 + 4 · salas asentadas, es decir, crece con la región
examinada y no con la cripta.
"""


class MonticuloMin:

    __slots__ = ('_elementos',)

    def __init__(self):
        self._elementos = []

    def __len__(self):
        return len(self._elementos)

    def esta_vacio(self) -> bool:
        return not self._elementos

    def vaciar(self):
        self._elementos.clear()

    def minimo(self):
        """Devuelve el par mínimo sin extraerlo, O(1)."""
        if not self._elementos:
            raise IndexError('El montículo está vacío')
        return self._elementos[0]

    def insertar(self, costo: int, indice: int):
        """Agrega al final y sube, O(log k)."""
        elementos = self._elementos
        par = (costo, indice)
        elementos.append(par)
        i = len(elementos) - 1
        while i > 0:
            padre = (i - 1) >> 1
            superior = elementos[padre]
            if par < superior:
                elementos[i] = superior
                i = padre
            else:
                break
        elementos[i] = par

    def extraer_minimo(self):
        """Quita la raíz, pone el último en su lugar y baja, O(log k)."""
        elementos = self._elementos
        if not elementos:
            raise IndexError('El montículo está vacío')
        raiz = elementos[0]
        ultimo = elementos.pop()
        if elementos:
            n = len(elementos)
            i = 0
            while True:
                hijo = 2 * i + 1
                if hijo >= n:
                    break
                if hijo + 1 < n and elementos[hijo + 1] < elementos[hijo]:
                    hijo += 1
                if elementos[hijo] < ultimo:
                    elementos[i] = elementos[hijo]
                    i = hijo
                else:
                    break
            elementos[i] = ultimo
        return raiz
