from src.modelos.cripta import Cripta, DatosCripta, EstadisticasJugador
from src.modelos.direcciones import indice_direccion
from src.modelos.entidades import Puerta, Sala, Salida
from src.modelos.errores import ErrorDatos

def _campo(datos, campo, contexto):
    if not isinstance(datos, dict) or campo not in datos:
        raise ErrorDatos(f"{contexto}: falta el campo '{campo}'")
    return datos[campo]

def cargar_datos(fuente, id_cripta: str) -> DatosCripta:
    crudo = fuente.obtener_datos_cripta(id_cripta)
    contexto = f'Datos generales de {id_cripta}'
    jugador = _campo(crudo, 'jugador', contexto)
    return DatosCripta(id_cripta=_campo(crudo, 'id', contexto), version=_campo(crudo, 'version', contexto), salas_total=_campo(crudo, 'salas_total', contexto), sala_inicial=_campo(crudo, 'sala_inicial', contexto), sala_salida=_campo(crudo, 'sala_salida', contexto), llave_salida=_campo(crudo, 'llave_salida', contexto), presupuesto=_campo(crudo, 'presupuesto_solicitudes', contexto), inventario_max=_campo(crudo, 'inventario_max', contexto), jugador=EstadisticasJugador(_campo(jugador, 'vida_max', contexto), _campo(jugador, 'ataque', contexto), _campo(jugador, 'defensa', contexto), _campo(jugador, 'velocidad', contexto)))

def _costo(info, id_sala, letra):
    """Costo de tránsito declarado por una salida (FR-001, FR-008): entero >= 1 o 100 si falta."""
    if 'costo' not in info:
        return 100, False
    valor = info['costo']
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        raise ErrorDatos(f'Sala {id_sala} salida {letra}: costo inválido {valor!r} (debe ser un entero mayor o igual que 1)')
    return valor, True

def _sala_desde_dict(crudo) -> Sala:
    contexto = 'Esqueleto'
    sala = Sala(_campo(crudo, 'id', contexto), crudo.get('nombre') or 'Sala')
    salidas = crudo.get('salidas') or {}
    for letra, info in salidas.items():
        direccion = indice_direccion(letra)
        if direccion is None:
            raise ErrorDatos(f'Sala {sala.id}: dirección desconocida {letra!r}')
        destino = _campo(info, 'sala', f'Sala {sala.id} salida {letra}')
        costo, declarado = _costo(info, sala.id, letra)
        puerta = Puerta(cerrada=bool(info.get('cerrada', False)), llave=info.get('llave'), cierre_automatico=info.get('cierre_automatico'), costo=costo, costo_declarado=declarado)
        sala.salidas[direccion] = Salida(destino, puerta)
    return sala

def cargar_esqueleto(fuente, datos: DatosCripta) -> Cripta:
    cripta = Cripta(datos)
    pagina = 1
    total = 1
    while pagina <= total:
        respuesta = fuente.obtener_esqueleto(datos.id, pagina)
        total = _campo(respuesta, 'total_paginas', f'Esqueleto página {pagina}')
        for crudo in _campo(respuesta, 'salas', f'Esqueleto página {pagina}'):
            cripta.agregar_sala(_sala_desde_dict(crudo))
        pagina += 1
    cripta.enlazar_puertas()
    if not cripta.existe(datos.sala_inicial):
        raise ErrorDatos(f'La sala inicial {datos.sala_inicial} no existe')
    if not cripta.existe(datos.sala_salida):
        raise ErrorDatos(f'La sala de salida {datos.sala_salida} no existe')
    return cripta
