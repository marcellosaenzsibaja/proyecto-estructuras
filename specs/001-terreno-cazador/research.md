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
  índice: `distancia`, `primer_paso`, `marca` y `cerrada`. Cada búsqueda incrementa un número de
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
- **Nota para el grupo**: el caso «un solo lado declara el costo» no está en el enunciado; se
  resolvió por coherencia con FR-002. Ver «Revisión pendiente» en el plan.

## R5. Cálculo compartido frente a individual (P2 §5.1) — preliminar, se valida con `--bench`

- **Decisión preliminar**: **cálculo compartido**. Una sola búsqueda acotada **desde la sala del
  jugador** con cota `R = máximo rango entre los cazadores activos` produce `dist(v, jugador)` para
  toda sala con distancia ≤ R. Cada cazador decide en O(4) con su regla: el mínimo de
  `costo(u, v) + dist(v)` entre sus salidas abiertas, con desempate por el menor id de `v` y, para
  salidas hacia la misma vecina, la salida más barata y luego el orden N, S, E, O (FR-014, FR-015).
  Si `dist(u)` no está registrada o `d > rango`, espera.
- **Corrección**: los costos son simétricos, así que la distancia del cazador al jugador es igual a
  la del jugador al cazador. Si `d ≤ rango ≤ R`, toda vecina `v` de una ruta óptima cumple
  `dist(v) = d − costo(u, v) < R`, así que está registrada. Una vecina sin distancia registrada
  tiene `dist(v) > R ≥ rango`, y no puede iniciar una ruta de costo ≤ rango. La decisión coincide
  con el cálculo desde cero (FR-019, FR-022).
- **Modo individual** (implementado para medir): una búsqueda desde la sala de cada cazador,
  acotada por **su** `rango`, que propaga el «primer paso» (la vecina de menor id entre las que
  inician caminos de igual costo) y se detiene al extraer la sala del jugador. Corresponde a la
  estrategia que propuso el grupo de explorar hacia afuera y cortar la rama que supera el límite.
- **Criterio de cambio**: con pocos cazadores y rangos muy distintos, el individual puede examinar
  menos salas. `--bench` mide ambos con 1 frente a 30 cazadores y rango pequeño frente a grande, y
  la decisión final se documenta en `DECISIONES.md` (P2 §7.1).

## R6. Reutilización e invalidación de rutas (P2 §5.2) — preliminar

- **Decisión preliminar**: el resultado de la búsqueda compartida (R5) se conserva junto con su
  **llave**: sala del jugador, cota R y `version_puertas`, un contador monotónico de la partida que
  aumenta con **cada** cambio de estado de una puerta, también cuando el retroceso restaura una
  puerta. El contador es infraestructura: no se revierte ni se guarda. Antes de decidir se reutiliza
  el resultado solo si:
  1. la sala del jugador es la misma;
  2. la cota pedida es ≤ la cota con la que se calculó;
  3. no cambió ninguna puerta, **o** todas las puertas cambiadas desde entonces tienen ambos
     extremos fuera de la región examinada.
- **Demostración del punto 3**: la búsqueda solo usó salidas de salas que extrajo. Una puerta con
  ambos extremos sin examinar no participó en ninguna distancia registrada. Abrirla no crea un
  camino de costo ≤ R, porque para usarla habría que alcanzar un extremo con costo ≤ R, y ese
  extremo habría sido examinado. Cerrarla no quita ningún camino usado. Por eso las distancias
  registradas no cambian. Los cambios se anotan en una lista corta de puertas modificadas desde la
  última búsqueda; si la lista supera un umbral, se recalcula sin revisarla.
- **Eventos que invalidan**: movimiento del jugador (cambia la sala), aperturas y cierres de
  puertas cercanas, retroceso (cambia la sala del jugador o las puertas) y aparición de un cazador
  con mayor rango (sube R). **No invalidan**: el movimiento o la muerte de otros actores, porque no
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

- **Decisión**: el buscador expone un contador de «salas examinadas» de la última búsqueda (las que
  se extrajeron más las del borde inmediato que se descartaron por superar la cota). Las pruebas lo
  usan para verificar SC-004 de forma determinista, y `--bench` lo reporta junto al tiempo.

## R10. Persistencia y formato

- **Decisión**: el costo forma parte de la `Puerta` en el guardado binario, y sube la versión del
  formato. Un archivo de la primera parte se detecta como incompatible por la validación de versión
  ya existente (FR-026, P1 §4.10). El esqueleto en caché ya se invalida por la versión nueva de la
  cripta. El conjunto completo de reglas de persistencia de la segunda parte se especifica en 004.
