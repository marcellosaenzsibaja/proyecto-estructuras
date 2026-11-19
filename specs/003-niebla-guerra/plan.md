# Implementation Plan: Niebla de guerra y viaje automático «ir a»

**Branch**: `003-niebla-guerra` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-niebla-guerra/spec.md`

## Summary

El jugador deja de ver el mapa completo. Se agrega un objeto de conocimiento propio de la partida,
separado de la cripta descargada, que guarda para cada sala si está explorada, avistada o
desconocida, y para cada salida de cada sala el estado en que el jugador vio su puerta la última vez.
La antorcha de P1 pasa a tener efecto: al entrar a una sala con antorcha encendida, las vecinas
quedan exploradas sin despertar nada. Sobre ese conocimiento se construye el comando `ir a`, que
lleva al jugador a una sala explorada dando movimientos ordinarios, recalculando el primer paso antes
de cada uno y deteniéndose ante enemigos, daño o falta de ruta.

Las dos decisiones de diseño con más consecuencias son indexar el conocimiento por el índice compacto
que P1 ya asigna a cada sala, en lugar de una tabla hash (research R1, R2), y **no** compartir el
recorrido de búsqueda con el cazador, aunque sí sus estructuras auxiliares (research R4). La primera
hace las consultas del camino caliente de la vista y del viaje una indexación directa y mantiene el
costo de explorar proporcional a lo revelado. La segunda evita pagar una indirección en el bucle del
cazador, que es el que tiene el límite de 20 ms, y hace imposible por construcción el defecto más
grave de esta capacidad: que el cazador respete la niebla de guerra o que `ir a` la atraviese.

## Technical Context

**Language/Version**: Python 3.11+ (el equipo local usa 3.14)

**Primary Dependencies**: `requests` (adaptador de red, sin cambios). Ninguna dependencia nueva.

**Storage**: el guardado binario y JSON existentes, con una sección nueva para el mapa conocido y la
versión de formato subida de 2 a 3 (research R9). La caché persistente y el esqueleto descargado no
cambian: el conocimiento del jugador no se cachea ni se descarga, se construye jugando.

**Testing**: `unittest`, ejecutable con `pytest`. Las pruebas nuevas citan su requisito calificado
(`003-FR-NNN`) en el nombre o en el docstring, para recorrer la trazabilidad escenario → tarea →
código → prueba de §2.5 del enunciado.

**Target Platform**: escritorio local (Windows, Linux o macOS), consola.

**Project Type**: aplicación de consola MVC con adaptadores (proyecto único).

**Performance Goals**: cálculo de un paso de `ir a` < 5 ms con el mapa conocido completo de la
cripta de referencia (FR-053, SC-003); consultas al mapa conocido en tiempo constante (FR-050);
trabajo de una exploración proporcional a las salas reveladas (FR-051, SC-004). Los límites de la
capacidad 001 siguen vigentes: el ciclo de eventos con decenas de cazadores sigue bajo 20 ms, y esta
capacidad no debe acercarlo al límite.

**Constraints**: Principio I (sin `dict`, `set`, `heapq`, `bisect`, `collections`, `networkx` ni
estructuras equivalentes de biblioteca como índice, caché o registro); separación MVC, con `--replay`
y `--bench` sin instanciar la vista; ningún dato de una cripta concreta en el código; determinismo
por semilla; toda afirmación de rendimiento respaldada con `--bench`.

**Scale/Scope**: criptas publicadas desde ~20 salas hasta varios cientos; criptas sintéticas de
`--bench` de hasta 1 600 salas, las mismas que usa la capacidad 001, para poder comparar.

## Constitution Check

| Principio | Cómo lo cumple esta capacidad |
| --- | --- |
| I. Estructuras propias | `MapaConocido` usa listas indexadas por `Sala.indice` y una lista de ids, sin `dict` ni `set` (R1, R2, R3). `BuscadorConocido` reutiliza `MonticuloMin` y `RegistroBusqueda`, ambas del grupo (R4). `tests/test_restricciones.py` verifica por AST los módulos nuevos. |
| II. Determinismo | El mapa conocido es función de la secuencia de acciones; el desempate de `ir a` es total (FR-032, FR-033) y no consulta el generador aleatorio. FR-049 y SC-008 lo comprueban con `--replay`. |
| III. Separación MVC | El cálculo de la ruta y las condiciones de parada viven en el modelo (R7); el controlador solo repite pasos; la vista solo lee el mapa conocido. `--bench` y `--replay` no instancian la vista (FR-056). |
| IV. Ningún dato de una cripta concreta | Las pruebas usan criptas sintéticas del generador existente, ampliado con costos y vecindades, deterministas por semilla. |
| V. Presupuesto de red | Esta capacidad no agrega ninguna solicitud: el conocimiento se deriva del esqueleto ya descargado y de lo que el jugador hace. |
| VI. Estado reversible sin copias completas | Cada cambio del mapa registra solo su valor anterior en el intervalo de la acción en curso (R8, FR-052); no se copia el mapa. |
| VII. Rendimiento demostrado | `--bench` agrega las secciones de consultas, exploración y `ir a` (FR-055), y SC-004 se verifica por conteo, no por tiempo (R10). |
| VIII. La especificación precede a la implementación | `spec.md`, `plan.md` y `tasks.md` se confirman antes de los cambios de código que las implementan. |

**Re-evaluación posterior al diseño (Phase 1)**: sin violaciones. No se requiere «Complexity
Tracking». La duplicación del recorrido de búsqueda entre el cazador y `ir a` es deliberada y está
justificada en R4; no se trata como deuda sino como una separación de las dos fuentes de verdad.

## Project Structure

### Documentation (this feature)

```
specs/003-niebla-guerra/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── tasks.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── interfaz-y-bench.md
```

### Source Code (repository root)

```
src/
├── modelos/
│   ├── mapa_conocido.py      NUEVO  estados de sala, memoria de puertas, exploración (R1, R2, R3)
│   ├── viaje.py              NUEVO  BuscadorConocido, Viaje y ServicioViaje (R4, R5, R7)
│   ├── partida.py            el mapa como estado de la partida; observación al mover y al abrir
│   ├── acciones.py           sin cambios: un paso de viaje es una acción MOVER ordinaria
│   └── entidades.py          sin cambios
├── estructuras_datos/
│   ├── monticulo.py          sin cambios, reutilizado por BuscadorConocido
│   └── registro_busqueda.py  sin cambios, reutilizado por BuscadorConocido
├── servicios/
│   ├── guardado.py           sección del mapa conocido; FORMATO_VERSION 2 -> 3 (R9)
│   ├── bitacora.py           líneas de comentario, ignoradas al leer (FR-043, FR-044)
│   ├── generador_criptas.py  criptas sintéticas con vecindades para medir exploración
│   └── banco_mapa.py         NUEVO  mediciones de consultas, exploración y «ir a»
├── controladores/
│   └── controlador_juego.py  comandos «mapa» e «ir a»
└── vistas/
    └── vista_consola.py      vista del mapa conocido y estados recordados

tests/
├── test_mapa_conocido.py            NUEVO  estados, memoria de puertas, conteos
├── test_antorcha_exploracion.py     NUEVO  efecto de la antorcha y su reversión
├── test_viaje.py                    NUEVO  rutas, desempate, paradas
├── test_viaje_bitacora.py           NUEVO  pasos individuales y comentario en partida.log
├── test_mapa_guardado.py            NUEVO  persistencia e incompatibilidad de formato
├── test_equivalencia_viaje.py       NUEVO  primer paso contra referencia desde cero
├── test_rendimiento_mapa.py         NUEVO  límite de 5 ms y conteos de SC-004
├── test_restricciones.py            se amplía ARCHIVOS_VIGILADOS con los módulos nuevos
└── referencia_conocido.py           NUEVO  referencia teórica del subgrafo conocido
```

**Structure Decision**: se conserva la estructura MVC de la primera parte. El conocimiento del
jugador va a `src/modelos/` porque es estado del juego y una regla, no infraestructura: a diferencia
del `BuscadorRutas` del cazador, que es un cálculo descartable, el mapa conocido se guarda y se
revierte. `viaje.py` acompaña a `mapa_conocido.py` en modelos porque la ruta y las paradas son reglas
del juego (R7), y el controlador queda como un bucle delgado sin lógica propia.

## Mediciones planificadas (`--bench`)

| Sección | Qué compara | Requisito |
| --- | --- | --- |
| `[mapa_consultas]` | consultas de estado de sala y de puerta recordada con mapas conocidos de 100, 400 y 1 600 salas exploradas; muestra que el costo por consulta no crece | FR-050 |
| `[mapa_exploracion]` | entrada con antorcha que revela k vecinas, con mapa conocido pequeño y grande; reporta salas y puertas tocadas, y los tiempos | FR-051, SC-004 |
| `[viaje_paso]` | cálculo de un paso de `ir a` con el mapa conocido completo de la cripta sintética de referencia; `CUMPLE` si es menor que 5 ms | FR-053, SC-003 |
| `[viaje_vs_cazador]` | costo de un paso de `ir a` y de una decisión del cazador en la misma cripta, para respaldar la separación de R4 | R4 |
| `[mapa_reversion]` | registrar e invertir los cambios de una entrada con antorcha, contra copiar el mapa completo | FR-052 |
| `[mapa_determinismo]` | dos ejecuciones con la misma semilla producen el mismo mapa y las mismas rutas | FR-049, FR-056 |

Las mediciones finales y su lectura van a `DECISIONES.md` §P2 5.3, que enlaza a esta especificación y
a este plan.

## Riesgos y límites conocidos

- **El orden dentro de `_mover` es parte de la corrección, no un detalle.** Observar las puertas de
  la sala de llegada antes de activar enemigos y trampas es lo que hace que el recálculo del paso
  siguiente parta del conocimiento corregido (FR-012). Una reordenación accidental rompe el caso del
  Apéndice B de la puerta que el mapa recordaba abierta, y lo rompe de una forma que solo se nota en
  ese escenario. La prueba de ese caso es la que protege el orden.
- **La tentación de leer la realidad.** Cualquier lugar de la vista o del viaje que consulte
  `Puerta.cerrada` en vez del estado recordado produce un programa que funciona y que está mal
  (FR-021). El riesgo se mitiga con una prueba que compara la ruta de `ir a` contra una referencia
  calculada sobre el subgrafo conocido, y con que `BuscadorConocido` no reciba la cripta real.
- **Salas exploradas por antorcha sin contenido.** Son el caso que más fácilmente se olvida: están
  exploradas, el viaje puede rutear por ellas, y al entrar despiertan enemigos y disparan trampas
  (FR-018). Si el guardado solo recorriera las salas con contenido incorporado, estas salas se
  perderían; de ahí la sección propia del mapa en el archivo (R9).
- **Subir la versión del formato invalida los guardados existentes.** Es el comportamiento que el
  enunciado pide (FR-047), pero conviene avisarlo en el README para que nadie lo lea como un error.
- **La línea de tiempo (004) va a reconstruir este mapa.** El diseño de R8 (registrar solo lo que
  cambió) es lo que hace viable esa reconstrucción, pero hasta que la 004 exista no hay prueba de
  que el formato de esos cambios le sirva. Es una dependencia asumida a conciencia, no verificada.
- **`ir a` no abre puertas (FR-041)** aunque el jugador tenga la llave. Es lo que el enunciado pide,
  y hace que el comando sea menos útil de lo que un jugador esperaría cuando su ruta pasa por una
  puerta que él mismo podría abrir. Queda documentado como límite, no como defecto.
