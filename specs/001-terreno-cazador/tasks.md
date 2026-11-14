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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dejar listo el andamiaje de pruebas de la capacidad.

- [ ] T001 Crear `tests/utilidades_cripta.py` con constructores de criptas pequeñas en memoria (salas, salidas con `costo`, puertas abiertas o cerradas) para usarlas en todas las pruebas de la capacidad, reutilizando `tests/utilidades.py` {FR-001, FR-011}
- [ ] T002 Ejecutar `python -m pytest -q` y registrar en el PR que la batería de P1 pasa antes de empezar (línea base de SC-007) {SC-007}

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: estructuras y campos de los que dependen todas las historias.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

### Pruebas de la fase (escribir primero)

- [ ] T003 [P] Escribir `tests/test_monticulo.py`: orden por (costo, índice), empates deterministas, extracción en vacío, reutilización tras `vaciar()` y entradas obsoletas con eliminación perezosa {FR-014, FR-030}
- [ ] T004 [P] Escribir `tests/test_registro_busqueda.py`: `nueva_busqueda()` invalida en O(1) sin limpiar posiciones, `tiene(i)` por generación y contador `examinadas` {FR-030}
- [ ] T005 [P] Escribir en `tests/test_terreno.py` las pruebas de carga del costo: ausente → 100; «entero ≥ 1»; un solo lado declara → vale para ambos; ambos distintos → `ErrorDatos` con salas y direcciones; menor que 1 o no entero → `ErrorDatos` con sala y dirección {FR-001, FR-002, FR-008}
- [ ] T006 [P] Escribir en `tests/test_cazador.py` las pruebas de la ficha: `comportamiento: cazador` con `rango` «int ≥ 0»; ficha `cazador` sin `rango` válido → `ErrorDatos` con el id de la ficha, sin valor por defecto {FR-009}

### Implementación de la fase

- [ ] T007 [P] Implementar `MonticuloMin` en `src/estructuras_datos/monticulo.py`: `list` de pares `(costo, indice)`, `insertar` y `extraer_minimo` O(log k), `esta_vacio`, `vaciar` O(1); sin `heapq` (research R1) {FR-014, FR-030}
- [ ] T008 [P] Implementar `RegistroBusqueda` en `src/estructuras_datos/registro_busqueda.py`: listas `distancia`, `primer_paso`, `marca` y `cerrada` indexadas por `Sala.indice`, `generacion` y `examinadas`; sin `dict`, `set` ni hash (research R2) {FR-021, FR-030}
- [ ] T009 Agregar `Puerta.costo` («int ≥ 1», 100 por defecto), `Salida.sala_destino` y `Sala.indice` en `src/modelos/entidades.py` (data-model) {FR-001, FR-002}
- [ ] T010 Asignar `Sala.indice` compacto en orden de carga en `Cripta.agregar_sala`, enlazar `Salida.sala_destino` y fusionar o validar el costo de ambos lados en `Cripta.enlazar_puertas` en `src/modelos/cripta.py` (depende de T009; research R3 y R4) {FR-001, FR-002, FR-008}
- [ ] T011 Leer y validar `costo` en `_sala_desde_dict` de `src/servicios/cargador_cripta.py`, guardando si el lado lo declaró para que `enlazar_puertas` valide la simetría (depende de T010) {FR-001, FR-002, FR-008, FR-025}
- [ ] T012 Agregar `rango` y el comportamiento `cazador` en `src/modelos/fichas.py`, y leerlos y validarlos en `src/servicios/fabrica_fichas.py` (ver T006) {FR-009, FR-025}

**Checkpoint**: T003 a T006 pasan; la batería de P1 sigue pasando.

---

## Phase 3: User Story 1 - El terreno determina cuánto tarda moverse (Priority: P1) 🎯 MVP

**Goal**: el costo de la salida es el costo base del movimiento de cualquier actor.

**Independent Test**: criptas con salidas de distintos costos; mover al jugador y a un errante y
comprobar el reloj con `max(1, costo*100 // velocidad)`.

### Tests for User Story 1 (escribir primero) ⚠️

- [ ] T013 [P] [US1] En `tests/test_terreno.py`: escenarios US1-1 (costo 250 → próxima acción en 250), US1-2 (sin costo → 100) y US1-5 (mismo costo en ambos sentidos) {FR-002, FR-003, FR-004}
- [ ] T014 [P] [US1] En `tests/test_terreno.py`: US1-3 / Apéndice B, «velocidad alta y costo 1 → intervalo ≥ 1» {FR-004}
- [ ] T015 [P] [US1] En `tests/test_terreno.py`: US1-4 / Apéndice B, cambio de velocidad tras atravesar una salida costosa, que escala el tiempo restante según P1 §2.3 {FR-006}
- [ ] T016 [P] [US1] En `tests/test_terreno.py`: US1-6, los costos de atacar, esperar, usar, equipar, recoger, soltar y abrir no cambian; un errante y un rastreador conservan sus decisiones y solo cambia su intervalo {FR-005, FR-007}

### Implementation for User Story 1

- [ ] T017 [US1] En `Partida._mover` de `src/modelos/partida.py`, devolver como costo el `costo` de la puerta atravesada en lugar de `COSTO_MOVER` {FR-003, FR-004}
- [ ] T018 [US1] En `Partida._turno_enemigo` y `_mover_enemigo` de `src/modelos/partida.py`, programar la próxima acción con el costo real de la acción (100 al atacar o esperar, costo de la salida al moverse) en lugar de 100 fijo (research R8) {FR-003, FR-004, FR-005, FR-007}
- [ ] T019 [US1] Verificar que `_cambiar_velocidad` en `src/modelos/partida.py` escala el tiempo restante sin depender del costo de origen; ajustar si T015 falla {FR-006}
- [ ] T020 [US1] Agregar `costo` de la puerta al guardado binario y subir la versión del formato en `src/servicios/guardado.py`; un archivo de P1 se rechaza como incompatible (research R10) {FR-026, FR-029}
- [ ] T021 [US1] Agregar en `tests/test_guardado.py` una prueba de guardar y cargar con costos y otra de rechazo del formato anterior {FR-026, FR-029}

**Checkpoint**: US1 funciona sola; la batería completa pasa.

---

## Phase 4: User Story 2 - El cazador persigue al jugador por la ruta más barata (Priority: P1)

**Goal**: el comportamiento `cazador` decide atacar, esperar o moverse por la ruta de costo mínimo
con el desempate del enunciado.

**Independent Test**: criptas sintéticas pequeñas con resultado conocido a mano; verificar cada
decisión y el costo de la acción.

### Tests for User Story 2 (escribir primero) ⚠️

- [ ] T022 [P] [US2] En `tests/test_cazador.py`: US2-1, misma sala → ataca con costo 100 y no se mueve {FR-010}
- [ ] T023 [P] [US2] En `tests/test_cazador.py`: US2-2 / Apéndice B, sin ruta abierta → espera con costo 100 {FR-011, FR-012}
- [ ] T024 [P] [US2] En `tests/test_cazador.py`: US2-3 / Apéndice B, `d > rango` → espera; US2-4, `d == rango` → se mueve {FR-012, FR-013}
- [ ] T025 [P] [US2] En `tests/test_cazador.py`: US2-5 / Apéndice B, gana la ruta de menos costo aunque tenga más salas {FR-011, FR-013}
- [ ] T026 [P] [US2] En `tests/test_cazador.py`: US2-6 / Apéndice B, dos vecinas con rutas mínimas → la de menor id; caso con muchas rutas de igual costo que se separan y se vuelven a unir {FR-014}
- [ ] T027 [P] [US2] En `tests/test_cazador.py`: dos salidas hacia la misma vecina → la abierta más barata y, si empatan, el orden N, S, E, O; la acción cuesta la salida elegida (US2-7) {FR-013, FR-015}
- [ ] T028 [P] [US2] En `tests/test_cazador.py`: US2-8, no atraviesa puertas cerradas aunque exista la llave; US2-9, la decisión no depende de si el contenido de una sala está descargado {FR-016, FR-017}
- [ ] T029 [P] [US2] En `tests/test_cazador.py`: US2-10, dormido no actúa aunque el jugador esté en rango; se activa al entrar el jugador, con primera acción de costo base 100; `rango` 0 → espera {FR-018, FR-012}

### Implementation for User Story 2

- [ ] T030 [US2] Implementar `BuscadorRutas.distancias_desde(sala_origen, cota)` en `src/modelos/rutas.py`: búsqueda acotada con `MonticuloMin` y `RegistroBusqueda`, solo salidas con puerta abierta, registra toda sala con distancia ≤ cota y cuenta las salas examinadas (research R5 y R9) {FR-011, FR-016, FR-017, FR-030}
- [ ] T031 [US2] Implementar `BuscadorRutas.primer_paso_desde(origen, objetivo, cota)` (modo individual) en `src/modelos/rutas.py`: propaga el primer paso con el desempate de FR-014 y FR-015, corta al superar la cota y se detiene al extraer el objetivo (depende de T030) {FR-013, FR-014, FR-015, FR-030}
- [ ] T032 [US2] Implementar `DecisorCazadores.decidir(cazador)` en `src/modelos/cazador.py` con modo `compartido` (búsqueda desde el jugador con cota = máximo rango activo, decisión local en O(4)) y modo `individual`, sin reutilización todavía (depende de T030 y T031) {FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-022}
- [ ] T033 [US2] Integrar el comportamiento `CAZADOR` en `Partida._comportamiento` y `_turno_enemigo` de `src/modelos/partida.py` usando `DecisorCazadores` y el costo de la acción decidida (depende de T018 y T032) {FR-010, FR-012, FR-013, FR-018}
- [ ] T034 [US2] Asegurar que el cazador usa activación, combate, muerte, `suelta` y efectos de P1 sin ramas especiales en `src/modelos/partida.py`; ajustar si T029 falla {FR-018}

**Checkpoint**: US1 y US2 funcionan; el cazador decide correctamente en criptas estáticas.

---

## Phase 5: User Story 3 - Las decisiones siguen siendo correctas cuando el mapa cambia (Priority: P2)

**Goal**: equivalencia observable con el cálculo desde cero, con reutilización demostrada.

**Independent Test**: partidas sintéticas largas con puertas que cambian y muchos cazadores,
comparando cada decisión con la referencia.

### Tests for User Story 3 (escribir primero) ⚠️

- [ ] T035 [P] [US3] Crear `tests/referencia_cazador.py`: decisión de referencia desde cero (búsqueda completa sin cota ni reutilización desde cada vecina, desempate literal), con estructuras propias {FR-019}
- [ ] T036 [P] [US3] En `tests/test_equivalencia_cazador.py`: US3-1 / Apéndice B (puerta de la ruta que se cierra entre turnos), US3-2 (se abre un atajo) y US3-3 (el jugador cambia de sala) {FR-019, FR-020}
- [ ] T037 [P] [US3] En `tests/test_equivalencia_cazador.py`: US3-4, cierre automático lejos de las rutas → mismas decisiones, y se reutiliza el cálculo {FR-020, FR-021}
- [ ] T038 [P] [US3] En `tests/test_equivalencia_cazador.py`: US3-5, 30 cazadores con orden de cálculo distinto → misma decisión individual; US3-6, retroceso con pergamino → decisión según el estado restaurado {FR-020, FR-022, FR-028}
- [ ] T039 [US3] En `tests/test_equivalencia_cazador.py`: prueba aleatoria sembrada de ≥ 10 000 decisiones en criptas sintéticas con puertas inestables, en modos compartido e individual, con cero diferencias frente a la referencia (depende de T035; SC-002) {FR-019, FR-020, FR-022}

### Implementation for User Story 3

- [ ] T040 [US3] Agregar `version_puertas` (contador monotónico de infraestructura) en `src/modelos/partida.py` y un único punto de cambio de `Puerta.cerrada` (abrir, cierre automático y deshacer) que lo incremente y llame a `DecisorCazadores.notificar_puerta` (research R6) {FR-020, FR-021}
- [ ] T041 [US3] Implementar la reutilización en `src/modelos/cazador.py`: llave (sala del jugador, cota, `version_puertas`), lista corta de puertas cambiadas con umbral, y regla «ambos extremos fuera de la región examinada»; sin `dict`, `set` ni estructuras equivalentes de biblioteca (research R6) {FR-019, FR-020, FR-021}
- [ ] T042 [US3] Verificar que el decisor, el registro y `version_puertas` no entran al historial de retroceso, al guardado ni a `partida.log` (`src/modelos/partida.py`, `src/servicios/guardado.py`) {FR-021, FR-028, FR-029}
- [ ] T043 [US3] Agregar prueba de `--replay` con cazadores en `tests/test_bitacora.py`: dos reproducciones del mismo log producen las mismas decisiones (SC-005) {FR-027}
- [ ] T044 [US3] Agregar prueba en `tests/test_guardado.py`: guardar a mitad de una persecución, cargar y continuar con las mismas decisiones {FR-029}

**Checkpoint**: US1 a US3 funcionan; SC-002 se cumple.

---

## Phase 6: User Story 4 - Ver el terreno y reconocer a los cazadores (Priority: P3)

**Goal**: la vista muestra el costo de cada salida y marca a los cazadores
([contrato](contracts/interfaz-y-bench.md)).

**Independent Test**: entrar a una sala con costos distintos, un cazador y otro enemigo.

### Tests for User Story 4 (escribir primero) ⚠️

- [ ] T045 [P] [US4] En `tests/test_main.py` o un `tests/test_vista_consola.py` nuevo: US4-1 (cada salida con dirección y costo) y US4-2 (cazador marcado y distinto de otro enemigo) sobre el texto que genera la vista {FR-023, FR-024}

### Implementation for User Story 4

- [ ] T046 [US4] Mostrar el costo de cada salida de la sala actual y la marca `[cazador]` en `src/vistas/vista_consola.py`, sin mostrar distancias ni rutas (contrato) {FR-023, FR-024}

**Checkpoint**: la interfaz mínima de P2 §7.3 para esta capacidad está completa.

---

## Phase 7: User Story 5 - Evidencia de rendimiento para defender las decisiones (Priority: P3)

**Goal**: `--bench` reporta los escenarios exigidos con criptas sintéticas deterministas.

**Independent Test**: ejecutar `--bench` sin vista y revisar las secciones del contrato.

### Tests for User Story 5 (escribir primero) ⚠️

- [ ] T047 [P] [US5] En `tests/test_rendimiento_cazador.py`: SC-004, mismo número de salas examinadas con cripta ×1 y ×10 y la misma región en rango, y ninguna sala examinada más allá del rango salvo el borde {FR-030}
- [ ] T048 [P] [US5] En `tests/test_banco_pruebas.py`: misma semilla → mismas criptas sintéticas y mismos `examinadas_media` y `reutilizaciones`; `--bench` no instancia la vista {FR-035}

### Implementation for User Story 5

- [ ] T049 [US5] Implementar el generador de criptas sintéticas sembradas (cuadrícula, costos aleatorios, puertas que cambian) en `src/servicios/banco_pruebas.py` {FR-035}
- [ ] T050 [US5] Agregar a `src/servicios/banco_pruebas.py` los escenarios de decisión del cazador (1 frente a 30, rango pequeño frente a grande, compartido frente a individual) y montículo frente a lista lineal (depende de T049) {FR-032}
- [ ] T051 [US5] Agregar el escenario de reutilización frente a recalcular siempre, con puertas estables e inestables (depende de T049 y T041) {FR-033}
- [ ] T052 [US5] Agregar el escenario de escala ×1 frente a ×10 y el de ciclo de eventos con ≥ 30 cazadores, reportando `ms_max` (depende de T049; SC-003 y SC-004) {FR-030, FR-031}
- [ ] T053 [US5] Repetir las mediciones de agenda e historial de retroceso de P1 con cazadores y costos variables en `src/servicios/banco_pruebas.py` (P2 §5.6) {FR-034}
- [ ] T054 [US5] Ajustar `formatear` en `src/servicios/banco_pruebas.py` para imprimir los campos del contrato de `--bench` {FR-032, FR-033, FR-035}

**Checkpoint**: todas las historias funcionan y hay evidencia medida.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T055 Ejecutar `python main.py --bench`, elegir el modo por defecto (compartido o individual) según la medición y fijarlo en `src/modelos/cazador.py` {FR-031, FR-032}
- [ ] T056 Escribir en `DECISIONES.md` las secciones de P2 §5.1 y §5.2 con la estructura de P1 §8, enlazando a [spec.md](spec.md) y [plan.md](plan.md), e indicando si la decisión final coincide con el plan y qué medición motivó un cambio {FR-030, FR-031, FR-032, FR-033}
- [ ] T057 Escribir en `DECISIONES.md` la parte de P2 §5.6 correspondiente a esta capacidad (agenda e historial con la carga nueva: antes y después, o datos que muestran que siguen siendo adecuados) {FR-034}
- [ ] T058 Actualizar `README.md` con cómo ejecutar las pruebas de aceptación de esta capacidad (ver [quickstart.md](quickstart.md)) {SC-001}
- [ ] T059 Revisar que ningún archivo nuevo o modificado importe `heapq`, `bisect`, `collections` ni `networkx`, ni use `dict` o `set` como índice o caché (constitución, Principio I) {FR-021}
- [ ] T060 Ejecutar `python -m pytest -q` completo y validar [quickstart.md](quickstart.md) de punta a punta {SC-001, SC-005, SC-007}

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup y **bloquea todas las historias**.
- **US1 (Phase 3)**: depende de Foundational.
- **US2 (Phase 4)**: depende de Foundational y de T018 (costo de la acción del enemigo).
- **US3 (Phase 5)**: depende de US2.
- **US4 (Phase 6)**: depende de Foundational y de T012; puede hacerse en paralelo con US2 y US3.
- **US5 (Phase 7)**: T049 y T050 dependen de US2; T051 depende de US3.
- **Polish (Phase 8)**: depende de todas las historias.

### Within Each User Story

- Las pruebas se escriben primero y deben fallar antes de implementar.
- Estructuras → modelo → integración en `Partida` → vista y bench.
- Commit al terminar cada tarea o grupo lógico; si la especificación resulta incorrecta, se corrige
  primero `spec.md` en un commit separado (constitución, Principio VIII).

### Parallel Opportunities

- Phase 2: T003, T004, T005 y T006 (pruebas), y luego T007 y T008.
- Phase 3: T013 a T016.
- Phase 4: T022 a T029.
- Phase 5: T035 a T038.
- US4 completa en paralelo con US2 y US3, porque toca otros archivos.

---

## Parallel Example: User Story 2

```bash
# Escribir juntas las pruebas de decisión del cazador (mismo archivo, secciones separadas):
Task: "T022 [US2] misma sala → ataca"
Task: "T023 [US2] sin ruta → espera"
Task: "T026 [US2] desempate por menor id"
Task: "T027 [US2] varias salidas hacia la misma vecina"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 y Phase 2.
2. Phase 3 (US1): el terreno con costo funciona para todos los actores.
3. **Validar** US1 y la batería de P1.

### Incremental Delivery

1. US1 → terreno.
2. US2 → cazador correcto en mapas estáticos.
3. US3 → equivalencia con mapas cambiantes y reutilización.
4. US4 → interfaz.
5. US5 + Polish → evidencia, `DECISIONES.md` y README.

### Trazabilidad para la defensa (P2 §2.5)

Para cualquier `FR-NNN`: escenario en [spec.md](spec.md) → tarea en este archivo (busca
`{… FR-NNN …}`) → código (archivo indicado en la tarea) → prueba que cita `FR-NNN`.
