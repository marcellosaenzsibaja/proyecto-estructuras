NORTE, SUR, ESTE, OESTE = (0, 1, 2, 3)
LETRAS = ('N', 'S', 'E', 'O')
OPUESTA = (SUR, NORTE, OESTE, ESTE)

def indice_direccion(texto):
    if isinstance(texto, str):
        limpio = texto.strip().upper()
        for i in range(4):
            if LETRAS[i] == limpio:
                return i
    return None
