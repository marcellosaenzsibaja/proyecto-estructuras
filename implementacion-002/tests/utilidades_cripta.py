"""Criptas pequeñas escritas a mano para los escenarios de aceptación (T003).

Las conexiones se describen como tuplas y se convierten en TEXTO JSON con las
mismas funciones del generador (G1); la cripta se carga con el cargador real a
través de una FuenteMemoria. No se crean diccionarios (T005).
"""
from src.modelos.direcciones import OPUESTA, indice_direccion
from src.servicios.generador_criptas import cargar_cripta_sintetica, fuente_sintetica, texto_llaves, texto_sala


class ConexionIncoherente(ValueError):
    pass


def textos_desde_conexiones(conexiones: list) -> list:
    """Convierte [(id_a, dir, id_b, costo, cerrada, llave), ...] en fragmentos JSON por sala.

    Crea automáticamente la salida opuesta (G2) y falla si una sala repite una
    dirección. costo=None significa que la conexión no declara costo.
    """
    maximo = 0
    for id_a, _, id_b, _, _, _ in conexiones:
        maximo = max(maximo, id_a, id_b)
    # Lista indexada por id; cada sala tiene 4 casillas (N, S, E, O).
    salidas = [None] * (maximo + 1)
    for i in range(1, maximo + 1):
        salidas[i] = [None, None, None, None]
    for id_a, letra, id_b, costo, cerrada, llave in conexiones:
        d = indice_direccion(letra)
        if d is None:
            raise ConexionIncoherente(f'Dirección desconocida {letra!r}')
        o = OPUESTA[d]
        if salidas[id_a][d] is not None:
            raise ConexionIncoherente(f'La sala {id_a} repite la dirección {letra}')
        if salidas[id_b][o] is not None:
            raise ConexionIncoherente(f'La sala {id_b} ya usa la dirección opuesta a {letra}')
        salidas[id_a][d] = (d, id_b, costo, cerrada, llave)
        salidas[id_b][o] = (o, id_a, costo, cerrada, llave)
    textos = []
    for i in range(1, maximo + 1):
        lista = []
        for d in range(4):
            if salidas[i][d] is not None:
                lista.append(salidas[i][d])
        textos.append(texto_sala(i, lista))
    return textos


def conexion(id_a, letra, id_b, costo=None, cerrada=False, llave=None):
    """Atajo para escribir conexiones legibles en las pruebas."""
    if cerrada and llave is None:
        llave = f'itm_llave_{id_a}_{id_b}'
    return (id_a, letra, id_b, costo, cerrada, llave)


def cripta_desde_conexiones(conexiones: list, sala_inicial: int = 1, sala_salida: int = None, **datos):
    """Cripta cargada con el cargador real desde conexiones escritas a mano (G1, G2)."""
    textos = textos_desde_conexiones(conexiones)
    fuente = fuente_sintetica(textos, sala_inicial=sala_inicial, sala_salida=sala_salida, **datos)
    return cargar_cripta_sintetica(fuente)


def cripta_con_llaves(conexiones: list, llaves: list, sala_inicial: int = 1, sala_salida: int = None,
                      llave_salida: str = 'itm_llave_salida_sint', **datos):
    """(cripta, fuente) con la ubicación de llaves [(id, sala) o (id, sala, enemigo), ...] (spec 002)."""
    textos = textos_desde_conexiones(conexiones)
    fuente = fuente_sintetica(textos, sala_inicial=sala_inicial, sala_salida=sala_salida, llave_salida=llave_salida,
                              texto_llaves=texto_llaves(llaves), **datos)
    return cargar_cripta_sintetica(fuente), fuente
