# CRIPTA

Proyecto de Estructuras de Datos II, II Ciclo 2026.

## Requisitos

- Python 3.11 o superior
- Dependencias: `requests`

## Desarrollo dirigido por especificaciones (segunda parte)

- Herramienta: GitHub spec-kit (`specify-cli`), versión **1.4.1.dev0**
  (todo el grupo debe usar la misma).
- Agente de programación: **Claude Code** (capacidad 001) y **Antigravity** (capacidad 002: `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`). Al agotarse la cuota de Antigravity, el análisis de consistencia y la implementación de la capacidad 002 se hicieron con **Claude (claude.ai)**; queda registrado en `PROMPTS_LLM.md`.
- Integración de Antigravity: `specify integration install agy --force` (convive con la de Claude).
- Inicialización usada: `specify init --here --integration claude --script ps`.
- Comandos del flujo (en esta versión se escriben con guion):
  `/speckit-constitution`, `/speckit-specify`, `/speckit-clarify`,
  `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze`, `/speckit-implement`.
- Artefactos: `.specify/memory/constitution.md` y `specs/<NNN-capacidad>/`.

## Instalación

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

En Linux o macOS la activación es `source .venv/bin/activate`.

## Ejecución

```
python main.py
python main.py --cripta cripta-01
python main.py --cripta cripta-01 --semilla 42
```

Sin `--cripta` se muestra la lista de criptas publicadas. Sin `--semilla` se
genera una y se muestra al iniciar la partida.

### Opciones de línea de comandos

| Opción | Acción |
| --- | --- |
| `--cripta <id>` | Cripta a jugar; sin esta opción se pide elegirla de la lista |
| `--semilla <n>` | Semilla del generador aleatorio; sin esta opción se genera una nueva |
| `--offline <carpeta>` | Juega sin red, leyendo de un volcado generado antes con `herramientas/exportar_offline.py` |
| `--cache-size <n>` | Capacidad en memoria de la caché de fichas de catálogo (por defecto 25) |
| `--cache-ruta <archivo>` | Archivo donde la caché de fichas persiste entre ejecuciones (por defecto `cache_fichas.json`) |
| `--bitacora <archivo>` | Archivo donde grabar la bitácora de esta partida (por defecto `bitacora.log`) |
| `--replay <archivo>` | Reproduce una bitácora grabada antes, sin interacción, y termina |
| `--cargar <archivo>` | Retoma una partida guardada (`.bin` o `.json`) en vez de empezar una nueva |
| `--puntajes-ruta <archivo>` | Archivo de la tabla de puntajes (por defecto `puntajes.json`) |
| `--bench` | Mide el desempeño de los subsistemas propios del proyecto y termina, sin jugar |
| `--verificar <cripta>` | Verifica si la cripta es resoluble, imprime el reporte y termina sin instanciar la vista (código 0 resoluble, 1 no resoluble, 2 error) |
| `--forzar` | Juega una cripta aunque no sea resoluble; sin esta opción la partida no inicia y se muestra el reporte |

Ejemplos:

```
python main.py --offline volcado/ --cripta demo
python main.py --cripta cripta-01 --cache-size 50 --cache-ruta cache_c1.json
python main.py --replay bitacora.log --cripta cripta-01
python main.py --bench
```

## Comandos del juego

| Comando | Acción |
| --- | --- |
| `mover <N\|S\|E\|O>` (`m`) | Moverse por una salida abierta |
| `abrir <N\|S\|E\|O>` (`ab`) | Abrir una puerta con la llave correspondiente |
| `atacar <número>` (`a`) | Atacar al enemigo con ese número en la lista de la sala |
| `esperar` (`e`) | Esperar |
| `recoger <número>` (`r`) | Recoger un objeto del suelo |
| `usar` (`u`) | Usar el objeto seleccionado del inventario |
| `equipar` (`eq`) | Equipar el objeto seleccionado |
| `soltar` (`so`) | Soltar el objeto seleccionado |
| `sig` / `ant` | Recorrer el inventario (no consume tiempo) |
| `ordenar` (`ord`) | Mostrar el inventario ordenado alfabéticamente, sin alterar su orden real |
| `pergamino` (`perg`) | Consumir un pergamino de retroceso y deshacer la última acción y todo lo ocurrido después |
| `guardar [archivo]` (`gu`) | Guardar la partida (binario por defecto; `.json` si el archivo termina en esa extensión) |
| `cargar [archivo]` (`ca`) | Retomar una partida guardada, dentro de la sesión en curso |
| `puntajes` (`pts`) | Mostrar la tabla de mejores puntajes |
| `ayuda` | Mostrar los comandos |
| `salir` | Terminar la sesión |

Al terminar una partida (victoria o derrota) se registra el puntaje y se
muestra la tabla de mejores puntajes. Abandonar con `salir` no registra
puntaje. En todos los casos se reportan al final: las solicitudes de red
realizadas y el presupuesto de la cripta, y los aciertos/fallos/desalojos
de la caché de fichas de catálogo.

## Modo sin conexión

```
python -m herramientas.exportar_offline --cripta cripta-01 --salida volcado/
python main.py --offline volcado/ --cripta cripta-01
```

`exportar_offline` recorre toda la cripta por la red (todas las páginas del
esqueleto, el contenido de todas las salas y todas las entradas de catálogo
referenciadas) y la guarda en disco en la misma estructura que
`FuenteSinConexion` espera leer. Se puede exportar más de una cripta a la
misma carpeta de salida: el índice `criptas.json` se combina, no se
sobrescribe.

## Guardado y reproducción

- `guardar`/`cargar` (en el juego) o `--cargar` (al iniciar `main.py`)
  persisten el estado estructural de la partida (mapa descubierto,
  inventario, vida, posición, enemigos) en un formato binario propio que
  permite leer una sola sala sin procesar el archivo completo. No se
  conserva el historial de retroceso (pergaminos) ni los temporizadores de
  efectos transitorios en curso; ver `DECISIONES.md` §4.10 para el detalle.
- Cada partida jugada o cargada deja una bitácora de sólo adición
  (`--bitacora`) con la cripta, la semilla y cada acción ejecutada.
  `--replay <archivo>` la reproduce de principio a fin sin interacción y
  verifica que la cripta, su versión y la versión del catálogo coincidan
  antes de reproducir.

## Medición de desempeño

```
python main.py --bench
```

Mide, sin necesidad de red ni de una cripta real, la agenda de eventos, la
caché de fichas, la recuperación de fichas en memoria, el inventario, el
historial de retroceso, el ordenamiento y el guardado/carga. Los resultados
de referencia y su análisis están en `DECISIONES.md`.

En la segunda parte agrega, con criptas sintéticas deterministas por semilla,
las secciones del terreno y el cazador (`specs/001-terreno-cazador`):

| Sección | Qué compara |
| --- | --- |
| `[cazador_decision]` | 1 frente a 30 cazadores, rango pequeño frente a grande, compartido frente a individual |
| `[cola_prioridad]` | Montículo binario propio frente a lista con búsqueda lineal |
| `[reutilizacion]` | Reutilizar frente a recalcular siempre, con puertas estables e inestables |
| `[escala]` | Salas examinadas con una cripta x1 y x10 con la misma región dentro del rango |
| `[ciclo_eventos]` | Peor ciclo entre dos decisiones del jugador con 30 cazadores; `CUMPLE` si es menor que 20 ms |
| `[revision_p1]` | Agenda e historial de retroceso de P1 con la carga nueva |
| `[determinismo]` | Misma semilla, mismas criptas sintéticas |
| `[resolubilidad]` | Recorrido reactivo frente a repetir el recorrido por llave, con cadenas de 10 a 500 llaves y una cuadrícula de 1 000 salas; `CUMPLE` si es menor que 200 ms |
| `[resolubilidad_determinismo]` | Dos verificaciones de la misma cripta dan el mismo orden |

## Pruebas

```
python -m unittest discover -s tests
```

También se pueden ejecutar con `pytest`:

```
python -m pytest -q
```

### Pruebas de aceptación de la segunda parte

Cada prueba cita en su nombre o en su docstring el requisito que verifica
(`FR-NNN`), para recorrer la trazabilidad escenario → tarea → código → prueba.

**001 — Terreno con costo y enemigo cazador** (ver
`specs/001-terreno-cazador/quickstart.md`):

```
python -m pytest tests/test_restricciones.py tests/test_generador_criptas.py tests/test_terreno.py tests/test_cazador.py tests/test_determinismo_cazador.py tests/test_equivalencia_cazador.py tests/test_reutilizacion_cazador.py tests/test_rendimiento_cazador.py tests/test_vista_consola.py -v
```

- `test_restricciones.py`: ningún módulo de la capacidad usa `dict`, `set`,
  `heapq`, `bisect`, `collections` ni bibliotecas de grafos (Principio I).
- `test_cazador.py`: escenarios de la US2 y comparación exhaustiva contra la
  referencia teórica (`tests/referencia_cazador.py`).
- `test_reutilizacion_cazador.py`: cambios de puertas alejadas no provocan
  recálculo.

**002 — Verificación de resolubilidad** (ver
`specs/002-verificacion-resolubilidad/quickstart.md`):

```
python -m unittest tests.test_busqueda_binaria tests.test_monticulo_llaves tests.test_resolubilidad tests.test_resolubilidad_irresoluble tests.test_verificador_servicio tests.test_cli_verificar tests.test_bench_resolubilidad tests.test_restricciones -v
```

- `test_resolubilidad.py` y `test_resolubilidad_irresoluble.py`: casos 1 a 3 del
  Apéndice B de resolubilidad y el diagnóstico (llaves, frontera, ciclos).
- `test_cli_verificar.py`: caso 4 (sin `--forzar` la partida no inicia), `--verificar`
  y sus códigos de salida.
- `test_bench_resolubilidad.py`: equivalencia con la alternativa ingenua y límite de 200 ms.

## Documentación adicional

- `DECISIONES.md` — documento de decisiones de diseño: una sección por cada
  problema de estructuras de datos del enunciado (§4), con alternativas
  consideradas, decisión, análisis de complejidad, evidencia empírica y
  límites conocidos.
- `PROMPTS_LLM.md` — bitácora de uso de LLM durante el desarrollo.
- `.specify/memory/constitution.md` y `specs/` — constitución y especificaciones
  de spec-kit de la segunda parte (`spec.md`, `plan.md`, `tasks.md` por capacidad).

## Estructura

```
main.py
src/
  adaptadores/       acceso a datos (red y sin conexión) detrás de FuenteDatos
  controladores/     flujo de la aplicación
  estructuras_datos/ tabla_hash, agenda, lista_doble, inventario,
                      buffer_circular, cache_fichas, ordenamiento,
                      monticulo, registro_busqueda
  modelos/           reglas del juego (partida, entidades, fichas, acciones,
                      rutas y cazador)
  servicios/         carga de cripta y catálogo, caché persistente,
                      guardado binario/JSON, puntajes, bitácora, banco de
                      pruebas de desempeño, generador de criptas sintéticas
  vistas/            interfaz de consola
herramientas/        exportar_offline (y herramientas de muestreo de la API)
tests/
```
