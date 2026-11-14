import argparse
import json
import os
import sys
from src.adaptadores.api_client import ApiClient
from src.adaptadores.errores import ErrorCliente
TAMANO_LOTE = 10
MAXIMO_LOTES_CATALOGO = 2

def guardar(carpeta, nombre, datos):
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    return ruta

def identificadores(contenido):
    vistos = []
    for sala in contenido['contenido']:
        referencias = [e['tipo'] for e in sala.get('enemigos') or []]
        referencias += list(sala.get('objetos') or [])
        referencias += [t['tipo'] for t in sala.get('trampas') or []]
        for referencia in referencias:
            if referencia not in vistos:
                vistos.append(referencia)
    return vistos

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Guarda una muestra de respuestas de la API')
    parser.add_argument('--cripta', required=True)
    parser.add_argument('--salida', default='muestra_api')
    args = parser.parse_args(argv)
    os.makedirs(args.salida, exist_ok=True)
    cliente = ApiClient()
    try:
        datos = cliente.obtener_datos_cripta(args.cripta)
        guardar(args.salida, 'datos_generales.json', datos)
        esqueleto = cliente.obtener_esqueleto(args.cripta, 1)
        guardar(args.salida, 'esqueleto_pagina_1.json', esqueleto)
        salas = [s['id'] for s in esqueleto['salas']][:TAMANO_LOTE]
        contenido = cliente.obtener_contenido_lote(args.cripta, salas)
        guardar(args.salida, 'contenido_primeras_salas.json', contenido)
        ids = identificadores(contenido)
        entidades = []
        for lote in range(MAXIMO_LOTES_CATALOGO):
            grupo = ids[lote * TAMANO_LOTE:(lote + 1) * TAMANO_LOTE]
            if not grupo:
                break
            entidades += cliente.obtener_catalogo_lote(grupo)['entidades']
        guardar(args.salida, 'catalogo.json', {'entidades': entidades})
    except ErrorCliente as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    print(f"Muestra guardada en '{args.salida}' ({cliente.solicitudes_realizadas} solicitudes de {cliente.presupuesto})")
    return 0
if __name__ == '__main__':
    sys.exit(main())
