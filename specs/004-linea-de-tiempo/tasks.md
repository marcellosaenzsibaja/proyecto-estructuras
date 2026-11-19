# Tasks: Línea de tiempo y puntos de control

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-18

Cada tarea referencia entre llaves los requisitos de [spec.md](spec.md) que atiende. `[P]` marca
tareas que pueden hacerse en paralelo con la anterior porque no tocan los mismos archivos.

## Fase 1 — Andamiaje

- [ ] T001 Ampliar `ARCHIVOS_VIGILADOS` en `tests/test_restricciones.py` con los módulos nuevos
  (`src/modelos/linea_tiempo.py`, `src/modelos/resumen_historia.py`,
  `src/servicios/banco_linea_tiempo.py`) y sus pruebas, verificando por AST la ausencia de `dict`,
  `set`, `heapq`, `bisect`, `collections` y bibliotecas de grafos {FR-027}
- [ ] T002 [P] Escribir las pruebas de `ultimo_menor_o_igual` en `tests/test_busqueda_binaria.py`:
  coincidencia exacta, valor entre dos elementos, menor que todos (devuelve -1), mayor que todos,
  lista vacía, lista de un elemento y valores repetidos {FR-026}
- [ ] T003 Implementar `ultimo_menor_o_igual` en `src/estructuras_datos/busqueda_binaria.py` en
  O(log n) sin `bisect`, sin modificar `buscar` {FR-026, FR-027}

## Fase 2 — La línea de tiempo

- [ ] T004 [P] Escribir `tests/test_linea_tiempo.py` con los escenarios de la User Story 5: a lo
  sumo un punto de control cada K acciones, a lo sumo K acciones re-aplicadas por consulta, y el
  conteo de copias mantenidas {FR-020, FR-022, SC-004, SC-005}
- [ ] T005 Implementar `EntradaLinea`, `PuntoControl` y `LineaTiempo` en
  `src/modelos/linea_tiempo.py`: listas de entradas y de puntos, lista paralela de instantes y el
  parámetro K {FR-004, FR-020, FR-023}
- [ ] T006 Implementar `punto_en_o_antes` usando `ultimo_menor_o_igual` sobre la lista de instantes
  {FR-026}
- [ ] T007 Implementar `tomar_punto`, que guarda el snapshot del estado y el estado de
  `random.Random` {FR-020, FR-025}
- [ ] T008 Implementar `recortar`, que quita entradas y puntos de control del final con costo
  proporcional a lo que quita {FR-013, FR-015, FR-016}
- [ ] T009 Implementar el conteo `reaplicadas` de la última consulta {SC-004}

## Fase 3 — Reconstrucción y resumen

- [ ] T010 Implementar `reconstruir_en(partida, t)` y `reconstruir_antes_de(partida, k)`: restaurar
  el punto de control anterior en una partida nueva con la línea en modo inerte y re-aplicar las
  entradas que faltan {FR-001, FR-002, FR-003, FR-022}
- [ ] T011 Verificar que la partida reconstruida no graba bitácora, no registra puntajes, no toma
  puntos de control y no emite ninguna solicitud al servicio {FR-007, FR-011}
- [ ] T012 [P] Implementar `ResumenHistoria` en `src/modelos/resumen_historia.py` con los campos de
  FR-006 como datos, sin imprimir, incluido el mapa conocido de la capacidad 003 {FR-006}
- [ ] T013 Implementar el campo `trunco`, que indica que la partida terminó antes del instante
  pedido {FR-018}

## Fase 4 — Enganches en la partida

- [ ] T014 Crear la `LineaTiempo` en el constructor de `Partida` con el K recibido, y tomar el punto
  de control del instante 0 en `iniciar` {FR-004, FR-020, FR-021}
- [ ] T015 Registrar la entrada de cada acción del jugador en `_cerrar_accion`, y tomar el punto de
  control cuando corresponde por K {FR-020, FR-023}
- [ ] T016 Implementar `Partida.mover_cursor`, que mueve el cursor del inventario y registra el
  movimiento en la línea de tiempo {research R5}
- [ ] T017 Recortar la línea de tiempo en `_usar_pergamino` al nuevo número de acción y al nuevo
  reloj {FR-013, FR-014, FR-016}
- [ ] T018 Implementar `Partida.historia_en(t)` y `Partida.historia_antes_de(k)`, que validan el
  argumento y devuelven el resumen o un rechazo {FR-005, FR-008, FR-009, FR-010, FR-012}
- [ ] T019 [P] Escribir `tests/test_historia_consulta.py` con los escenarios de las User Stories 1,
  2 y 3, incluidos cuatro casos del Apéndice B: instante mayor que el reloj se rechaza; después de un
  pergamino no se muestran las acciones revertidas; varios eventos en el mismo t muestran el estado
  después de todos; y la consulta no consume tiempo, no se registra y no toca el historial de
  retroceso {FR-001 a FR-016, SC-008}
- [ ] T020 Escribir la prueba de SC-002: para al menos 200 instantes de una partida sintética de
  1 000 acciones, el resumen de la consulta coincide con el de re-simular desde el inicio {SC-002}

## Fase 5 — Bitácora y reproducción

- [ ] T021 [P] Escribir `tests/test_historia_replay.py`: `--hasta` imprime el mismo resumen que
  `historia`, un `t` posterior al final muestra el estado final indicando que la partida terminó
  antes, y una bitácora con movimientos de cursor reproduce la misma partida {FR-017, FR-018,
  FR-019}
- [ ] T022 Registrar los movimientos de cursor en `src/servicios/bitacora.py` como registros que no
  son acciones del jugador {research R5}
- [ ] T023 Hacer que `reproducir` acepte un instante límite, aplique los movimientos de cursor sin
  contarlos como acciones y devuelva la partida al llegar al límite {FR-017, FR-019}
- [ ] T024 Verificar que una bitácora de las capacidades anteriores sigue leyéndose, y que una
  bitácora con cursor reproduce fielmente una partida que usa objetos no primeros del inventario
  {research R5}

## Fase 6 — Interfaz

- [ ] T025 Agregar al `ControladorJuego` el comando `historia <t>` e `historia #k`, que no consume
  tiempo, no se registra en `partida.log` y no toca el historial de retroceso {FR-005, FR-007}
- [ ] T026 Hacer que `sig` y `ant` pasen por `Partida.mover_cursor` en vez de llamar al inventario
  directamente {research R5}
- [ ] T027 [P] Implementar `mostrar_resumen_historia` en `src/vistas/vista_consola.py`, que formatea
  los campos del resumen, incluido el mapa conocido {FR-006}
- [ ] T028 Implementar el formateador del resumen de modo que `--hasta` lo use sin instanciar la
  vista {FR-017}
- [ ] T029 Agregar `--checkpoint-cada K` a `main.py`, con el K por defecto del grupo y rechazo de
  K < 1 {FR-021}
- [ ] T030 Agregar `--hasta <t>` a `main.py`, válido solo junto con `--replay`, que imprime el
  resumen y termina {FR-017, FR-018}

## Fase 7 — Persistencia

- [ ] T031 [P] Escribir `tests/test_linea_guardado.py`: guardar y cargar conserva la historia
  completa y las consultas dan los mismos resúmenes; un archivo de la primera parte y uno de las
  capacidades 001 y 002 se rechazan {FR-028, FR-029}
- [ ] T032 Agregar la sección `linea` a `tomar_snapshot` con las entradas en orden, y omitirla
  cuando el snapshot se toma como punto de control {FR-028}
- [ ] T033 Reconstruir la `LineaTiempo` en `restaurar_partida` desde esa sección, dejando los puntos
  de control para reconstruirse en la primera consulta {FR-028}
- [ ] T034 Subir `FORMATO_VERSION` de 2 a 3 en `src/servicios/guardado.py`, coordinado con la
  capacidad 003, y comprobar el rechazo de las versiones 1 y 2 {FR-029}

## Fase 8 — Mediciones y K por defecto

- [ ] T035 [P] Escribir `src/servicios/banco_linea_tiempo.py` con la sección `[linea_tiempo]`:
  memoria y tiempo de consulta para K = 1, 25 y 200 en una partida sintética de 5 000 acciones
  {FR-030, FR-032}
- [ ] T036 Agregar a ese banco la alternativa «copia por acción» y la alternativa «sin puntos de
  control» {FR-032}
- [ ] T037 Agregar al banco los conteos de acciones re-aplicadas por consulta y de copias
  mantenidas, y la medición del tamaño en memoria de la línea para comprobar que crece con los
  cambios ocurridos más un punto de control cada K y no como «acciones por tamaño del estado»
  {FR-024, SC-004, SC-005}
- [ ] T038 Agregar la sección `[linea_determinismo]`: dos ejecuciones con la misma semilla dan la
  misma historia y los mismos resúmenes {FR-034}
- [ ] T039 Conectar `banco_linea_tiempo` al `--bench` existente, sin instanciar la vista y
  manteniendo el formato de salida de las capacidades anteriores {FR-032, FR-034}
- [ ] T040 Repetir el escenario `[ciclo_eventos]` de la capacidad 001 con la línea de tiempo activa,
  reportando el máximo y no solo la media {FR-031, FR-033, SC-006}
- [ ] T041 [P] Escribir `tests/test_rendimiento_linea.py`: la consulta queda bajo 50 ms en una
  partida de 5 000 acciones con el K por defecto, las acciones re-aplicadas nunca superan K y las
  copias mantenidas no pasan de `n/K + 1` {FR-030, SC-003, SC-004, SC-005}
- [ ] T042 Ejecutar las mediciones, **fijar el K por defecto** con el valor que respalden y
  escribirlo en el código {FR-021}

## Fase 9 — Documentación y cierre

- [ ] T043 [P] Escribir la sección §P2 5.5 de `DECISIONES.md` con la estructura de P1 §8: problema,
  alternativas consideradas (hacia adelante frente a hacia atrás, R1), decisión, análisis de
  complejidad, evidencia empírica con los tres valores de K y las dos alternativas, y límites
  conocidos; enlazar a esta especificación y a este plan, e indicar si la decisión final coincide con
  la del plan original {FR-032}
- [ ] T044 [P] Actualizar `README.md`: comando `historia`, opciones `--checkpoint-cada` y `--hasta`,
  el K por defecto y su justificación, la versión 3 del formato de guardado y su efecto sobre los
  archivos existentes, el cambio de formato de `partida.log` por los registros de cursor, y las
  secciones nuevas de `--bench` {FR-021, FR-029}
- [ ] T045 Actualizar §P2 5.6 de `DECISIONES.md` con las mediciones de la agenda y del historial de
  retroceso repetidas con la línea de tiempo activa {FR-033}
- [ ] T046 Registrar en `PROMPTS_LLM.md` las invocaciones de spec-kit y los prompts de LLM usados en
  esta capacidad, según P1 §10.3 y §2.6 del enunciado {—}
- [ ] T047 Ejecutar la validación completa guiada en [quickstart.md](quickstart.md) {FR-030, FR-032}

## Dependencias

- T001 a T003 no dependen de nada; T005 y T006 dependen de T003.
- T004 antes de T005; T019 antes de T014 a T018 (las pruebas de cada historia se escriben primero).
- T010 depende de T005 a T007; T012 depende de la capacidad 003 para el campo del mapa conocido.
- T014 a T018 dependen de T005 a T010.
- T021 antes de T022 y T023; T023 depende de T010.
- T025 a T030 dependen de T018 y T012.
- T032 a T034 dependen de T005, y T034 se coordina con la tarea equivalente de la capacidad 003.
- T035 a T041 dependen de toda la implementación.
- T042 depende de T035 a T037 y bloquea a T043.
- T043 depende de T042, porque la evidencia empírica sale de las mediciones.
- T047 va al final.
