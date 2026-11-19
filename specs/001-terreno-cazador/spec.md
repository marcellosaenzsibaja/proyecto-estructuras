# Feature Specification: Terreno con costo y enemigo cazador

**Feature Branch**: `001-terreno-cazador`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "Terreno y cazadores (P2 §3.1, §3.2, §5.1, §5.2, §6.1, §6.3 y Apéndice B «Terreno y cazador»). Cada salida puede declarar un costo de tránsito entero ≥ 1 (100 si no lo declara, igual en ambos sentidos); moverse por una salida cuesta su costo en lugar de 100 y el intervalo se calcula con max(1, costo*100 // velocidad) para todos los actores. Se agrega el comportamiento de enemigo «cazador» con un rango en unidades de costo: ataca si comparte sala con el jugador; si no, calcula el costo mínimo d hasta la sala actual del jugador usando solo salidas abiertas en ese instante; espera (costo 100) si no hay ruta o si d > rango; si no, da un paso por una ruta de costo d, desempatando por la vecina de menor id. Conoce el esqueleto completo y el estado real de las puertas, no lo afecta la niebla de guerra y no abre puertas. Su decisión debe ser siempre idéntica a la de un cálculo desde cero. Con decenas de cazadores, el ciclo entre dos decisiones del jugador debe tomar menos de 20 ms, y el costo de decidir debe depender de la región dentro del rango y no del tamaño de la cripta."

## Contexto y alcance

Esta capacidad amplía las reglas de la primera parte (P1 §2.3, §2.5 y §2.8). Todo lo que no se
modifica aquí sigue igual: costos de las demás acciones, activación de enemigos, combate, efectos,
pergamino de retroceso, guardado y reproducción.

**Dentro del alcance**: costo de tránsito de las salidas para todos los actores; el comportamiento
`cazador`; la equivalencia de sus decisiones con un cálculo desde cero; la presentación de costos y
cazadores en la vista; y las mediciones de `--bench` asociadas.

**Fuera del alcance** (tienen su propia especificación): verificación de resolubilidad (002),
niebla de guerra e «ir a» (003) y línea de tiempo (004).

## Clarifications

### Session 2026-11-14

- Q: ¿Desde cuándo actúa un cazador: desde que el jugador entra a su sala o desde el inicio de la
  partida? → A: Como cualquier enemigo (P1 §2.4): dormido hasta que el jugador entra a su sala; una
  vez activo sigue activo aunque cambie de sala.
- Q: Si el servicio entrega una salida con `costo` menor que 1 o no entero, o un cazador sin
  `rango`, ¿qué debe hacer el programa? → A: Error de datos: se informa la sala y la dirección (o
  el id de la ficha) y esa cripta no se juega; nunca se corrige en silencio.
- Q: Si dos salidas de una misma sala llevan a la misma sala vecina, ¿por cuál pasa el cazador?
  → A: Por la salida abierta más barata; si cuestan lo mismo, por el orden fijo de direcciones
  N, S, E, O.
- Q: ¿Cómo debe comprobarse que decidir la jugada de un cazador con rango pequeño no se vuelve más
  caro cuando la cripta crece? → A: Por conteo: una decisión solo examina salas a distancia de
  costo ≤ `rango` más su borde inmediato, y ese número no cambia si la cripta crece 10 veces con la
  misma región dentro del rango; `--bench` reporta además los tiempos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El terreno determina cuánto tarda moverse (Priority: P1)

Como jugador, cuando atravieso una salida, el tiempo virtual que consume mi movimiento depende del
costo de esa salida, de modo que un pasillo difícil me hace más lento que uno despejado. La misma
regla vale para todos los enemigos que se mueven.

**Why this priority**: es la base de toda la capacidad. El cazador, «ir a» y la verificación de
rutas dependen de que el movimiento tenga costo variable.

**Independent Test**: cargar una cripta con salidas de costos distintos (incluidas salidas sin
costo declarado), mover al jugador y a un errante, y comprobar el reloj resultante con la fórmula
del intervalo.

**Acceptance Scenarios**:

1. **Given** una salida con `costo` 250 y un jugador de velocidad 100 en el instante 0, **When** el
   jugador la atraviesa, **Then** su próxima acción queda programada en el instante 250.
2. **Given** una salida sin campo `costo`, **When** un actor de velocidad 100 la atraviesa,
   **Then** el movimiento cuesta 100, como en la primera parte.
3. **Given** una salida con `costo` 1 y un actor de velocidad 150, **When** el actor la atraviesa,
   **Then** el intervalo resultante es 1, nunca 0 (Apéndice B, «actor de velocidad alta atraviesa
   una salida de costo 1»).
4. **Given** un actor que acaba de atravesar una salida de `costo` 400 y tiene su próxima acción
   pendiente, **When** un efecto cambia su velocidad antes de esa acción, **Then** el tiempo restante
   se escala con `max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)` según
   P1 §2.3 (Apéndice B, «cambia la velocidad de un actor que atraviesa una salida costosa»).
5. **Given** una salida de `costo` 300 entre las salas A y B, **When** se atraviesa de A a B y
   luego de B a A, **Then** ambos movimientos cuestan 300.
6. **Given** un jugador que ataca, espera, usa, equipa, recoge, suelta o abre una puerta, **When**
   ejecuta esa acción, **Then** su costo es el mismo de la primera parte, independiente del terreno.

---

### User Story 2 - El cazador persigue al jugador por la ruta más barata (Priority: P1)

Como jugador, enfrento un enemigo que no sigue rastros ni camina al azar: conoce el mapa y se
acerca a mí por el camino de menor costo total, siempre que yo esté dentro de su alcance.

**Why this priority**: es la regla nueva central y el problema de estructuras de datos de mayor
peso de la capacidad (P2 §5.1).

**Independent Test**: colocar un cazador y al jugador en criptas sintéticas pequeñas cuyo resultado
se conoce a mano, y verificar cada decisión (atacar, esperar o la sala exacta a la que se mueve) y
el costo de la acción.

**Acceptance Scenarios**:

1. **Given** un cazador activo en la misma sala que el jugador, **When** llega su turno, **Then**
   ataca según P1 §2.6, con costo 100, y no se mueve.
2. **Given** un cazador sin ninguna ruta de salidas abiertas hasta la sala del jugador, **When**
   llega su turno, **Then** espera con costo 100 (Apéndice B).
3. **Given** un cazador cuya ruta más barata hasta el jugador cuesta más que su `rango`, **When**
   llega su turno, **Then** espera con costo 100 (Apéndice B).
4. **Given** un cazador cuya ruta más barata cuesta exactamente su `rango`, **When** llega su turno,
   **Then** se mueve un paso por esa ruta.
5. **Given** dos rutas hacia el jugador, una de 2 salidas con costo total 500 y otra de 4 salidas
   con costo total 400, **When** llega el turno del cazador, **Then** da el primer paso de la ruta
   de costo 400 (Apéndice B).
6. **Given** dos vecinas v1 y v2 (id de v1 < id de v2) que inician rutas de costo mínimo, **When**
   llega el turno del cazador, **Then** se mueve a v1 (Apéndice B).
7. **Given** que el cazador se mueve por una salida de `costo` 250, **When** se programa su próxima
   acción, **Then** el costo base de la acción es 250 y el intervalo se calcula con su velocidad.
8. **Given** una ruta más barata que atraviesa una puerta cerrada, **When** llega el turno del
   cazador, **Then** esa puerta no se considera: el cazador no abre puertas, aunque exista una llave.
9. **Given** un cazador cuya sala de destino nunca ha sido visitada por el jugador ni tiene su
   contenido descargado, **When** decide, **Then** su decisión es la misma que si el contenido
   estuviera descargado: solo dependen del esqueleto y del estado de las puertas.
10. **Given** un cazador en una sala a la que el jugador nunca ha entrado, **When** avanza el reloj,
    **Then** no actúa aunque el jugador esté dentro de su `rango`; **When** el jugador entra a esa
    sala, **Then** se activa y su primera acción se programa con una acción base de costo 100
    (P1 §2.4).

---

### User Story 3 - Las decisiones siguen siendo correctas cuando el mapa cambia (Priority: P2)

Como jugador, si cierro o abro una puerta, me muevo o un enemigo muere, el cazador reacciona en su
siguiente turno exactamente como lo haría alguien que mira el mapa de nuevo desde cero, aunque haya
decenas de cazadores persiguiéndome a la vez.

**Why this priority**: asegura la regla de equivalencia observable (P2 §3.2 y §5.2). Sin ella, una
optimización podría cambiar la partida.

**Independent Test**: ejecutar partidas sintéticas largas con puertas que cambian y muchos
cazadores, y comparar en cada turno la decisión del juego con una decisión de referencia calculada
desde cero.

**Acceptance Scenarios**:

1. **Given** que una puerta de la ruta del cazador se cierra entre dos de sus turnos, **When** llega
   su siguiente turno, **Then** decide como si calculara desde cero con la puerta cerrada
   (Apéndice B).
2. **Given** que se abre una puerta que acorta la ruta, **When** llega el turno del cazador,
   **Then** usa la ruta nueva más barata.
3. **Given** que el jugador cambia de sala entre dos turnos del cazador, **When** llega su turno,
   **Then** la distancia se mide hasta la sala actual del jugador.
4. **Given** que una puerta con cierre automático se cierra lejos de todas las rutas de los
   cazadores, **When** llegan sus turnos, **Then** sus decisiones son las mismas que sin el cierre.
5. **Given** treinta cazadores activos que persiguen al jugador, **When** se ejecuta un ciclo de
   eventos, **Then** cada uno toma la decisión que le correspondería individualmente desde cero,
   sin importar el orden en que se calcularon.
6. **Given** que el jugador usa un pergamino de retroceso, **When** los cazadores vuelven a actuar,
   **Then** deciden según el estado restaurado, igual que con un cálculo desde cero.

---

### User Story 4 - Ver el terreno y reconocer a los cazadores (Priority: P3)

Como jugador, veo el costo de cada salida de la sala en la que estoy y distingo a simple vista qué
enemigos son cazadores, para decidir por dónde huir o avanzar (P2 §7.3).

**Why this priority**: la regla funciona sin esto, pero la interfaz mínima del enunciado lo exige.

**Independent Test**: entrar a una sala con salidas de costos distintos y con un cazador y otro
enemigo, y revisar la presentación.

**Acceptance Scenarios**:

1. **Given** una sala con salidas de costos 100, 250 y sin costo declarado, **When** se muestra la
   sala, **Then** cada salida indica su dirección y su costo (100, 250 y 100).
2. **Given** una sala con un cazador y una rata errante, **When** se muestra la lista de enemigos,
   **Then** el cazador se distingue del resto (por ejemplo, con una marca o etiqueta propia).

---

### User Story 5 - Evidencia de rendimiento para defender las decisiones (Priority: P3)

Como grupo evaluado, ejecutamos `--bench` y obtenemos mediciones reproducibles que respaldan cómo se
calculan y reutilizan las rutas de los cazadores (P2 §5.1, §5.2, §5.6 y §6.3).

**Why this priority**: es obligatorio para la evaluación y para `DECISIONES.md`, pero no cambia el
comportamiento del juego.

**Independent Test**: ejecutar `--bench` sin vista y verificar que reporta cada escenario exigido
con criptas sintéticas deterministas por semilla.

**Acceptance Scenarios**:

1. **Given** `--bench`, **When** se ejecuta, **Then** reporta la decisión del cazador con un
   cazador frente a muchos, con rango pequeño frente a rango grande y con cálculo compartido frente
   a cálculo individual.
2. **Given** `--bench`, **When** se ejecuta, **Then** compara reutilizar cálculos frente a recalcular
   siempre, con puertas que casi nunca cambian y con puertas que cambian con frecuencia.
3. **Given** `--bench`, **When** se ejecuta, **Then** repite las mediciones de la agenda de eventos
   y del historial de retroceso de la primera parte con cazadores activos y costos variables.
4. **Given** la misma semilla, **When** se ejecuta `--bench` dos veces, **Then** las criptas
   sintéticas generadas son idénticas.

---

### Edge Cases

- Un cazador con `rango` 0 que no comparte sala con el jugador: espera, porque toda salida cuesta al
  menos 1.
- El jugador está en una sala vecina, pero la salida que las une está cerrada y existe un rodeo
  abierto: el cazador toma el rodeo si su costo no supera el rango.
- Muchas rutas de igual costo, incluidas rutas que se separan y se vuelven a unir: el desempate se
  aplica solo sobre la vecina del primer paso y siempre elige la de menor id.
- Dos salidas distintas de la sala del cazador llevan a la misma vecina: cuenta la abierta de menor
  costo; si empatan, la primera en el orden N, S, E, O. La acción cuesta el costo de esa salida.
- El cazador está dormido (el jugador aún no entra a su sala): no actúa hasta activarse según
  P1 §2.4.
- Otro enemigo ocupa una sala de la ruta: no bloquea el paso; los actores no impiden el movimiento.
- El cazador muere con eventos futuros programados: esos eventos no producen acciones (P1 §4.1).
- El jugador muere en el mismo instante: la partida termina y ningún cazador vuelve a decidir.
- Un actor ya está al otro lado cuando una puerta se cierra automáticamente: permanece allí y solo
  se le impide volver a atravesarla (P1, Apéndice B).
- Una salida declara un `costo` menor que 1 o que no es entero: los datos de la cripta son inválidos
  y se reporta el error con la sala y la dirección afectadas, en lugar de jugar con datos dudosos.
- Una ficha con comportamiento `cazador` sin campo `rango`: los datos del catálogo son inválidos y
  se reporta el error con el id de la ficha.
- Solo uno de los dos lados de una conexión declara `costo`: ese valor vale en ambos sentidos. Si
  los dos lo declaran con valores distintos, es error de datos.

## Requirements *(mandatory)*

### Functional Requirements

**Terreno**

- **FR-001**: Cada salida DEBE tener un costo de tránsito entero mayor o igual que 1. Si el
  esqueleto no lo declara, su costo DEBE ser 100.
- **FR-002**: El costo de una salida DEBE ser el mismo en ambos sentidos. Si solo uno de los dos
  lados de la conexión declara `costo`, ese valor vale para ambos sentidos; si ambos lo declaran
  con valores distintos, DEBE reportarse como error de datos que identifique las salas y las
  direcciones, y la cripta no se juega con ese dato.
- **FR-003**: Moverse a través de una salida DEBE ser una acción cuyo costo base es el costo de esa
  salida, para todos los actores (jugador, errante, rastreador y cazador).
- **FR-004**: El intervalo de toda acción DEBE seguir calculándose como
  `max(1, costo * 100 // velocidad)`.
- **FR-005**: Los costos de atacar, esperar, usar, equipar, recoger, soltar y abrir una puerta NO
  DEBEN cambiar respecto de la primera parte.
- **FR-006**: Un cambio de velocidad sobre un actor con una acción pendiente DEBE escalar el tiempo
  restante según P1 §2.3, sin importar el costo de la salida que originó esa acción.
- **FR-007**: Errantes y rastreadores DEBEN conservar sus reglas de decisión de la primera parte;
  solo cambia lo que tarda su movimiento.
- **FR-008**: Un costo de salida inválido (menor que 1 o no entero) DEBE reportarse como error de
  datos que identifique la sala y la dirección, y la cripta no se juega con ese dato.

**Cazador: reglas de decisión**

- **FR-009**: El sistema DEBE soportar el comportamiento de enemigo `cazador`, cuya ficha incluye
  `rango`, un entero mayor o igual que 0 en unidades de costo. Una ficha `cazador` sin `rango`
  válido DEBE reportarse como error de datos que identifique el id de la ficha, y la cripta no se
  juega con ese dato; nunca se asume un valor por defecto.
- **FR-010**: En su turno, si el cazador comparte sala con el jugador, DEBE atacar según P1 §2.6 con
  costo 100 y no moverse.
- **FR-011**: Si no comparte sala, DEBE considerar el costo mínimo `d` para llegar desde su sala
  hasta la sala actual del jugador, sumando el costo de cada salida recorrida y usando únicamente las
  salidas abiertas en ese instante.
- **FR-012**: Si no existe ruta, o si `d > rango`, el cazador DEBE esperar con costo 100.
- **FR-013**: Si existe una ruta con `d ≤ rango`, el cazador DEBE moverse un paso por una ruta de
  costo `d`, y el costo de esa acción DEBE ser el costo de la salida que atraviesa.
- **FR-014**: Desempate: siendo `u` la sala del cazador, entre las vecinas `v` que cumplen
  `costo(u, v) + dist(v, jugador) = d`, el cazador DEBE moverse a la de menor id. El resultado NO
  DEBE depender del método de cálculo.
- **FR-015**: Si varias salidas abiertas de `u` llevan a la misma vecina `v`, `costo(u, v)` DEBE
  ser el menor de sus costos y el cazador DEBE atravesar esa salida. Si dos o más empatan en costo,
  DEBE elegirse la primera según el orden fijo de direcciones N, S, E, O. La acción cuesta el costo
  de la salida elegida.
- **FR-016**: El cazador NO DEBE abrir puertas cerradas, aunque exista la llave correspondiente.
- **FR-017**: La decisión del cazador DEBE depender solo del esqueleto completo (con los costos) y
  del estado real actual de las puertas. NO DEBE depender de la niebla de guerra del jugador ni de
  si el contenido de una sala ya fue descargado.
- **FR-018**: El cazador DEBE activarse como cualquier enemigo (P1 §2.4): permanece dormido, sin
  decidir ni actuar, hasta que el jugador entra a su sala; una vez activo sigue activo aunque cambie
  de sala. Su combate, muerte, campo `suelta` y efectos DEBEN seguir las reglas generales de
  enemigos de la primera parte.

**Cazador: equivalencia observable**

- **FR-019**: La decisión del cazador en cada turno DEBE ser idéntica a la que se obtendría
  calculando la ruta desde cero en ese instante.
- **FR-020**: Entre dos turnos de un cazador pueden ocurrir aperturas y cierres de puertas,
  movimientos del jugador, cambios de sala o muerte de otros actores, cambios de velocidad y
  retrocesos con pergamino. Ninguno de ellos DEBE producir una decisión distinta de la del cálculo
  desde cero.
- **FR-021**: Reutilizar información de cálculos anteriores DEBE estar permitido solo cuando no
  cambie la decisión. Esa información auxiliar no es estado del juego: no se guarda, no forma parte
  del retroceso y su presencia o ausencia no altera ninguna partida. Toda información que se
  conserve o reutilice para estos cálculos DEBE cumplir el Principio I de la constitución: la
  implementa el grupo y está PROHIBIDO usar estructuras de conveniencia del lenguaje o estructuras
  equivalentes de biblioteca como índice, caché o registro de esa información.
- **FR-022**: Con varios cazadores activos, la decisión de cada uno DEBE ser la misma que tendría si
  fuera el único que calcula, sin importar si el cálculo se comparte o es individual.

**Presentación**

- **FR-023**: La vista DEBE mostrar el costo de cada salida de la sala actual.
- **FR-024**: La vista DEBE distinguir a los cazadores de los demás enemigos.

**Datos, persistencia y reproducción**

- **FR-025**: Los costos de las salidas DEBEN obtenerse del esqueleto, y `comportamiento: cazador`
  y `rango` del catálogo, sin solicitudes adicionales al servicio, y DEBEN persistirse y validarse
  con las versiones de cripta y de catálogo existentes.
- **FR-026**: Lo persistido por la primera parte sin costos DEBE invalidarse mediante la validación
  de versión, no borrando archivos a mano.
- **FR-027**: La misma cripta, semilla y secuencia de acciones DEBEN producir las mismas decisiones
  de todos los cazadores, también al reproducir con `--replay`.
- **FR-028**: El pergamino de retroceso DEBE restaurar la sala, la vida y la próxima acción de los
  cazadores igual que para cualquier otro enemigo.
- **FR-029**: Guardar y cargar una partida DEBE conservar el estado de los cazadores, y la partida
  cargada DEBE continuar con las mismas decisiones que la original.

**Rendimiento y medición**

- **FR-030**: El trabajo de una decisión de un cazador con `rango` pequeño DEBE ser proporcional a
  la región de la cripta que queda dentro de su rango, no al tamaño total de la cripta: para
  decidir solo se examinan salas a distancia de costo ≤ `rango` y su borde inmediato (las salas
  donde se detecta que se supera el rango).
- **FR-031**: El ciclo de eventos entre dos decisiones consecutivas del jugador DEBE tomar menos de
  20 ms en la cripta de referencia con decenas de cazadores activos, sin red ni renderizado.
- **FR-032**: `--bench` DEBE medir la decisión del cazador con un cazador frente a muchos, con rango
  pequeño frente a rango grande, y con cálculo compartido frente a individual.
- **FR-033**: `--bench` DEBE medir la reutilización de cálculos frente a recalcular siempre, al menos
  en un escenario con puertas que casi nunca cambian y otro con puertas que cambian con frecuencia.
- **FR-034**: `--bench` DEBE repetir las mediciones de la agenda de eventos y del historial de
  retroceso de la primera parte con cazadores activos y costos variables.
- **FR-035**: Las criptas sintéticas de `--bench` DEBEN ser deterministas por semilla, y `--bench`
  NO DEBE instanciar la vista.

### Key Entities *(include if feature involves data)*

- **Salida**: conexión entre dos salas en una dirección (N, S, E, O). Atributos: sala destino,
  costo de tránsito (≥ 1, 100 por defecto, simétrico), si está cerrada, la llave que la abre y su
  cierre automático.
- **Ficha de cazador**: ficha de catálogo de clase enemigo con `comportamiento: cazador` y `rango`
  (entero en unidades de costo), además de las estadísticas comunes de un enemigo.
- **Cazador (instancia)**: actor enemigo concreto con su sala, vida y próxima acción, que usa la
  ficha anterior.
- **Distancia de costo**: el costo mínimo para ir de una sala a la sala del jugador por salidas
  abiertas en un instante dado. Es un concepto de la regla, no un dato que se guarde.
- **Decisión del cazador**: el resultado de su turno: atacar, esperar o moverse a una vecina
  concreta, con el costo de la acción.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 7 casos de «Terreno y cazador» del Apéndice B de P2 tienen una prueba automatizada
  que cita su requisito, y todas pasan.
- **SC-002**: En al menos 10 000 decisiones de cazadores tomadas en partidas sintéticas con puertas
  que cambian, no hay ninguna diferencia entre la decisión del juego y una decisión de referencia
  calculada desde cero.
- **SC-003**: Con al menos 30 cazadores activos en la cripta de referencia, ningún ciclo de eventos
  entre dos decisiones del jugador supera los 20 ms en el equipo local.
- **SC-004**: Con un rango fijo, el número de salas examinadas en una decisión del cazador es
  exactamente el mismo cuando la cripta sintética crece 10 veces manteniendo igual la región dentro
  del rango, y ninguna sala examinada está más allá del rango salvo su borde inmediato. `--bench`
  reporta además el tiempo medio de decisión en ambos tamaños como evidencia complementaria.
- **SC-005**: Dos reproducciones con `--replay` del mismo `partida.log` producen exactamente la
  misma secuencia de decisiones de los cazadores.
- **SC-006**: `--bench` reporta los cuatro grupos de mediciones de la User Story 5, y dos ejecuciones
  con la misma semilla generan las mismas criptas sintéticas.
- **SC-007**: Toda la batería de pruebas de la primera parte sigue pasando con los costos por
  defecto.

## Assumptions

- Los demás actores no bloquean el paso: el cazador puede atravesar salas ocupadas por otros
  enemigos.
- En el instante en que decide, el cazador mide hasta la sala en la que está el jugador en ese
  momento, no hasta donde estará después.
- La cripta de referencia y las criptas con decenas de cazadores las publicará el profesor. Mientras
  tanto, el límite de 20 ms se verifica con criptas sintéticas de `--bench` de tamaño comparable a
  la cripta publicada más grande.
- Los límites de P2 §6.1 pueden ajustarse mediante una enmienda del enunciado (P2 §2.7); si ocurre,
  se actualiza esta especificación antes que el código.
