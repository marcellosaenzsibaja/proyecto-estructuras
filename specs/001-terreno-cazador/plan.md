# Implementation Plan: Terreno con costo y enemigo cazador

**Branch**: `001-terreno-cazador` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-terreno-cazador/spec.md`

## Summary

Se agrega el costo de tránsito a las salidas y el comportamiento de enemigo `cazador`. El costo se
guarda una sola vez por conexión, en la `Puerta` compartida, y se usa como costo base de cada
movimiento de cualquier actor. El cazador decide con una **búsqueda acotada de costo mínimo**
implementada por el grupo: un montículo binario de mínimos propio para escoger la sala pendiente
más barata, y registros en listas indexadas por un índice compacto de sala con marca de generación,
sin `dict`, `set` ni hash. La estrategia preliminar es un **cálculo compartido incremental desde la sala
del jugador**, que se expande solo hasta el rango del cazador que decide y se retoma para rangos
mayores, y que se **reutiliza** mientras la sala del jugador, la
cota y las puertas relevantes no cambien. La alternativa individual, que explora desde cada cazador
y corta la rama que supera su rango, y la de recalcular siempre se implementan para medirlas con
`--bench`. Detalle en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11+ (el equipo local usa 3.14)

**Primary Dependencies**: `requests` (adaptador de red, sin cambios). Ninguna dependencia nueva.

**Storage**: caché persistente y guardado binario existentes. El costo se agrega a la `Puerta` y
sube la versión del formato binario.

**Testing**: `unittest`, ejecutable con `pytest`. Las pruebas nuevas citan su requisito (`FR-NNN`)
en el nombre o en el docstring.

**Target Platform**: escritorio local (Windows, Linux o macOS), consola.

**Project Type**: aplicación de consola MVC con adaptadores (proyecto único).

**Performance Goals**: ciclo de eventos < 20 ms con ≥ 30 cazadores activos (FR-031, SC-003). El
número de salas examinadas por decisión es independiente del tamaño de la cripta con rango fijo
(FR-030, SC-004).

**Constraints**: Principio I (sin `dict`, `set`, `heapq`, `bisect`, `collections`, `networkx` ni
estructuras equivalentes de biblioteca); determinismo (Principio II); la decisión debe ser idéntica
a la de un cálculo desde cero (FR-019 a FR-022).

**Scale/Scope**: criptas publicadas desde ~20 salas hasta varios cientos; criptas sintéticas de
`--bench` hasta ~10 000 salas para la prueba de escala de SC-004; decenas de cazadores activos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| I. Estructuras propias | Montículo binario propio (R1) y registros en `list` con generación (R2). Sin `dict`, `set`, `heapq` ni equivalentes. La referencia de pruebas y todos los recorridos usan `list` indexadas (G5 de tasks.md). El generador de criptas sintéticas escribe **texto JSON** y solo se leen los diccionarios que produce `json.loads`, lo único que autoriza la constitución. `tests/test_restricciones.py` lo verifica automáticamente con `ast`, sin excepciones. | ✅ |
| II. Determinismo | Orden del montículo por (costo, índice). Desempate explícito FR-014 y FR-015 (clave D4). Las decisiones no dependen del índice compacto (D5). Una sola `random.Random(semilla)` en el generador, con orden fijo de consumo y Fisher–Yates escrito a mano (G3, G4). | ✅ |
| III. MVC | `rutas.py` y `cazador.py` son modelo puro. La vista solo agrega presentación (costos y marca de cazador). `--bench` no instancia la vista. | ✅ |
| IV. Sin datos de cripta | Costos y rango vienen del esqueleto y del catálogo. Ningún id ni costo de una cripta publicada en el código; los nombres y llaves sintéticos del generador (`itm_llave_sint_<k>`) no corresponden a ninguna cripta del servicio. | ✅ |
| V. Presupuesto de red | El costo viene en el esqueleto y el rango en el catálogo: cero solicitudes nuevas (FR-025). | ✅ |
| VI. Estado reversible | Los cachés de rutas, `version_puertas` y el registro son infraestructura: no se guardan ni se revierten. El retroceso de P1 sigue registrando deltas, sin copias. | ✅ |
| VII. Rendimiento medido | Escenarios de `--bench` de FR-032 a FR-035, incluida la alternativa ingenua (lista lineal y recalcular siempre). | ✅ |
| VIII. Spec antes que código | La especificación y la sesión de clarify están confirmadas antes de este plan. | ✅ |

**Re-evaluación posterior al diseño (Phase 1)**: sin violaciones. No se requiere «Complexity
Tracking».

## Project Structure

### Documentation (this feature)

```text
specs/001-terreno-cazador/
├── spec.md              # Especificación (con Clarifications)
├── plan.md              # Este archivo
├── research.md          # Phase 0: decisiones R1–R10
├── data-model.md        # Phase 1: entidades y estructuras
├── quickstart.md        # Phase 1: cómo validar la capacidad
├── contracts/
│   └── interfaz-y-bench.md  # Contrato de presentación y de salida de --bench
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks; no lo crea este comando)
```

### Source Code (repository root)

```text
src/
├── estructuras_datos/
│   ├── monticulo.py            # NUEVO  MonticuloMin con eliminación perezosa (R1)
│   └── registro_busqueda.py    # NUEVO  listas por índice + generación (R2)
├── modelos/
│   ├── entidades.py            # MOD    Puerta.costo, Salida.sala_destino, Sala.indice
│   ├── cripta.py               # MOD    índice compacto, enlace directo, simetría de costo
│   ├── fichas.py               # MOD    comportamiento cazador + rango
│   ├── rutas.py                # NUEVO  BuscadorRutas (búsqueda acotada, modo primer paso)
│   ├── cazador.py              # NUEVO  DecisorCazadores (compartido/individual, reutilización)
│   └── partida.py              # MOD    costo de movimiento, turno del cazador, version_puertas
├── adaptadores/
│   └── fuente_memoria.py       # NUEVO  fuente de datos en memoria para criptas sintéticas (misma interfaz que --offline)
├── servicios/
│   ├── cargador_cripta.py      # MOD    leer y validar costo (FR-001, FR-008)
│   ├── fabrica_fichas.py       # MOD    leer y validar rango (FR-009)
│   ├── guardado.py             # MOD    costo en el formato binario; versión de formato
│   ├── generador_criptas.py    # NUEVO  criptas sintéticas sembradas (pruebas y --bench)
│   ├── banco_pruebas.py        # MOD    integra las secciones del cazador en --bench
│   └── banco_cazador.py        # NUEVO  escenarios FR-032 a FR-035 (cazador, cola, reutilización, escala, ciclo, revisión P1)
└── vistas/
    └── vista_consola.py        # MOD    costo por salida y marca de cazador (FR-023, FR-024)

tests/
├── test_generador_criptas.py   # NUEVO  corrección y reproducibilidad del generador
├── test_restricciones.py       # NUEVO  prohibición de estructuras de conveniencia (ast)
├── test_monticulo.py           # NUEVO
├── test_registro_busqueda.py   # NUEVO
├── test_terreno.py             # NUEVO  FR-001 a FR-008 (US1, Apéndice B)
├── test_cazador.py             # NUEVO  FR-009 a FR-018 (US2, Apéndice B)
├── test_equivalencia_cazador.py# NUEVO  FR-019 a FR-022, SC-002 (US3)
├── test_determinismo_cazador.py# NUEVO  trazas idénticas, orden de carga, modos (US2)
├── test_reutilizacion_cazador.py# NUEVO no recálculo ante puertas alejadas (US3)
├── utilidades_cripta.py        # NUEVO  criptas escritas a mano como texto JSON
├── test_rendimiento_cazador.py # NUEVO  FR-030, SC-004 (conteo de salas examinadas)
├── referencia_cazador.py       # NUEVO  implementación de referencia desde cero (solo pruebas)
└── (pruebas existentes de P1)  # deben seguir pasando (SC-007)
```

**Structure Decision**: se conserva la estructura MVC de la primera parte. El cálculo de rutas va
en `src/modelos/` porque es lógica del juego. Las estructuras genéricas van en
`src/estructuras_datos/`, como en P1. `BuscadorRutas` se diseña para poder reutilizarse en «ir a»
(002); si conviene compartirlo o separarlo se justifica en el plan de 002 (P2 §5.3).

## Mediciones planificadas (`--bench`)

| Escenario | Qué compara | Requisito |
|---|---|---|
| Decisión del cazador | 1 frente a 30 cazadores; rango pequeño frente a grande; compartido frente a individual | FR-032 |
| Cola de prioridad | Montículo binario frente a lista lineal | R1, Principio VII |
| Reutilización | Reutilizar frente a recalcular siempre, con puertas estables e inestables | FR-033 |
| Escala | Salas examinadas y tiempo con cripta ×1 y ×10, misma región en rango | FR-030, SC-004 |
| Ciclo de eventos | Tiempo máximo entre decisiones del jugador con ≥ 30 cazadores | FR-031, SC-003 |
| Revisión de P1 | Agenda e historial de retroceso con cazadores y costos variables | FR-034, P2 §5.6 |

Las criptas sintéticas (`src/servicios/generador_criptas.py`, reglas G1 a G5 de tasks.md) son cuadrículas con costos aleatorios sembrados y puertas que se abren y
cierran según la semilla (FR-035).

## Riesgos y límites conocidos

- Si los rangos de los cazadores son muy dispares (uno enorme y muchos pequeños), el cálculo
  compartido examina la región del rango mayor: el modo individual podría ganar. Lo decide la
  medición (R5).
- Con puertas que cambian en cada evento cerca del jugador, la reutilización casi nunca aplica: su
  costo debe ser despreciable frente a recalcular (FR-033).
- La equivalencia descansa en que los costos son simétricos (FR-002). Si el enunciado cambia eso,
  el cálculo compartido desde el jugador deja de ser válido.

## Revisión del grupo

- **R4**: confirmado por el grupo e incorporado a FR-002 de la especificación.
- **R5 y R6**: revisados. La estrategia compartida con reutilización sigue siendo preliminar; la
  decisión final sale de `--bench` y se documenta en `DECISIONES.md`.

## Complexity Tracking

No aplica: no hay violaciones de la constitución.
