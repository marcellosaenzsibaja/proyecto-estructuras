# Specification Quality Checklist: Verificación de resolubilidad de una cripta

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-17
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

## Notes

- La especificación describe estrictamente reglas del juego, historias de usuario, escenarios de aceptación y requisitos funcionales y de rendimiento numerados, sin nombrar estructuras de datos, clases ni módulos (conforme a la Constitución y las instrucciones del usuario).
- Se cubren como escenarios de aceptación los 4 casos del Apéndice B «Resolubilidad»:
  1. `llave_salida` detrás de la única puerta que ella misma abre: irresoluble y se señala el ciclo concreto (US3-1, FR-015).
  2. Llave en el campo `suelta` de un enemigo errante: ubicada en la sala inicial del enemigo (US2-3, FR-006).
  3. Múltiples órdenes válidos de obtención de llaves: dos ejecuciones producen el mismo orden (US2-2, FR-009).
  4. Cripta no resoluble sin `--forzar`: la partida no inicia y se muestra el reporte (US1-2, FR-018).
- Se integran los comandos y opciones CLI requeridos (`--verificar <cripta>`, `--forzar`, `--bench`, `--offline`).
- El presupuesto de red y persistencia por versión de cripta queda especificado en FR-021 a FR-024 y SC-007.
- La restricción de rendimiento lineal O(|V| + |E| + |llaves|) en < 200 ms y la no repetición de recorridos quedan acotadas en FR-026 a FR-030 y SC-003 a SC-004.
- En la sesión de clarificación `/speckit-clarify` (2026-11-17) se resolvieron 5 decisiones clave de dominio e interfaz:
  - Códigos de salida para `--verificar` (0: resoluble, 1: no resoluble, 2: error).
  - Desempate canónico de obtención de llaves por orden alfanumérico creciente de `id`.
  - Ubicación directa de llaves desde el campo `sala` de `GET /criptas/<id>/llaves` (sin consultas HTTP de contenido adicionales).
  - Formato canónico cerrado de ciclos `[L1 -> L2 -> L1]` iniciando en la llave lexicográficamente menor.
  - Transición inmediata no bloqueante entre el reporte y la vista interactiva al iniciar partida.
