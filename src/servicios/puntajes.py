import json
import os
import time
from src.estructuras_datos.ordenamiento import ordenar
RUTA_POR_DEFECTO = 'puntajes.json'

def calcular_puntaje(partida) -> int:
    base = partida.enemigos_derrotados * 100
    penalizacion = partida.reloj.tiempo_virtual // 10
    bono = 500 if partida.estado == 'victoria' else 0
    return max(0, base + bono - penalizacion)

def cargar(ruta: str=RUTA_POR_DEFECTO) -> list:
    if not os.path.isfile(ruta):
        return []
    with open(ruta, 'r', encoding='utf-8') as archivo:
        return json.load(archivo)

def registrar(partida, ruta: str=RUTA_POR_DEFECTO) -> dict:
    entrada = {'cripta_id': partida.cripta.datos.id, 'semilla': partida.semilla, 'resultado': partida.estado, 'acciones': partida.acciones_jugador, 'enemigos_derrotados': partida.enemigos_derrotados, 'tiempo_virtual': partida.reloj.tiempo_virtual, 'puntaje': calcular_puntaje(partida), 'fecha': time.strftime('%Y-%m-%d %H:%M:%S')}
    tabla = cargar(ruta)
    tabla.append(entrada)
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    temporal = f'{ruta}.tmp'
    with open(temporal, 'w', encoding='utf-8') as archivo:
        json.dump(tabla, archivo, ensure_ascii=False, indent=2)
    os.replace(temporal, ruta)
    return entrada

def mejores(ruta: str=RUTA_POR_DEFECTO, cantidad: int=10) -> list:
    tabla = ordenar(cargar(ruta), clave=lambda entrada: -entrada['puntaje'])
    return tabla[:cantidad]
