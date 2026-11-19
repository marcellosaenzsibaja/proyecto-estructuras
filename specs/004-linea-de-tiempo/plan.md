# Implementation Plan: Línea de tiempo y puntos de control

**Branch**: `004-linea-de-tiempo` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-linea-de-tiempo/spec.md`

## Summary

Se agrega la posibilidad de consultar el estado de la partida en cualquier instante pasado, sin
modificarla. La historia se almacena como la secuencia de acciones del jugador con su instante, y
cada K acciones se guarda una copia completa del estado con el estado del generador aleatorio. Una
consulta localiza por búsqueda binaria el punto de control anterior al instante pedido, lo restaura
en una partida **aparte** y re-aplica las acciones que faltan, a lo sumo K. El resumen se construye
como datos, de modo que la vista lo formatea para `historia` y `--replay … --hasta` lo imprime sin
instanciar la vista.

La decisión central, que el enunciado pide documentar, es reconstruir **hacia adelante
re-simulando** en vez de hacia atrás invirtiendo cambios (research R1). No se elige por rendimiento,
que es comparable, sino porque vuelve consecuencias del diseño las dos propiedades más difíciles de
garantizar a mano: que guardar y cargar conserve la historia (FR-028), porque lo que se persiste es
una lista de acciones y no cierres en memoria; y que una consulta no altere la partida (FR-007),
porque la consulta ni siquiera toca el estado vivo.

La segunda decisión con consecuencias es que los puntos de control **no** se guardan en el archivo
(research R2): son caché de consulta y se reconstruyen al cargar.

## Technical Context

**Language/Version**: Python 3.11+ (el equipo local usa 3.14)

**Primary Dependencies**: `requests` (adaptador de red, sin cambios). Ninguna dependencia nueva. Se
usa `random.Random.getstate` / `setstate` de la biblioteca estándar, que no es una estructura de
datos y no cae bajo el Principio I.

**Storage**: guardado binario y JSON existentes, con una sección nueva para la línea de tiempo y la
versión de formato subida de 2 a 3, compartida con la capacidad 003 (research R8).

**Testing**: `unittest`, ejecutable con `pytest`. Las pruebas citan su requisito calificado
(`004-FR-NNN`) en el nombre o en el docstring.

**Target Platform**: escritorio local (Windows, Linux o macOS), consola.

**Project Type**: aplicación de consola MVC con adaptadores (proyecto único).

**Performance Goals**: consulta `historia` < 50 ms en una partida de ≥ 5 000 acciones del jugador con
el K por defecto y los puntos de control construidos (FR-030, SC-003); ciclo de eventos < 20 ms con
decenas de cazadores y la línea activa (FR-031, SC-006); a lo sumo `n/K + 1` copias completas
(SC-005); a lo sumo K acciones re-aplicadas por consulta (FR-022, SC-004).

**Constraints**: Principio I (sin `dict`, `set`, `heapq`, `bisect`, `collections` ni estructuras
equivalentes de biblioteca como índice, caché o registro); separación MVC, con `--replay`, `--hasta`
y `--bench` sin instanciar la vista; determinismo por semilla; toda afirmación de rendimiento
respaldada con `--bench`.

**Scale/Scope**: partidas sintéticas de hasta 5 000 acciones del jugador; criptas de hasta 1 600
salas, las mismas de 001 y 003 para poder comparar.

## Constitution Check

| Principio | Cómo lo cumple esta capacidad |
| --- | --- |
| I. Estructuras propias | La búsqueda del punto de control es `ultimo_menor_o_igual`, propia, sobre listas propias (R3). Las entradas y los puntos viven en listas indexadas por posición. El `dict` del snapshot es la carga de serialización que P1 ya usaba para guardar, no un índice, una caché ni un registro; queda declarado en la nota transversal de `DECISIONES.md`. |
| II. Determinismo | El punto de control guarda el estado de `random.Random` (FR-025), así que una re-simulación reproduce exactamente la partida original. SC-002 lo comprueba contra la re-simulación desde el inicio. |
| III. Separación MVC | El resumen se construye como datos en el modelo (R7); la vista solo formatea. `--hasta` y `--bench` no instancian la vista (FR-017, FR-034). |
| IV. Ningún dato de una cripta concreta | Las pruebas y el bench usan el generador sintético determinista por semilla. |
| V. Presupuesto de red | Una consulta no emite ninguna solicitud (FR-011). |
| VI. Estado reversible sin copias completas | Es el principio que esta capacidad tensa, y la tensión está acotada: se permiten copias completas, pero no más de una cada K acciones (FR-020), y entre ellas solo se almacenan las acciones (FR-023). El pergamino sigue usando el mecanismo de P1 sin cambios. |
| VII. Rendimiento demostrado | `--bench` mide tres valores de K, la alternativa de copia por acción y la de no usar puntos de control (FR-032), y repite el ciclo de eventos de 001 con la línea activa (FR-033). |
| VIII. La especificación precede a la implementación | `spec.md`, `plan.md` y `tasks.md` se confirman antes de los cambios de código. |

**Re-evaluación posterior al diseño (Phase 1)**: una violación aparente y declarada. El Principio VI
dice «estado reversible sin copias completas», y esta capacidad guarda copias completas. No es una
violación real: el enunciado las autoriza explícitamente y acota su frecuencia, y el principio existe
para prohibir una copia **por acción**, que es exactamente la alternativa que `--bench` mide para
descartarla. Queda anotado aquí para que la defensa no lo lea como una contradicción no vista.

## Project Structure

### Documentation (this feature)

```
specs/004-linea-de-tiempo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── tasks.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── interfaz-y-resumen.md
```

### Source Code (repository root)

```
src/
├── modelos/
│   ├── linea_tiempo.py       NUEVO  EntradaLinea, PuntoControl, LineaTiempo y la reconstrucción
│   ├── resumen_historia.py   NUEVO  el resumen de FR-006 como datos (R7)
│   └── partida.py            línea como estado; registro en _cerrar_accion; recorte en el pergamino
├── estructuras_datos/
│   └── busqueda_binaria.py   ultimo_menor_o_igual (R3)
├── servicios/
│   ├── guardado.py           sección de la línea; FORMATO_VERSION 2 -> 3 (R8)
│   ├── bitacora.py           registros de cursor; reproducir con instante límite (R5)
│   └── banco_linea_tiempo.py NUEVO  mediciones de K, memoria y consulta
├── controladores/
│   └── controlador_juego.py  comando historia; sig y ant pasan por la partida
└── vistas/
    └── vista_consola.py      formateo del resumen de historia

main.py                       --checkpoint-cada y --hasta

tests/
├── test_linea_tiempo.py          NUEVO  entradas, puntos, recorte, conteo de re-aplicadas
├── test_historia_consulta.py     NUEVO  los 4 primeros casos del Apéndice B y los rechazos
├── test_historia_replay.py       NUEVO  --hasta, partida terminada antes, cursor en la bitácora
├── test_linea_guardado.py        NUEVO  persistencia e incompatibilidad de formato
├── test_rendimiento_linea.py     NUEVO  50 ms, SC-004 y SC-005 por conteo
└── test_restricciones.py         se amplía con los módulos nuevos
```

**Structure Decision**: `linea_tiempo.py` y `resumen_historia.py` van a `src/modelos/` porque la
definición del estado pasado es una regla del juego y la línea es estado de la partida. El banco de
mediciones va a `src/servicios/` junto a los otros bancos. No se crea ninguna capa nueva.

## Mediciones planificadas (`--bench`)

| Sección | Qué compara | Requisito |
| --- | --- | --- |
| `[linea_tiempo]` | memoria de la línea y tiempo de consulta para K = 1, 25 y 200 en una partida de 5 000 acciones; `CUMPLE` si la consulta queda bajo 50 ms | FR-030, FR-032, SC-003 |
| `[linea_tiempo]` | alternativa «copia por acción»: memoria y tiempo con una copia completa en cada acción | FR-032 |
| `[linea_tiempo]` | alternativa «sin puntos de control»: re-simular siempre desde el inicio | FR-032 |
| `[linea_tiempo]` | conteo de acciones re-aplicadas por consulta y de copias mantenidas | SC-004, SC-005 |
| `[ciclo_eventos]` | se repite el escenario de 001 con la línea activa, reportando el máximo | FR-033, SC-006 |
| `[linea_determinismo]` | dos ejecuciones con la misma semilla dan la misma historia y los mismos resúmenes | FR-034 |

El K por defecto se fija con estas mediciones y se justifica en `DECISIONES.md` §P2 5.5. El valor que
se escriba en el código es el que las mediciones respalden, no uno elegido antes de medir.

## Riesgos y límites conocidos

- **La primera consulta de una partida cargada es lenta.** Es la consecuencia aceptada de R2: los
  puntos de control no viajan en el archivo y hay que reconstruirlos. Está declarado en las
  clarificaciones de `spec.md` y queda fuera del límite de FR-030, que se mide con los puntos ya
  construidos. Es un costo de una sola vez.
- **La re-simulación depende del determinismo de toda la partida.** Si cualquier regla consultara una
  fuente de aleatoriedad fuera de `Partida.azar`, o dependiera del orden de iteración de una
  estructura no determinista, las consultas devolverían estados sutilmente distintos de los reales.
  El proyecto ya garantiza esto por el Principio II y lo prueba con `--replay`; esta capacidad lo
  convierte en algo de lo que depende la corrección y no solo la reproducibilidad. SC-002 es la
  prueba que lo vigila.
- **El cursor del inventario era un agujero de reproducción.** Arreglarlo (R5) cambia el formato de
  `partida.log`. Una bitácora grabada por las capacidades anteriores sigue leyéndose, porque solo se
  agregan registros nuevos, pero una bitácora nueva no reproduce igual en una versión vieja del
  programa. Queda anotado en el README.
- **El pico de la acción que toma un punto de control.** Es el único trabajo caro que esta capacidad
  agrega al camino de una acción, y el límite de 20 ms de 001 sigue vigente. R10 explica por qué se
  espera que quepa de sobra y por qué lo que hay que medir es el máximo y no la media. Si no
  cupiera, la salida es subir K, que es el parámetro que estas mediciones fijan.
- **`historia` muestra el mapa conocido, que viene de la 003.** Si la 003 no estuviera integrada, el
  campo `mapa` del resumen quedaría vacío y FR-006 no se cumpliría. Es una dependencia real entre las
  dos capacidades, y el orden de integración importa.
- **Una consulta de un instante muy antiguo con K grande re-aplica hasta K acciones.** Con K = 200 y
  una cripta grande eso puede acercarse al límite de 50 ms. Es precisamente el compromiso que las
  mediciones de tres valores de K sirven para resolver, y la razón de que el K por defecto no se
  elija por intuición.
