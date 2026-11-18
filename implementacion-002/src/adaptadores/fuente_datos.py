from abc import ABC, abstractmethod

class FuenteDatos(ABC):

    @abstractmethod
    def obtener_criptas(self) -> dict:
        ...

    @abstractmethod
    def obtener_datos_cripta(self, cripta_id: str) -> dict:
        ...

    @abstractmethod
    def obtener_esqueleto(self, cripta_id: str, pagina: int=1) -> dict:
        ...

    @abstractmethod
    def obtener_contenido_lote(self, cripta_id: str, ids_salas: list[int]) -> dict:
        ...

    @abstractmethod
    def obtener_catalogo_lote(self, ids_entidades: list[str]) -> dict:
        ...

    @abstractmethod
    def obtener_version_cripta(self, cripta_id: str) -> dict:
        ...

    @abstractmethod
    def obtener_version_catalogo(self) -> dict:
        ...

    @abstractmethod
    def obtener_llaves(self, cripta_id: str) -> dict:
        ...
