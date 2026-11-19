# Feature Specification: Línea de tiempo y puntos de control

**Feature Branch**: `004-linea-de-tiempo`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Línea de tiempo (P2 §3.6, §5.5, §6.1, §6.3 y Apéndice B «Línea de tiempo»). El pergamino de retroceso sigue limitado a 5 acciones; la línea de tiempo es independiente y permite consultar, sin modificar la partida, el estado en cualquier instante desde el inicio. El estado en el instante t es el estado después de ejecutar todos los eventos con tiempo menor o igual que t; si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla. En partida, el comando `historia <t>` o `historia #k` (estado justo antes de la acción número k del jugador) muestra como mínimo: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido en ese momento; la consulta no consume tiempo virtual, no se registra como acción y no altera ningún estado del juego ni del historial de retroceso. Sin interacción, `--replay partida.log --hasta <t>` reproduce la partida hasta t e imprime el mismo resumen sin instanciar la vista. Las acciones revertidas con un pergamino dejan de existir en la línea de tiempo: la línea describe la historia de la partida tal como quedó. Consultar un instante posterior al reloj actual se rechaza. Se permite guardar copias completas del estado, llamadas puntos de control, pero no más de una cada K acciones del jugador; K se configura con `--checkpoint-cada K` y el valor por defecto lo escoge el grupo y lo justifica con mediciones. Una consulta no puede requerir aplicar o deshacer cambios de más de K acciones del jugador. Fuera de los puntos de control, solo se almacena la información necesaria para reconstruir los cambios. Se puede reconstruir hacia adelante desde un punto de control, re-simulando, o hacia atrás desde el estado actual, invirtiendo cambios; si se re-simula, el punto de control debe incluir el estado del generador random.Random. Guardar y cargar la partida conserva la línea de tiempo completa; el formato binario cambia y un archivo de la primera parte debe detectarse como incompatible o migrarse de forma explícita. La memoria total debe crecer con la cantidad de cambios ocurridos más un punto de control cada K acciones, nunca con «acciones por tamaño del estado». Ubicar el punto de control más cercano a un instante pedido es una búsqueda frecuente y su costo importa en partidas largas. Al usar un pergamino, la línea debe recortarse sin recorrer toda la historia. Hay que mostrar con mediciones cómo varían memoria y tiempo de consulta para al menos tres valores de K y justificar el valor por defecto. La consulta `historia` debe tomar menos de 50 ms en una partida de al menos 5 000 acciones del jugador con el K por defecto."

## Contexto y alcance

Esta capacidad amplía P1 §2.11 (pergamino de retroceso), §4.6 (historial reversible) y §4.10
(guardado), y se apoya en las capacidades 001 (costos de tránsito) y 003 (mapa conocido, que la
consulta debe mostrar).

**Dentro del alcance**: la consulta del estado en cualquier instante pasado; los puntos de control y
su frecuencia configurable; el recorte de la línea al usar un pergamino; el resumen que la consulta
imprime; `historia <t>` e `historia #k` en partida; `--replay … --hasta <t>` sin vista; la
persistencia de la línea de tiempo; y las mediciones asociadas.

**Fuera del alcance** (tienen su propia especificación): terreno y cazador (001), verificación de
resolubilidad (002) y niebla de guerra e «ir a» (003). Esta especificación consume el mapa conocido
que define la 003 y exige poder mostrarlo en el instante consultado, pero no define sus reglas.

**Relación con el pergamino**: el pergamino sigue siendo lo que era, limitado a 5 acciones, y sigue
modificando la partida. La línea de tiempo no modifica nada y no tiene límite de alcance hacia
atrás. Son dos mecanismos distintos que se cruzan en un solo punto: lo que un pergamino revierte
desaparece de la línea.

## Identificadores

Los requisitos se numeran `FR-NNN` dentro de esta especificación, como en las capacidades 001, 002 y
003. Cuando se citan desde fuera de este archivo se escriben calificados por la capacidad,
`004-FR-007`, porque la numeración reinicia en cada especificación.

## Clarifications

### Session 2026-11-18

- Q: ¿Qué significa «estado en el instante t» cuando varios eventos caen exactamente en t?
  → A: El estado después de ejecutar todos ellos, sin excepción. Si además a t le corresponde una
  decisión del jugador, es el estado justo antes de que el jugador decida, pero después de todos los
  eventos de t (Apéndice B).
- Q: ¿`historia #k` muestra el estado antes o después de la acción k?
  → A: Justo antes de tomarla: es el estado que el jugador tenía delante cuando decidió. `historia
  #1` es el estado inicial de la partida.
- Q: ¿Qué pasa si se consulta un instante anterior al inicio, o un `#k` que no existe?
  → A: Se rechaza con un mensaje, igual que un instante futuro. Los únicos valores válidos son
  `0 ≤ t ≤ reloj actual` y `1 ≤ k ≤ acciones del jugador + 1`.
- Q: ¿Los puntos de control se guardan en el archivo de partida?
  → A: No. Lo que se guarda es la secuencia de acciones del jugador con su instante, que es la
  información mínima necesaria para reconstruir cualquier estado. Los puntos de control son una
  caché de consulta: se reconstruyen al cargar y no viajan en el archivo, que así no crece con el
  tamaño del estado por cada K acciones.
- Q: Si se consulta la historia de una partida recién cargada, ¿la primera consulta es más lenta?
  → A: Sí, y se asume. Reconstruir los puntos de control de una partida cargada cuesta una
  re-simulación completa, una sola vez. A partir de ahí toda consulta cumple el límite. El límite de
  50 ms de FR-030 se mide con los puntos de control ya construidos, que es la situación de una
  partida en curso.
- Q: ¿La consulta puede cambiar lo que el jugador conoce, descargar contenido o gastar presupuesto de
  red? → A: No. La consulta trabaja sobre los datos de la cripta ya disponibles y no emite ninguna
  solicitud. Si un estado pasado necesitara contenido que ya no está disponible, la consulta informa
  que no puede reconstruirse en vez de pedirlo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar cómo estaba la partida en un instante pasado (Priority: P1)

Como jugador, quiero poder preguntar cómo estaba todo en un momento anterior de la partida, sin que
eso cambie nada de mi partida actual, para entender qué me llevó a la situación en la que estoy.

**Why this priority**: es la capacidad entera desde el punto de vista del jugador.

**Independent Test**: jugar una secuencia conocida de acciones en una cripta sintética, consultar
varios instantes y comparar cada resumen contra el estado que la misma secuencia produce al
re-simularla desde el inicio.

**Acceptance Scenarios**:

1. **Given** una partida con varias acciones jugadas, **When** el jugador consulta `historia <t>`
   con `0 ≤ t ≤ reloj actual`, **Then** se muestra el estado en ese instante y la partida en curso no
   cambia en nada.
2. **Given** la misma partida, **When** el jugador consulta `historia #k`, **Then** se muestra el
   estado justo antes de la acción número k del jugador.
3. **Given** una consulta cualquiera, **When** se ejecuta, **Then** el resumen incluye el reloj, la
   sala del jugador, su vida y sus estadísticas, su inventario, sus efectos activos, los enemigos de
   esa sala con su vida, y el mapa conocido en ese momento.
4. **Given** un instante t en el que varios eventos ocurren a la vez, **When** se consulta
   `historia <t>`, **Then** el estado mostrado es el de después de ejecutar todos ellos (Apéndice B).
5. **Given** un instante t que corresponde a una decisión del jugador, **When** se consulta,
   **Then** el estado mostrado es el de justo antes de esa decisión, con todos los eventos de t ya
   ejecutados.
6. **Given** `historia #1`, **When** se consulta, **Then** se muestra el estado inicial de la
   partida.
7. **Given** una consulta, **When** termina, **Then** no consumió tiempo virtual, no se registró en
   `partida.log` y el historial de retroceso quedó igual: los pergaminos disponibles son los mismos
   (Apéndice B).

---

### User Story 2 - Las consultas inválidas se rechazan (Priority: P1)

Como jugador, si pregunto por un instante que no existe, quiero un mensaje claro y no un resultado
inventado.

**Why this priority**: el Apéndice B lo exige explícitamente y es la frontera del comando.

**Independent Test**: consultar instantes fuera de rango y comprobar el rechazo y que el reloj no
avanzó.

**Acceptance Scenarios**:

1. **Given** una partida cuyo reloj está en t_actual, **When** el jugador consulta `historia <t>`
   con `t > t_actual`, **Then** la consulta se rechaza y no se muestra ningún estado (Apéndice B).
2. **Given** una partida, **When** el jugador consulta un instante negativo, **Then** se rechaza.
3. **Given** una partida con n acciones del jugador, **When** consulta `historia #k` con `k > n+1` o
   `k < 1`, **Then** se rechaza.
4. **Given** un argumento que no es un número ni tiene la forma `#k`, **When** se usa, **Then** se
   rechaza con un mensaje que explica las dos formas válidas.
5. **Given** cualquier rechazo, **When** ocurre, **Then** no consume tiempo virtual ni altera nada.

---

### User Story 3 - El pergamino recorta la historia (Priority: P1)

Como jugador, si deshago una acción con un pergamino, esa acción deja de haber ocurrido: la historia
que puedo consultar es la de la partida tal como quedó, no la de todo lo que intenté.

**Why this priority**: es la única interacción entre los dos mecanismos y la fuente del caso del
Apéndice B más fácil de implementar mal.

**Independent Test**: jugar acciones, revertir con un pergamino y comprobar que los instantes
posteriores al retroceso se rechazan y que las acciones revertidas no aparecen en ninguna consulta.

**Acceptance Scenarios**:

1. **Given** una partida con varias acciones, **When** el jugador usa un pergamino, **Then** las
   acciones revertidas dejan de existir en la línea de tiempo y ninguna consulta las muestra
   (Apéndice B).
2. **Given** la situación anterior, **When** el jugador consulta un instante que era válido antes
   del retroceso pero que ahora es posterior al reloj, **Then** se rechaza.
3. **Given** una partida con muchas acciones, **When** se usa un pergamino, **Then** el recorte de
   la línea no recorre toda la historia.
4. **Given** una partida en la que se usó un pergamino y después se jugaron acciones nuevas,
   **When** se consulta la historia, **Then** se muestra la historia resultante: las acciones nuevas
   ocupan el lugar de las revertidas.
5. **Given** un pergamino que revierte una entrada con antorcha que exploró varias salas, **When**
   se consulta un instante anterior a esa entrada, **Then** el mapa conocido que se muestra es el de
   ese instante, sin las salas que la antorcha había revelado.

---

### User Story 4 - Consultar sin jugar (Priority: P2)

Como miembro del grupo, quiero poder ver el estado de una partida grabada en un instante dado sin
abrir la interfaz, para depurar y para las pruebas automatizadas.

**Why this priority**: es el camino que usan las pruebas y el que el enunciado exige que no instancie
la vista.

**Independent Test**: grabar una bitácora, reproducirla con `--hasta` en varios instantes y comparar
los resúmenes con los de las consultas en partida.

**Acceptance Scenarios**:

1. **Given** una bitácora grabada, **When** se ejecuta `--replay partida.log --hasta <t>`, **Then**
   se reproduce la partida hasta t, se imprime el mismo resumen que `historia <t>` y no se instancia
   la vista.
2. **Given** la misma bitácora, **When** se usa `--hasta` con un t posterior al final de la partida,
   **Then** se muestra el estado final y se indica que la partida terminó antes (Apéndice B).
3. **Given** `--replay` sin `--hasta`, **When** se ejecuta, **Then** se comporta como en las
   capacidades anteriores: reproduce toda la bitácora.
4. **Given** una bitácora de una partida con viajes `ir a`, **When** se reproduce con `--hasta`,
   **Then** los pasos individuales se ejecutan y los comentarios se ignoran, como en la 003.

---

### User Story 5 - La memoria no crece con copias completas (Priority: P1)

Como miembro del grupo, necesito que una partida larga no guarde una copia del estado por cada
acción, y que aun así cualquier consulta sea rápida.

**Why this priority**: es el problema de estructuras de datos de la capacidad (P2 §5.5) y lo que se
evalúa con mediciones.

**Independent Test**: jugar partidas sintéticas de 5 000 acciones con tres valores de K y medir la
memoria de la línea de tiempo y el tiempo de consulta.

**Acceptance Scenarios**:

1. **Given** una partida de n acciones del jugador con parámetro K, **When** se mide la línea de
   tiempo, **Then** hay a lo sumo una copia completa del estado cada K acciones.
2. **Given** cualquier consulta, **When** se resuelve, **Then** requiere aplicar o deshacer los
   cambios de a lo sumo K acciones del jugador.
3. **Given** una partida larga, **When** crece el número de acciones, **Then** la memoria de la
   línea de tiempo crece con la cantidad de cambios ocurridos más un punto de control cada K
   acciones, y no con «acciones por tamaño del estado».
4. **Given** una partida de al menos 5 000 acciones del jugador con el K por defecto y los puntos de
   control ya construidos, **When** se consulta la historia, **Then** la consulta tarda menos de
   50 ms.
5. **Given** una partida larga, **When** se ubica el punto de control más cercano a un instante
   pedido, **Then** el costo de esa búsqueda no es proporcional al número de puntos de control.
6. **Given** `--checkpoint-cada K`, **When** se pasa un valor distinto del predeterminado, **Then**
   la frecuencia de los puntos de control cambia y las consultas siguen siendo correctas.

---

### User Story 6 - La historia sobrevive a guardar y cargar (Priority: P2)

Como jugador, si guardo mi partida y la retomo mañana, quiero poder seguir consultando toda su
historia.

**Why this priority**: lo exige el enunciado y es lo que obliga a cambiar el formato del archivo.

**Independent Test**: jugar, guardar, cargar y comparar las consultas de la partida cargada con las
de la original.

**Acceptance Scenarios**:

1. **Given** una partida con historia, **When** se guarda y se vuelve a cargar, **Then** la línea de
   tiempo completa sigue disponible y las consultas dan los mismos resúmenes que antes de guardar.
2. **Given** un archivo de partida de la primera parte, **When** se intenta cargar, **Then** se
   reporta la incompatibilidad de formato y no se carga en silencio (Apéndice B).
3. **Given** un archivo de partida de las capacidades 001 o 002, **When** se intenta cargar,
   **Then** también se reporta como incompatible.
4. **Given** una partida cargada, **When** se consulta la historia por primera vez, **Then** la
   consulta es correcta aunque los puntos de control hayan tenido que reconstruirse.

---

### Edge Cases

- `historia 0` en una partida ya avanzada: muestra el estado inicial, que es válido.
- Consultar el instante exacto del reloj actual: es válido y muestra el estado actual.
- Una partida sin ninguna acción del jugador todavía: solo `historia 0` e `historia #1` son válidas.
- `K = 1`: hay un punto de control por acción; la consulta es inmediata y la memoria es la máxima
  permitida. Es un valor legal y las mediciones lo usan como extremo.
- `K` mayor que el número de acciones jugadas: existe un solo punto de control, el inicial, y una
  consulta puede tener que re-simular todas las acciones. Es legal y es el otro extremo medido.
- `--checkpoint-cada 0` o negativo: argumento inválido, se rechaza al arrancar.
- Un pergamino que revierte la acción inmediatamente posterior a un punto de control: ese punto de
  control sigue siendo válido, porque describe un instante que sigue existiendo.
- Un pergamino que revierte varias acciones de golpe: el recorte quita todas las entradas y los
  puntos de control que quedaron después del nuevo final.
- La partida termina en victoria o derrota: la línea de tiempo sigue consultable, y el reloj actual
  es el del final.
- Consultar la historia con la partida terminada: válido, con el mismo límite superior.
- Dos consultas seguidas al mismo instante: la segunda no puede dar un resultado distinto de la
  primera.
- Una consulta no debe dejar rastro en la bitácora de pantalla ni en el buffer de mensajes de la
  partida en curso.

## Requirements *(mandatory)*

### Functional Requirements

**Definición del estado pasado**

- **FR-001**: El estado en el instante t DEBE ser el estado después de ejecutar todos los eventos
  con tiempo menor o igual que t.
- **FR-002**: Si a t le corresponde una decisión del jugador, el estado en t DEBE ser el de justo
  antes de tomar esa decisión, con todos los eventos de t ya ejecutados.
- **FR-003**: El estado justo antes de la acción número k del jugador DEBE ser consultable como
  `#k`, con `#1` igual al estado inicial de la partida.
- **FR-004**: La línea de tiempo DEBE cubrir todos los instantes desde 0 hasta el reloj actual, sin
  límite de alcance hacia atrás, independientemente del límite de 5 acciones del pergamino.

**Consulta en partida**

- **FR-005**: La interfaz DEBE ofrecer el comando `historia <t>` y el comando `historia #k`.
- **FR-006**: El resumen de una consulta DEBE incluir como mínimo: el reloj, la sala del jugador, su
  vida y sus estadísticas, su inventario, sus efectos activos, los enemigos de esa sala con su vida,
  y el mapa conocido en ese momento.
- **FR-007**: Una consulta NO DEBE consumir tiempo virtual, NO DEBE registrarse como acción en
  `partida.log` y NO DEBE alterar ningún estado del juego ni el historial de retroceso.
- **FR-008**: Consultar un instante posterior al reloj actual DEBE rechazarse.
- **FR-009**: Consultar un instante negativo, un `#k` fuera del rango `1 ≤ k ≤ acciones + 1`, o un
  argumento que no sea un entero ni tenga la forma `#k`, DEBE rechazarse con un mensaje que explique
  las formas válidas.
- **FR-010**: Un rechazo NO DEBE consumir tiempo virtual ni alterar nada.
- **FR-011**: Una consulta NO DEBE emitir ninguna solicitud al servicio ni consumir
  `presupuesto_solicitudes`. Si un estado pasado necesitara datos de la cripta que no están
  disponibles, la consulta DEBE informar que no puede reconstruirse.
- **FR-012**: Dos consultas al mismo instante DEBEN producir el mismo resumen.

**Interacción con el pergamino**

- **FR-013**: Las acciones revertidas con un pergamino DEBEN dejar de existir en la línea de tiempo:
  la línea describe la historia de la partida tal como quedó.
- **FR-014**: Después de un retroceso, los instantes posteriores al nuevo reloj DEBEN rechazarse.
- **FR-015**: El recorte de la línea de tiempo al usar un pergamino NO DEBE recorrer toda la
  historia: su costo DEBE depender de lo que se recorta.
- **FR-016**: Las acciones jugadas después de un retroceso DEBEN ocupar el lugar de las revertidas en
  la línea de tiempo.

**Consulta sin interacción**

- **FR-017**: `--replay <bitácora> --hasta <t>` DEBE reproducir la partida hasta t, imprimir el
  mismo resumen que `historia <t>` y NO DEBE instanciar la vista.
- **FR-018**: `--hasta` con un t posterior al final de la partida grabada DEBE mostrar el estado
  final e indicar que la partida terminó antes.
- **FR-019**: `--replay` sin `--hasta` DEBE seguir comportándose como en las capacidades anteriores.

**Puntos de control y memoria**

- **FR-020**: El programa PUEDE guardar copias completas del estado, llamadas puntos de control, y
  NO DEBE guardar más de una cada K acciones del jugador.
- **FR-021**: K DEBE configurarse con `--checkpoint-cada K`. El valor por defecto lo fija el grupo y
  DEBE justificarse con mediciones. Un K menor que 1 DEBE rechazarse al arrancar.
- **FR-022**: Una consulta NO DEBE requerir aplicar o deshacer los cambios de más de K acciones del
  jugador.
- **FR-023**: Fuera de los puntos de control, solo DEBE almacenarse la información necesaria para
  reconstruir los cambios.
- **FR-024**: La memoria total de la línea de tiempo DEBE crecer con la cantidad de cambios ocurridos
  más un punto de control cada K acciones, y NO DEBE crecer como «acciones por tamaño del estado».
- **FR-025**: Si la reconstrucción es hacia adelante re-simulando, el punto de control DEBE incluir
  el estado del generador `random.Random`, de modo que la re-simulación sea idéntica a la partida
  original.
- **FR-026**: Ubicar el punto de control más cercano a un instante pedido NO DEBE costar
  proporcionalmente al número de puntos de control.
- **FR-027**: Toda estructura con la que se indexen, busquen o almacenen los puntos de control y las
  entradas de la línea DEBE cumplir el Principio I de la constitución: la implementa el grupo, y está
  PROHIBIDO usar `dict`, `set`, `heapq`, `bisect`, `collections` o estructuras equivalentes de
  biblioteca como índice, caché o registro.

**Persistencia**

- **FR-028**: Guardar y cargar una partida DEBE conservar la línea de tiempo completa: toda consulta
  válida antes de guardar DEBE seguir dando el mismo resumen después de cargar.
- **FR-029**: El formato del archivo de partida cambia. Un archivo de un formato anterior, incluido
  el de la primera parte, DEBE detectarse como incompatible mediante la validación de versión y NO
  DEBE cargarse en silencio.

**Rendimiento y medición**

- **FR-030**: Con el K por defecto y los puntos de control ya construidos, una consulta `historia`
  DEBE tomar menos de 50 ms en una partida de al menos 5 000 acciones del jugador, sin red ni
  renderizado.
- **FR-031**: El ciclo de eventos entre dos decisiones del jugador DEBE seguir tomando menos de
  20 ms con decenas de cazadores activos y la línea de tiempo activa (001, FR-031).
- **FR-032**: `--bench` DEBE medir la memoria de la línea de tiempo y el tiempo de consulta para al
  menos tres valores de K, y DEBE comparar contra la alternativa de guardar una copia completa por
  acción y contra la de no usar puntos de control.
- **FR-033**: `--bench` DEBE repetir la medición del ciclo de eventos de la capacidad 001 con la
  línea de tiempo activa.
- **FR-034**: Las criptas y partidas sintéticas de `--bench` DEBEN ser deterministas por semilla, y
  `--bench` NO DEBE instanciar la vista.

### Key Entities *(include if feature involves data)*

- **Instante**: un valor del reloj virtual. El dominio consultable es `0 ≤ t ≤ reloj actual`.
- **Entrada de la línea de tiempo**: el registro de una acción del jugador: su número, el instante en
  que se tomó y lo necesario para volver a aplicarla. Es la información mínima de FR-023.
- **Punto de control**: una copia completa del estado de la partida en el instante de una acción del
  jugador, con el estado del generador aleatorio. Es una caché de consulta, no la historia.
- **Línea de tiempo**: la sucesión de entradas desde el inicio de la partida, con sus puntos de
  control. Describe la historia tal como quedó después de los retrocesos.
- **Resumen de historia**: lo que una consulta imprime, con los campos de FR-006.
- **K**: el número máximo de acciones del jugador entre dos puntos de control consecutivos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 6 casos de «Línea de tiempo» del Apéndice B de P2 tienen una prueba automatizada
  que cita su requisito, y todas pasan.
- **SC-002**: Para una partida sintética de al menos 1 000 acciones, el resumen que devuelve
  `historia <t>` coincide, para al menos 200 instantes distintos elegidos de forma determinista, con
  el estado que se obtiene re-simulando la partida desde el inicio hasta t.
- **SC-003**: En una partida de al menos 5 000 acciones del jugador con el K por defecto y los
  puntos de control construidos, ninguna consulta `historia` supera los 50 ms en el equipo local.
- **SC-004**: Para cualquier instante consultado, el número de acciones del jugador que la consulta
  re-aplica o deshace es menor o igual que K, verificado por conteo y no por tiempo.
- **SC-005**: La cantidad de copias completas del estado que la línea de tiempo mantiene para una
  partida de n acciones es a lo sumo `n/K + 1`.
- **SC-006**: Con al menos 30 cazadores activos y la línea de tiempo activa, ningún ciclo de eventos
  entre dos decisiones del jugador supera los 20 ms.
- **SC-007**: `--bench` reporta memoria y tiempo de consulta para al menos tres valores de K, más
  las alternativas de copia por acción y de no usar puntos de control, y el K por defecto queda
  justificado en `DECISIONES.md` con esos números.
- **SC-008**: Una consulta deja la partida intacta: el reloj, el número de acciones, los pergaminos
  disponibles, el buffer de mensajes y el mapa conocido son idénticos antes y después.
- **SC-009**: Guardar y cargar una partida con historia reproduce los mismos resúmenes para los
  mismos instantes, y un archivo de formato anterior se rechaza con un mensaje de incompatibilidad.
- **SC-010**: Ningún módulo de la capacidad usa `dict`, `set`, `heapq`, `bisect`, `collections` ni
  bibliotecas de grafos, verificado por la prueba de restricciones.
- **SC-011**: Toda la batería de pruebas de las capacidades 001, 002 y 003 sigue pasando.
