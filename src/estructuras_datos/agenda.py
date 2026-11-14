class Evento:
    __slots__ = ('tiempo', 'secuencia', 'tipo', 'carga', 'indice', 'cancelado')

    def __init__(self, tiempo: int, secuencia: int, tipo: str, carga=None):
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.tipo = tipo
        self.carga = carga
        self.indice = -1
        self.cancelado = False

    def __lt__(self, otro):
        if self.tiempo == otro.tiempo:
            return self.secuencia < otro.secuencia
        return self.tiempo < otro.tiempo

class Agenda:

    def __init__(self):
        self._elementos = []

    def __len__(self):
        return len(self._elementos)

    def esta_vacio(self) -> bool:
        return not self._elementos

    def minimo(self) -> Evento:
        if not self._elementos:
            raise IndexError('La agenda de eventos está vacía')
        return self._elementos[0]

    def contiene(self, evento: Evento) -> bool:
        i = evento.indice
        return 0 <= i < len(self._elementos) and self._elementos[i] is evento

    def insertar(self, evento: Evento):
        if evento.indice >= 0:
            raise ValueError('El evento ya está programado')
        evento.cancelado = False
        self._elementos.append(evento)
        self._subir_desde(len(self._elementos) - 1, evento)

    def extraer_minimo(self) -> Evento:
        if not self._elementos:
            raise IndexError('La agenda de eventos está vacía')
        raiz = self._elementos[0]
        self._quitar_en(0)
        return raiz

    def cancelar(self, evento: Evento) -> bool:
        if not self.contiene(evento):
            return False
        self._quitar_en(evento.indice)
        evento.cancelado = True
        return True

    def reprogramar(self, evento: Evento, tiempo: int, secuencia: int):
        if not self.contiene(evento):
            raise ValueError('El evento no está programado en esta agenda')
        evento.tiempo = tiempo
        evento.secuencia = secuencia
        self._subir_desde(evento.indice, evento)
        self._bajar_desde(evento.indice, evento)

    def _quitar_en(self, i: int):
        elementos = self._elementos
        quitado = elementos[i]
        ultimo = elementos.pop()
        quitado.indice = -1
        if ultimo is not quitado:
            elementos[i] = ultimo
            self._subir_desde(i, ultimo)
            self._bajar_desde(ultimo.indice, ultimo)

    def _subir_desde(self, i: int, evento: Evento):
        elementos = self._elementos
        while i > 0:
            padre = i - 1 >> 1
            sup = elementos[padre]
            if evento < sup:
                elementos[i] = sup
                sup.indice = i
                i = padre
            else:
                break
        elementos[i] = evento
        evento.indice = i

    def _bajar_desde(self, i: int, evento: Evento):
        elementos = self._elementos
        n = len(elementos)
        while True:
            h = 2 * i + 1
            if h >= n:
                break
            if h + 1 < n and elementos[h + 1] < elementos[h]:
                h += 1
            hijo = elementos[h]
            if hijo < evento:
                elementos[i] = hijo
                hijo.indice = i
                i = h
            else:
                break
        elementos[i] = evento
        evento.indice = i
