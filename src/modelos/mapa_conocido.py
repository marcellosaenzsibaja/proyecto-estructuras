from src.estructuras_datos.ordenamiento import ordenar
from src.modelos.direcciones import OPUESTA

DESCONOCIDA = 0
AVISTADA = 1
EXPLORADA = 2

SIN_OBSERVAR = 0
RECORDADA_ABIERTA = 1
RECORDADA_CERRADA = 2

NOMBRE_ESTADO = ('desconocida', 'avistada', 'explorada')
NOMBRE_PUERTA = ('sin observar', 'abierta', 'cerrada')


class MapaConocido:

    __slots__ = ('n', 'estado', 'puertas', 'exploradas', 'salas_tocadas', 'puertas_tocadas')

    def __init__(self, n: int):
        self.n = n
        self.estado = [DESCONOCIDA] * n
        self.puertas = [SIN_OBSERVAR] * (4 * n)
        self.exploradas = []
        self.salas_tocadas = 0
        self.puertas_tocadas = 0

    def estado_de(self, sala) -> int:
        return self.estado[sala.indice]

    def explorada(self, sala) -> bool:
        return self.estado[sala.indice] == EXPLORADA

    def avistada(self, sala) -> bool:
        return self.estado[sala.indice] == AVISTADA

    def conocida(self, sala) -> bool:
        return self.estado[sala.indice] != DESCONOCIDA

    def puerta_recordada(self, sala, direccion: int) -> int:
        return self.puertas[sala.indice * 4 + direccion]

    def recordada_abierta(self, sala, direccion: int) -> bool:
        return self.puertas[sala.indice * 4 + direccion] == RECORDADA_ABIERTA

    def _fijar_estado(self, sala, valor: int, registrar) -> bool:
        i = sala.indice
        anterior = self.estado[i]
        if anterior >= valor:
            return False
        self.estado[i] = valor
        self.salas_tocadas += 1
        if valor == EXPLORADA:
            self.exploradas.append(sala.id)

            def deshacer():
                self.estado[i] = anterior
                self.exploradas.pop()
        else:

            def deshacer():
                self.estado[i] = anterior
        if registrar is not None:
            registrar(deshacer)
        return True

    def avistar(self, sala, registrar=None) -> bool:
        return self._fijar_estado(sala, AVISTADA, registrar)

    def explorar(self, sala, registrar=None) -> bool:
        if not self._fijar_estado(sala, EXPLORADA, registrar):
            return False
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None:
                continue
            vecina = salida.sala_destino
            if vecina is not None and vecina is not sala:
                self.avistar(vecina, registrar)
        return True

    def _fijar_puerta(self, sala, direccion: int, valor: int, registrar):
        p = sala.indice * 4 + direccion
        anterior = self.puertas[p]
        if anterior == valor:
            return
        self.puertas[p] = valor
        self.puertas_tocadas += 1

        def deshacer():
            self.puertas[p] = anterior
        if registrar is not None:
            registrar(deshacer)

    def observar_puerta(self, sala, direccion: int, cerrada: bool, registrar=None):
        valor = RECORDADA_CERRADA if cerrada else RECORDADA_ABIERTA
        self._fijar_puerta(sala, direccion, valor, registrar)
        salida = sala.salidas[direccion]
        if salida is None:
            return
        vecina = salida.sala_destino
        if vecina is None or vecina is sala:
            return
        contraria = vecina.salidas[OPUESTA[direccion]]
        if contraria is not None and contraria.puerta is salida.puerta:
            self._fijar_puerta(vecina, OPUESTA[direccion], valor, registrar)

    def observar_puertas(self, sala, registrar=None):
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None:
                continue
            self.observar_puerta(sala, direccion, salida.puerta.cerrada, registrar)

    def reiniciar_conteos(self):
        self.salas_tocadas = 0
        self.puertas_tocadas = 0

    def salas_exploradas(self):
        return list(self.exploradas)

    def avistadas_de(self, sala):
        ids = []
        for direccion in range(4):
            salida = sala.salidas[direccion]
            if salida is None:
                continue
            vecina = salida.sala_destino
            if vecina is not None and self.estado[vecina.indice] == AVISTADA:
                ids.append(vecina.id)
        return ids

    def ids_avistadas(self, cripta):
        ids = []
        for sala in cripta.salas():
            if self.estado[sala.indice] == AVISTADA:
                ids.append(sala.id)
        return ordenar(ids)

    def total_exploradas(self) -> int:
        return len(self.exploradas)

    def total_avistadas(self) -> int:
        total = 0
        for valor in self.estado:
            if valor == AVISTADA:
                total += 1
        return total

    def volcar(self, cripta):
        filas = []
        for id_sala in self.exploradas:
            sala = cripta.sala(id_sala)
            i = sala.indice
            filas.append((id_sala, EXPLORADA, self.puertas[i * 4:i * 4 + 4]))
        for sala in cripta.salas():
            if self.estado[sala.indice] == AVISTADA:
                i = sala.indice
                filas.append((sala.id, AVISTADA, self.puertas[i * 4:i * 4 + 4]))
        return filas

    def cargar(self, cripta, filas):
        self.estado = [DESCONOCIDA] * self.n
        self.puertas = [SIN_OBSERVAR] * (4 * self.n)
        self.exploradas = []
        for id_sala, estado, puertas in filas:
            sala = cripta.sala(id_sala)
            i = sala.indice
            self.estado[i] = estado
            for direccion in range(4):
                self.puertas[i * 4 + direccion] = puertas[direccion]
            if estado == EXPLORADA:
                self.exploradas.append(id_sala)
