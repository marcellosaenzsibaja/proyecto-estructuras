from abc import ABC, abstractmethod

class ContenidoSala:

    def __init__(self, enemigos=(), objetos=(), trampas=()):
        self.enemigos = list(enemigos)
        self.objetos = list(objetos)
        self.trampas = list(trampas)

class ProveedorContenido(ABC):

    def asegurar_disponible(self, id_sala: int) -> None:
        return None

    @abstractmethod
    def contenido_disponible(self, id_sala: int) -> bool:
        ...

    @abstractmethod
    def obtener_contenido(self, id_sala: int) -> ContenidoSala:
        ...

    @abstractmethod
    def ficha(self, id_ficha: str):
        ...

    def fijar(self, id_ficha: str) -> None:
        return None

    def liberar(self, id_ficha: str) -> None:
        return None
