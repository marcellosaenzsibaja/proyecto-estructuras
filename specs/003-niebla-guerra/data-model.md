# Data Model: Niebla de guerra y viaje automático «ir a»

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Las referencias `RN` remiten a [research.md](research.md). Los requisitos se citan como `FR-NNN`
dentro de esta capacidad (003).

## Estructuras nuevas (estado del juego)

### MapaConocido (`src/modelos/mapa_conocido.py`) — R1, R2, R3

El conocimiento del jugador. Es estado del juego: se guarda, se revierte y forma parte de la línea
de tiempo (FR-022). Vive aparte de la `Cripta` para no mezclarlo con el mapa descargado (FR-021).

| Campo | Tipo | Propósito |
| --- | --- | --- |
| `n` | entero | cantidad de salas de la cripta |
| `estado` | lista de enteros, tamaño `n`, indexada por `Sala.indice` | `DESCONOCIDA` (0), `AVISTADA` (1) o `EXPLORADA` (2) — R1 |
| `puertas` | lista de enteros, tamaño `4n`, indexada por `indice * 4 + direccion` | `SIN_OBSERVAR` (0), `RECORDADA_ABIERTA` (1) o `RECORDADA_CERRADA` (2) — R2 |
| `exploradas` | lista de ids de sala, en orden de exploración | recorrer el mapa conocido sin recorrer la cripta — R3 |
| `salas_tocadas` | entero | conteo de la última exploración, para SC-004 — R10 |
| `puertas_tocadas` | entero | conteo de la última exploración, para SC-004 — R10 |

**Invariantes**:

- `estado[i]` nunca disminuye durante el juego normal; solo una reversión lo baja (FR-003).
- `exploradas` contiene exactamente los ids de las salas con `estado == EXPLORADA`, en el orden en
  que se exploraron.
- Una posición de `puertas` solo es distinta de `SIN_OBSERVAR` si el jugador estuvo en la sala de ese
  lado (FR-011, FR-017).
- El tamaño de las tres listas no cambia después de construir el objeto: una exploración solo escribe
  posiciones existentes y agrega al final de `exploradas` (FR-051).

**Operaciones**:

| Operación | Costo | Requisito |
| --- | --- | --- |
| `estado_de(sala)` | O(1) | FR-050 |
| `explorada(sala)`, `avistada(sala)` | O(1) | FR-050 |
| `puerta_recordada(sala, direccion)` | O(1) | FR-050 |
| `recordada_abierta(sala, direccion)` | O(1) | FR-030 |
| `explorar(sala, registrar)` | O(1) más sus 4 salidas | FR-003, FR-007, FR-051 |
| `avistar(sala, registrar)` | O(1) | FR-005 |
| `observar_puertas(sala, registrar)` | O(1): sus 4 salidas | FR-008, FR-009, FR-012 |
| `observar_puerta(sala, direccion, cerrada, registrar)` | O(1) | FR-013 |
| `salas_exploradas()` | O(exploradas) | FR-024 |
| `avistadas_de(sala)` | O(1): sus 4 salidas | FR-024 |

`registrar` es la función de la partida que acumula una reversión en el intervalo de la acción en
curso (P1 §4.6). Cada operación que cambia una posición registra su valor anterior, y solo si lo
cambia (R8, FR-048, FR-052). Ninguna operación del mapa conocido mira el estado real de una puerta
por su cuenta: la observación recibe el estado real como argumento, de modo que el único punto del
programa que lee la realidad para escribir el conocimiento es la partida.

**Por qué no se usa `TablaHash` ni un conjunto**: el índice compacto `Sala.indice` que P1 asigna al
cargar da acceso por posición sin hash, y las consultas son el camino caliente de la vista y del
viaje (R1). Las estructuras de conveniencia del lenguaje están prohibidas por el Principio I, y una
tabla hash propia costaría más que una indexación directa sin dar nada a cambio.

### Viaje (`src/modelos/viaje.py`) — R5, R6, R7

El estado de una orden `ir a` en curso. No es estado persistente de la partida (R9): existe mientras
el viaje se ejecuta y desaparece al terminar.

| Campo | Tipo | Propósito |
| --- | --- | --- |
| `destino` | entero | id de la sala explorada a la que se viaja |
| `motivo` | cadena | `LLEGADA`, `ENEMIGOS`, `DANO`, `SIN_RUTA` o `FIN_PARTIDA` (FR-042) |
| `pasos` | entero | pasos efectivamente dados, para el mensaje final |

### BuscadorConocido (`src/modelos/viaje.py`) — R4, R5

Búsqueda de costo mínimo sobre el subgrafo conocido. Comparte las estructuras auxiliares de la
capacidad 001 (`MonticuloMin` y `RegistroBusqueda`) y no comparte el recorrido, por las razones de
R4.

| Operación | Costo | Requisito |
| --- | --- | --- |
| `primer_paso(origen, destino)` | O((salas conocidas + salidas conocidas) log salas conocidas) | FR-030 a FR-033, FR-053 |

Solo expande salas con `estado == EXPLORADA` y solo atraviesa salidas con
`puerta_recordada == RECORDADA_ABIERTA`. Nunca lee `Puerta.cerrada` (FR-021). El desempate por menor
id del primer paso es el mismo de 001 FR-014, con la misma técnica de etiquetar cada sala con el
menor primer paso de sus caminos mínimos.

## Entidades modificadas

### Partida (`src/modelos/partida.py`)

| Campo o método | Cambio | Requisito |
| --- | --- | --- |
| `mapa` | campo nuevo: el `MapaConocido` de esta partida, creado en el constructor | FR-022 |
| `iniciar` | explora la sala inicial y observa sus puertas | FR-002 |
| `_mover` | al llegar, observa las puertas de la sala destino y la explora; si la antorcha está encendida, explora sus vecinas | FR-003, FR-012, FR-014 |
| `_abrir` | registra la puerta como recordada abierta | FR-013 |
| `siguiente_paso_viaje` | método nuevo: dirección del siguiente paso hacia un destino, o `None` | FR-030 a FR-033 |
| `ruta_conocida_existe` | método nuevo: si hay ruta conocida al destino | FR-029, FR-039 |
| `destino_valido` | método nuevo: si un id de sala es un destino aceptable | FR-029 |
| `resolver_destino` | método nuevo: id o nombre a id de sala explorada, o un rechazo | FR-028 |

El orden dentro de `_mover` importa: primero se observan las puertas de la sala a la que se llegó y
se explora, y solo después se activan enemigos y trampas. Así el recálculo de la ruta del paso
siguiente parte del conocimiento ya corregido (FR-012), y una parada por enemigos o por daño ocurre
con el mapa al día.

### Jugador (`src/modelos/entidades.py`)

Sin cambios. La antorcha ya es un efecto del jugador (`Jugador.antorcha`) desde P1; esta capacidad
solo le da consecuencias sobre el mapa (FR-014) y no cambia su representación ni su duración.

### ServicioViaje (`src/modelos/viaje.py`) — R7

El servicio que el controlador usa para ejecutar un viaje. Pide a la partida el siguiente paso,
ejecuta ese paso como una acción de mover ordinaria a través del mismo camino que un movimiento
manual, y evalúa las condiciones de parada.

| Operación | Propósito | Requisito |
| --- | --- | --- |
| `iniciar(destino)` | valida el destino y rechaza sin consumir tiempo si no corresponde | FR-029 |
| `siguiente()` | la acción de mover del próximo paso, o `None` con el motivo | FR-035, FR-036, FR-039 |
| `registrar_resultado(resultado)` | evalúa paradas por enemigos, daño o fin de partida | FR-037, FR-038, FR-040 |

### ControladorJuego (`src/controladores/controlador_juego.py`)

| Cambio | Requisito |
| --- | --- |
| comando `ir` / `ir a <sala>`: ejecuta el viaje paso a paso con `ServicioViaje` | FR-027 |
| comando `mapa`: muestra el mapa conocido sin consumir tiempo | FR-024, FR-026 |
| graba el comentario de la orden en la bitácora antes del primer paso | FR-043 |

### VistaConsola (`src/vistas/vista_consola.py`)

| Cambio | Requisito |
| --- | --- |
| `mostrar_mapa_conocido`: salas exploradas con sus salidas y estados recordados, y las avistadas | FR-024, FR-025 |
| `mostrar_estado`: las salidas de la sala actual se describen con el estado recordado | FR-021, FR-025 |
| `mostrar_fin_viaje`: informa el motivo de detención y los pasos dados | FR-042 |

La vista no recibe la `Cripta`: todo lo que muestra del mapa sale del `MapaConocido` y de las salas
que este declara exploradas.

### Bitacora (`src/servicios/bitacora.py`)

| Cambio | Requisito |
| --- | --- |
| `registrar_comentario(texto)`: escribe una línea de tipo `comentario` | FR-043 |
| `leer`: ignora las líneas de tipo `comentario` al construir la lista de acciones | FR-044 |

### Guardado (`src/servicios/guardado.py`) — R9

| Cambio | Requisito |
| --- | --- |
| `FORMATO_VERSION` sube de 2 a 3 | FR-047 |
| `tomar_snapshot`: agrega la sección `mapa` con una entrada por sala conocida | FR-046 |
| `restaurar_partida`: reconstruye el `MapaConocido` desde esa sección | FR-046 |

Formato de una entrada de la sección `mapa`: id de sala, estado, y los cuatro estados recordados de
sus puertas en el orden N, S, E, O. Se emiten solo las salas con estado distinto de `DESCONOCIDA`, en
el orden de `exploradas` seguido de las avistadas, para que cargar reconstruya la lista
`exploradas` en el mismo orden y el mapa quede idéntico (SC-007).

## Transiciones relevantes

**Estado de una sala** (FR-001, FR-003, FR-007):

```
DESCONOCIDA --avistar--> AVISTADA --explorar--> EXPLORADA
DESCONOCIDA ------------explorar-------------> EXPLORADA
```

`explorar` sobre una sala ya explorada y `avistar` sobre una sala explorada o avistada no son
cambios y no registran reversión (R8). Las flechas solo se recorren hacia atrás al revertir.

**Estado recordado de una puerta** (FR-009, FR-010, FR-011):

```
SIN_OBSERVAR --observar--> RECORDADA_ABIERTA  <--observar--> RECORDADA_CERRADA
```

Una observación fija el valor al estado real de ese instante, venga del valor que venga. El estado
real que cambia sin observación no mueve nada.

**Motivo de detención de un viaje** (FR-036 a FR-040): se evalúa en este orden después de cada paso,
y el primero que se cumple es el que se informa:

```
FIN_PARTIDA  ->  LLEGADA  ->  DANO  ->  ENEMIGOS  ->  (continuar)
```

y antes de cada paso:

```
SIN_RUTA  ->  (dar el paso)
```

`FIN_PARTIDA` va primero porque una victoria o una derrota hace irrelevante todo lo demás.
`LLEGADA` va antes de `DANO` y de `ENEMIGOS` porque un viaje que alcanzó su destino cumplió su
objetivo: las demás causas solo explican una parada cuando el jugador todavía no llegó (ver el caso
borde «recibe daño en el mismo instante en que llega al destino»). Entre las dos causas restantes,
`DANO` va antes que `ENEMIGOS` porque el daño es lo concreto que le pasó al jugador y los enemigos
presentes suelen ser su causa.
