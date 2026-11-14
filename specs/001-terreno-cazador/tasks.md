---

description: "Lista de tareas de la capacidad terreno con costo y enemigo cazador"
---

# Tasks: Terreno con costo y enemigo cazador

**Input**: Documentos de diseño de `/specs/001-terreno-cazador/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/interfaz-y-bench.md](contracts/interfaz-y-bench.md)

**Tests**: son obligatorios. La constitución («Separación de artefactos y trazabilidad») y SC-001
exigen al menos una prueba automatizada por escenario de aceptación, y cada prueba cita su
requisito (`FR-NNN`) en el nombre o en el docstring. Las pruebas se escriben primero y deben fallar
antes de implementar.

**Organization**: tareas agrupadas por historia de usuario. Cada tarea indica entre llaves los
requisitos que atiende; no hay tareas sin requisito (constitución).

## Format: `[ID] [P?] [Story] Descripción {requisitos}`

- **[P]**: puede hacerse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de usuario de la tarea (US1 a US5)

## Path Conventions

Proyecto único: `src/` y `tests/` en la raíz del repositorio (ver la estructura del plan).

## Convenciones de determinismo (aplican a todas las fases)

Estas reglas fijan el resultado exacto que deben producir el código y la referencia:

- **D1. Solo enteros.** Costos, distancias y cotas son `int`. «Sin distancia» se representa con la
  ausencia de marca de generación en el registro, nunca con `float('inf')` ni con `None` mezclado
  en comparaciones.
- **D2. Orden de salidas fijo.** Toda iteración sobre las salidas de una sala recorre las
  direcciones en el orden N, S, E, O (índices 0 a 3 de `Sala.salidas`), nunca el orden de un
  diccionario de JSON.
- **D3. Orden del montículo.** Las entradas se comparan como la tupla `(costo, indice_sala)`: menor
  costo primero y, si empatan, menor índice. Ninguna decisión del juego depende de este orden
  secundario (ver D5); solo hace que la ejecución sea repetible.
- **D4. Clave de decisión del cazador.** Entre todas las salidas abiertas `s` de la sala `u` del
  cazador, con vecina `v` registrada, se elige la de menor tupla
  `(costo(s) + dist(v), id(v), costo(s), orden_direccion(s))`. Así se obtienen en ese orden: costo
  total mínimo (FR-013), menor id de vecina (FR-014), salida más barata hacia esa vecina y orden
  N, S, E, O (FR-015). Si la tupla mínima tiene `costo(s) + dist(v) > rango`, o no hay ninguna, el
  cazador espera (FR-012).
- **D5. Independencia del índice compacto.** Las decisiones dependen de los **id** de sala, nunca
  de `Sala.indice`. Cargar las mismas salas en otro orden de páginas DEBE producir exactamente las
  mismas decisiones.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dejar listo el andamiaje de pruebas de la capacidad. Todas las pruebas de
equivalencia, determinismo, reutilización y escala dependen de que las criptas generadas sean
**correctas y reproducibles**; por eso la generación se especifica y se prueba antes que todo lo
demás.

### Generación de criptas: reglas comunes

- **G1. Mismo camino que los datos reales, como texto JSON.** El generador **no crea
  diccionarios**: escribe el esqueleto como **texto JSON** con exactamente la estructura que devuelve
  el servicio en `GET /criptas/<id>/salas?pagina=n`. Ese texto se lee con `json.loads`, igual que
  `--offline` lee sus archivos, y la cripta se construye con el cargador real (`_sala_desde_dict` y
  `Cripta.enlazar_puertas`). Así los únicos diccionarios que existen son **los que produce la
  lectura de JSON y solo se leen**, que es lo que permite la constitución (Principio I, P1 §7). Las
  pruebas ejercitan además la misma lectura y validación del costo que los datos reales.
  - **Cómo se escribe el texto**: con una `list` de fragmentos de texto que se une al final con
    `"".join(...)`. Los textos se escriben con `json.dumps` aplicado **solo a valores escalares**
    (`int` y `str`), nunca a diccionarios. Ninguna parte del generador usa `{...}`, `dict(...)` ni
    `set(...)`.
  - **Salida de `cripta_sintetica`**: una `list` de `str`, un fragmento de texto JSON por sala,
    ordenada por id ascendente (`1..n`).
  - **Cada sala**: `{"id": int, "nombre": str, "salidas": {...}}`, con `nombre` igual a
    `"Sala sintética <id>"`.
  - **`salidas`**: claves solo entre `"N"`, `"S"`, `"E"`, `"O"`, insertadas siempre en ese orden y
    solo para las conexiones que existen. Cada valor es `{"sala": int}` más, solo cuando aplican:
    `"costo": int` (entero entre `costo_min` y `costo_max`; se omite si la conexión no declara
    costo); `"cerrada": true` (se omite si está abierta); `"llave": str` (solo si está cerrada, con
    la forma `"itm_llave_sint_<k>"`, donde `k` es el número de la conexión); y
    `"cierre_automatico": int` (solo si se pidió).
  - **Simetría en la salida**: los dos lados de una conexión llevan los mismos `costo`, `cerrada` y
    `llave` (G2).
  - **Paginación**: `paginar` une los fragmentos en textos de página con la forma del servicio,
    `{"pagina": int, "total_paginas": int, "salas": [...]}`, también por concatenación de texto.
- **G2. Coherencia del mapa.** Toda salida tiene su pareja en la dirección opuesta (N↔S, E↔O) con la
  misma sala de vuelta; ninguna sala usa dos veces la misma dirección; los ids son únicos; ninguna
  salida apunta a una sala inexistente; el costo es simétrico, y cuando se omite en un lado, el otro
  lo declara o ninguno (FR-002).
- **G3. Reproducibilidad.** Toda aleatoriedad usa una instancia propia `random.Random(semilla)`,
  nunca el generador global. Misma semilla y mismos parámetros → la misma lista de salas, byte a
  byte al serializarla.
- **G4. Ids no correlacionados con la posición.** Los ids `1..n` se asignan con una permutación
  sembrada, para que el desempate por menor id (FR-014) se pruebe de verdad y no coincida por
  casualidad con el orden de la cuadrícula. Su estructura es:
  - **Posición**: cada celda `(fila, columna)` de la cuadrícula tiene la posición
    `p = fila · ancho + columna`, en `0..n-1`, con `n = ancho · alto`.
  - **`id_de_posicion`**: `list` de tamaño `n`. Empieza como `[1, 2, …, n]` y se baraja con
    Fisher–Yates explícito: para `i` desde `n-1` hasta `1`, `j = rng.randrange(i + 1)` e intercambiar
    las posiciones `i` y `j`. No se usa `random.shuffle`, para que el algoritmo quede escrito y
    documentado.
  - **`posicion_de_id`**: `list` de tamaño `n + 1` (la posición 0 no se usa), la inversa:
    `posicion_de_id[id_de_posicion[p]] = p`.
  - **Vecinas por posición**, sin buscar en ninguna tabla: N = `p - ancho` si `fila > 0`;
    S = `p + ancho` si `fila < alto - 1`; E = `p + 1` si `columna < ancho - 1`; O = `p - 1` si
    `columna > 0`.
  - **Conexiones numeradas**: la conexión hacia el E de `p` tiene número `2p` y la conexión hacia el
    S de `p` tiene número `2p + 1`. Las de O y N son las mismas vistas desde la otra sala. Todo el
    estado de una conexión (`existe`, `en_arbol`, `costo`, `declara_costo`, `cerrada`) va en `list`
    de tamaño `2n` indexadas por ese número.

- **G5. Recorridos sin `set` ni `dict`.** Todo recorrido sobre el mapa, ya sea en el generador, en
  sus pruebas, en la referencia o en `--bench`, marca las salas visitadas en una **`list` de
  booleanos o de generación indexada** (por posición en el generador, por `Sala.indice` en el
  modelo o por id en la referencia, con tamaño `n + 1`) y usa una `list` como pila o cola. Nunca se
  usa `set`, `dict` ni `in` sobre una lista de visitadas.

- [ ] T001 Implementar `src/servicios/generador_criptas.py`, usado tanto por las pruebas como por `--bench` (FR-035), con estas funciones:
  - `cripta_sintetica(semilla, ancho, alto, costo_min=1, costo_max=300, prob_cerrada=0.0, prob_sin_costo=0.0, prob_hueco=0.0, conexa=True, conexa_abierta=False)`: cuadrícula `ancho × alto` donde cada sala se conecta con sus vecinas N, S, E, O. Usa una sola instancia `rng = random.Random(semilla)` y consume sus números **siempre en este orden**, para que la misma semilla dé la misma cripta (G3):
    1. **Permutación de ids** con Fisher–Yates sobre `id_de_posicion` y cálculo de `posicion_de_id` (G4).
    2. **Árbol de expansión** (solo si `conexa`): recorrido en profundidad desde la posición 0 con `visitada = [False] * n` (lista indexada por posición, G5) y `pila = [0]` (`list`). En cada paso se toma la posición de la cima, se juntan en una `list` sus vecinas no visitadas en orden N, S, E, O; si hay, se elige una con `rng.randrange(len(candidatas))`, se marca `en_arbol[numero_conexion] = True` y `visitada[v] = True`, y se apila; si no hay, se desapila. Termina con la pila vacía.
    3. **Huecos**: se recorren las conexiones posibles de la cuadrícula por número ascendente; para cada una se sortea `r = rng.random()` y `existe[c] = en_arbol[c] or r >= prob_hueco`.
    4. **Costos**: por número ascendente, para **cada** conexión posible se sortean `r = rng.random()` y `valor = rng.randint(costo_min, costo_max)`; si la conexión existe, `declara_costo[c] = r >= prob_sin_costo` y `costo[c] = valor`.
    5. **Puertas cerradas**: por número ascendente, para cada conexión posible se sortea `r = rng.random()`; si existe, `cerrada[c] = r < prob_cerrada`, salvo que `conexa_abierta` y `en_arbol[c]`, en cuyo caso queda abierta.
    6. **Salida**: para cada id de `1` a `n`, se toma `p = posicion_de_id[id]` y la función `_texto_sala` arma el fragmento de texto JSON de esa sala con sus salidas en orden N, S, E, O y la estructura de G1, uniendo fragmentos de una `list` con `"".join`; los valores escalares pasan por `json.dumps`. No se crea ningún diccionario.
  - Los sorteos de cada paso se hacen para todas las conexiones posibles y aunque la probabilidad sea 0, para que cambiar un parámetro o el resultado de un paso no desplace los números aleatorios de los pasos siguientes;
  - `cripta_ampliada_x10(semilla, parametros_base, sala_jugador, rango)`: regenera la base con la misma semilla y parámetros (sus listas internas de G4, no texto ya leído) y devuelve una cripta 10 veces más grande en la que la **región a distancia ≤ rango de `sala_jugador` es idéntica** a la de `base`. Las salas nuevas se cuelgan de una sala de la base que está fuera del rango, mediante un pasillo cuyo costo supera `rango`, para que ninguna sala nueva quede dentro de la región (SC-004);
  - `paginar(fragmentos, tam_pagina, semilla=None)`: parte la lista de fragmentos en textos de página como el servicio, en orden original o barajado con Fisher–Yates sembrado (para D5);
  - `ficha_cazador(id, rango, velocidad=100, ...)`: texto JSON de una ficha de catálogo con `comportamiento: cazador` y `rango`, armado igual que las salas;
  - `cargar_cripta_sintetica(paginas)`: entrega los textos mediante una fuente en memoria, `src/adaptadores/fuente_memoria.py`, que implementa la misma interfaz de fuente de datos que usa `--offline` (`src/adaptadores/fuente_datos.py`, P1 §3.4), la cual lee cada texto con `json.loads`, y construye la `Cripta` con el cargador real (G1). Así el modelo no distingue datos sintéticos de datos del servicio;
  - ningún `dict` ni `set` en todo el módulo: todo el estado interno va en `list` indexadas (G4, G5). {FR-001, FR-002, FR-030, FR-035}
- [ ] T002 Escribir `tests/test_generador_criptas.py`, que verifica la corrección del generador antes de usarlo en cualquier otra prueba:
  - G3: la misma semilla produce exactamente los mismos textos (comparación de `str`); semillas distintas producen textos distintos;
  - G2: cada salida tiene su pareja opuesta con el mismo costo y el mismo estado de puerta; no hay direcciones repetidas ni destinos inexistentes; los ids son exactamente `1..n`;
  - G1: cada fragmento es JSON válido; al **leerlo** con `json.loads`, la estructura coincide campo por campo con G1 (claves permitidas comparadas contra una `list` de nombres, orden N, S, E, O, campos opcionales omitidos cuando no aplican, tipos `int` y `str`, salas ordenadas por id). La prueba solo lee los diccionarios producidos por `json.loads`; no escribe ninguno;
  - G4: `posicion_de_id` es la inversa exacta de `id_de_posicion`; los ids no siguen el orden de la cuadrícula (la permutación no es la identidad para las semillas usadas); con una semilla fija, la permutación coincide con un valor esperado escrito en la prueba, que detecta cambios accidentales en el orden de consumo de `rng`;
  - con `conexa=True` y sin puertas cerradas, toda sala es alcanzable desde la sala 1, verificado con un recorrido que usa `visitada = [False] * (n + 1)` indexada por id y una `list` como pila (G5); con `prob_hueco` alto y `conexa=False` aparece al menos una sala inalcanzable para alguna semilla fija;
  - las proporciones de huecos, puertas cerradas y costos omitidos están dentro de ±5 puntos de lo pedido en una cripta de 10 000 salas;
  - `cripta_ampliada_x10`: tiene 10 veces las salas, y el conjunto de salas a distancia ≤ rango de la sala del jugador (calculado con la referencia de T025) es idéntico en ambas (este punto se activa cuando exista T025);
  - la cripta generada se carga sin error con el cargador real (G1). {FR-001, FR-002, FR-030, FR-035}
- [ ] T003 Crear `tests/utilidades_cripta.py` con constructores de criptas pequeñas **escritas a mano** para los escenarios de aceptación: `cripta_desde_conexiones([(id_a, dir, id_b, costo, cerrada, llave), ...])`, que crea automáticamente la salida opuesta, arma el texto JSON con las mismas funciones de texto de T001 (sin crear diccionarios), lo carga con `cargar_cripta_sintetica` y aplica G1 y G2 (lanza error si se repite una dirección o una conexión es incoherente), más ayudas para colocar al jugador y a los cazadores, reutilizando `tests/utilidades.py` {FR-001, FR-011}
- [ ] T004 Ejecutar `python -m pytest -q` y registrar que la batería de P1 pasa antes de empezar (línea base de SC-007) {FR-005, FR-007, SC-007}

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: estructuras y campos de los que dependen todas las historias.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

### 2.1 Prohibición de estructuras de conveniencia (primero que todo)

La constitución (Principio I) y FR-021 prohíben resolver los problemas evaluados con estructuras de
conveniencia de Python o de bibliotecas. Esta fase empieza con una verificación automática para que
la prohibición no dependa de revisiones manuales.

- [ ] T005 Escribir `tests/test_restricciones.py`, una prueba estática con el módulo `ast` que recorre los archivos de la capacidad (`src/estructuras_datos/monticulo.py`, `src/estructuras_datos/registro_busqueda.py`, `src/modelos/rutas.py`, `src/modelos/cazador.py`, `src/servicios/generador_criptas.py`, `tests/referencia_cazador.py`, `tests/test_generador_criptas.py` y `tests/utilidades_cripta.py`) y **falla** si encuentra:
  - importaciones de `heapq`, `bisect`, `collections` (incluidos `deque`, `OrderedDict`, `defaultdict`, `Counter`), `queue`, `networkx`, `functools.lru_cache` o `functools.cache`, ni ninguna biblioteca de grafos o de búsqueda de rutas;
  - literales o constructores de diccionario o conjunto (`{}`, `{k: v}`, `{a, b}`, `dict(...)`, `set(...)`, `frozenset(...)`) y comprensiones de diccionario o conjunto;
  - llamadas a `sorted(...)` o `.sort(...)` (P1 §4.9);
  - el mensaje de falla indica archivo, línea y construcción prohibida.
  **Sin excepciones**: como el generador escribe texto JSON (G1), ningún archivo vigilado necesita literales de diccionario. Se permite leer los diccionarios que devuelve `json.loads`, que es lo que autoriza la constitución.
  La lista de archivos vigilados se amplía en cada tarea que crea un módulo nuevo de la capacidad. Se permite `list` como almacenamiento contiguo (P1 §7). {FR-021, FR-030}

### 2.2 Pruebas de la fase (escribir primero)

- [ ] T006 [P] Escribir `tests/test_monticulo.py` para el mecanismo exacto de T010:
  - orden por la tupla `(costo, indice)` (D3), con empates de costo resueltos por menor índice;
  - **entradas obsoletas**: insertar `(50, 7)` y después `(30, 7)` para la misma sala; el primer `extraer_minimo` devuelve `(30, 7)`; el `(50, 7)` sigue en el montículo y, al extraerlo, el consumidor lo reconoce como obsoleto (ver T010), así que una sala nunca se asienta dos veces;
  - el tamaño del montículo es el número de inserciones menos el de extracciones (las obsoletas no se borran antes de tiempo); `minimo()` devuelve lo mismo que el siguiente `extraer_minimo()` y no cambia el tamaño;
  - `extraer_minimo` en vacío lanza `IndexError`; `vaciar()` deja el montículo reutilizable;
  - secuencia sembrada de 10 000 operaciones comparada con una referencia de búsqueda lineal: misma secuencia de extracciones. {FR-014, FR-030}
- [ ] T007 [P] Escribir `tests/test_registro_busqueda.py`: `nueva_busqueda()` incrementa la generación en O(1) sin recorrer las listas; tras ella `tiene(i)` y `asentada(i)` son falsos para todo `i`; los valores de una generación anterior no se leen como válidos; el contador `examinadas` se reinicia por búsqueda y suma 1 **solo la primera vez** que una sala recibe distancia en la generación, de modo que una sala de borde que después se asienta (al extender la búsqueda) no se cuenta dos veces (research R9) {FR-030}
- [ ] T008 [P] Escribir en `tests/test_terreno.py` las pruebas de carga del costo: ausente → 100; «entero ≥ 1»; un solo lado declara → vale para ambos; ambos distintos → `ErrorDatos` con salas y direcciones; menor que 1 o no entero → `ErrorDatos` con sala y dirección; y cargar una cripta con costos y cazadores hace **exactamente la misma cantidad de solicitudes** que la misma cripta sin esos campos, medido con el contador de la fuente simulada {FR-001, FR-002, FR-008, FR-025}
- [ ] T009 [P] Escribir en `tests/test_cazador.py` las pruebas de la ficha: `comportamiento: cazador` con `rango` «int ≥ 0»; ficha `cazador` sin `rango` válido → `ErrorDatos` con el id de la ficha, sin valor por defecto {FR-009}

### 2.3 Implementación de la fase

- [ ] T010 [P] Implementar `MonticuloMin` en `src/estructuras_datos/monticulo.py` (research R1), sin `heapq`, con **eliminación perezosa** exacta:
  - **Almacenamiento**: una `list` de pares `(costo, indice)` organizada como montículo binario de mínimos (hijo izquierdo `2i+1`, derecho `2i+2`, padre `(i-1)//2`), con comparación por la tupla de D3.
  - **Operaciones**: `insertar(costo, indice)` agrega al final y sube, O(log k); `extraer_minimo()` intercambia la raíz con el último, quita el último y baja, O(log k); `minimo()` devuelve la raíz sin extraerla, O(1), para que la búsqueda pueda **pausar** sin perder la entrada (research R5); `esta_vacio()` O(1); `vaciar()` reutiliza la lista.
  - **Sin «disminuir clave»**: el montículo no sabe nada de salas ni de obsolescencia. Cuando la búsqueda (T036) encuentra un costo menor para una sala, **inserta una entrada nueva** y deja la anterior en el montículo.
  - **Regla de obsolescencia** (la aplica el consumidor, T036, al extraer `(c, i)`): la entrada es obsoleta y se descarta sin examinar la sala si (a) la sala `i` ya está asentada en la generación actual, o (b) `c` es distinto de la distancia registrada de `i` en la generación actual (llegó una entrada más barata después). En otro caso se asienta.
  - **Cota de memoria**: cada inserción corresponde a una mejora de distancia; con a lo sumo 4 salidas por sala, el montículo nunca supera `1 + 4 · salas_asentadas` entradas, así que la memoria crece con la región examinada y no con la cripta.
  - Documentar en el docstring el porqué de la eliminación perezosa (evita llevar la posición de cada sala dentro del montículo) y su costo: hasta 4 entradas por sala en lugar de 1. {FR-014, FR-030}
- [ ] T011 [P] Implementar `RegistroBusqueda` en `src/estructuras_datos/registro_busqueda.py` (research R2): listas de tamaño n indexadas por `Sala.indice` para `distancia`, `primer_paso`, `marca` (generación en que se registró una distancia tentativa) y `asentada` (generación en que se asentó); entero `generacion`; contador `examinadas` que suma 1 la primera vez que una sala recibe `marca == generacion` (research R9). Sin `dict`, `set` ni hash {FR-021, FR-030}
- [ ] T012 Agregar `Puerta.costo` («int ≥ 1», 100 por defecto), `Salida.sala_destino` y `Sala.indice` en `src/modelos/entidades.py` (data-model) {FR-001, FR-002}
- [ ] T013 Asignar `Sala.indice` compacto en orden de carga en `Cripta.agregar_sala`, enlazar `Salida.sala_destino` y fusionar o validar el costo de ambos lados en `Cripta.enlazar_puertas` en `src/modelos/cripta.py` (depende de T012; research R3 y R4) {FR-001, FR-002, FR-008}
- [ ] T014 Leer y validar `costo` en `_sala_desde_dict` de `src/servicios/cargador_cripta.py`, guardando si el lado lo declaró para que `enlazar_puertas` valide la simetría (depende de T013) {FR-001, FR-002, FR-008, FR-025}
- [ ] T015 Agregar `rango` y el comportamiento `cazador` en `src/modelos/fichas.py`, y leerlos y validarlos en `src/servicios/fabrica_fichas.py` (ver T009) {FR-009, FR-025}

**Checkpoint**: T005 a T009 pasan; la batería de P1 sigue pasando.

---

## Phase 3: User Story 1 - El terreno determina cuánto tarda moverse (Priority: P1) 🎯 MVP

**Goal**: el costo de la salida es el costo base del movimiento de cualquier actor.

**Independent Test**: criptas con salidas de distintos costos; mover al jugador y a un errante y
comprobar el reloj con `max(1, costo*100 // velocidad)`.

### Tests for User Story 1 (escribir primero) ⚠️

- [ ] T016 [P] [US1] En `tests/test_terreno.py`: escenarios US1-1 (costo 250 → próxima acción en 250), US1-2 (sin costo → 100) y US1-5 (mismo costo en ambos sentidos) {FR-002, FR-003, FR-004}
- [ ] T017 [P] [US1] En `tests/test_terreno.py`: US1-3 / Apéndice B, «velocidad alta y costo 1 → intervalo ≥ 1» {FR-004}
- [ ] T018 [P] [US1] En `tests/test_terreno.py`: US1-4 / Apéndice B, cambio de velocidad tras atravesar una salida costosa, que escala el tiempo restante según P1 §2.3 {FR-006}
- [ ] T019 [P] [US1] En `tests/test_terreno.py`: US1-6, los costos de atacar, esperar, usar, equipar, recoger, soltar y abrir no cambian; un errante y un rastreador conservan sus decisiones y solo cambia su intervalo {FR-005, FR-007}

### Implementation for User Story 1

- [ ] T020 [US1] En `Partida._mover` de `src/modelos/partida.py`, devolver como costo el `costo` de la puerta atravesada en lugar de `COSTO_MOVER` {FR-003, FR-004}
- [ ] T021 [US1] En `Partida._turno_enemigo` y `_mover_enemigo` de `src/modelos/partida.py`, programar la próxima acción con el costo real de la acción (100 al atacar o esperar, costo de la salida al moverse) en lugar de 100 fijo (research R8) {FR-003, FR-004, FR-005, FR-007}
- [ ] T022 [US1] Verificar que `_cambiar_velocidad` en `src/modelos/partida.py` escala el tiempo restante sin depender del costo de origen; ajustar si T018 falla {FR-006}
- [ ] T023 [US1] Agregar `costo` de la puerta al guardado binario y subir la versión del formato en `src/servicios/guardado.py`; un archivo de P1 se rechaza como incompatible (research R10) {FR-026, FR-029}
- [ ] T024 [US1] Agregar en `tests/test_guardado.py` una prueba de guardar y cargar con costos y otra de rechazo del formato anterior; y en `tests/test_cache_persistente.py`, un esqueleto persistido con una versión de cripta distinta no se usa y se vuelve a pedir (validación de versión existente) {FR-026, FR-029}

**Checkpoint**: US1 funciona sola; la batería completa pasa.

---

## Phase 4: User Story 2 - El cazador persigue al jugador por la ruta más barata (Priority: P1)

**Goal**: el comportamiento `cazador` decide atacar, esperar o moverse por la ruta de costo mínimo,
de forma 100 % determinista y coincidiendo exactamente con la referencia teórica.

**Independent Test**: criptas sintéticas pequeñas con resultado conocido a mano y comparación
exhaustiva contra la referencia teórica.

### Referencia teórica (escribir primero, antes de cualquier búsqueda)

- [ ] T025 [US2] Crear `tests/referencia_cazador.py`, la **referencia teórica** independiente del código del juego. Debe ser deliberadamente simple y no compartir código con `rutas.py`, `cazador.py` ni `monticulo.py`:
  - `dist_referencia(cripta, origen, destino)`: búsqueda de costo mínimo **sin cota y sin reutilización**, con distancias y marcas de asentada en `list` de tamaño `n + 1` **indexadas por id** (G5), que en cada paso escoge la sala pendiente de menor costo **recorriendo linealmente** los ids `1..n` (O(n²), sin montículo), solo por salidas con puerta abierta en ese instante, con enteros (D1) y orden de salidas N, S, E, O (D2);
  - `decision_referencia(cripta, cazador, jugador)`: aplica la regla del enunciado **literalmente**: misma sala → `ATACAR`; `d = dist_referencia(u, jugador)`; sin ruta o `d > rango` → `ESPERAR`; si no, calcula `dist_referencia(v, jugador)` **desde cada vecina** `v` por separado y elige con la clave D4;
  - devuelve una tupla comparable `(accion, id_vecina, direccion, costo_accion)`;
  - usa solo estructuras propias o `list` (vigilado por T005). {FR-013, FR-014, FR-015, FR-019}

### Tests for User Story 2 (escribir primero) ⚠️

- [ ] T026 [P] [US2] En `tests/test_cazador.py`: US2-1, misma sala → ataca con costo 100 y no se mueve {FR-010}
- [ ] T027 [P] [US2] En `tests/test_cazador.py`: US2-2 / Apéndice B, sin ruta abierta → espera con costo 100 {FR-011, FR-012}
- [ ] T028 [P] [US2] En `tests/test_cazador.py`: US2-3 / Apéndice B, `d > rango` → espera; US2-4, `d == rango` → se mueve {FR-012, FR-013}
- [ ] T029 [P] [US2] En `tests/test_cazador.py`: US2-5 / Apéndice B, gana la ruta de menos costo aunque tenga más salas {FR-011, FR-013}
- [ ] T030 [P] [US2] En `tests/test_cazador.py`: US2-6 / Apéndice B, dos vecinas con rutas mínimas → la de menor id; cuadrícula de costos uniformes con muchísimas rutas de igual costo que se separan y se vuelven a unir, donde la respuesta esperada está calculada a mano {FR-014}
- [ ] T031 [P] [US2] En `tests/test_cazador.py`: dos salidas hacia la misma vecina → la abierta más barata y, si empatan, el orden N, S, E, O; la acción cuesta la salida elegida (US2-7); y otro enemigo que ocupa una sala de la ruta no la bloquea: el cazador pasa igual (caso borde de la spec) {FR-013, FR-015, FR-017}
- [ ] T032 [P] [US2] En `tests/test_cazador.py`: US2-8, no atraviesa puertas cerradas aunque exista la llave; US2-9, la decisión no depende de si el contenido de una sala está descargado {FR-016, FR-017}
- [ ] T033 [P] [US2] En `tests/test_cazador.py`: US2-10, dormido no actúa aunque el jugador esté en rango; se activa al entrar el jugador, con primera acción de costo base 100; `rango` 0 → espera {FR-018, FR-012}
- [ ] T034 [P] [US2] En `tests/test_determinismo_cazador.py`, pruebas de **determinismo total**:
  - la misma cripta, semilla y acciones ejecutadas dos veces producen la misma traza de decisiones `(instante, id_cazador, accion, id_vecina, direccion, costo)`, comparada elemento por elemento;
  - D5: cargar las mismas salas en orden de páginas invertido o barajado con semilla produce **exactamente** la misma traza;
  - los modos `compartido` e `individual` producen la misma traza;
  - ninguna decisión usa `float`: se verifica que las distancias registradas son `int`. {FR-014, FR-019, FR-022, FR-027}
- [ ] T035 [US2] En `tests/test_cazador.py`, **comparación exhaustiva con la referencia** (depende de T025): en 50 criptas sintéticas sembradas pequeñas (de 10 a 40 salas, costos entre 1 y 300, con puertas cerradas al azar), para **cada** par (sala del cazador, sala del jugador) y para rangos {0, 1, 100, 250, 600, sin límite práctico}, la decisión del juego en ambos modos es idéntica a `decision_referencia`, comparando la tupla completa {FR-011, FR-012, FR-013, FR-014, FR-015, FR-019, FR-022}

### Implementation for User Story 2

- [ ] T036 [US2] Implementar `BuscadorRutas.distancias_desde(sala_origen, cota)` en `src/modelos/rutas.py` (research R5 y R9) con este algoritmo exacto:
  1. `registro.nueva_busqueda()`; `monticulo.vaciar()`; registrar `distancia[origen] = 0` e insertar `(0, origen.indice)`.
  2. **Expandir hasta `cota`**: mientras el montículo no esté vacío, **consultar** `(c, i) = minimo()`. Si `c > cota`, **pausar**: la entrada queda en el montículo y se guarda `cota_alcanzada = cota`. Si no, extraerla; si es obsoleta según la regla de T010, descartarla y continuar; si no, marcar `i` como asentada.
  3. Para cada salida de la sala `i` en orden N, S, E, O (D2) con puerta abierta: `nc = c + puerta.costo`. Si la vecina no está asentada y (no tiene distancia en esta generación o `nc < distancia[vecina]`), registrar `distancia[vecina] = nc` (si es la primera vez en la generación, sumar 1 a `examinadas`) e insertar `(nc, vecina.indice)`, **aunque `nc > cota`**: esas entradas forman el borde y permiten retomar la búsqueda después.
  4. **`extender_hasta(cota_nueva)`**: si `cota_nueva > cota_alcanzada`, repetir el paso 2 con la misma generación y el mismo montículo; si no, no hace nada. Así, la decisión de un cazador de rango r solo examina salas a distancia ≤ r y su borde (FR-030), y un rango mayor retoma sin repetir trabajo (research R5).
  5. En pausa, toda sala con distancia real ≤ `cota_alcanzada` está asentada con su distancia exacta. Nunca se lee la niebla de guerra ni el contenido de las salas. {FR-011, FR-016, FR-017, FR-030}
- [ ] T037 [US2] Implementar `BuscadorRutas.primer_paso_desde(origen, objetivo, cota)` (modo individual) en `src/modelos/rutas.py` (depende de T036):
  - igual que T036, pero desde la sala del cazador; para cada vecina directa `v` del origen se fija `primer_paso[v] = id(v)` al relajarla;
  - al relajar `w` desde `x` con `nc == distancia[w]` (empate), se actualiza `primer_paso[w] = min(primer_paso[w], primer_paso[x])`; con `nc < distancia[w]`, se reemplaza por `primer_paso[x]`. Como todo costo es ≥ 1, todas las mejoras y empates de `w` llegan antes de que `w` se asiente;
  - se detiene al **asentar** el objetivo (su distancia ya es la mínima) o al superar la cota;
  - devuelve `d` y la vecina `primer_paso[objetivo]`; la salida concreta hacia esa vecina se elige con D4. {FR-013, FR-014, FR-015, FR-030}
- [ ] T038 [US2] Implementar en `src/modelos/cazador.py` la **regla de decisión local** común a ambos modos: dada la sala `u` y una función `dist(v)` (registrada o ausente), recorrer las salidas de `u` en orden N, S, E, O, descartar puertas cerradas y vecinas **no asentadas** (solo las distancias asentadas son exactas), y quedarse con la tupla mínima D4; devolver `ESPERAR` si no hay candidata o su total supera `rango` {FR-012, FR-013, FR-014, FR-015}
- [ ] T039 [US2] Implementar `DecisorCazadores.decidir(cazador)` en `src/modelos/cazador.py` con modo `compartido` **incremental** (una búsqueda T036 desde la sala del jugador que, para cada cazador que decide, se lleva con `extender_hasta(rango del cazador)` y luego aplica la regla T038; research R5) y modo `individual` (T037 por cazador con su propio rango), sin reutilización todavía (depende de T036, T037 y T038) {FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-022}
- [ ] T040 [US2] Integrar el comportamiento `CAZADOR` en `Partida._comportamiento` y `_turno_enemigo` de `src/modelos/partida.py` usando `DecisorCazadores` y el costo de la acción decidida (depende de T021 y T039) {FR-010, FR-012, FR-013, FR-018}
- [ ] T041 [US2] Asegurar que el cazador usa activación, combate, muerte, `suelta` y efectos de P1 sin ramas especiales en `src/modelos/partida.py`; ajustar si T033 falla {FR-018}

**Checkpoint**: US1 y US2 funcionan; T034 y T035 dan cero diferencias con la referencia.

---

## Phase 5: User Story 3 - Las decisiones siguen siendo correctas cuando el mapa cambia (Priority: P2)

**Goal**: equivalencia observable con el cálculo desde cero, con una reutilización **demostrada**:
ante cambios de puertas alejados de la región asentada, el sistema no recalcula nada.

**Independent Test**: partidas sintéticas largas con puertas que cambian y muchos cazadores,
comparando cada decisión con la referencia teórica (T025) y verificando con contadores cuándo se
recalcula y cuándo no.

### Definiciones usadas por las pruebas y el código

- **Región asentada** del último cálculo: las salas **asentadas** en la generación con la que se
  calculó (`asentada[i] == generacion_cache`). Las salas de borde no forman parte de ella, porque su
  distancia real es mayor que la cota.
- **Puerta alejada**: una puerta cuyas dos salas están fuera de la región asentada. (No se confunde con el contador `examinadas`, que incluye también el borde; research R9.)
- **Contadores de instrumentación** de `DecisorCazadores` (infraestructura, no estado del juego):
  `busquedas` (búsquedas T036/T037 ejecutadas), `reutilizaciones` (decisiones resueltas con el
  cálculo guardado), `salas_examinadas_total` (suma de `examinadas` de todas las búsquedas).

### Tests for User Story 3 (escribir primero) ⚠️

- [ ] T042 [P] [US3] En `tests/test_equivalencia_cazador.py`: US3-1 / Apéndice B (una puerta de la ruta se cierra entre turnos), US3-2 (se abre un atajo) y US3-3 (el jugador cambia de sala); en los tres la decisión es igual a `decision_referencia` y `busquedas` aumenta en 1 {FR-019, FR-020}
- [ ] T043 [P] [US3] En `tests/test_reutilizacion_cazador.py`, **prueba de no recálculo ante puertas alejadas** (US3-4):
  - cripta sintética sembrada grande (≥ 2 000 salas) con el jugador y los cazadores en una esquina y rango pequeño;
  - tras la primera decisión, abrir y cerrar 100 puertas alejadas (ambas salas fuera de la región asentada), incluido un cierre automático;
  - **afirmar** que en las decisiones siguientes `busquedas` **no cambia**, `salas_examinadas_total` **no cambia**, `reutilizaciones` aumenta en cada decisión, y cada decisión es igual a `decision_referencia`;
  - el docstring reproduce la demostración de research R6: una puerta con ambos extremos sin asentar no participó en ninguna distancia registrada, y abrirla no puede crear un camino de costo ≤ cota. {FR-020, FR-021}
- [ ] T044 [P] [US3] En `tests/test_reutilizacion_cazador.py`, **casos que sí deben recalcular y casos que no**:
  - puerta con **una** sala dentro de la región asentada que se abre o se cierra → `busquedas` aumenta en 1;
  - puerta entre una sala de borde y una sala sin asentar → **no** recalcula;
  - más cambios de puerta que el umbral de la lista → recalcula sin revisar la lista;
  - aparece un cazador con rango mayor que la cota alcanzada → la búsqueda se **extiende** (`busquedas` no cambia y `salas_examinadas_total` aumenta solo con las salas nuevas); con rango menor o igual → no hay trabajo nuevo;
  - movimiento o muerte de otros enemigos y cambios de velocidad → `busquedas` **no** cambia (no alteran distancias). {FR-020, FR-021, FR-022}
- [ ] T045 [P] [US3] En `tests/test_equivalencia_cazador.py`: US3-5, 30 cazadores con orden de cálculo distinto → misma decisión individual; US3-6, retroceso con pergamino → decisión según el estado restaurado e igual a la referencia {FR-020, FR-022, FR-028}
- [ ] T046 [US3] En `tests/test_equivalencia_cazador.py`: prueba aleatoria sembrada de ≥ 10 000 decisiones en criptas sintéticas con puertas inestables, en modos compartido e individual **con la reutilización activada**, con cero diferencias frente a `decision_referencia` comparando la tupla completa; se reportan además `busquedas` y `reutilizaciones` para mostrar que la reutilización realmente ocurrió (depende de T025; SC-002) {FR-019, FR-020, FR-021, FR-022}

### Implementation for User Story 3

- [ ] T047 [US3] Agregar `version_puertas` (contador monotónico de infraestructura) en `src/modelos/partida.py` y un **único punto de cambio** de `Puerta.cerrada` (abrir con llave, cierre automático y deshacer del retroceso) que lo incremente y llame a `DecisorCazadores.notificar_puerta(puerta)` (research R6) {FR-020, FR-021}
- [ ] T048 [US3] Agregar a `DecisorCazadores` los contadores `busquedas`, `reutilizaciones` y `salas_examinadas_total` en `src/modelos/cazador.py`, expuestos para pruebas y `--bench`, fuera del estado del juego {FR-021, FR-033}
- [ ] T049 [US3] Implementar la reutilización en `src/modelos/cazador.py` con esta regla exacta (research R6):
  - guardar con el cálculo: sala del jugador, cota, `generacion_cache` y una lista corta de puertas cambiadas desde entonces (con umbral fijo, por ejemplo 32);
  - `notificar_puerta(puerta)`: si la lista no superó el umbral, agregar la puerta; si lo superó, marcar «recalcular»;
  - antes de decidir, **reutilizar** solo si: (1) la sala del jugador es la misma, (2) no se marcó «recalcular» y (3) toda puerta de la lista tiene sus dos salas con `asentada[i] != generacion_cache`; si además la cota pedida es mayor que la alcanzada, se usa `extender_hasta` en lugar de recalcular; si se reutiliza, vaciar la lista;
  - en cualquier otro caso, recalcular con T036 y reemplazar lo guardado;
  - sin `dict`, `set` ni estructuras equivalentes de biblioteca (vigilado por T005). {FR-019, FR-020, FR-021}
- [ ] T050 [US3] Verificar que el decisor, el registro, los contadores y `version_puertas` no entran al historial de retroceso, al guardado ni a `partida.log` (`src/modelos/partida.py`, `src/servicios/guardado.py`) {FR-021, FR-028, FR-029}
- [ ] T051 [US3] Agregar prueba de `--replay` con cazadores en `tests/test_bitacora.py`: dos reproducciones del mismo log producen las mismas decisiones (SC-005) {FR-027}
- [ ] T052 [US3] Agregar prueba en `tests/test_guardado.py`: guardar a mitad de una persecución, cargar y continuar con las mismas decisiones {FR-029}

**Checkpoint**: US1 a US3 funcionan; SC-002 se cumple y T043 demuestra el no recálculo.

---

## Phase 6: User Story 4 - Ver el terreno y reconocer a los cazadores (Priority: P3)

**Goal**: la vista muestra el costo de cada salida y marca a los cazadores
([contrato](contracts/interfaz-y-bench.md)).

**Independent Test**: entrar a una sala con costos distintos, un cazador y otro enemigo.

### Tests for User Story 4 (escribir primero) ⚠️

- [ ] T053 [P] [US4] En `tests/test_main.py` o un `tests/test_vista_consola.py` nuevo: US4-1 (cada salida con dirección y costo) y US4-2 (cazador marcado y distinto de otro enemigo) sobre el texto que genera la vista {FR-023, FR-024}

### Implementation for User Story 4

- [ ] T054 [US4] Mostrar el costo de cada salida de la sala actual y la marca `[cazador]` en `src/vistas/vista_consola.py`, sin mostrar distancias ni rutas (contrato) {FR-023, FR-024}

**Checkpoint**: la interfaz mínima de P2 §7.3 para esta capacidad está completa.

---

## Phase 7: User Story 5 - Evidencia de rendimiento para defender las decisiones (Priority: P3)

**Goal**: `--bench` reporta los escenarios exigidos con criptas sintéticas deterministas.

**Independent Test**: ejecutar `--bench` sin vista y revisar las secciones del contrato.

### Tests for User Story 5 (escribir primero) ⚠️

- [ ] T055 [P] [US5] En `tests/test_rendimiento_cazador.py`: SC-004, en **ambos modos**: mismo número de salas examinadas con cripta ×1 y ×10 y la misma región en rango, y ninguna sala examinada más allá del rango salvo el borde; y con un cazador de rango 100 junto a otro de rango 2000, la primera decisión del de rango 100 examina solo salas a distancia ≤ 100 y su borde (hallazgo H1) {FR-030}
- [ ] T056 [P] [US5] En `tests/test_banco_pruebas.py`: misma semilla → mismas criptas sintéticas y mismos `examinadas_media` y `reutilizaciones`; `--bench` no instancia la vista; y la salida contiene las secciones de los cuatro grupos de la US5 (decisión del cazador, reutilización, revisión de P1 y determinismo por semilla), verificado buscando sus nombres de escenario en el texto {FR-032, FR-033, FR-034, FR-035, SC-006}

### Implementation for User Story 5

- [ ] T057 [US5] Conectar `src/servicios/banco_pruebas.py` con el generador de T001 (sin duplicarlo) y agregar la secuencia sembrada de cambios de puertas que usan los escenarios de puertas estables e inestables {FR-035}
- [ ] T058 [US5] Agregar a `src/servicios/banco_pruebas.py` los escenarios de decisión del cazador (1 frente a 30, rango pequeño frente a grande, compartido frente a individual) y montículo frente a lista lineal (depende de T057) {FR-032}
- [ ] T059 [US5] Agregar el escenario de reutilización frente a recalcular siempre, con puertas estables e inestables, reportando `busquedas` y `reutilizaciones` (depende de T057 y T049). Estructuras del escenario (G5): las puertas candidatas a cambiar se eligen por **número de conexión** desde una `list` de números sembrada; para clasificar una puerta como alejada o cercana se consulta la lista indexada `asentada` del `RegistroBusqueda` por `Sala.indice` de sus dos salas (O(1) cada una); el registro de puertas ya cambiadas en una ronda es una `list` de booleanos de tamaño `2n` indexada por número de conexión, que se reinicia con una marca de generación. Sin `set` ni `dict` {FR-033}
- [ ] T060 [US5] Agregar el escenario de escala ×1 frente a ×10 y el de ciclo de eventos con ≥ 30 cazadores, reportando `ms_max` junto a «CUMPLE» o «NO CUMPLE» según el límite de 20 ms (depende de T057; SC-003 y SC-004) {FR-030, FR-031}
- [ ] T061 [US5] Repetir las mediciones de agenda e historial de retroceso de P1 con cazadores y costos variables en `src/servicios/banco_pruebas.py` (P2 §5.6) {FR-034}
- [ ] T062 [US5] Ajustar `formatear` en `src/servicios/banco_pruebas.py` para imprimir los campos del contrato de `--bench` {FR-032, FR-033, FR-035}

**Checkpoint**: todas las historias funcionan y hay evidencia medida.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T063 Ejecutar `python main.py --bench`, comparar compartido incremental, individual y recalcular siempre, elegir el modo por defecto según la medición y fijarlo en `src/modelos/cazador.py` {FR-031, FR-032}
- [ ] T064 Escribir en `DECISIONES.md` las secciones de P2 §5.1 y §5.2 con la estructura de P1 §8, enlazando a [spec.md](spec.md) y [plan.md](plan.md), e indicando si la decisión final coincide con el plan y qué medición motivó un cambio {FR-030, FR-031, FR-032, FR-033}
- [ ] T065 Escribir en `DECISIONES.md` la parte de P2 §5.6 correspondiente a esta capacidad (agenda e historial con la carga nueva: antes y después, o datos que muestran que siguen siendo adecuados) {FR-034}
- [ ] T066 Actualizar `README.md` con cómo ejecutar las pruebas de aceptación de esta capacidad (ver [quickstart.md](quickstart.md)), incluidos `--bench` y los criterios que se verifican {FR-031, FR-035, SC-001}
- [ ] T067 Confirmar que `tests/test_restricciones.py` (T005) vigila todos los módulos nuevos de la capacidad y pasa {FR-021}
- [ ] T068 Ejecutar `python -m pytest -q` completo y validar [quickstart.md](quickstart.md) de punta a punta {FR-005, FR-007, FR-027, SC-001, SC-005, SC-007}

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias. T001 y T002 (generador y su prueba) van antes que cualquier prueba que use criptas sintéticas; el punto de `cripta_ampliada_x10` de T002 se completa al existir T025.
- **Foundational (Phase 2)**: depende de Setup y **bloquea todas las historias**. T005 va primero.
- **US1 (Phase 3)**: depende de Foundational.
- **US2 (Phase 4)**: depende de Foundational y de T021 (costo de la acción del enemigo). T025 (la referencia) va antes que las búsquedas.
- **US3 (Phase 5)**: depende de US2 (usa T025 y T036).
- **US4 (Phase 6)**: depende de Foundational y de T015; puede hacerse en paralelo con US2 y US3.
- **US5 (Phase 7)**: T057 y T058 dependen de US2; T059 depende de US3.
- **Polish (Phase 8)**: depende de todas las historias.

### Within Each User Story

- Las pruebas se escriben primero y deben fallar antes de implementar.
- Estructuras → modelo → integración en `Partida` → vista y bench.
- Commit al terminar cada tarea o grupo lógico; si la especificación resulta incorrecta, se corrige
  primero `spec.md` en un commit separado (constitución, Principio VIII).

### Parallel Opportunities

- Phase 2: T006 a T009 (pruebas, después de T005), y luego T010 y T011.
- Phase 3: T016 a T019.
- Phase 4: T026 a T034, después de T025.
- Phase 5: T042 a T045.
- US4 completa en paralelo con US2 y US3, porque toca otros archivos.

---

## Parallel Example: User Story 2

```bash
# Primero la referencia teórica:
Task: "T025 [US2] tests/referencia_cazador.py"
# Luego, en paralelo, las pruebas de decisión (mismo archivo, secciones separadas):
Task: "T026 [US2] misma sala → ataca"
Task: "T027 [US2] sin ruta → espera"
Task: "T030 [US2] desempate por menor id"
Task: "T034 [US2] determinismo total"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (generador de criptas probado) y Phase 2 (empezando por T005).
2. Phase 3 (US1): el terreno con costo funciona para todos los actores.
3. **Validar** US1 y la batería de P1.

### Incremental Delivery

1. US1 → terreno.
2. US2 → cazador correcto y determinista en mapas estáticos, idéntico a la referencia.
3. US3 → equivalencia con mapas cambiantes y no recálculo demostrado.
4. US4 → interfaz.
5. US5 + Polish → evidencia, `DECISIONES.md` y README.

### Trazabilidad para la defensa (P2 §2.5)

Para cualquier `FR-NNN`: escenario en [spec.md](spec.md) → tarea en este archivo (busca
`{… FR-NNN …}`) → código (archivo indicado en la tarea) → prueba que cita `FR-NNN`.
