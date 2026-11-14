"""Registro de una búsqueda en listas indexadas por Sala.indice (research R2 y R9).

Cada posición solo es válida si su marca coincide con la generación actual.
Empezar una búsqueda nueva incrementa la generación en O(1), sin recorrer ni
limpiar las n posiciones, así que una búsqueda solo toca las salas que examina
(FR-030). No usa diccionarios, conjuntos ni hash (Principio I).
"""


class RegistroBusqueda:

    __slots__ = ('n', 'distancia', 'primer_paso', 'marca', 'marca_asentada', 'generacion', 'examinadas')

    def __init__(self, n: int):
        self.n = n
        self.distancia = [0] * n
        self.primer_paso = [0] * n
        self.marca = [0] * n
        self.marca_asentada = [0] * n
        self.generacion = 0
        self.examinadas = 0

    def nueva_busqueda(self):
        self.generacion += 1
        self.examinadas = 0

    def tiene(self, i: int) -> bool:
        """Hay una distancia tentativa registrada para i en esta generación."""
        return self.marca[i] == self.generacion

    def asentada(self, i: int) -> bool:
        return self.marca_asentada[i] == self.generacion

    def registrar(self, i: int, distancia: int):
        """Registra o mejora la distancia tentativa de i; cuenta i una sola vez (R9)."""
        if self.marca[i] != self.generacion:
            self.marca[i] = self.generacion
            self.examinadas += 1
        self.distancia[i] = distancia

    def asentar(self, i: int):
        self.marca_asentada[i] = self.generacion
