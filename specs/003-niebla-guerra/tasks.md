# Tasks: Niebla de guerra y viaje automático «ir a»

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-18

Cada tarea referencia entre llaves los requisitos de [spec.md](spec.md) que atiende. `[P]` marca
tareas que pueden hacerse en paralelo con la anterior porque no tocan los mismos archivos.

## Fase 1 — Andamiaje de pruebas y restricciones

- [ ] T001 Ampliar `ARCHIVOS_VIGILADOS` en `tests/test_restricciones.py` con los módulos nuevos de la
  capacidad (`src/modelos/mapa_conocido.py`, `src/modelos/viaje.py`, `src/servicios/banco_mapa.py`) y
  sus pruebas, verificando por AST la ausencia de `dict`, `set`, `heapq`, `bisect`, `collections` y
  bibliotecas de grafos {FR-054}
- [ ] T002 [P] Extender `src/servicios/generador_criptas.py` para generar criptas sintéticas
  deterministas por semilla con vecindades controladas: una rejilla con costos variados, puertas
  cerradas y la posibilidad de fijar el grado de una sala, para medir exploración con antorcha
  {FR-051, FR-056}
- [ ] T003 Escribir `tests/referencia_conocido.py`: referencia teórica que, dado un mapa conocido,
  calcula por fuerza bruta el costo mínimo y el primer paso correcto sobre el subgrafo conocido, para
  comparar contra la implementación {FR-030, FR-031, FR-032}

## Fase 2 — El mapa conocido

- [ ] T004 [P] Escribir `tests/test_mapa_conocido.py` con los escenarios de la User Story 1: los tres
  estados, la sala inicial explorada desde el instante 0, el avistamiento de las vecinas al explorar,
  y que una sala avistada no expone nombre ni salidas ni costos {FR-001, FR-002, FR-003, FR-004,
  FR-005, FR-006, FR-007}
- [ ] T005 Implementar `MapaConocido` en `src/modelos/mapa_conocido.py`: listas de estado de sala y de
  estado recordado de puertas indexadas por `Sala.indice`, lista de ids explorados en orden, y las
  consultas en tiempo constante {FR-001 a FR-007, FR-050}
- [ ] T006 Agregar a `tests/test_mapa_conocido.py` los escenarios de la User Story 2: observación
  desde cualquiera de los dos extremos, memoria del estado de la última observación, «sin observar»
  distinto de abierta, y corrección al volver a la sala {FR-008 a FR-012}
- [ ] T007 Implementar en `MapaConocido` la observación de puertas: `observar_puertas` y
  `observar_puerta` reciben el estado real como argumento y fijan el estado recordado, sin leer la
  cripta por su cuenta {FR-008 a FR-012}
- [ ] T008 Implementar en `MapaConocido` el registro de reversión: cada operación que cambia una
  posición registra su valor anterior mediante la función de deshacer de la partida, y solo si
  efectivamente cambia {FR-048, FR-052}
- [ ] T009 Implementar en `MapaConocido` los conteos `salas_tocadas` y `puertas_tocadas` de la última
  exploración, para verificar SC-004 por conteo y no por tiempo {FR-051}

## Fase 3 — Integración con la partida

- [ ] T010 Crear el `MapaConocido` en el constructor de `Partida` y explorar la sala inicial con sus
  puertas observadas en `Partida.iniciar` {FR-002, FR-022}
- [ ] T011 En `Partida._mover`, al llegar a la sala destino: observar sus puertas y explorarla, en ese
  orden y antes de activar enemigos y trampas {FR-003, FR-007, FR-012}
- [ ] T012 En `Partida._abrir`, registrar la puerta abierta como recordada abierta {FR-013}
- [ ] T013 [P] Escribir `tests/test_antorcha_exploracion.py` con los escenarios de la User Story 3,
  incluidos los dos casos del Apéndice B: la antorcha explora las vecinas por salidas abiertas y
  cerradas sin activar enemigos ni trampas, y un pergamino revierte esa exploración {FR-014 a FR-019,
  FR-048}
- [ ] T014 Implementar en `Partida._mover` el efecto de la antorcha encendida: explorar todas las
  salas destino de las salidas de la sala a la que se entró, sin incorporar contenido, sin activar
  enemigos ni trampas y sin observar las puertas que esas vecinas no comparten con la sala del
  jugador {FR-014 a FR-017, FR-019}
- [ ] T015 Verificar que entrar físicamente a una sala explorada antes por la antorcha incorpora su
  contenido y activa sus enemigos y trampas como cualquier primera entrada {FR-018}
- [ ] T016 Comprobar que el conocimiento del jugador no influye en las decisiones del cazador ni en
  la infraestructura: ampliar `tests/test_cazador.py` con un caso donde la ruta del cazador atraviesa
  salas desconocidas para el jugador y su decisión no cambia, y comprobar que la precarga sigue
  usando el esqueleto completo sin mirar el mapa conocido {FR-020, FR-023}

## Fase 4 — Búsqueda sobre el subgrafo conocido

- [ ] T017 [P] Escribir `tests/test_viaje.py` con los escenarios de ruta de la User Story 4: ruta de
  menor costo frente a ruta de menos salas, desempate por menor id, salidas paralelas a la misma
  vecina, y que una puerta recordada cerrada no se usa aunque el jugador tenga la llave {FR-030 a
  FR-033, FR-041}
- [ ] T018 Implementar `BuscadorConocido` en `src/modelos/viaje.py`: búsqueda de costo mínimo sobre
  salas exploradas y salidas recordadas abiertas, reutilizando `MonticuloMin` y `RegistroBusqueda`,
  sin recibir nunca el estado real de las puertas {FR-030, FR-031, FR-053}
- [ ] T019 Implementar en `BuscadorConocido` el desempate por menor id del primer paso con la misma
  técnica de etiquetado de la capacidad 001, y el criterio de salidas paralelas {FR-032, FR-033}
- [ ] T020 Escribir `tests/test_equivalencia_viaje.py`: comparar el primer paso que devuelve
  `BuscadorConocido` contra `tests/referencia_conocido.py` en al menos 10 000 cálculos sobre mapas
  conocidos sintéticos {FR-030 a FR-033, SC-005}
- [ ] T021 Exponer en `Partida` los métodos `siguiente_paso_viaje`, `ruta_conocida_existe`,
  `destino_valido` y `resolver_destino`, que son el único punto por el que el viaje consulta la ruta
  {FR-028, FR-029, FR-035}

## Fase 5 — El viaje

- [ ] T022 Agregar a `tests/test_viaje.py` los escenarios de rechazo de la User Story 4, incluido el
  caso del Apéndice B del destino no explorado: destino no explorado, destino igual a la sala actual,
  nombre ambiguo y destino sin ruta conocida, todos sin consumir tiempo virtual {FR-028, FR-029}
- [ ] T023 Implementar `Viaje` y `ServicioViaje` en `src/modelos/viaje.py`: validación del destino,
  cálculo del siguiente paso antes de cada paso y evaluación del motivo de detención en el orden
  declarado en `data-model.md` {FR-027, FR-035, FR-036, FR-042}
- [ ] T024 [P] Agregar a `tests/test_viaje.py` los escenarios de parada de la User Story 5, incluidos
  los dos casos del Apéndice B restantes: enemigos dormidos que se activan y detienen el viaje, y la
  puerta recordada abierta que al observarse cierra la ruta y detiene el viaje sin consumir tiempo
  adicional {FR-037, FR-038, FR-039, FR-040}
- [ ] T025 Implementar las condiciones de parada en `ServicioViaje`: fin de partida, llegada, daño
  recibido comparando la vida del jugador antes y después de cada paso, enemigos activos o dormidos
  en la sala de llegada, y ausencia de ruta conocida antes de un paso {FR-036 a FR-040}
- [ ] T026 Implementar el recálculo del primer paso antes de cada paso, sin conservar ninguna ruta
  entre pasos {FR-035}
- [ ] T027 Verificar que cada paso del viaje es una acción del jugador completa: consume el costo de
  su salida, despacha los eventos del reloj entre pasos y cuenta en `acciones_jugador` {FR-034}
- [ ] T028 Verificar que el pergamino de retroceso revierte únicamente el último paso de un viaje y
  que el viaje no continúa {FR-045}

## Fase 6 — Interfaz

- [ ] T029 [P] Implementar `mostrar_mapa_conocido` en `src/vistas/vista_consola.py`: salas exploradas
  con sus salidas y el estado recordado de cada puerta, distinguiendo «sin observar», y las salas
  avistadas {FR-024, FR-025}
- [ ] T030 Cambiar `mostrar_estado` para que las salidas de la sala actual se describan con el estado
  recordado del mapa y no con el estado real de las puertas {FR-021, FR-025}
- [ ] T031 Implementar `mostrar_fin_viaje`: informa el motivo de detención y los pasos dados
  {FR-042}
- [ ] T032 Agregar al `ControladorJuego` el comando `mapa`, que muestra el mapa conocido sin consumir
  tiempo, sin registrarse en `partida.log` y sin tocar el historial de retroceso {FR-024, FR-026}
- [ ] T033 Agregar al `ControladorJuego` el comando `ir a <sala>`: resuelve el destino, graba el
  comentario en la bitácora y ejecuta el viaje paso a paso con `ServicioViaje` {FR-027, FR-028,
  FR-043}
- [ ] T034 Ampliar `tests/test_vista_consola.py` con la vista del mapa conocido y la del fin de
  viaje, comprobando que la vista no expone nada de una sala avistada ni el estado real de una puerta
  {FR-021, FR-024, FR-025, FR-042}

## Fase 7 — Bitácora, persistencia y reproducción

- [ ] T035 [P] Escribir `tests/test_viaje_bitacora.py`: un viaje de varios pasos graba un movimiento
  por paso más una línea de comentario, y la reproducción ejecuta solo los movimientos {FR-043,
  FR-044}
- [ ] T036 Implementar `registrar_comentario` en `src/servicios/bitacora.py` y hacer que `leer`
  ignore las líneas de tipo comentario al construir la lista de acciones {FR-043, FR-044}
- [ ] T037 [P] Escribir `tests/test_mapa_guardado.py`: guardar y cargar una partida con mapa parcial
  reproduce el mapa exacto, incluidas salas avistadas y exploradas sin contenido; un archivo de
  formato anterior se rechaza {FR-046, FR-047}
- [ ] T038 Implementar la sección del mapa conocido en `tomar_snapshot` y su reconstrucción en
  `restaurar_partida`, emitiendo las salas exploradas en orden seguidas de las avistadas {FR-046}
- [ ] T039 Subir `FORMATO_VERSION` de 2 a 3 en `src/servicios/guardado.py` y comprobar que un archivo
  de versión 2 se reporta como incompatible {FR-047}
- [ ] T040 Verificar el determinismo del mapa y de las rutas con `--replay`: dos reproducciones del
  mismo `partida.log` producen el mismo mapa conocido y la misma secuencia de salas {FR-049, SC-008}

## Fase 8 — Mediciones

- [ ] T041 [P] Escribir `src/servicios/banco_mapa.py` con las seis secciones del plan:
  `[mapa_consultas]`, `[mapa_exploracion]`, `[viaje_paso]`, `[viaje_vs_cazador]`,
  `[mapa_reversion]` y `[mapa_determinismo]` {FR-055, FR-056}
- [ ] T042 Conectar `banco_mapa` al `--bench` existente, manteniendo el formato de salida de las
  capacidades 001 y 002 y sin instanciar la vista {FR-055, FR-056}
- [ ] T043 [P] Escribir `tests/test_rendimiento_mapa.py`: el cálculo de un paso de `ir a` con el mapa
  conocido completo de la cripta sintética de referencia queda bajo 5 ms, y los conteos de una
  exploración con antorcha son iguales en la cripta pequeña y en la 10 veces más grande {FR-051,
  FR-053, SC-003, SC-004}
- [ ] T044 Escribir la prueba de SC-002: en una partida sintética de al menos 1 000 acciones con
  antorchas, cierres automáticos y pergaminos, el mapa conocido coincide con el que se obtiene
  recalculándolo desde el inicio a partir de la secuencia de acciones {FR-049, SC-002}

## Fase 9 — Documentación y cierre

- [ ] T045 [P] Escribir la sección §P2 5.3 de `DECISIONES.md` con la estructura de P1 §8: problema,
  alternativas consideradas, decisión, análisis de complejidad, evidencia empírica y límites
  conocidos; enlazar a esta especificación y a este plan, e indicar si la decisión final coincide con
  la del plan original {FR-055}
- [ ] T046 [P] Actualizar `README.md`: comandos `mapa` e `ir a`, la nueva versión de formato de
  guardado y su efecto sobre los archivos existentes, las secciones nuevas de `--bench` y los
  comandos para correr las pruebas de aceptación de esta capacidad {FR-024, FR-027, FR-047}
- [ ] T047 Corregir la referencia desactualizada de `specs/001-terreno-cazador/spec.md`, que en
  «Fuera del alcance» numera la niebla de guerra como 002 y la resolubilidad como 003, cuando la
  resolubilidad quedó como 002 y esta capacidad como 003. La especificación se corrige en una
  confirmación separada de los cambios de código, según §2.6 del enunciado {—}
- [ ] T048 Registrar en `PROMPTS_LLM.md` las invocaciones de spec-kit y los prompts de LLM usados en
  esta capacidad, según P1 §10.3 y §2.6 del enunciado {—}
- [ ] T049 Ejecutar la validación completa guiada en [quickstart.md](quickstart.md): pruebas de la
  capacidad, regresión de 001 y 002, comandos en partida y salida de `--bench` {FR-053, FR-055}

## Dependencias

- T001 a T003 no dependen de nada y habilitan el resto.
- T005 depende de T004; T007 de T006; ambos de T005.
- T010 a T012 dependen de T005, T007 y T008.
- T014 depende de T013 y de T010 a T012.
- T018 y T019 dependen de T017 y de T005.
- T020 depende de T018, T019 y T003.
- T023 a T026 dependen de T021 y de T018.
- T029 a T033 dependen de T005 y de T023.
- T038 y T039 dependen de T005.
- T041 a T044 dependen de toda la implementación.
- T045 depende de T041 y T043, porque la evidencia empírica sale de las mediciones.
- T049 va al final.
