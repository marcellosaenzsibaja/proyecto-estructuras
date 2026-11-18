# Implementation Plan: Verificación de resolubilidad de una cripta

**Branch**: `002-verificacion-resolubilidad` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-verificacion-resolubilidad/spec.md`

## Summary

Se implementa la verificación estática previa al inicio de una partida para determinar si una cripta puede completarse bajo supuestos ideales (llaves no consumibles, enemigos derrotables, puertas reabribles). La verificación emplea un **recorrido único de expansión lineal $O(|V| + |E| + |K|)$** implementado por el grupo:
1. Una cola continua de salas alcanzables con puntero de lectura directo (R1).
2. Un registro de salas alcanzadas en listas indexadas por el índice compacto `Sala.indice` (R2).
3. Mapeo e indexación canónica de llaves mediante búsqueda binaria propia (R3).
4. Selección determinista de la llave de menor `id` lexicográfico entre varias disponibles mediante la reutilización del montículo propio `MonticuloMin` (`src/estructuras_datos/monticulo.py`), garantizando orden estricto (FR-010) en $O(|K| \log |K|)$ sin degradar a cuadrático (R3b).
5. Un registro de puertas en espera indexado por llave que reactiva las salidas bloqueadas en $O(1)$ cuando se descubre su llave correspondiente (R4), sin volver a explorar salas ya visitadas.
6. Construcción del grafo de dependencias de llaves y detección determinista de ciclos mediante una **búsqueda en profundidad (DFS) estrictamente iterativa con pila propia**, desvinculada del límite de recursión del intérprete ante cadenas largas de llaves (R5).
7. Integración en CLI (`--verificar <cripta>`, `--forzar`) con códigos de salida explícitos (0, 1, 2) y sin instanciar la vista interactiva (R7).
8. Consulta de llaves en `GET /criptas/<id>/llaves` reutilizando directamente `ApiClient._get` con espera exacta según `reintentar_en` ante HTTP 429 (sin retroceso exponencial), respetando el presupuesto de red y con persistencia validada por versión (R6).
9. Escenarios de `--bench` que miden el escalamiento lineal frente a la alternativa ingenua de recorrido repetido, verifican la robustez iterativa ante cadenas profundas y validan el límite de 200 ms (R8). Detalle en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11+ (entorno de pruebas en Python 3.14).

**Primary Dependencies**: `requests` (únicamente en el adaptador de red existente `ApiClient`, sin librerías nuevas). Cero dependencias adicionales.

**Storage**: Archivos JSON locales para la caché de llaves (`llaves.json`) validados contra la versión de la cripta y el catálogo.

**Testing**: `unittest`, ejecutable también mediante `pytest`. Cada prueba unitaria o de aceptación cita su requisito funcional (`FR-NNN`) o escenario de aceptación correspondiente.

**Target Platform**: Consola multiplataforma (Windows, Linux, macOS).

**Project Type**: Aplicación de consola MVC con adaptadores de red y persistencia.

**Performance Goals**:
- Verificación completa en menos de 200 ms en la cripta publicada más grande sin red ni renderizado (FR-026, SC-003).
- Crecimiento de tiempo total aproximadamente lineal $O(|V| + |E| + |K|)$ en función de salas, salidas y llaves (FR-027, SC-004).
- Ejecución de `--verificar <cripta>` en menos de 250 ms en consola local (SC-006).

**Constraints**:
- Principio I: Prohibido el uso de `dict` y `set` como índice, caché, tabla de búsqueda o registro de visitados; prohibidos `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` o cualquier biblioteca de grafos.
- Principio II: Determinismo estricto; el mismo orden de llaves y la misma detección de ciclos ante ejecuciones repetidas.
- Principio III: Separación estricta MVC; `--verificar` no instancia la vista gráfica/interactiva.
- Principio IV: Ningún dato de una cripta concreta grabado en código.
- Principio V: Toda llamada de red cuenta en `presupuesto_solicitudes`; no se consulta lo que ya esté persistido con versión vigente.

**Scale/Scope**: Criptas publicadas desde 20 hasta más de 1 000 salas; criptas sintéticas en `--bench` con cadenas de hasta 100+ llaves encadenadas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento en este plan | Estado |
|---|---|---|
| **I. Estructuras propias** | Toda la lógica de verificación utiliza arreglos contiguos nativos (`list` indexada por entero) para visitados y colas, ordenamiento propio (`src/estructuras_datos/ordenamiento.py`) y búsqueda binaria propia. Se reutiliza `MonticuloMin` (`src/estructuras_datos/monticulo.py`) para el desempate determinista de llaves disponibles (R3b). La detección de ciclos utiliza DFS iterativo con pila propia en lista nativa (R5). Sin `dict`, `set`, `deque`, `bisect` ni bibliotecas de grafos. `tests/test_restricciones.py` vigilará automáticamente los módulos nuevos mediante AST. | ✅ |
| **II. Determinismo** | Desempate canónico de llaves disponibles por orden alfanumérico creciente de `id` (FR-010). Detección de ciclos normalizada iniciando por la llave de menor `id` lexicográfico (FR-016). Criptas sintéticas deterministas gobernadas por `random.Random(semilla)`. | ✅ |
| **III. MVC** | El módulo `src/modelos/resolubilidad.py` es modelo puro. La orquestación reside en `src/servicios/verificador_servicio.py`. El controlador (`main.py`) coordina `--verificar` y `--forzar` sin instanciar la vista interactiva. | ✅ |
| **IV. Sin datos de cripta** | No se incluyen identificadores, nombres ni salas de criptas publicadas en el código fuente. Las pruebas utilizan fixtures y criptas sintéticas generadas deterministamente. | ✅ |
| **V. Presupuesto de red** | `GET /criptas/<id>/llaves` cuenta 1 solicitud en `presupuesto_solicitudes`. La respuesta se persiste localmente y no se vuelve a pedir mientras coincida la versión ni en modo `--offline` (FR-022, FR-024). | ✅ |
| **VI. Estado reversible** | La verificación se ejecuta antes de la partida y no forma parte del historial de juego ni del pergamino de retroceso. | ✅ |
| **VII. Rendimiento medido** | `--bench` incorpora escenarios para medir el tiempo en cripta grande (< 200 ms) y comparar la linealidad del recorrido único frente a la alternativa ingenua cuadrática de recorrido repetido. | ✅ |
| **VIII. Spec antes que código** | La especificación `spec.md` y la sesión de clarificación fueron formalizadas y completadas previamente. | ✅ |

**Re-evaluación posterior al diseño (Phase 1)**: El diseño satisface la totalidad de las directrices constitucionales sin excepciones.

## Project Structure

### Documentation (this feature)

```text
specs/002-verificacion-resolubilidad/
├── spec.md                  # Especificación de requisitos y clarificaciones
├── plan.md                  # Este archivo de arquitectura y diseño
├── research.md              # Phase 0: Decisiones técnicas R1–R8 y alternativas
├── data-model.md            # Phase 1: Entidades, estructuras y modelos de datos
├── quickstart.md            # Phase 1: Guía de validación y escenarios ejecutables
├── contracts/
│   └── interfaz-y-reporte.md # Phase 1: Contrato de CLI, salida en consola y API de llaves
└── checklists/
    └── requirements.md      # Lista de control de calidad de requisitos
```

### Source Code (repository root)

```text
src/
├── estructuras_datos/
│   ├── monticulo.py              # REUTILIZADO: MonticuloMin de capacidad 001 para desempate canónico de llaves (R3b)
│   ├── ordenamiento.py           # EXISTENTE: ordenamiento por mezcla e inserción del grupo
│   └── busqueda_binaria.py       # NUEVO: búsqueda binaria propia en lista ordenada
├── modelos/
│   ├── resolubilidad.py          # NUEVO: VerificadorResolubilidad, ReporteResolubilidad (modelo puro con DFS iterativo)
│   └── cripta.py                 # EXISTENTE: Cripta, Sala, Salida, Puerta (reutiliza Sala.indice)
├── adaptadores/
│   ├── api_client.py             # MOD: obtener_llaves(cripta_id) reutilizando _get y espera en reintentar_en ante HTTP 429
│   ├── fuente_datos.py           # MOD: firma abstracta obtener_llaves
│   ├── fuente_sin_conexion.py    # MOD: lectura de llaves desde llaves.json local
│   └── fuente_memoria.py         # MOD: soporte de llaves en memoria para pruebas y bench
├── servicios/
│   ├── verificador_servicio.py   # NUEVO: carga de esqueleto + llaves con persistencia y verificación
│   ├── cargador_cripta.py        # EXISTENTE: carga de datos y esqueleto
│   └── banco_resolubilidad.py    # NUEVO: escenarios de --bench para resolubilidad y alternativa ingenua
├── controladores/
│   └── controlador_juego.py      # MOD: flujo de inicio con verificación previa y soporte --forzar
└── main.py                       # MOD: argumentos --verificar y --forzar, despacho de salida

tests/
├── test_resolubilidad.py         # NUEVO: pruebas unitarias de resolubilidad y Apéndice B
├── test_verificador_servicio.py  # NUEVO: pruebas de persistencia, presupuesto y red de llaves
├── test_cli_verificar.py         # NUEVO: pruebas de interfaz CLI (--verificar, --forzar, exit codes)
└── test_restricciones.py         # MOD: vigilar módulos nuevos de capacidad 002 con AST
```

---

## Diseño del Algoritmo de Recorrido Único $O(|V| + |E| + |K|)$

### 1. Inicialización e Indexación de Llaves
1. Se extrae la lista de identificadores únicos de llaves presentes en la cripta (obtenidas de `GET /criptas/<id>/llaves` y de las puertas cerradas del esqueleto).
2. Se ordenan lexicográficamente con `ordenar(ids)` para construir una lista canónica `claves_llaves` de tamaño $m = |K|$.
3. Se inicializan las estructuras de tamaño fijo indexadas por enteros:
   - `llave_obtenida = [False] * m`
   - `puertas_en_espera = [[] for _ in range(m)]`
   - `sala_de_llave = [None] * m` (asigna la sala inicial de cada llave según los datos del endpoint)
   - `llaves_en_sala = [[] for _ in range(n)]` (indexado por `Sala.indice`, agrupa llaves presentes en cada sala)
   - `llaves_disponibles = MonticuloMin()`: montículo binario propio reutilizado de `src/estructuras_datos/monticulo.py` para gestionar la frontera de llaves alcanzadas (R3b).

### 2. Recorrido Principal (BFS Reactivo con Selección por Montículo)
1. Se inicializa la cola de exploración continua `cola = [sala_inicial]`, `cabeza = 0`, y el arreglo `visitada = [False] * n` con `visitada[sala_inicial.indice] = True`.
2. Se ejecuta el bucle de expansión por etapas:
   - Mientras `cabeza < len(cola)` o no `llaves_disponibles.esta_vacio()`:
     a. **Fase de expansión de salas**: Mientras `cabeza < len(cola)`:
        - Se toma `u = cola[cabeza]` y se incrementa `cabeza += 1`.
        - **Detección de llaves en sala**: Si en la sala $u$ existen llaves en `llaves_en_sala[u.indice]`:
          - Por cada llave $k$ con índice $j$:
            - Si no ha sido obtenida ni insertada previamente en disponibles, se inserta en el montículo: `llaves_disponibles.insertar(j, j)`.
        - **Exploración de salidas**: Para cada salida saliente $(u, v)$ desde $u$:
          - Si la salida no está cerrada:
            - Si `visitada[v.indice]` es `False`: se marca `visitada[v.indice] = True` y `cola.append(v)`.
          - Si la salida está cerrada requiriendo llave $k$ (con índice $j$):
            - Si `llave_obtenida[j]` es `True`:
              - Si `visitada[v.indice]` es `False`: se marca `visitada[v.indice] = True` y `cola.append(v)`.
            - Si `llave_obtenida[j]` es `False`:
              - Se registra la puerta en espera: `puertas_en_espera[j].append(v)`.
              - Se agrega la puerta a la lista de `frontera_bloqueada`.
     b. **Fase de obtención determinista de llave**: Si `cabeza == len(cola)` pero existen llaves alcanzadas en `llaves_disponibles`:
        - Se extrae la llave mínima disponible: `(j_min, _) = llaves_disponibles.extraer_minimo()`.
        - Dado que los índices $0 \dots m-1$ preservan el orden alfanumérico creciente de `id`, esto garantiza que se escoja deterministamente la llave de menor `id` lexicográfico entre todas las disponibles en esa etapa (FR-010).
        - Se marca `llave_obtenida[j_min] = True` y se agrega `claves_llaves[j_min]` a la lista de resultado `orden_llaves`.
        - **Reactivación de salidas en espera**: Se recuperan las puertas que esperaban por $j_{\min}$ en `puertas_en_espera[j_min]`. Para cada sala destino $v$:
          - Si `visitada[v.indice]` es `False`:
            - Se marca `visitada[v.indice] = True`.
            - Se añade $v$ al final de la cola `cola.append(v)`.
        - Se limpia `puertas_en_espera[j_min]`.
        - El bucle continúa expandiendo las salas recién desbloqueadas.

### 3. Veredicto de Resolubilidad
1. Una vez que no quedan salas por explorar ni llaves disponibles por procesar:
   - Se comprueba si `llave_salida` fue obtenida.
   - Se comprueba si se alcanzó `sala_salida` a través de una puerta que requiera `llave_salida` (FR-007).
2. Si ambas condiciones se cumplen:
   - **Veredicto**: `resoluble = True`.
   - **Resultado**: `orden_llaves` (secuencia canónica determinista).

---

## Detección Determinista de Ciclos mediante DFS Iterativo con Pila Propia

Si la cripta no es resoluble:
1. **Llaves inalcanzables**: Llaves en $K$ que mantuvieron `llave_obtenida == False`.
2. **Frontera bloqueada**: Todas las puertas registradas en `puertas_en_espera` para llaves no obtenidas. Para cada puerta se reporta su sala origen, dirección, llave requerida y la sala donde se ubica dicha llave.
3. **Grafo de dependencias de llaves**:
   - Para cada puerta de frontera hacia $v \notin R$ que requiere llave $k$:
     - Se exploran las salas no alcanzadas conectadas a $v$ que se volverían accesibles si se abriera la puerta.
     - Si en esa región se encuentra otra llave no obtenida $k'$, se registra la dependencia dirigida $k \to k'$.
4. **Búsqueda en profundidad (DFS) estrictamente iterativa**:
   - Para evitar `RecursionError` ante el límite de recursión del intérprete (`sys.getrecursionlimit()`) con cadenas largas de llaves ($\ge 1000$ llaves encadenadas), la búsqueda se implementa de manera **iterativa utilizando una lista nativa como pila propia LIFO** (`pila = [...]`) y un arreglo de estados de tres marcas (`0: NO_VISITADO, 1: EN_PROCESO, 2: PROCESADO`).
   - Se procesan los nodos en orden alfabético creciente de su `id` de llave:
     - Si un nodo está en estado `0`, se inicia un recorrido iterativo apilando `(nodo_inicial, 0)` y agregando `nodo_inicial` a una lista `camino`. Se marca como `1: EN_PROCESO`.
     - En cada paso del bucle iterativo, se examina el tope de la pila `(u, idx)`:
       - Si `idx < len(adyacentes[u])`:
         - Se toma el vecino $v = \text{adyacentes}[u][idx]$ y se actualiza el tope a `(u, idx + 1)`.
         - Si `estado[v] == 1` (`EN_PROCESO`):
           - Se detecta un ciclo. Se extrae la subsecuencia desde $v$ hasta el final de `camino` y se añade $v$ para cerrar el ciclo (`[v, ..., u, v]`).
           - Se rota la secuencia para que comience con la llave de menor identificador lexicográfico del ciclo (`[L_min -> ... -> L_min]`).
           - Se almacena el ciclo normalizado si no fue registrado previamente.
         - Si `estado[v] == 0` (`NO_VISITADO`):
           - Se marca `estado[v] = 1`, se añade $v$ a `camino` y se apila `(v, 0)`.
       - Si `idx == len(adyacentes[u])`:
         - Se terminaron los vecinos de $u$. Se marca `estado[u] = 2` (`PROCESADO`), se desapila de `pila` y se remueve $u$ de `camino` con `pop()`.
   - Se ordenan canónicamente todos los ciclos detectados por su llave inicial.
   - **Complejidad**: $O(|K| + |E_K|)$ tiempo y $O(|K|)$ memoria en el heap, totalmente inmune a desbordamientos de la pila de llamadas del sistema.

---

## Plan de Pruebas y Validación con `--bench`

1. **Casos de aceptación obligatorios (Apéndice B)**:
   - `test_caso_1_ciclo_llave_salida`: `llave_salida` tras la única puerta que abre -> irresoluble, ciclo reportado `[llave_salida -> llave_salida]`.
   - `test_caso_2_llave_enemigo_errante`: Llave en `suelta` de errante -> ubicada en sala inicial del enemigo.
   - `test_caso_3_orden_determinista_bifurcaciones`: Cripta con múltiples órdenes válidos -> dos ejecuciones generan exactamente la misma secuencia desempatando con `MonticuloMin` por `id` lexicográfico.
   - `test_caso_4_bloqueo_sin_forzar`: Cripta no resoluble sin `--forzar` detiene la partida y muestra reporte; con `--forzar` inicia la partida.
2. **Pruebas de CLI y retorno de proceso**:
   - `--verificar <cripta>` devuelve 0 en resoluble, 1 en irresoluble, 2 en error.
3. **Pruebas de robustez y límite de recursión**:
   - Prueba unitaria con cadena sintética profunda de 1 500 llaves encadenadas cíclicamente para validar que el DFS iterativo detecta el ciclo sin lanzar `RecursionError`.
4. **Mediciones en `--bench`**:
   - **Límite de 200 ms**: Cripta sintética de 1 000 salas con decenas de puertas y llaves para verificar que el tiempo medio es < 200 ms.
   - **Escalamiento lineal vs. Alternativa ingenua**: Familias de cadenas de llaves encadenadas crecientes ($N \in \{10, 25, 50, 100, 500\}$), comparando:
     - *Algoritmo lineal reactivo propuesto*: $O(|V| + |E| + |K| \log |K|)$ con reactivación de puertas y selección con `MonticuloMin`.
     - *Alternativa ingenua*: Repetición completa del recorrido cada vez que se descubre una llave ($O(|K| \cdot (|V| + |E|))$).
     - Medición y graficación empírica demostrando el crecimiento lineal frente a la curva cuadrática de la alternativa ingenua.
