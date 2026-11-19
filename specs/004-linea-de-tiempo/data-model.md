# Data Model: Línea de tiempo y puntos de control

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Las referencias `RN` remiten a [research.md](research.md).

## Estructuras nuevas (estado del juego)

### EntradaLinea (`src/modelos/linea_tiempo.py`) — R5

El registro de un paso de la historia. Es la información mínima de FR-023.

| Campo | Tipo | Propósito |
| --- | --- | --- |
| `numero` | entero | número de acción del jugador; 0 para un registro de cursor |
| `tiempo` | entero | instante del reloj en que se tomó |
| `tipo` | cadena | tipo de acción, o `cursor_sig` / `cursor_ant` |
| `argumento` | entero, cadena o `None` | argumento de la acción |

Los registros de cursor llevan `numero = 0` porque no son acciones del jugador: no consumen tiempo,
no incrementan el contador y no generan punto de control, pero se re-aplican en su posición al
re-simular (R5).

### PuntoControl (`src/modelos/linea_tiempo.py`) — R1, R2

Una copia completa del estado. Es caché de consulta, no historia: no se guarda en el archivo (R2).

| Campo | Tipo | Propósito |
| --- | --- | --- |
| `numero` | entero | número de acciones del jugador ya tomadas en ese instante |
| `tiempo` | entero | instante del reloj |
| `indice_entrada` | entero | posición en la lista de entradas desde la que hay que re-aplicar |
| `snapshot` | el dict de `guardado.tomar_snapshot` | el estado completo |
| `estado_azar` | la tupla de `random.Random.getstate()` | FR-025 |

### LineaTiempo (`src/modelos/linea_tiempo.py`) — R1 a R5, R9

| Campo | Tipo | Propósito |
| --- | --- | --- |
| `k` | entero ≥ 1 | acciones del jugador entre puntos de control (FR-020, FR-021) |
| `entradas` | lista de `EntradaLinea`, en orden creciente | la historia (FR-013) |
| `puntos` | lista de `PuntoControl`, en orden creciente de `tiempo` | la caché (FR-020) |
| `tiempos_punto` | lista de enteros paralela a `puntos` | claves de la búsqueda binaria (R3) |
| `acciones` | entero | acciones del jugador registradas |
| `reaplicadas` | entero | conteo de la última consulta, para SC-004 (R9) |

**Invariantes**:

- `tiempos_punto[i] == puntos[i].tiempo` y la lista es no decreciente, porque el reloj nunca
  retrocede durante el juego normal.
- `puntos` siempre contiene el punto del instante 0, tomado en `iniciar` (R6), así que la búsqueda
  del punto anterior a cualquier instante consultable nunca queda vacía.
- Entre dos puntos de control consecutivos hay a lo sumo `k` entradas con `numero > 0` (FR-020,
  SC-005).
- `entradas` describe la historia tal como quedó: un retroceso quita entradas del final (FR-013).

**Operaciones**:

| Operación | Costo | Requisito |
| --- | --- | --- |
| `registrar_accion(numero, tiempo, tipo, argumento)` | O(1) amortizado | FR-023 |
| `registrar_cursor(tiempo, tipo)` | O(1) amortizado | R5 |
| `tomar_punto(partida)` | O(tamaño del estado), una vez cada `k` acciones | FR-020, FR-025 |
| `punto_en_o_antes(t)` | O(log puntos) | FR-026, R3 |
| `recortar(numero, tiempo)` | O(entradas y puntos quitados) | FR-015, R4 |
| `entradas_hasta(t)`, `entradas_antes_de_accion(k)` | O(log puntos + acciones re-aplicadas) | FR-022 |
| `tiempo_maximo()` | O(1) | FR-008 |

`punto_en_o_antes` usa `ultimo_menor_o_igual` de `src/estructuras_datos/busqueda_binaria.py` sobre
`tiempos_punto`. No se usa `bisect` (FR-027).

## Estructura nueva en una estructura existente

### `ultimo_menor_o_igual` (`src/estructuras_datos/busqueda_binaria.py`) — R3

```
ultimo_menor_o_igual(lista_ordenada, valor) -> int
```

Devuelve la última posición cuyo valor es menor o igual que `valor`, o `-1` si ninguna lo es.
Complejidad O(log n), sin `bisect`. Convive con `buscar`, que resuelve la pregunta distinta de la
coincidencia exacta y no se modifica (R3).

## Módulos nuevos (infraestructura de consulta)

### `reconstruir` y `consultar` (`src/modelos/linea_tiempo.py`) — R1, R6

| Operación | Qué hace | Requisito |
| --- | --- | --- |
| `reconstruir_en(partida, t)` | restaura el punto de control anterior a `t` en una partida nueva y re-aplica las entradas hasta `t` | FR-001, FR-002, FR-022 |
| `reconstruir_antes_de(partida, k)` | lo mismo, hasta justo antes de la acción `k` | FR-003 |

La partida reconstruida se construye sin bitácora, sin puntajes y con la línea de tiempo en modo
inerte: no toma puntos de control propios y no registra entradas (R6). Se descarta al terminar la
consulta, así que la partida en curso no se toca (FR-007, SC-008).

### ResumenHistoria (`src/modelos/resumen_historia.py`) — R7

Construye los campos de FR-006 como datos, sin imprimir.

| Campo | Contenido |
| --- | --- |
| `tiempo` | reloj del instante consultado |
| `accion_numero` | número de acción del jugador correspondiente |
| `sala_id`, `sala_nombre` | sala del jugador |
| `vida`, `vida_max`, `ataque`, `defensa`, `velocidad` | vida y estadísticas |
| `inventario` | nombres de los objetos, en el orden del inventario, con el seleccionado marcado |
| `efectos` | efectos activos con su valor y su instante de fin |
| `enemigos` | enemigos de esa sala con su nombre, instancia y vida |
| `mapa` | salas exploradas y avistadas en ese instante (capacidad 003) |
| `estado` | en curso, victoria o derrota |
| `trunco` | cierto si la partida terminó antes del instante pedido (FR-018) |

La vista formatea estos campos para `historia`; `--hasta` usa el mismo formateador sin instanciar la
vista (FR-017).

## Entidades modificadas

### Partida (`src/modelos/partida.py`) — R6

| Campo o método | Cambio | Requisito |
| --- | --- | --- |
| `linea` | campo nuevo: la `LineaTiempo` de esta partida | FR-004 |
| `registra_linea` | campo nuevo: falso en una partida reconstruida para una consulta | FR-007 |
| `iniciar` | toma el punto de control del instante 0 | R6 |
| `_cerrar_accion` | registra la entrada de la acción y, si toca por K, toma el punto de control | FR-020, FR-023 |
| `_usar_pergamino` | recorta la línea de tiempo al nuevo número de acción y reloj | FR-013, FR-015 |
| `mover_cursor(sentido)` | método nuevo: mueve el cursor del inventario y lo registra | R5 |
| `historia_en(t)`, `historia_antes_de(k)` | métodos nuevos: validan y devuelven el resumen | FR-005, FR-008, FR-009 |

`_cerrar_accion` es el único punto por el que pasan todas las acciones del jugador, así que es donde
se engancha el registro y no hay forma de que una acción quede fuera de la historia.

### Inventario y el cursor (`src/estructuras_datos/inventario.py`) — R5

Sin cambios en la estructura. Lo que cambia es quién llama a `avanzar` y `retroceder`: hasta ahora el
controlador los llamaba directamente, y ahora pasa por `Partida.mover_cursor`, para que el movimiento
quede registrado en la línea de tiempo y en la bitácora.

### Bitacora (`src/servicios/bitacora.py`) — R5, R8

| Cambio | Requisito |
| --- | --- |
| registra los movimientos de cursor como registros propios | R5 |
| `reproducir` acepta un instante límite y devuelve la partida al llegar a él | FR-017, FR-018 |
| `reproducir` aplica los movimientos de cursor sin contarlos como acciones | R5 |

### Guardado (`src/servicios/guardado.py`) — R8

| Cambio | Requisito |
| --- | --- |
| `FORMATO_VERSION` sube de 2 a 3, compartido con la capacidad 003 | FR-029 |
| `tomar_snapshot` agrega la sección `linea` con las entradas en orden | FR-028 |
| `restaurar_partida` reconstruye la `LineaTiempo` desde esa sección | FR-028 |

`tomar_snapshot` se usa para dos cosas distintas: el archivo de partida y los puntos de control en
memoria. La sección `linea` se omite al tomar un punto de control, porque un punto de control no
necesita contener la historia que lo contiene.

### ControladorJuego y VistaConsola

| Cambio | Requisito |
| --- | --- |
| comando `historia <t>` / `historia #k`, que no consume tiempo ni se registra como acción | FR-005, FR-007 |
| `sig` y `ant` pasan por `Partida.mover_cursor` | R5 |
| `mostrar_resumen_historia`: formatea los campos de `ResumenHistoria` | FR-006 |

### main.py

| Cambio | Requisito |
| --- | --- |
| `--checkpoint-cada K`, con el valor por defecto del grupo y rechazo de K < 1 | FR-021 |
| `--hasta <t>`, válido solo junto con `--replay`, imprime el resumen sin instanciar la vista | FR-017, FR-018 |

## Transiciones relevantes

**Vida de una entrada**:

```
acción del jugador --registrar--> entrada al final de la lista
                                      |
                                      +-- cada K acciones --> punto de control
pergamino ----------recortar--------> entradas y puntos del final descartados
```

**Resolución de una consulta de `t`** (FR-001, FR-022, FR-026):

```
validar 0 <= t <= reloj actual
  -> ultimo_menor_o_igual(tiempos_punto, t)      O(log puntos)
  -> restaurar ese snapshot y su estado de azar en una partida nueva
  -> re-aplicar las entradas con tiempo <= t      a lo sumo K acciones
  -> construir el resumen
  -> descartar la partida reconstruida
```

**Elección entre `#k` y `t`**: `#k` busca el punto de control con `numero <= k-1` y re-aplica hasta
la entrada `k-1`; `t` busca por instante. Las dos recorren el mismo camino y difieren solo en la
clave de búsqueda y en la condición de parada.
