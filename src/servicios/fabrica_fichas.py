from src.modelos.errores import ErrorDatos
from src.modelos.fichas import ANTIDOTO, ANTORCHA, ARMA, ARMADURA, CAZADOR, ERRANTE, GUARDIAN, LLAVE, PERGAMINO, POCION, RASTREADOR, FichaEnemigo, FichaObjeto, FichaTrampa
CLASES_OBJETO = (ARMA, ARMADURA, POCION, ANTIDOTO, LLAVE, ANTORCHA, PERGAMINO)
_ACENTOS = (('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'))

def _normalizar(texto: str) -> str:
    resultado = texto.strip().lower()
    for con, sin in _ACENTOS:
        resultado = resultado.replace(con, sin)
    return resultado

def _comportamiento(texto):
    if isinstance(texto, str):
        normal = _normalizar(texto)
        if normal == 'guardian':
            return GUARDIAN
        if normal == 'errante':
            return ERRANTE
        if normal == 'rastreador':
            return RASTREADOR
        if normal == 'cazador':
            return CAZADOR
    raise ErrorDatos(f'Comportamiento de enemigo desconocido: {texto!r}')

def _entero(datos, campo, minimo=None, obligatorio=True):
    if campo not in datos or datos[campo] is None:
        if obligatorio:
            raise ErrorDatos(f"falta el campo '{campo}'")
        return None
    valor = datos[campo]
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ErrorDatos(f"el campo '{campo}' debe ser entero: {valor!r}")
    if minimo is not None and valor < minimo:
        raise ErrorDatos(f"el campo '{campo}' debe ser al menos {minimo}: {valor}")
    return valor

def _texto(datos, campo):
    valor = datos.get(campo)
    if not isinstance(valor, str) or not valor:
        raise ErrorDatos(f"falta el campo '{campo}'")
    return valor

def dict_desde_ficha(ficha) -> dict:
    base = {'id': ficha.id, 'clase': ficha.clase, 'nombre': ficha.nombre}
    if isinstance(ficha, FichaEnemigo):
        base.update(vida_max=ficha.vida_max, ataque=ficha.ataque, defensa=ficha.defensa, velocidad=ficha.velocidad, comportamiento=ficha.comportamiento, suelta=list(ficha.suelta))
        if ficha.regeneracion is not None:
            base['regeneracion'] = ficha.regeneracion
        if ficha.rango is not None:
            base['rango'] = ficha.rango
        return base
    if isinstance(ficha, FichaTrampa):
        base.update(daño=ficha.dano)
        if ficha.rearme is not None:
            base['rearme'] = ficha.rearme
        return base
    base.update(peso=ficha.peso, valor=ficha.valor)
    if ficha.clase == ARMA:
        base['ataque_bonus'] = ficha.ataque_bonus
    elif ficha.clase == ARMADURA:
        base['defensa_bonus'] = ficha.defensa_bonus
    elif ficha.clase == POCION:
        if ficha.cura is not None:
            base['cura'] = ficha.cura
        if ficha.modificador_velocidad is not None:
            base['modificador_velocidad'] = ficha.modificador_velocidad
            base['duracion'] = ficha.duracion
    elif ficha.clase == ANTORCHA:
        base['duracion'] = ficha.duracion
    return base

def ficha_desde_dict(datos):
    if not isinstance(datos, dict):
        raise ErrorDatos(f'Ficha de catálogo inválida: {datos!r}')
    identificador = datos.get('id', '?')
    try:
        return _construir(datos)
    except ErrorDatos as error:
        raise ErrorDatos(f"Ficha '{identificador}': {error}") from error

def _construir(datos):
    id_ficha = _texto(datos, 'id')
    clase = _texto(datos, 'clase')
    nombre = _texto(datos, 'nombre')
    if clase == 'enemigo':
        suelta = datos.get('suelta') or []
        if not isinstance(suelta, list):
            raise ErrorDatos("el campo 'suelta' debe ser una lista")
        comportamiento = _comportamiento(datos.get('comportamiento'))
        rango = _entero(datos, 'rango', 0) if comportamiento == CAZADOR else None
        return FichaEnemigo(id_ficha, nombre, _entero(datos, 'vida_max', 1), _entero(datos, 'ataque', 0), _entero(datos, 'defensa', 0), _entero(datos, 'velocidad', 1), comportamiento, suelta, _entero(datos, 'regeneracion', 1, obligatorio=False), rango)
    if clase == 'trampa':
        return FichaTrampa(id_ficha, nombre, _entero(datos, 'daño', 0), _entero(datos, 'rearme', 1, obligatorio=False))
    if clase not in CLASES_OBJETO:
        raise ErrorDatos(f'clase desconocida: {clase!r}')
    peso = _entero(datos, 'peso', 0)
    valor = _entero(datos, 'valor', 0)
    ataque_bonus = 0
    defensa_bonus = 0
    cura = None
    modificador = None
    duracion = None
    if clase == ARMA:
        ataque_bonus = _entero(datos, 'ataque_bonus')
    elif clase == ARMADURA:
        defensa_bonus = _entero(datos, 'defensa_bonus')
    elif clase == POCION:
        cura = _entero(datos, 'cura', 0, obligatorio=False)
        modificador = _entero(datos, 'modificador_velocidad', obligatorio=False)
        if cura is None and modificador is None:
            raise ErrorDatos("la poción no declara 'cura' ni 'modificador_velocidad'")
        if modificador is not None:
            duracion = _entero(datos, 'duracion', 1)
    elif clase == ANTORCHA:
        duracion = _entero(datos, 'duracion', 1)
    return FichaObjeto(id_ficha, clase, nombre, peso, valor, ataque_bonus, defensa_bonus, cura, modificador, duracion)
