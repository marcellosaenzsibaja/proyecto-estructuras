"""Búsqueda acotada de costo mínimo para el cazador (research R5, R9; tasks T036, T037).

Usa estructuras propias: MonticuloMin con eliminación perezosa para escoger la
sala pendiente más barata y RegistroBusqueda (listas indexadas por Sala.indice
con marca de generación) para distancias, primer paso y salas asentadas. No
usa diccionarios, conjuntos ni bibliotecas de grafos (Principio I).

Solo mira el esqueleto y el estado actual de las puertas: no conoce la niebla
de guerra ni el contenido de las salas (FR-017).
"""
from src.estructuras_datos.monticulo import MonticuloMin
from src.estructuras_datos.registro_busqueda import RegistroBusqueda


class BuscadorRutas:

    def __init__(self, cripta):
        n = len(cripta)
        self.registro = RegistroBusqueda(n)
        self.monticulo = MonticuloMin()
        self.salas = [None] * n
        for sala in cripta.salas():
            self.salas[sala.indice] = sala
        self.origen = None
        self.cota_alcanzada = -1

    # -- búsqueda compartida con pausa (T036) ---------------------------------

    def distancias_desde(self, sala_origen, cota: int):
        """Inicia una búsqueda desde sala_origen y la expande hasta cota (queda en pausa)."""
        registro = self.registro
        registro.nueva_busqueda()
        self.monticulo.vaciar()
        self.origen = sala_origen
        self.cota_alcanzada = -1
        registro.registrar(sala_origen.indice, 0)
        self.monticulo.insertar(0, sala_origen.indice)
        self.extender_hasta(cota)

    def extender_hasta(self, cota: int):
        """Retoma la misma búsqueda hasta cota si es mayor que la alcanzada (research R5).

        Pausar cuando el mínimo supera la cota no pierde información: las
        entradas pendientes (incluido el borde, con costo mayor que la cota)
        siguen en el montículo y las distancias asentadas son definitivas.
        """
        if cota <= self.cota_alcanzada:
            return
        registro = self.registro
        monticulo = self.monticulo
        salas = self.salas
        distancia = registro.distancia
        while not monticulo.esta_vacio():
            c, i = monticulo.minimo()
            if c > cota:
                break
            monticulo.extraer_minimo()
            if registro.asentada(i) or c != distancia[i]:
                continue  # entrada obsoleta (eliminación perezosa, T010)
            registro.asentar(i)
            salidas = salas[i].salidas
            for direccion in range(4):  # orden N, S, E, O (D2)
                salida = salidas[direccion]
                if salida is None or salida.puerta.cerrada:
                    continue
                vecina = salida.sala_destino.indice
                if registro.asentada(vecina):
                    continue
                nc = c + salida.puerta.costo
                if not registro.tiene(vecina) or nc < distancia[vecina]:
                    registro.registrar(vecina, nc)
                    monticulo.insertar(nc, vecina)  # aunque nc > cota: forma el borde
        self.cota_alcanzada = cota

    def distancia(self, sala):
        """Distancia exacta (asentada) de sala al origen, o None si no está asentada."""
        i = sala.indice
        if self.registro.asentada(i):
            return self.registro.distancia[i]
        return None

    @property
    def examinadas(self) -> int:
        return self.registro.examinadas

    # -- modo individual con primer paso (T037) -------------------------------

    def primer_paso_desde(self, origen, objetivo, cota: int):
        """Busca desde origen hasta objetivo con cota; devuelve (d, id_vecina) o None.

        id_vecina es la vecina de menor id entre las que inician una ruta de
        costo mínimo (FR-014): cada sala guarda el menor primer paso entre todos
        sus caminos mínimos. Como todo costo es >= 1, todas las mejoras y
        empates de una sala llegan antes de que se asiente.
        """
        registro = self.registro
        monticulo = self.monticulo
        salas = self.salas
        distancia = registro.distancia
        primer_paso = registro.primer_paso
        registro.nueva_busqueda()
        monticulo.vaciar()
        self.origen = None  # la búsqueda compartida deja de ser válida
        self.cota_alcanzada = -1
        if origen is objetivo:
            return (0, None)
        registro.registrar(origen.indice, 0)
        monticulo.insertar(0, origen.indice)
        objetivo_i = objetivo.indice
        origen_i = origen.indice
        while not monticulo.esta_vacio():
            c, i = monticulo.minimo()
            if c > cota:
                return None
            monticulo.extraer_minimo()
            if registro.asentada(i) or c != distancia[i]:
                continue
            registro.asentar(i)
            if i == objetivo_i:
                return (c, primer_paso[i])
            salidas = salas[i].salidas
            for direccion in range(4):
                salida = salidas[direccion]
                if salida is None or salida.puerta.cerrada:
                    continue
                vecina_sala = salida.sala_destino
                vecina = vecina_sala.indice
                if registro.asentada(vecina):
                    continue
                etiqueta = vecina_sala.id if i == origen_i else primer_paso[i]
                nc = c + salida.puerta.costo
                if not registro.tiene(vecina) or nc < distancia[vecina]:
                    registro.registrar(vecina, nc)
                    primer_paso[vecina] = etiqueta
                    monticulo.insertar(nc, vecina)
                elif nc == distancia[vecina] and etiqueta < primer_paso[vecina]:
                    primer_paso[vecina] = etiqueta
        return None
