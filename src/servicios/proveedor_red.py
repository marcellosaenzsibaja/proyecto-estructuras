from src.estructuras_datos.tabla_hash import TablaHash
from src.modelos.contenido import ContenidoSala, ProveedorContenido
from src.modelos.errores import ErrorDatos
from src.modelos.fichas import FichaEnemigo, FichaObjeto, FichaTrampa
from src.servicios.fabrica_fichas import ficha_desde_dict
TAMANO_LOTE = 10

def _campo(datos, campo, contexto):
    if not isinstance(datos, dict) or campo not in datos:
        raise ErrorDatos(f"{contexto}: falta el campo '{campo}'")
    return datos[campo]

class ProveedorRed(ProveedorContenido):

    def __init__(self, fuente, cripta, cache_fichas):
        self._fuente = fuente
        self._cripta = cripta
        self._cache = cache_fichas
        self._contenidos = TablaHash()
        self._solicitadas = TablaHash()

    def contenido_disponible(self, id_sala: int) -> bool:
        return self._contenidos.contiene(id_sala)

    def asegurar_disponible(self, id_sala: int) -> None:
        if self._contenidos.contiene(id_sala):
            return
        lote = self._construir_lote(id_sala)
        self._cargar_lote(lote)

    def obtener_contenido(self, id_sala: int) -> ContenidoSala:
        contenido = self._contenidos.obtener(id_sala)
        if contenido is None:
            raise ErrorDatos(f'No hay contenido cargado para la sala {id_sala}')
        return contenido

    def _construir_lote(self, id_sala) -> list:
        lote = [id_sala]
        self._solicitadas.poner(id_sala, True)
        visitadas = TablaHash()
        visitadas.poner(id_sala, True)
        frontera = [id_sala]
        indice = 0
        while len(lote) < TAMANO_LOTE and indice < len(frontera):
            actual = self._cripta.sala(frontera[indice])
            indice += 1
            for direccion in range(4):
                salida = actual.salidas[direccion]
                if salida is None or salida.puerta.cerrada:
                    continue
                vecina = salida.destino
                if visitadas.contiene(vecina):
                    continue
                visitadas.poner(vecina, True)
                frontera.append(vecina)
                ya_pedida = self._solicitadas.contiene(vecina) or self._contenidos.contiene(vecina)
                if not ya_pedida:
                    lote.append(vecina)
                    self._solicitadas.poner(vecina, True)
                    if len(lote) >= TAMANO_LOTE:
                        break
        return lote

    def _cargar_lote(self, ids_salas: list):
        respuesta = self._fuente.obtener_contenido_lote(self._cripta.datos.id, ids_salas)
        crudos = _campo(respuesta, 'contenido', 'Contenido de salas')
        ids_catalogo = []
        vistos = TablaHash()
        for crudo in crudos:
            for enemigo in crudo.get('enemigos') or []:
                self._anotar(vistos, ids_catalogo, enemigo.get('tipo'))
            for id_objeto in crudo.get('objetos') or []:
                self._anotar(vistos, ids_catalogo, id_objeto)
            for trampa in crudo.get('trampas') or []:
                self._anotar(vistos, ids_catalogo, trampa.get('tipo'))
        resueltas = self._resolver_catalogo(ids_catalogo)
        for crudo in crudos:
            self._contenidos.poner(crudo['sala'], self._construir_contenido(crudo, resueltas))

    def _anotar(self, vistos, lista, id_ficha):
        if not isinstance(id_ficha, str):
            raise ErrorDatos(f'Referencia de catálogo inválida: {id_ficha!r}')
        if not vistos.contiene(id_ficha):
            vistos.poner(id_ficha, True)
            lista.append(id_ficha)

    def _resolver_catalogo(self, ids) -> TablaHash:
        resultado = TablaHash()
        faltantes = []
        vistos = TablaHash()
        for id_ficha in ids:
            ficha = self._cache.obtener(id_ficha)
            if ficha is not None:
                resultado.poner(id_ficha, ficha)
                continue
            if not vistos.contiene(id_ficha):
                vistos.poner(id_ficha, True)
                faltantes.append(id_ficha)
        for inicio in range(0, len(faltantes), TAMANO_LOTE):
            lote = faltantes[inicio:inicio + TAMANO_LOTE]
            respuesta = self._fuente.obtener_catalogo_lote(lote)
            for crudo in _campo(respuesta, 'entidades', 'Catálogo'):
                ficha = ficha_desde_dict(crudo)
                self._cache.poner(ficha.id, ficha)
                resultado.poner(ficha.id, ficha)
            for id_ficha in lote:
                if not resultado.contiene(id_ficha):
                    raise ErrorDatos(f"El catálogo no devolvió la ficha '{id_ficha}'")
        return resultado

    def _ficha_de(self, resueltas, id_ficha, tipo_esperado, contexto):
        ficha = resueltas.obtener(id_ficha)
        if not isinstance(ficha, tipo_esperado):
            raise ErrorDatos(f"{contexto}: '{id_ficha}' no es del tipo esperado")
        return ficha

    def _construir_contenido(self, crudo, resueltas) -> ContenidoSala:
        contexto = f"Contenido de la sala {crudo['sala']}"
        enemigos = []
        for e in crudo.get('enemigos') or []:
            ficha = self._ficha_de(resueltas, e['tipo'], FichaEnemigo, contexto)
            enemigos.append((e['instancia'], ficha, e.get('vida')))
        objetos = [self._ficha_de(resueltas, i, FichaObjeto, contexto) for i in crudo.get('objetos') or []]
        trampas = []
        for t in crudo.get('trampas') or []:
            ficha = self._ficha_de(resueltas, t['tipo'], FichaTrampa, contexto)
            trampas.append((t['instancia'], ficha))
        return ContenidoSala(enemigos, objetos, trampas)

    def ficha(self, id_ficha: str):
        ficha = self._cache.obtener(id_ficha)
        if ficha is not None:
            return ficha
        respuesta = self._fuente.obtener_catalogo_lote([id_ficha])
        entidades = _campo(respuesta, 'entidades', 'Catálogo')
        for crudo in entidades:
            candidata = ficha_desde_dict(crudo)
            self._cache.poner(candidata.id, candidata)
            if candidata.id == id_ficha:
                ficha = candidata
        if ficha is None:
            raise ErrorDatos(f"El catálogo no devolvió la ficha '{id_ficha}'")
        return ficha

    def fijar(self, id_ficha: str) -> None:
        self._cache.fijar(id_ficha)

    def liberar(self, id_ficha: str) -> None:
        self._cache.liberar(id_ficha)
