# Specification Quality Checklist: Línea de tiempo y puntos de control

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-18
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Regla editorial del proyecto

- [x] `spec.md` no nombra estructuras de datos, clases ni módulos
- [x] La elección entre reconstruir hacia adelante o hacia atrás está en `research.md` R1 y en
      `plan.md`, no en `spec.md`
- [x] Cada requisito funcional tiene identificador estable, y la convención `004-FR-NNN` está
      declarada en la sección «Identificadores»

## Cobertura del Apéndice B

Los seis casos de «Línea de tiempo» del Apéndice B de P2 aparecen como escenario de aceptación:

- [x] `historia <t>` con t mayor que el reloj actual se rechaza → US2, escenario 1
- [x] `historia` después de usar un pergamino no muestra las acciones revertidas → US3, escenario 1
- [x] Varios eventos en el mismo instante t: `historia <t>` muestra el estado después de todos ellos
      → US1, escenario 4
- [x] `historia` no consume tiempo virtual, no se registra en `partida.log` y no modifica el
      historial de retroceso → US1, escenario 7
- [x] `--replay partida.log --hasta t` con t posterior al final muestra el estado final e indica que
      la partida terminó antes → US4, escenario 2
- [x] Se carga un archivo de partida de la primera parte: se reporta la incompatibilidad y nunca se
      carga en silencio → US6, escenario 2

## Cobertura de los requisitos del enunciado

- [x] P2 §3.6 (definición del estado en t, `historia <t>` e `historia #k`, resumen mínimo, consulta
      sin interacción, interacción con el retroceso, restricción de memoria, reconstrucción hacia
      adelante o hacia atrás, persistencia) → FR-001 a FR-029
- [x] P2 §5.5 (máximo K acciones por consulta, crecimiento de memoria, ubicar el punto de control,
      recorte sin recorrer la historia, mediciones con tres valores de K, reconstrucción
      documentada) → FR-022, FR-024, FR-026, FR-015, FR-032, y `research.md` R1
- [x] P2 §6.1 (consulta `historia` bajo 50 ms con 5 000 acciones) → FR-030, SC-003
- [x] P2 §6.1 (el ciclo de eventos sigue bajo 20 ms) → FR-031, SC-006
- [x] P2 §6.2 (restricciones de implementación) → FR-027, SC-010
- [x] P2 §6.3 (`--bench` mide memoria y tiempo para tres valores de K y la alternativa sin puntos de
      control) → FR-032, FR-033

## Preguntas resueltas en `/speckit-clarify`

- [x] Qué significa el estado en t cuando varios eventos caen en t
- [x] Si `historia #k` es antes o después de la acción k
- [x] Qué pasa con un instante anterior al inicio o un `#k` inexistente
- [x] Si los puntos de control se guardan en el archivo de partida
- [x] Si la primera consulta de una partida cargada es más lenta
- [x] Si una consulta puede descargar contenido o gastar presupuesto de red

## Tensión declarada con la constitución

- [x] El Principio VI («estado reversible sin copias completas») y FR-020 («se permiten copias
      completas, no más de una cada K acciones») se tocan. Queda anotado en `plan.md` →
      «Re-evaluación posterior al diseño»: el enunciado autoriza las copias y acota su frecuencia, y
      el principio existe para prohibir una copia por acción, que es precisamente la alternativa que
      `--bench` mide para descartarla.
