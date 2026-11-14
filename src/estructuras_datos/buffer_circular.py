class BufferCircular:

    def __init__(self, capacidad: int):
        if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
            raise ValueError('La capacidad del buffer debe ser un entero positivo')
        self.capacidad = capacidad
        self._datos = [None] * capacidad
        self._inicio = 0
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    def agregar(self, elemento):
        if self._cantidad < self.capacidad:
            posicion = (self._inicio + self._cantidad) % self.capacidad
            self._cantidad += 1
        else:
            posicion = self._inicio
            self._inicio = (self._inicio + 1) % self.capacidad
        self._datos[posicion] = elemento

    def __iter__(self):
        for i in range(self._cantidad):
            yield self._datos[(self._inicio + i) % self.capacidad]

    def elementos(self) -> list:
        return list(self)
