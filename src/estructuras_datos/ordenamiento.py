UMBRAL_TAMANO = 24
UMBRAL_DESORDEN = 0.15

def _clave(clave, elemento):
    return elemento if clave is None else clave(elemento)

def insercion(lista, clave=None):
    resultado = list(lista)
    for i in range(1, len(resultado)):
        actual = resultado[i]
        clave_actual = _clave(clave, actual)
        j = i - 1
        while j >= 0 and _clave(clave, resultado[j]) > clave_actual:
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = actual
    return resultado

def mezcla(lista, clave=None):
    n = len(lista)
    if n <= 1:
        return list(lista)
    mitad = n // 2
    izquierda = mezcla(lista[:mitad], clave)
    derecha = mezcla(lista[mitad:], clave)
    return _combinar(izquierda, derecha, clave)

def _combinar(izquierda, derecha, clave):
    combinado = []
    i = j = 0
    while i < len(izquierda) and j < len(derecha):
        if _clave(clave, izquierda[i]) <= _clave(clave, derecha[j]):
            combinado.append(izquierda[i])
            i += 1
        else:
            combinado.append(derecha[j])
            j += 1
    combinado.extend(izquierda[i:])
    combinado.extend(derecha[j:])
    return combinado

def _proporcion_de_desorden(lista, clave) -> float:
    n = len(lista)
    if n < 2:
        return 0.0
    desordenados = 0
    anterior = _clave(clave, lista[0])
    for i in range(1, n):
        actual = _clave(clave, lista[i])
        if actual < anterior:
            desordenados += 1
        anterior = actual
    return desordenados / (n - 1)

def ordenar(lista, clave=None):
    if len(lista) <= UMBRAL_TAMANO:
        return insercion(lista, clave)
    if _proporcion_de_desorden(lista, clave) <= UMBRAL_DESORDEN:
        return insercion(lista, clave)
    return mezcla(lista, clave)
