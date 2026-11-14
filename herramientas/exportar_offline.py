import argparse
import json
import os
import sys
from src.adaptadores.api_client import ApiClient
from src.adaptadores.errores import ErrorCliente
TAMANO_LOTE = 10

def _guardar(ruta, datos):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)

def _referencias_de(sala) -> list:
    referencias = [e['tipo'] for e in sala.get('enemigos') or []]
    referencias += list(sala.get('objetos') or [])
    referencias += [t['tipo'] for t in sala.get('trampas') or []]
    return referencias

def exportar(cliente: ApiClient, cripta_id: str, salida: str):
    base = os.path.join(salida, cripta_id)
    datos = cliente.obtener_datos_cripta(cripta_id)
    _guardar(os.path.join(base, 'datos_generales.json'), datos)
    _guardar(os.path.join(salida, cripta_id, 'version.json'), cliente.obtener_version_cripta(cripta_id))
    ids_salas = []
    pagina = 1
    total = 1
    while pagina <= total:
        esqueleto = cliente.obtener_esqueleto(cripta_id, pagina)
        _guardar(os.path.join(base, 'esqueleto', f'pagina_{pagina}.json'), esqueleto)
        total = esqueleto['total_paginas']
        ids_salas += [s['id'] for s in esqueleto['salas']]
        pagina += 1
    ids_catalogo = []
    for inicio in range(0, len(ids_salas), TAMANO_LOTE):
        lote = ids_salas[inicio:inicio + TAMANO_LOTE]
        respuesta = cliente.obtener_contenido_lote(cripta_id, lote)
        for crudo in respuesta['contenido']:
            _guardar(os.path.join(base, 'salas', f"{crudo['sala']}.json"), crudo)
            for referencia in _referencias_de(crudo):
                if referencia not in ids_catalogo:
                    ids_catalogo.append(referencia)
    for inicio in range(0, len(ids_catalogo), TAMANO_LOTE):
        lote = ids_catalogo[inicio:inicio + TAMANO_LOTE]
        respuesta = cliente.obtener_catalogo_lote(lote)
        for ficha in respuesta['entidades']:
            _guardar(os.path.join(salida, 'catalogo', 'entidades', f"{ficha['id']}.json"), ficha)
    _guardar(os.path.join(salida, 'catalogo', 'version.json'), cliente.obtener_version_catalogo())
    return (len(ids_salas), len(ids_catalogo))

def _actualizar_indice_criptas(cliente: ApiClient, salida: str, cripta_id: str):
    ruta = os.path.join(salida, 'criptas.json')
    indice = {'criptas': []}
    if os.path.isfile(ruta):
        with open(ruta, 'r', encoding='utf-8') as archivo:
            indice = json.load(archivo)
    conocidos = {c['id'] for c in indice['criptas']}
    if cripta_id not in conocidos:
        for c in cliente.obtener_criptas()['criptas']:
            if c['id'] == cripta_id:
                indice['criptas'].append(c)
                break
        else:
            indice['criptas'].append({'id': cripta_id})
    _guardar(ruta, indice)

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Exporta una cripta completa para jugarla luego con --offline')
    parser.add_argument('--cripta', required=True)
    parser.add_argument('--salida', default='datos_offline')
    args = parser.parse_args(argv)
    cliente = ApiClient()
    try:
        _actualizar_indice_criptas(cliente, args.salida, args.cripta)
        salas, entidades = exportar(cliente, args.cripta, args.salida)
    except ErrorCliente as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    print(f"Exportadas {salas} salas y {entidades} fichas de catálogo de '{args.cripta}' a '{args.salida}' ({cliente.solicitudes_realizadas} solicitudes de {cliente.presupuesto})")
    return 0
if __name__ == '__main__':
    sys.exit(main())
