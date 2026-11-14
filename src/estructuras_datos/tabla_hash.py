MASCARA_64 = 18446744073709551615
BASE_FNV = 14695981039346656037
PRIMO_FNV = 1099511628211
CAPACIDAD_INICIAL = 16

def _mezclar(x):
    x ^= x >> 33
    x = x * 18397679294719823053 & MASCARA_64
    x ^= x >> 33
    x = x * 14181476777654086739 & MASCARA_64
    x ^= x >> 33
    return x

def codigo_hash(clave):
    if type(clave) is int:
        return _mezclar(clave & MASCARA_64)
    if type(clave) is str:
        h = BASE_FNV
        for octeto in clave.encode('utf-8'):
            h = (h ^ octeto) * PRIMO_FNV & MASCARA_64
        return _mezclar(h)
    raise TypeError(f'Clave no soportada: {type(clave).__name__}')

class TablaHash:

    def __init__(self, capacidad_inicial: int=CAPACIDAD_INICIAL):
        capacidad = 1
        while capacidad < capacidad_inicial:
            capacidad <<= 1
        self._cubetas = [None] * capacidad
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    def _localizar(self, clave, codigo):
        cubeta = self._cubetas[codigo & len(self._cubetas) - 1]
        if cubeta is None:
            return (None, -1)
        for i in range(len(cubeta)):
            entrada = cubeta[i]
            if entrada[0] == codigo and entrada[1] == clave:
                return (cubeta, i)
        return (cubeta, -1)

    def _agregar(self, entrada):
        posicion = entrada[0] & len(self._cubetas) - 1
        cubeta = self._cubetas[posicion]
        if cubeta is None:
            self._cubetas[posicion] = [entrada]
        else:
            cubeta.append(entrada)

    def _crecer(self):
        anteriores = self._cubetas
        self._cubetas = [None] * (len(anteriores) * 2)
        for cubeta in anteriores:
            if cubeta is not None:
                for entrada in cubeta:
                    self._agregar(entrada)

    def poner(self, clave, valor):
        codigo = codigo_hash(clave)
        cubeta, i = self._localizar(clave, codigo)
        if i >= 0:
            cubeta[i][2] = valor
            return
        if (self._cantidad + 1) * 4 > len(self._cubetas) * 3:
            self._crecer()
        self._agregar([codigo, clave, valor])
        self._cantidad += 1

    def obtener(self, clave, defecto=None):
        cubeta, i = self._localizar(clave, codigo_hash(clave))
        if i < 0:
            return defecto
        return cubeta[i][2]

    def contiene(self, clave) -> bool:
        return self._localizar(clave, codigo_hash(clave))[1] >= 0

    def eliminar(self, clave):
        cubeta, i = self._localizar(clave, codigo_hash(clave))
        if i < 0:
            raise KeyError(clave)
        valor = cubeta[i][2]
        del cubeta[i]
        self._cantidad -= 1
        return valor

    def __contains__(self, clave):
        return self.contiene(clave)

    def __getitem__(self, clave):
        cubeta, i = self._localizar(clave, codigo_hash(clave))
        if i < 0:
            raise KeyError(clave)
        return cubeta[i][2]

    def __setitem__(self, clave, valor):
        self.poner(clave, valor)

    def __delitem__(self, clave):
        self.eliminar(clave)

    def items(self):
        for cubeta in self._cubetas:
            if cubeta is not None:
                for entrada in cubeta:
                    yield (entrada[1], entrada[2])

    def claves(self):
        for clave, _ in self.items():
            yield clave

    def valores(self):
        for _, valor in self.items():
            yield valor

    def __iter__(self):
        return self.claves()
