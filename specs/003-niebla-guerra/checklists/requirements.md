# Specification Quality Checklist: Niebla de guerra y viaje automático «ir a»

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
- [x] Las estructuras elegidas y sus alternativas están en `plan.md` y `research.md`, no aquí
- [x] Cada requisito funcional tiene identificador estable, y la convención de calificarlo por
      capacidad (`003-FR-NNN`) está declarada en la sección «Identificadores»

## Cobertura del Apéndice B

Los seis casos de «Niebla de guerra e ir a» del Apéndice B de P2 aparecen como escenario de
aceptación:

- [x] `ir a` hacia una sala no explorada se rechaza y no consume tiempo → US4, escenario 2
- [x] El mapa recuerda abierta una puerta cerrada: se corrige, se recalcula la ruta y si no queda
      ruta el viaje se detiene sin consumir tiempo adicional → US4, escenarios 6 y 7
- [x] `ir a` entra a una sala con enemigos dormidos: se activan según P1 §2.4 y el viaje se detiene
      → US5, escenario 2
- [x] Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni
      sus trampas → US3, escenarios 1 y 3
- [x] Un pergamino revierte una entrada con antorcha encendida: las salas exploradas por la antorcha
      vuelven a su estado anterior → US6, escenario 1
- [x] Un pergamino durante un viaje revierte solo el último paso y el viaje no continúa → US6,
      escenario 2

## Cobertura de los requisitos del enunciado

- [x] P2 §3.3 (tres estados, memoria de puertas, antorcha, separación mapa/conocimiento, comando de
      mapa) → FR-001 a FR-026
- [x] P2 §3.4 (`ir a`: ruta conocida, desempate, pasos como acciones, recálculo, paradas, no abre
      puertas, bitácora, pergamino) → FR-027 a FR-045
- [x] P2 §5.3 (consultas frecuentes, costo de explorar, reversión barata, subgrafo conocido y
      justificación de compartir o separar) → FR-050 a FR-054, y la justificación en `research.md` R4
- [x] P2 §6.1 (límite de 5 ms para un paso de `ir a`) → FR-053, SC-003
- [x] P2 §6.2 (restricciones de implementación) → FR-054, SC-009
- [x] P2 §6.3 (`--bench` mide consultas al mapa conocido y cálculo de «ir a») → FR-055, FR-056

## Preguntas resueltas en `/speckit-clarify`

- [x] Cómo se nombra la sala destino de `ir a`
- [x] Si una sala explorada por antorcha conserva contenido, enemigos y trampas
- [x] Qué puertas recuerda el mapa de una sala explorada por antorcha
- [x] Qué hace `ir a` con un destino igual a la sala actual o sin ruta conocida
- [x] Qué se ejecuta de un `ir a` al reproducir con `--replay`
- [x] Cómo se comprueba que explorar no se encarece al crecer el mapa conocido
