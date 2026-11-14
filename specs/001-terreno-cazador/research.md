# Research: Terreno con costo y enemigo cazador

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-14

Cada sección sigue el formato Decisión / Justificación / Alternativas. Las decisiones marcadas
«confirmada por el grupo» se consultaron antes de escribir el plan; las demás son preliminares y se
validan con `--bench` durante la implementación (constitución, Principio VII).

## R1. Selección de la sala pendiente más barata — confirmada por el grupo

- **Decisión**: un montículo binario de mínimos de implementación propia, nuevo en
  `src/estructuras_datos/monticulo.py`, con entradas `(costo_acumulado, indice_sala)` y
  **eliminación perezosa**: no hay operación de «disminuir clave». Si una sala mejora su costo se
  inserta otra entrada, y al extraer se descartan las entradas obsoletas comparando con la distancia
  registrada.
- **Justificación**: extraer el mínimo cuesta O(log k), con k entradas pendientes, independiente de
  la magnitud de los costos (que pueden ser 1, 100, 250…). Con eliminación perezosa, k ≤ número de
  relajaciones ≤ 4 · salas examinadas, porque cada sala tiene a lo sumo 4 salidas. La implementación
  es mínima y fácil de defender. La `Agenda` de P1 ya es un montículo propio y probado, pero está
  especializada en `Evento` (índice interno, cancelación y reprogramación), así que no se modifica
  para no arriesgar P1. Se reutiliza su diseño de subir y bajar.
- **Alternativas**:
  - Cola por cubetas indexada por costo: inserción O(1), pero la extracción recorre cubetas vacías
    hasta el costo final, lo que depende del `rango` y del costo máximo de las salidas. Queda
    descartada como principal.
  - Lista con búsqueda lineal del mínimo, O(k) por extracción: es la **alternativa ingenua medida**
    en `--bench` (FR-032).
  - `heapq`: prohibido (constitución, Principio I).

## R2. Registro de distancias, primer paso y visitados — confirmada por el grupo

- **Decisión**: cada sala recibe al cargar la cripta un **índice compacto** `0..n-1`, según el orden
  de llegada de las páginas del esqueleto, que es determinista. Un `RegistroBusqueda`
  (`src/estructuras_datos/registro_busqueda.py`) guarda listas de tamaño n indexadas por ese
  índice: `distancia`, `primer_paso`, `marca` y `asentada`. Cada búsqueda incrementa un número de
  **generación**, y una posición solo es válida si `marca[i] == generación`. Así, empezar una
  búsqueda nueva cuesta O(1) y no se limpian n posiciones.
- **Justificación**: cumple FR-030, porque una búsqueda solo toca las salas que examina. No usa
  `dict`, `set` ni hash (Principio I, FR-021). `list` está permitida como almacenamiento contiguo
  (P1 §7). El acceso es O(1) sin calcular hash.
- **Alternativas**: una `TablaHash` de P1 por búsqueda (O(1) promedio, pero con más costo constante
  y una tabla nueva por búsqueda) o limpiar las listas en cada búsqueda (O(n), viola FR-030).

## R3. Representación del mapa para la búsqueda

- **Decisión**: no se crea otra estructura de mapa. Se usa la que ya existe: `Sala.salidas[4]` con
  objetos `Salida` y `Puerta` compartidos entre ambos lados. Se agregan dos cosas al cargar:
  `Sala.indice` (R2) y `Salida.sala_destino`, una referencia directa a la sala vecina para no
  consultar la `TablaHash` de salas en cada relajación.
- **Justificación**: evita duplicar el mapa y una búsqueda hash por cada vecina examinada.
- **Alternativas**: listas de adyacencia nuevas, que duplican datos sin ventaja con grado ≤ 4, o
  consultar `cripta.sala(id)` en cada relajación, que pone un hash en el camino crítico.

## R4. Dónde vive el costo y cómo se valida la simetría

- **Decisión**: el costo se guarda en la `Puerta`, que ya es un objeto compartido por las dos
  `Salida` que forman el par (`Cripta.enlazar_puertas`). Al cargar: si ningún lado declara `costo`,
  vale 100; si un solo lado lo declara, se usa ese valor; si ambos lo declaran con valores
  distintos, es un **error de datos** (FR-002 y FR-008). Un valor que no es entero o es menor que 1
  es error de datos con sala y dirección (FR-008).
- **Justificación**: un solo dato por conexión garantiza la simetría por construcción y no duplica
  información.
- **Alternativas**: un costo por `Salida` y comprobar la simetría en cada movimiento, con riesgo de
  divergencia.
- **Nota**: el caso «un solo lado declara el costo» no está en el enunciado. El grupo confirmó
  esta regla y se incorporó a FR-002 de la especificación.

## R5. Cálculo compartido frente a individual (P2 §5.1) — preliminar, se valida con `--bench`

- **Decisión preliminar**: **cálculo compartido incremental**. Una sola búsqueda **desde la sala
  del jugador** que se expande solo hasta la cota que pide el cazador que está decidiendo (su
  `rango`) y queda en **pausa**. Si otro cazador pide una cota mayor, la misma búsqueda se
  **retoma** sin repetir salas ya asentadas. Así, la decisión de un cazador de rango r examina solo
  las salas a distancia ≤ r y su borde (FR-030), y el trabajo total del ciclo es una sola búsqueda
  hasta el mayor rango solicitado (P2 §5.1). Con la búsqueda expandida hasta una cota `R ≥ rango`,
  cada cazador decide en O(4) con su regla: el mínimo de
  `costo(u, v) + dist(v)` entre sus salidas abiertas, con desempate por el menor id de `v` y, para
  salidas hacia la misma vecina, la salida más barata y luego el orden N, S, E, O (FR-014, FR-015).
  Si `dist(u)` no está registrada o `d > rango`, espera.
- **Corrección**: los costos son simétricos, así que la distancia del cazador al jugador es igual a
  la del jugador al cazador. Si `d ≤ rango ≤ R`, toda vecina `v` de una ruta óptima cumple
  `dist(v) = d − costo(u, v) < R`, así que está registrada. Una vecina sin distancia registrada
  tiene `dist(v) > R ≥ rango`, y no puede iniciar una ruta de costo ≤ rango. La decisión coincide
  con el cálculo desde cero (FR-019, FR-022). Pausar cuando el mínimo del montículo supera la cota
  no pierde información: las entradas pendientes, incluidas las de costo mayor que la cota, quedan
  en el montículo, y las distancias asentadas son definitivas; retomar con una cota mayor continúa
  exactamente donde se pausó.
- **Modo individual** (implementado para medir): una búsqueda desde la sala de cada cazador,
  acotada por **su** `rango`, que propaga el «primer paso» (la vecina de menor id entre las que
  inician caminos de igual costo) y se detiene al extraer la sala del jugador. Corresponde a la
  estrategia que propuso el grupo de explorar hacia afuera y cortar la rama que supera el límite.
- **Hallazgo de `/speckit-analyze` (H1)**: una versión anterior de esta decisión expandía siempre
  hasta el **mayor** rango activo, lo que hacía pagar a un cazador de rango pequeño la región de uno
  grande y contradecía FR-030. La versión incremental lo corrige.
- **Criterio de cambio**: con pocos cazadores, el individual puede examinar menos salas en total. `--bench` mide ambos con 1 frente a 30 cazadores y rango pequeño frente a grande, y
  la decisión final se documenta en `DECISIONES.md` (P2 §7.1).

## R6. Reutilización e invalidación de rutas (P2 §5.2) — preliminar

- **Decisión preliminar**: la búsqueda compartida (R5), con su estado de pausa, se conserva junto
  con su **llave**: sala del jugador, cota alcanzada y `version_puertas`, un contador monotónico de la partida que
  aumenta con **cada** cambio de estado de una puerta, también cuando el retroceso restaura una
  puerta. El contador es infraestructura: no se revierte ni se guarda. Antes de decidir se reutiliza
  el resultado solo si:
  1. la sala del jugador es la misma;
  2. no cambió ninguna puerta, **o** todas las puertas cambiadas desde entonces tienen ambos
     extremos fuera de la región asentada.
  Si se cumplen y la cota pedida es mayor que la alcanzada, la búsqueda se **extiende** (R5) en lugar
  de recalcularse.
- **Demostración del punto 2**: la búsqueda solo usó salidas de salas asentadas. Una puerta con
  ambos extremos sin asentar no participó en ninguna distancia asentada. Abrirla no crea un camino
  de costo ≤ cota alcanzada, porque para usarla habría que alcanzar un extremo con costo ≤ esa cota,
  y ese extremo estaría asentado. Cerrarla no quita ningún camino usado. Por eso las distancias
  registradas no cambian. Los cambios se anotan en una lista corta de puertas modificadas desde la
  última búsqueda; si la lista supera un umbral, se recalcula sin revisarla.
- **Eventos que invalidan**: movimiento del jugador (cambia la sala), aperturas y cierres de
  puertas cercanas y retroceso (cambia la sala del jugador o las puertas). Un cazador con mayor
  rango no invalida: **extiende** la búsqueda. **No invalidan**: el movimiento o la muerte de otros actores, porque no
  bloquean el paso, ni los cambios de velocidad, porque no cambian distancias.
- **Alternativa medida**: recalcular siempre (FR-033), con puertas estables y con puertas
  inestables.

## R7. Verificación de la equivalencia (SC-002)

- **Decisión**: una implementación de referencia **solo para pruebas**
  (`tests/referencia_cazador.py`), con búsqueda completa sin cota ni reutilización desde cada
  cazador, y el desempate aplicado literalmente con `dist` calculada desde cada vecina. Una prueba
  ejecuta partidas sintéticas con puertas que cambian y compara la decisión del juego con la de
  referencia en ≥ 10 000 decisiones.
- **Justificación**: comprueba FR-019 a FR-022 sin confiar en la misma lógica que se prueba.

## R8. Costo de la acción del enemigo (corrección de P1)

- **Decisión**: hoy `Partida._turno_enemigo` programa siempre `100`. Pasará a programar el costo de
  la acción realizada: 100 para atacar o esperar, y el costo de la salida para moverse. El jugador
  usa el costo de la salida en `_mover`.
- **Justificación**: FR-003 y FR-004.

## R9. Conteo de salas examinadas (SC-004)

- **Decisión**: el buscador expone un contador de «salas examinadas» de la búsqueda actual: las
  salas que recibieron una distancia tentativa en esta generación, sean asentadas (distancia ≤ cota)
  o de borde (vecinas de una asentada con distancia tentativa > cota). Cada sala cuenta **una sola
  vez**, la primera vez que se le registra una distancia en la generación, así que una sala de borde
  que después se asienta al extender la búsqueda no se cuenta dos veces (hallazgo M1). Las pruebas lo
  usan para verificar SC-004 de forma determinista, y `--bench` lo reporta junto al tiempo.

## R10. Persistencia y formato

- **Decisión**: el costo forma parte de la `Puerta` en el guardado binario, y sube la versión del
  formato. Un archivo de la primera parte se detecta como incompatible por la validación de versión
  ya existente (FR-026, P1 §4.10). El esqueleto en caché ya se invalida por la versión nueva de la
  cripta. El conjunto completo de reglas de persistencia de la segunda parte se especifica en 004.
- **Ajuste durante la implementación**: para que la partida cargada continúe con las mismas
  decisiones (FR-029), el guardado incluye también el instante del próximo turno de cada enemigo;
  P1 lo reprogramaba a 100 desde el momento de cargar. Además, al restaurar se vuelven a unir las
  puertas de ambos lados con `Cripta.enlazar_puertas`, que P1 dejaba separadas.
