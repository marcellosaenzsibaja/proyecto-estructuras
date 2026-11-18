def buscar(lista_ordenada, valor, clave=None) -> int:
    bajo = 0
    alto = len(lista_ordenada) - 1
    while bajo <= alto:
        medio = (bajo + alto) >> 1
        elemento = lista_ordenada[medio]
        actual = elemento if clave is None else clave(elemento)
        if actual == valor:
            return medio
        if actual < valor:
            bajo = medio + 1
        else:
            alto = medio - 1
    return -1
