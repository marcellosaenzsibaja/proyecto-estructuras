---

description: "Lista de tareas para la implementación de la verificación de resolubilidad de una cripta"
---

# Tasks: Verificación de resolubilidad de una cripta

**Input**: Documentos de diseño de `/specs/002-verificacion-resolubilidad/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/interfaz-y-reporte.md](contracts/interfaz-y-reporte.md), [quickstart.md](quickstart.md)

**Tests**: Obligatorios (Principio VIII de la Constitución y SC-001). Cada escenario de aceptación cuenta con al menos una prueba automatizada que cita el requisito (`FR-NNN`) en su nombre o docstring. Las pruebas se escriben primero y deben fallar antes de implementar.

**Organization**: Tareas agrupadas por historia de usuario en orden de dependencias. Cada tarea referencia explícitamente los requisitos `FR-NNN` que atiende; no existen tareas sin requisito asociado.

## Format: `- [ ] [ID] [P?] [Story?] Descripción con ruta de archivo {requisitos}`

- **[P]**: Ejecutable en paralelo (archivos independientes, sin dependencias pendientes).
- **[Story]**: Etiqueta de historia de usuario (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`), requerida exclusivamente en fases de historias.

---

## Phase 1: Setup & Restricciones Constitucionales

**Purpose**: Preparar el andamiaje de pruebas sintéticas reproducibles y blindar el proyecto contra el uso de estructuras de conveniencia prohibidas por la Constitución.

- [x] T001 Actualizar `ARCHIVOS_VIGILADOS` en `tests/test_restricciones.py` para incluir todos los módulos y pruebas nuevos de la capacidad 002 (`src/estructuras_datos/busqueda_binaria.py`, `src/modelos/resolubilidad.py`, `src/servicios/verificador_servicio.py`, `src/servicios/banco_resolubilidad.py`, etc.), asegurando mediante AST la ausencia de `dict`, `set`, `heapq`, `bisect`, `collections` y librerías de grafos {FR-025, FR-028, FR-031}
- [x] T002 [P] Extender el generador sintético en `src/servicios/generador_criptas.py` para construir texto JSON determinista por semilla con puertas cerradas, cadenas de llaves encadenadas y asignación de llaves a salas o instancias de enemigos sin usar diccionarios de conveniencia {FR-025, FR-030}
- [x] T003 Escribir pruebas unitarias en `tests/test_generador_criptas.py` para validar la correcta generación sintética determinista de criptas con llaves y salidas con cerradura {FR-025, FR-030}

---

## Phase 2: Foundational (Estructuras Auxiliares Propias)

**Purpose**: Implementar las estructuras de datos propias de bajo nivel indispensables antes de iniciar el modelo de resolubilidad.

- [x] T004 [P] Escribir pruebas unitarias en `tests/test_busqueda_binaria.py` que validen la búsqueda binaria sobre listas ordenadas (búsqueda exacta, elemento ausente, extremos, lista vacía) {FR-010, FR-027}
- [x] T005 Implementar la función de búsqueda binaria propia en `src/estructuras_datos/busqueda_binaria.py` sobre listas de identificadores ordenados en $O(\log m)$ sin utilizar `bisect` {FR-010, FR-027}
- [x] T006 [P] Escribir pruebas unitarias en `tests/test_monticulo_llaves.py` comprobando la reutilización de `MonticuloMin` (`src/estructuras_datos/monticulo.py`) almacenando pares `(indice_llave, indice_llave)` para extraer deterministamente la llave de menor `id` lexicográfico en $O(\log k)$ {FR-009, FR-010}
- [x] T007 Implementar en `src/modelos/resolubilidad.py` las clases y estructuras de datos base: `LlaveInfo`, `PuertaBloqueada`, `ReporteResolubilidad`, `IndexadorLlaves` (mapeo con `ordenar()` y búsqueda binaria) y `RegistroEsperaPuertas` {FR-001, FR-005, FR-006, FR-010, FR-014}

**Checkpoint**: Estructuras auxiliares completas y verificadas sin dependencias externas.

---

## Phase 3: User Story 2 - Secuencia determinista de obtención de llaves en criptas resolubles (Priority: P1) 🎯 MVP Core

**Goal**: Implementar el recorrido lineal reactivo $O(|V| + |E| + |K|)$ que determina si una cripta es resoluble y produce el orden determinista de obtención de llaves bajo supuestos ideales.

**Independent Test**: Verificar criptas lineales y con bifurcaciones, comprobando que cada llave aparece tras las necesarias para alcanzarla y que dos ejecuciones producen el mismo orden alfanumérico.

### Pruebas de User Story 2 (TDD) ⚠️

- [x] T008 [P] [US2] Escribir pruebas unitarias y de aceptación en `tests/test_resolubilidad.py` para criptas resolubles:
  - Cadena lineal simple de llaves (Escenario US2-1 {FR-007, FR-008})
  - Apéndice B Caso 3: Cripta con bifurcaciones y múltiples caminos válidos, comprobando idéntico orden determinista mediante desempate alfanumérico con `MonticuloMin` (Escenario US2-2 {FR-009, FR-010})
  - Apéndice B Caso 2: Llave en el campo `suelta` de un enemigo errante ubicada en su sala inicial (Escenario US2-3 {FR-005, FR-006})
  - Supuestos de verificación: no consumo de llaves, trampas y puertas con autocierre que no bloquean permanentemente (Escenario US2-4 {FR-002, FR-003, FR-004})

### Implementación de User Story 2

- [x] T009 [US2] Implementar el motor de exploración lineal reactiva `VerificadorResolubilidad.verificar()` en `src/modelos/resolubilidad.py`:
  - Arreglo de visitados `[False] * n` indexado por `Sala.indice` (R2)
  - Cola continua nativa con puntero de lectura entero `cabeza` (R1)
  - Frontera de llaves alcanzadas gestionada con `MonticuloMin` para desempate canónico en $O(|K| \log |K|)$ (R3b)
  - Reactivación en $O(1)$ de puertas en espera al descubrir su llave mediante `RegistroEsperaPuertas` (R4)
  - Validación de la condición de victoria: obtención de `llave_salida` y llegada a `sala_salida` a través de puerta que la requiere {FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-028}

**Checkpoint**: El modelo determina resolubilidad y produce órdenes deterministas en criptas ganables.

---

## Phase 4: User Story 3 - Diagnóstico y reporte determinista de criptas irresolubles (Priority: P2)

**Goal**: Diagnosticar criptas no resolubles identificando llaves inalcanzables, puertas de frontera bloqueada con ubicación de llaves y detección de ciclos mediante DFS iterativo con pila propia.

**Independent Test**: Verificar criptas irresolubles con puertas sin llave, llaves inalcanzables y ciclos directos e indirectos, comprobando la exactitud del reporte y la normalización canónica de los ciclos.

### Pruebas de User Story 3 (TDD) ⚠️

- [x] T010 [P] [US3] Escribir pruebas unitarias y de aceptación en `tests/test_resolubilidad_irresoluble.py` para criptas irresolubles:
  - Apéndice B Caso 1: `llave_salida` detrás de la única puerta que abre -> no resoluble y reporte señala el ciclo directo `[llave_salida -> llave_salida]` (Escenario US3-1 {FR-011, FR-015, FR-016})
  - Dependencia circular indirecta (cadena $A \to B \to C \to A$), comprobando la detección determinista del ciclo canónico cerrado `[L_min -> ... -> L_min]` (Escenario US3-2 {FR-015, FR-016})
  - Identificación de todas las puertas de la frontera bloqueada adyacentes a la región accesible (Escenario US3-3 {FR-012, FR-013})
  - Identificación de la sala donde se ubica cada llave requerida por la frontera bloqueada (Escenario US3-4 {FR-014})
  - Llegada a `sala_salida` pero sin atravesar puerta que requiera `llave_salida` (Escenario US3-5 {FR-007, FR-011})
  - Robustez iterativa: prueba con cadena sintética profunda ($\ge 1500$ llaves) comprobando que no ocurre `RecursionError` {FR-015, FR-016}

### Implementación de User Story 3

- [x] T011 [US3] Implementar en `src/modelos/resolubilidad.py` la extracción de la frontera bloqueada (`PuertaBloqueada`) y la lista de llaves no obtenidas desde las puertas que quedaron en espera al agotarse la exploración {FR-011, FR-012, FR-013, FR-014, FR-029}
- [x] T012 [US3] Implementar en `src/modelos/resolubilidad.py` la construcción del grafo de dependencias dirigidas entre llaves no alcanzadas explorando las componentes inaccesibles desde las puertas de frontera en el mismo recorrido lineal {FR-015, FR-029}
- [x] T013 [US3] Implementar en `src/modelos/resolubilidad.py` la detección de ciclos mediante búsqueda en profundidad (DFS) **estrictamente iterativa con pila propia LIFO** (`pila = [...]`), normalización canónica iniciando en la llave de menor `id` (`[L_min -> ... -> L_min]`) y ordenamiento canónico de múltiples ciclos {FR-015, FR-016}
- [x] T014 [US3] Implementar el método de formateo en `src/modelos/resolubilidad.py` para generar el texto del reporte de resolubilidad e irresolubilidad según el contrato de consola {FR-011, FR-013, FR-014, FR-015}

**Checkpoint**: Diagnóstico completo de criptas no resolubles con reporte estructurado y detección de ciclos robusta.

---

## Phase 5: User Story 4 - Consulta de llaves bajo presupuesto y persistencia por versión (Priority: P2)

**Goal**: Consultar la ubicación de llaves mediante `GET /criptas/<id>/llaves` respetando el presupuesto de solicitudes, manejando HTTP 429 con `reintentar_en` (sin retroceso exponencial), y persistiendo los datos validados por versión en modo con y sin conexión.

**Independent Test**: Ejecutar consultas consecutivas comprobando que el presupuesto solo se descuenta en la primera solicitud, que se leen datos de disco en llamadas posteriores o en `--offline`, y que se maneja 429.

### Pruebas de User Story 4 (TDD) ⚠️

- [x] T015 [P] [US4] Escribir pruebas unitarias y de integración en `tests/test_verificador_servicio.py`:
  - Solicitud a `GET /criptas/<id>/llaves` descuenta 1 unidad del `presupuesto_solicitudes` (Escenario US4-1 {FR-021, FR-022})
  - Reutilización de `ApiClient._get` esperando `reintentar_en` ante código HTTP 429 sin retroceso exponencial (Escenario US4-1 {FR-021, FR-022})
  - Persistencia de `llaves.json` asociada a versión y reutilización con 0 llamadas HTTP y 0 consumo de presupuesto cuando la versión coincide (Escenario US4-2 {FR-023, FR-024})
  - Operación en modo `--offline` leyendo desde almacenamiento local sin peticiones de red (Escenario US4-3 {FR-024})
  - Invalidación de caché local si la versión en el servidor difiere (Escenario US4-4 {FR-023, FR-024})

### Implementación de User Story 4

- [x] T016 [P] [US4] Declarar la firma del método abstracto `obtener_llaves(self, cripta_id: str) -> dict` en `src/adaptadores/fuente_datos.py` {FR-021}
- [x] T017 [US4] Implementar `obtener_llaves(self, cripta_id: str) -> dict` en `src/adaptadores/api_client.py` delegando en `self._get(f'/criptas/{cripta_id}/llaves', ...)` para reservar presupuesto y reutilizar la espera exacta de `reintentar_en` ante HTTP 429 {FR-021, FR-022}
- [x] T018 [P] [US4] Implementar `obtener_llaves(self, cripta_id: str) -> dict` en `src/adaptadores/fuente_sin_conexion.py` leyendo `<carpeta>/<cripta_id>/llaves.json` {FR-024}
- [x] T019 [P] [US4] Implementar soporte de llaves en memoria en `src/adaptadores/fuente_memoria.py` para pruebas unitarias y benchmarks sin disco ni red {FR-024, FR-025}
- [x] T020 [US4] Actualizar la herramienta `herramientas/exportar_offline.py` para exportar `llaves.json` por cada cripta consultada {FR-024}
- [x] T021 [US4] Implementar en `src/servicios/verificador_servicio.py` la carga orquestada de llaves con caché persistente en disco validada por versión de cripta {FR-021, FR-022, FR-023, FR-024}

**Checkpoint**: Acceso a datos de llaves integrado, persistido y protegido contra sobreconsumo de cuota.

---

## Phase 6: User Story 1 - Verificación previa y control de inicio de partida (Priority: P1)

**Goal**: Integrar la verificación en la interfaz CLI del juego, soportando el arranque normal, el bloqueo ante criptas irresolubles salvo uso de `--forzar`, y la ejecución independiente con `--verificar <cripta>` sin instanciar la vista interactiva.

**Independent Test**: Ejecutar comandos CLI con criptas resolubles e irresolubles con y sin `--forzar` y con `--verificar`, comprobando la salida en consola y los códigos de retorno del proceso (0, 1, 2).

### Pruebas de User Story 1 (TDD) ⚠️

- [x] T022 [P] [US1] Escribir pruebas funcionales en `tests/test_cli_verificar.py` validando:
  - Cripta resoluble imprime reporte e inicia la partida de inmediato sin pausas bloqueantes (Escenario US1-1 {FR-017})
  - Apéndice B Caso 4: Cripta no resoluble sin `--forzar` aborta la partida, muestra el reporte y sale con código 1 (Escenario US1-2 {FR-018})
  - Cripta no resoluble con `--forzar` imprime el reporte y permite iniciar la partida interactiva (Escenario US1-3 {FR-019})
  - Opción `--verificar <cripta>` ejecuta únicamente la verificación sin instanciar `VistaConsola` y devuelve 0 (resoluble), 1 (no resoluble) o 2 (error técnico) (Escenario US1-4 {FR-020})

### Implementación de User Story 1

- [x] T023 [US1] Añadir los argumentos `--verificar` (con identificador de cripta) y `--forzar` (bandera booleana) a `leer_argumentos()` en `main.py` {FR-019, FR-020}
- [x] T024 [US1] Implementar en `main.py` la ejecución aislada de `--verificar <cripta>` invocando `verificador_servicio`, imprimiendo el reporte en `stdout` y retornando código 0, 1 o 2 sin instanciar `VistaConsola` ni el bucle de juego {FR-020}
- [x] T025 [US1] Modificar `_ejecutar_partida()` en `main.py` y `ControladorJuego` para ejecutar la verificación previa al iniciar partida: imprimir reporte en consola, abortar con código 1 si es irresoluble y no se pasa `--forzar`, o continuar inmediatamente sin pausas bloqueantes {FR-017, FR-018, FR-019}

**Checkpoint**: Comandos `--verificar`, `--forzar` y arranque normal completamente funcionales y trazables.

---

## Phase 7: User Story 5 - Rendimiento lineal y reproducibilidad en `--bench` (Priority: P3)

**Goal**: Implementar escenarios de benchmark reproducibles por semilla en `--bench` para demostrar la verificación en $< 200\text{ ms}$ en cripta grande y contrastar el escalamiento lineal $O(N)$ frente a la alternativa ingenua cuadrática $O(N^2)$ con cadenas de hasta 500 llaves.

**Independent Test**: Ejecutar `python main.py --bench` y verificar que emite las secciones de resolubilidad con tiempos $< 200\text{ ms}$, sin instanciar la vista y con resultados idénticos ante la misma semilla.

### Pruebas de User Story 5 (TDD) ⚠️

- [x] T026 [P] [US5] Escribir pruebas unitarias en `tests/test_bench_resolubilidad.py` validando:
  - Cripta sintética grande de 1 000 salas y 40 llaves verificada en $< 200\text{ ms}$ sin red ni vista (Escenario US5-1 {FR-026})
  - Escalamiento empírico del algoritmo lineal reactivo frente a la alternativa ingenua con cadenas de 10 a 500 llaves (Escenario US5-2 {FR-027, FR-028})
  - Frontera bloqueada y dependencias de llaves derivadas del mismo recorrido único sin recorridos adicionales por llave (Escenario US5-3 {FR-029})
  - Determinismo por semilla: dos ejecuciones con la misma semilla generan idénticas criptas sintéticas y resultados (Escenario US5-4 {FR-030, FR-031})

### Implementación de User Story 5

- [x] T027 [US5] Implementar en `src/servicios/banco_resolubilidad.py` la alternativa ingenua de verificación (reinicio completo de la exploración desde `sala_inicial` cada vez que se recolecta una llave) exclusivamente como línea base de medición en `--bench` {FR-028}
- [x] T028 [US5] Implementar en `src/servicios/banco_resolubilidad.py` los generadores de escenarios sintéticos deterministas por semilla (cripta grande de 1 000 salas y familias de cadenas de 10, 25, 50, 100 y 500 llaves) y las rutinas de cronometraje de alta resolución {FR-026, FR-027, FR-030}
- [x] T029 [US5] Integrar los escenarios de resolubilidad en `ejecutar_todo()` y `formatear()` de `src/servicios/banco_pruebas.py`, asegurando que no instancie la vista interactiva y emita el formato de contrato {FR-030, FR-031}

**Checkpoint**: Mediciones de `--bench` implementadas y listas para defender las decisiones de complejidad empíricamente.

---

## Phase 8: Polish & Verificación Integral

**Purpose**: Verificación de restricciones constitucionales, regresión global y validación del flujo completo.

- [x] T030 [P] Ejecutar la suite `tests/test_restricciones.py` para validar mediante análisis de AST que ningún módulo nuevo en `src/` o `tests/` utiliza `dict`, `set`, `heapq`, `bisect`, `collections` ni bibliotecas externas de grafos {FR-025, FR-028, FR-031}
- [x] T031 Ejecutar la suite completa de pruebas unitarias y de aceptación (`python -m unittest discover tests/`) comprobando que todas las pruebas existentes de P1 y de la capacidad 001 continúan pasando al 100% (SC-008) {FR-025}
- [~] T032 Ejecutar la validación completa guiada en [quickstart.md](quickstart.md) verificando pruebas unitarias, comandos CLI (`--verificar`, `--forzar`) y salida formateada de `--bench` {FR-020, FR-026, FR-030}

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup & Restricciones
   │
   ▼
Phase 2: Foundational (Búsqueda Binaria, MonticuloMin, Modelos Base)
   │
   ▼
Phase 3: User Story 2 (P1) ──► Núcleo del algoritmo BFS reactivo resoluble
   │
   ▼
Phase 4: User Story 3 (P2) ──► Diagnóstico irresoluble y DFS iterativo de ciclos
   │
   ▼
Phase 5: User Story 4 (P2) ──► Adaptadores de red, persistencia y presupuesto de llaves
   │
   ▼
Phase 6: User Story 1 (P1) ──► Integración CLI (--verificar, --forzar y arranque normal)
   │
   ▼
Phase 7: User Story 5 (P3) ──► Mediciones empíricas en --bench
   │
   ▼
Phase 8: Polish & Verificación Integral (AST, regresión global, quickstart)
```

### Oportunidades de ejecución en paralelo

- **En Phase 1**: T002 puede desarrollarse en paralelo con T001.
- **En Phase 2**: T004 y T006 pueden implementarse en paralelo (archivos de prueba independientes).
- **En Phase 3 (US2)**: T008 (pruebas TDD) se escribe primero; una vez establecida, desbloquea T009.
- **En Phase 4 (US3)**: T010 (pruebas TDD) se escribe primero; T011 y T012 pueden avanzar conjuntamente hacia T013.
- **En Phase 5 (US4)**: T016, T018 y T019 (adaptadores) pueden implementarse en paralelo tras definir la interfaz.
- **En Phase 6 (US1)**: T022 (pruebas CLI) se escribe antes de implementar los despachos en `main.py`.
- **En Phase 7 (US5)**: T026 (pruebas de bench) se escribe antes de los generadores en T028.
- **En Phase 8**: T030 puede ejecutarse en paralelo con la revisión de documentación.

---

## Implementation Strategy & MVP

1. **MVP (Mínimo Producto Viable)**:
   - Completar Fases 1, 2 y 3 (T001 a T009).
   - En este punto, el sistema ya puede verificar deterministamente criptas resolubles con el algoritmo lineal reactivo y desempate por montículo binario propio.
2. **Diagnóstico Completo**:
   - Completar Fase 4 (T010 a T014): diagnóstico exhaustivo de irresolubilidad y detección iterativa de ciclos de dependencias.
3. **Integración con Infraestructura y CLI**:
   - Completar Fases 5 y 6 (T015 a T025): persistencia de llaves, respeto del presupuesto de red y comandos CLI (`--verificar`, `--forzar`).
4. **Validación Empírica**:
   - Completar Fases 7 y 8 (T026 a T032): mediciones en `--bench`, verificación de restricciones constitucionales por AST y regresión total.

## Desviaciones respecto de lo planificado (registradas al implementar)

- T007 y T009: la implementación expone la función `verificar()` y funciones auxiliares de módulo en `src/modelos/resolubilidad.py`; no existen las clases `IndexadorLlaves`, `RegistroEsperaPuertas` ni `VerificadorResolubilidad`. Los arreglos indexados que describe el plan se usan directamente. {FR-001, FR-007, FR-027}
- T012: el grafo de dependencias se obtiene con un recorrido lineal adicional sobre las salas no alcanzadas (componentes unidas por salidas pasables), no por un recorrido por llave; el costo total sigue siendo O(|V| + |E| + |llaves|). Una dependencia K → k significa que K está en una componente cuya entrada, en el nivel anterior, es una puerta que requiere k. {FR-015, FR-029}
- T006: la prueba del montículo con pares de llaves está en `tests/test_monticulo_llaves.py`; T026: el archivo es `tests/test_bench_resolubilidad.py`.
- T025: `--cargar` y `--replay` no ejecutan la verificación; solo la ejecuta el inicio de una partida nueva. Al abortar una partida no resoluble sin `--forzar` el proceso devuelve código 1.
- T032 (validación guiada de `quickstart.md`) queda pendiente.

> T032 queda parcial: las pruebas unitarias, la salida de `--bench` y los códigos de
> salida de `--verificar` y `--forzar` se validaron; las cuatro comprobaciones contra
> una cripta publicada del servicio requieren red y las ejecuta el grupo.
