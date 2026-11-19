# Bitácora de uso de LLM

## Entrada 1
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Este es el enunciado de un proyecto que necesito desarrollar. Necesito que lo analices completo y comprendas en qué consiste y cuál debe ser el resultado final. Te adjunto el avance que se tiene hasta el momento construido, necesito que lo revises y según lo que se pide y me digas si está correcto, además que me digas con qué se debe continuar y lo construyamos. Recuerda siempre regirte bajo las instrucciones del proyecto, sin inventar nada ni asumir decisiones que no se respalden en lo solicitado."
- Uso de la respuesta: revisar el avance contra el enunciado y definir las etapas de construcción.

## Entrada 2
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "No nos han dado el paquete de respuestas para --offline. Y sí, arranquemos, necesito corregir lo malo y avanzar con lo que se necesita para cumplir con la entrega como se debe"
- Uso de la respuesta: construir la etapa 1 (cliente de red corregido, interfaz de fuente de datos, README, .gitignore y pruebas).

## Entrada 3
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "ya esta versión se puede correr? Y si es así dime dónde y cómo"
- Uso de la respuesta: obtener las instrucciones para ejecutar la etapa 1.

## Entrada 4
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "como me ubico sobre la carpeta en la terminal"
- Uso de la respuesta: ubicar la terminal en la carpeta del proyecto.

## Entrada 5
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: [captura de pantalla de PowerShell con el error "Could not open requirements file"]
- Uso de la respuesta: corregir la carpeta desde la que se ejecutaban los comandos.

## Entrada 6
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Al correr salió esto" [dos capturas de pantalla de la ejecución de main.py]
- Uso de la respuesta: validar el cliente de red contra el servicio y señalar los defectos de reglas del avance anterior.

## Entrada 7
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Sí"
- Uso de la respuesta: construir la etapa 2 (tabla hash, agenda de eventos, lista doble, inventario y buffer circular, con pruebas).

## Entrada 8
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Sí"
- Uso de la respuesta: confirmar la etapa 2 y comenzar la etapa 3 (modelo del juego sin vista).

## Entrada 9
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Continuar"
- Uso de la respuesta: terminar la etapa 3 (pruebas, cargador, controlador, vista y herramienta de muestra de datos).

## Entrada 10
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "bueno ya tienes las instrucciones del proyecto y asi es como lo llevo, puedes terminarlo por favor y no hagas comentarios"
- Uso de la respuesta: completar de forma autónoma, contra el enunciado completo, todo lo que faltaba del proyecto: modo `--offline` y `herramientas/exportar_offline.py` (§3.4); ordenamiento propio con selección automática entre inserción y mezcla (§4.9); guardado binario con acceso aleatorio por sala, equivalente JSON de comparación y tabla de puntajes (§4.10); bitácora de sólo adición y `--replay` (§4.11); sistema de retroceso reversible por deltas e implementación completa del pergamino de retroceso, incluidas sus exclusiones de alcance (§2.11/§4.6); caché de fichas de catálogo con política LRU y protección de fichas en uso, y su persistencia en disco entre ejecuciones (§4.4); banco de pruebas de desempeño `--bench` (§5.3); reescritura del controlador y de `main.py` para integrar todos los comandos y opciones nuevos; ampliación de la batería de pruebas (`unittest`) para cada módulo nuevo; este documento de decisiones de diseño (`DECISIONES.md`, §8) y la actualización de `README.md` y de esta bitácora. Se verificaron además, en una relectura completa del enunciado, tres vacíos de cumplimiento que se corrigieron en el mismo trabajo: la versión del catálogo faltaba en el encabezado de la bitácora (§4.11), la caché de fichas no se conectaba a la persistencia en disco ya construida (§4.4), y el reporte final no incluía los aciertos/fallos de caché (§5.1).

# Segunda parte

## Entrada 11
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic)
- Prompt: "speck kit con claude ,ya esta colocado ahora bien" y, adjuntando el enunciado "Cripta - Parte II.pdf", "necesito realizar esto"
- Uso de la respuesta: orientación sobre el flujo de spec-kit y revisión del estado del repositorio.

## Entrada 12
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic)
- Prompt: "hagamoslo paso a paso ok ? tambien por cada etapa commit en una branch separada esta bien" y "hazlo en local yo luego lo subo a git"
- Uso de la respuesta: paso 0 en la rama `000-preparacion-speckit`: extraer el código de la primera parte a la raíz y ejecutar `specify init --here --integration claude --script ps`.

## Entrada 13
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0
- Prompt: `/speckit-constitution Proyecto CRIPTA en Python 3.11+. Principios: (1) estructuras de datos de los problemas evaluados implementadas a mano; prohibidos dict y set como índice o caché, heapq, bisect, collections, networkx y bibliotecas de grafos; (2) determinismo: misma cripta, semilla y acciones producen la misma partida; (3) separación MVC, --replay y --bench no instancian la vista; (4) ningún dato de una cripta concreta en el código; (5) respetar presupuesto_solicitudes; (6) toda afirmación de rendimiento respaldada con --bench; (7) una especificación precede a su implementación y se confirma antes que el código.`
- Uso de la respuesta: primer borrador de `.specify/memory/constitution.md`. Se descartó (ver entrada 15) porque solo consideraba el enunciado de la segunda parte.

## Entrada 14
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic)
- Prompt: "ok antes de continuar tienes acceso al pdf del primer proyecto ya que hay cosas del 2 que se ven en el primer enunciado" y, adjuntando "Primer Proyecto - Estructuras de Datos II 2026.pdf", "es este"
- Uso de la respuesta: identificar las reglas de la primera parte que hereda la segunda y lo que le faltaba al borrador de la constitución.

## Entrada 15
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-constitution`)
- Prompt: "ahora que tienes los 2 documentos elimina el commit anterior y crea de nuevo la constitucion tomando en cuenta los 2 documentos ,no a;adas lo siguiente a la constitucion :si hay una estructura que se pueda utilizar que recomiendes de estas ,arboles binarios ,grafos,hash preguntame antes"
- Uso de la respuesta: rehacer `.specify/memory/constitution.md` v1.0.0 con base en ambos enunciados (P1 y P2), en la rama `paso-1-constitucion`.

## Entrada 16
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-specify`)
- Prompt: "Sí, paso 2". La descripción de la capacidad para `/speckit-specify` la redactó el asistente a partir de P2 §3.1, §3.2, §5.1, §5.2, §6.1, §6.3 y el Apéndice B, y quedó copiada textualmente en el campo **Input** de `specs/001-terreno-cazador/spec.md`.
- Uso de la respuesta: generar `specs/001-terreno-cazador/spec.md` y su checklist de calidad en la rama `001-terreno-cazador`; el grupo revisa la especificación antes de `/speckit-clarify`.

## Entrada 17
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic)
- Prompt: "En FR-021 ten presente la restriccion de la constitucion y ademas la prohibicion de utilizar dict y solamente seria eso"
- Uso de la respuesta: ajustar FR-021 de `specs/001-terreno-cazador/spec.md` para que la información reutilizada en los cálculos del cazador cumpla el Principio I (sin `dict` ni `set`).

## Entrada 18
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic)
- Prompt: "A fr-021 a;adele al final ; estructuras equivalentes de biblioteca como índice, caché o registro para terminar de aclarar el tema de estructuras"
- Uso de la respuesta: completar FR-021 de `specs/001-terreno-cazador/spec.md` con la prohibición de estructuras equivalentes de biblioteca.

## Entrada 19
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-clarify`)
- Prompt: "Sí, clarify"; respuestas a las preguntas 1 a 4: "A (recomendada)", "A (recomendada)", "A (recomendada)", "b"
- Uso de la respuesta: resolver 4 ambigüedades de `specs/001-terreno-cazador/spec.md` (activación del cazador, datos inválidos, varias salidas hacia la misma vecina y verificación por conteo del costo acotado por el rango).

## Entrada 20
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-plan`)
- Prompt: "Sí, plan"; respuestas a las preguntas de estructuras: "A: Montículo binario (Recommended)" y "A: Arreglos por índice (Recommended)"; revisión: "ok las revisiones estan bien"
- Uso de la respuesta: generar el plan de `specs/001-terreno-cazador/` (plan.md, research.md, data-model.md, quickstart.md y contrato) e incorporar a FR-002 la regla del costo declarado por un solo lado.

## Entrada 21
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-tasks`)
- Prompt: "Sí, ambas"
- Uso de la respuesta: generar `specs/001-terreno-cazador/tasks.md` con las tareas trazadas a los requisitos.

## Entrada 22
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic)
- Prompt: "okey en la fase 2 quiero lo detalles mucho mas enfasis en primero la prohibicion de las estructuras de conveniencia y el mecanismo exacto de elimnacion perezosa de entradas obsoletas al monticulo Fase 4 detallar mas para hacerlo 100%determinista concida correctamente con la referencia teorica (esta tambien para la fase 5) fase 5 que demuestre que ante cambios de puertas alejadas a la region examinada el sistema no recalcula nada en t003 detalla mucho mas la generacion correca de criptas solo es"; "solo eso era lo del final"; "define mejor g4 y g1 su estructura ,evita set en los dfs mejor utiliza listas indexadas en t059"; "ademas revisa que estos no rompan la constitucion"; "La opcion A,ademas ;ademas a;ade la trazabilidad de t004 t066 y t068y haz la verificacion superficial de plan"
- Uso de la respuesta: detallar y corregir `tasks.md` y el plan de 001 (prohibición de estructuras de conveniencia, eliminación perezosa, determinismo, referencia teórica, no recálculo, generación de criptas como texto JSON con listas indexadas, trazabilidad y verificación contra la constitución).

## Entrada 23
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-analyze`)
- Prompt: "Sí, ambas"; "Sí, propónlas"; "si esta bien"
- Uso de la respuesta: analizar la coherencia de spec, plan y tareas de 001 (1 crítico, 2 altos, 4 medios, 4 bajos) y aplicar las correcciones aprobadas.

## Entrada 24
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-implement`)
- Prompt: "Sí, ambas"; "Reviso primero"; "ya lo revise , puedes seguir"
- Uso de la respuesta: implementar las fases 1 a 3 de `specs/001-terreno-cazador/tasks.md` (generador de criptas, base de estructuras, costo y rango, y US1 del terreno en el movimiento).

## Entrada 25
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-implement`)
- Prompt: "Sí, ambas"
- Uso de la respuesta: implementar la fase 4 de 001 (referencia teórica, búsqueda con pausa y extensión, modo individual e integración del cazador en la partida).

## Entrada 26
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-implement`)
- Prompt: "Sí, fase 5"
- Uso de la respuesta: implementar la fase 5 de 001 (punto único de cambio de puertas, reutilización de rutas con no recálculo demostrado y guardado que continúa con las mismas decisiones).

## Entrada 27
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-implement`)
- Prompt: "Sí, ambas"
- Uso de la respuesta: implementar la fase 6 de 001 (costo de cada salida y marca de cazador en la vista).

## Entrada 28
- Fecha aproximada: 14 de noviembre de 2026
- Herramienta: Claude Code (Anthropic) con spec-kit 1.4.1.dev0 (`/speckit-implement`)
- Prompt: "Sí, fase 7"
- Uso de la respuesta: implementar la fase 7 de 001 (escenarios de `--bench` del cazador y medición robusta del ciclo de eventos).

## Entrada 29
- Fecha aproximada: 17 de noviembre de 2026
- Herramienta: Antigravity con spec-kit (`/speckit-specify`)
- Prompt: "Verificación de resolubilidad de una cripta (P2 §3.5, §4.2, §5.4, §6.1, §6.3 y Apéndice B «Resolubilidad»). Antes de iniciar una partida, el programa determina si la cripta puede ganarse, usando el esqueleto completo y la ubicación de las llaves que entrega el servicio en GET /criptas/<id>/llaves. Cada llave indica su sala y, si la suelta un enemigo, el id de esa instancia; en ese caso la llave se considera obtenible en la sala donde el enemigo inicia. Supuestos de la verificación: el jugador atraviesa cualquier salida abierta y cualquier salida cerrada cuya llave ya obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; las trampas y los cierres automáticos no bloquean porque una puerta puede volver a abrirse con la misma llave. Una cripta es resoluble si, partiendo de la sala inicial y bajo esos supuestos, el jugador puede obtener llave_salida y llegar a sala_salida a través de una puerta que la requiere. Si es resoluble, el resultado es un orden de obtención de llaves en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. Si hay varios órdenes válidos, cualquiera sirve, pero dos ejecuciones sobre la misma cripta producen el mismo orden. Si no es resoluble, el reporte indica: las llaves que no pueden obtenerse; las puertas de la frontera bloqueada (puertas cerradas adyacentes a la región alcanzable) con la llave que requiere cada una; y en qué sala está cada una de esas llaves. Si una llave está detrás de puertas que solo ella abre, directamente o mediante una cadena de llaves, el reporte señala el ciclo concreto, y esa detección es determinista. Interfaz: el reporte se muestra al iniciar una partida. Si la cripta no es resoluble y no se usa la bandera --forzar, la partida no inicia y se muestra el reporte. La opción --verificar <cripta> ejecuta únicamente la verificación sin instanciar la vista. La consulta de llaves cuenta dentro de presupuesto_solicitudes y su respuesta es válida mientras coincida la versión de la cripta, por lo que puede persistirse con el resto de los datos de la cripta. Ningún dato de una cripta concreta puede estar escrito en el código; el servicio publicará criptas no resolubles y en la revisión se usará una cripta nueva. Rendimiento: la verificación toma menos de 200 ms en la cripta publicada más grande, sin red ni renderizado. El costo total debe crecer aproximadamente de forma lineal con salas, salidas y llaves; no se acepta repetir el recorrido completo cada vez que se obtiene una llave. La información del reporte (frontera bloqueada y dependencias entre llaves) debe salir del mismo recorrido, sin recorridos adicionales por llave. La medición con criptas sintéticas deterministas por semilla, incluidas cadenas largas de llaves encadenadas, debe poder reproducirse con --bench. Casos que deben ser escenarios de aceptación (Apéndice B): (1) llave_salida detrás de la única puerta que ella misma abre: no resoluble y el reporte señala el ciclo; (2) una llave está en el campo suelta de un enemigo errante: la verificación la ubica en la sala inicial del enemigo; (3) existen varios órdenes válidos de obtención de llaves: dos ejecuciones producen el mismo orden; (4) cripta no resoluble sin --forzar: la partida no inicia y se muestra el reporte. Este documento describe solo reglas del juego, historias de usuario, escenarios de aceptación y requisitos funcionales y de rendimiento numerados. No nombres estructuras de datos, clases ni módulos: eso corresponde al plan."
- Uso de la respuesta: generar la especificación `specs/002-verificacion-resolubilidad/spec.md` y la lista de control de requisitos `specs/002-verificacion-resolubilidad/checklists/requirements.md`.

## Entrada 30
- Fecha aproximada: 17 de noviembre de 2026
- Herramienta: Antigravity con spec-kit (`/speckit-clarify`)
- Prompt: "/speckit-clarify"; respuestas a las preguntas de clarificación: "A" (código de salida 0: resoluble, 1: no resoluble, 2: error en `--verificar`), "A" (desempate alfanumérico por `id` de llave), "A" (sala de llaves provista directamente en campo `sala` de `GET /criptas/<id>/llaves`), "A" (formato canónico cerrado de ciclos `[L1 -> L2 -> L1]`), "A" (transición continua sin pausa al iniciar partida normal).
- Uso de la respuesta: clarificar 5 decisiones críticas en `specs/002-verificacion-resolubilidad/spec.md` y actualizar la lista de control de requisitos.

## Entrada 31
- Fecha aproximada: 17 de noviembre de 2026
- Herramienta: Antigravity con spec-kit (`/speckit-plan`)
- Prompt: "Planificar la verificación de resolubilidad (specs/002-verificacion-resolubilidad/spec.md) respetando la constitución del proyecto. Restricciones: todas las estructuras que resuelven este problema se implementan a mano en el proyecto. Está prohibido dict y set como índice, caché o registro de visitados, y están prohibidos heapq, bisect, collections (deque, OrderedDict, defaultdict, Counter), networkx y cualquier biblioteca de grafos o búsqueda. Se pueden reutilizar las estructuras propias de la primera parte (src/estructuras_datos) solo si son adecuadas, y se debe justificar cada reutilización. No se introducen dependencias nuevas. El plan debe incluir: las estructuras elegidas para el recorrido, para registrar qué puertas esperan cada llave y para las dependencias entre llaves; al menos dos alternativas consideradas por decisión, con su complejidad esperada; el diseño de un recorrido único que produzca a la vez el orden de llaves, la frontera bloqueada y las dependencias, de modo que el costo crezca de forma aproximadamente lineal con salas, salidas y llaves; la detección determinista del ciclo concreto; los módulos afectados respetando la separación modelo, vista y controlador; el tratamiento del presupuesto de solicitudes y de la persistencia validada por versión para la ubicación de llaves; y las mediciones planificadas en --bench, que deben incluir la alternativa ingenua de repetir el recorrido por llave con criptas sintéticas deterministas por semilla de muchas llaves encadenadas, y la verificación del límite de 200 ms. El plan no introduce reglas nuevas que no estén en spec.md. Ningún dato de una cripta concreta se escribe en el código."
- Uso de la respuesta: generar los artefactos del plan de implementación en `specs/002-verificacion-resolubilidad/` (`plan.md`, `research.md`, `data-model.md`, `contracts/interfaz-y-reporte.md` y `quickstart.md`).

## Entrada 32
- Fecha aproximada: 17 de noviembre de 2026
- Herramienta: Antigravity
- Prompt: "Revisa y corrige specs/002-verificacion-resolubilidad/plan.md, research.md y data-model.md con estos tres ajustes, sin cambiar spec.md ni introducir reglas nuevas: 1. Define explícitamente cómo se escoge, entre varias llaves disponibles en una misma etapa, la de menor id lexicográfico (FR-010), con la estructura propia elegida, al menos una alternativa considerada, su complejidad y cómo se mantiene el costo total aproximadamente lineal. Indica si se reutiliza src/estructuras_datos/monticulo.py de la primera parte y por qué. 2. La detección de ciclos con búsqueda en profundidad debe ser iterativa, con una pila propia, para no depender del límite de recursión del intérprete con cadenas largas de llaves. Ajusta la complejidad y las mediciones planificadas. 3. Para el HTTP 429 reutiliza el manejo existente de ApiClient._get (espera el tiempo indicado por el servidor en reintentar_en); elimina la mención de retroceso exponencial. Mantén la constitución: sin dict, set, heapq, bisect ni collections."
- Uso de la respuesta: actualizar `plan.md`, `research.md`, `data-model.md`, `contracts/interfaz-y-reporte.md` y `quickstart.md` incorporando la selección con `MonticuloMin` de disponibles, DFS iterativo con pila propia en heap, y reutilización de `ApiClient._get` para 429.

## Entrada 33
- Fecha aproximada: 17 de noviembre de 2026
- Herramienta: Antigravity con spec-kit (`/speckit-tasks`)
- Prompt: "Descomponer el plan de la verificación de resolubilidad (specs/002-verificacion-resolubilidad) en tareas pequeñas y verificables, ordenadas por dependencias. Cada tarea debe referenciar los requisitos FR-NNN que atiende; no deben existir tareas sin requisito asociado. Cada escenario de aceptación debe tener al menos una prueba automatizada que cite el identificador del requisito. Los cuatro casos del Apéndice B de Resolubilidad deben quedar cubiertos por pruebas. Incluye las tareas de: modelo de resolubilidad, desempate por id, detección de ciclos iterativa, obtención y persistencia de la ubicación de llaves, las opciones --verificar y --forzar, el reporte al iniciar partida, los escenarios de --bench (1 000 salas y cadenas de llaves encadenadas frente a la alternativa ingenua) y la prueba que verifique la ausencia de dict, set, heapq, bisect y collections en los módulos nuevos. Las pruebas de cada historia se escriben antes de su implementación."
- Uso de la respuesta: generar `specs/002-verificacion-resolubilidad/tasks.md` con 32 tareas estructuradas en 8 fases, trazadas a requisitos funcionales y cubriendo los 4 casos del Apéndice B.

## Entrada 34
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai), por agotarse la cuota de Antigravity
- Prompt: resumen; el texto íntegro está en el historial de la conversación. Se pidió ejecutar el análisis de consistencia de `/speckit-analyze` sobre `spec.md`, `plan.md` y `tasks.md` de la capacidad 002.
- Uso de la respuesta: revisión de consistencia sin cambios en los artefactos; resultado: los 31 requisitos con tarea, sin estructuras prohibidas en el plan y tres observaciones menores (T012 frente a FR-029, código de salida 1 al abortar, vigilancia de `tests/`).

## Entrada 35
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai)
- Prompt: resumen; el texto íntegro está en el historial de la conversación. Se pidió implementar las tareas T001 a T031 de `specs/002-verificacion-resolubilidad/tasks.md` (verificación de resolubilidad, llaves, `--verificar`, `--forzar`, bench) con pruebas y documentación.
- Uso de la respuesta: código de `src/modelos/resolubilidad.py`, `src/estructuras_datos/busqueda_binaria.py`, `src/servicios/verificador_servicio.py`, `src/servicios/banco_resolubilidad.py`, cambios en adaptadores, `main.py`, generador y pruebas; actualización de `README.md`, `DECISIONES.md` y `tasks.md`.


## Entrada 36
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai), sesión de trabajo sobre el repositorio
- Prompt: "hola este es nuestro proyecto y eso es lo que llevamos, que falta?", adjuntando el repositorio completo y el enunciado de la segunda parte (`Cripta - Parte II.pdf`).
- Uso de la respuesta: diagnóstico del estado del proyecto frente al enunciado. Detectó que la capacidad 002 estaba implementada en la carpeta paralela `implementacion-002/` y no integrada en la raíz (el `main.py` de la raíz no tenía `--verificar` ni `--forzar` y la batería de pruebas se caía al recolectar), que faltaban por completo las capacidades de niebla de guerra y línea de tiempo, y que los identificadores `FR-NNN` se repiten entre especificaciones.

## Entrada 37
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai)
- Prompt: "mejor hazlo en la carpeta" (integrar la capacidad 002 en la raíz del repositorio).
- Uso de la respuesta: integración del contenido de `implementacion-002/` en la raíz, eliminación de esa carpeta y validación. Se tomaron como definitivas las versiones del overlay de `DECISIONES.md`, `PROMPTS_LLM.md`, `README.md` y `specs/002-verificacion-resolubilidad/tasks.md`. Resultado: de 256 pruebas en la raíz (con las de la 002 sin poder ejecutarse) a 321 pruebas pasando.

## Entrada 38
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai) con spec-kit (`/speckit-specify` y `/speckit-clarify` de la capacidad 003)
- Prompt: "Niebla de guerra y viaje automático (P2 §3.3, §3.4, §5.3, §6.1, §6.3 y Apéndice B «Niebla de guerra e ir a»). El jugador deja de ver el mapa completo: cada sala está explorada, avistada o desconocida; de una explorada conoce nombre, salidas, costo de cada salida y el estado de sus puertas según la última observación; de una avistada solo que existe una sala detrás de esa salida. El jugador observa una puerta cuando está en cualquiera de las dos salas que conecta, y el mapa recuerda el estado de esa última observación aunque después cambie. La antorcha adquiere efecto: al entrar a una sala con ella encendida quedan exploradas todas sus vecinas por cualquier salida, revelando nombre y salidas pero no contenido, y sin activar sus enemigos ni sus trampas. Todo lo que la vista muestra y lo que usa «ir a» debe derivarse exclusivamente del conocimiento del jugador. El conocimiento es estado del juego: se guarda, se revierte con el pergamino y forma parte de la línea de tiempo. `ir a <sala>` lleva al jugador a una sala explorada por movimientos ordinarios, con la ruta calculada sobre salas exploradas y salidas recordadas abiertas, minimizando la suma de costos y desempatando por la vecina de menor id; cada paso es una acción completa, la ruta se recalcula antes de cada paso, y el viaje se detiene al llegar, ante enemigos activos o dormidos, al recibir daño o si deja de existir ruta conocida; no abre puertas; en partida.log cada paso se graba como movimiento individual y la orden como comentario; el pergamino revierte solo el último paso. Consultar el estado de una sala y el estado recordado de una puerta deben costar tiempo constante; explorar salas nuevas debe costar proporcionalmente a las reveladas; registrar e invertir cambios debe ser barato; un paso de «ir a» debe tomar menos de 5 ms con el mapa conocido completo. No nombres estructuras de datos, clases ni módulos: eso corresponde al plan."
- Uso de la respuesta: `specs/003-niebla-guerra/spec.md` con 56 requisitos funcionales numerados, 7 historias de usuario, 45 escenarios de aceptación que cubren los 6 casos del Apéndice B, 11 criterios de éxito medibles, 6 preguntas de clarificación resueltas y una sección que declara la convención de identificadores `003-FR-NNN`.

## Entrada 39
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai) con spec-kit (`/speckit-plan` de la capacidad 003)
- Prompt: "Planificar la implementación de la niebla de guerra y el viaje automático a partir de specs/003-niebla-guerra/spec.md. Registra en research.md cada pregunta abierta con sus alternativas, la decisión y lo que la respalda. En particular, el enunciado (P2 §5.3) pide justificar explícitamente si la ruta de «ir a» comparte implementación con la búsqueda del cazador o si conviene separarlas: resuélvelo con argumentos concretos y di qué se va a medir para respaldarlo. Define también sobre qué se indexa el estado de conocimiento para que las consultas sean en tiempo constante y explorar cueste proporcional a lo revelado, dónde se guarda el estado recordado de cada puerta, cómo se recorre el mapa conocido sin recorrer la cripta, qué información mínima hay que registrar para revertir una exploración con antorcha, y cómo cambia el formato de guardado. Respeta el Principio I de la constitución."
- Uso de la respuesta: `plan.md`, `research.md` con 10 decisiones (R1 a R10), `data-model.md` y `contracts/interfaz-y-bench.md`. La decisión central fue no compartir el recorrido de búsqueda con el cazador pero sí sus estructuras propias, por el límite de 20 ms del cazador y porque un parámetro que conmute entre el estado real y el conocimiento hace fácil escribir por accidente los dos peores defectos de la capacidad.

## Entrada 40
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai) con spec-kit (`/speckit-tasks` y `/speckit-analyze` de las capacidades 003 y 004)
- Prompt: "Descomponer los planes de las capacidades 003 y 004 en tareas pequeñas y verificables, ordenadas por dependencias, donde cada tarea referencie los requisitos que atiende y no exista ninguna tarea sin requisito asociado; las pruebas de cada historia se escriben antes de su implementación. Después ejecuta el análisis de consistencia entre especificación, plan y tareas de las cuatro capacidades: comprueba que cada requisito funcional tenga al menos una tarea que lo cite, que ninguna tarea quede sin requisito, y que el plan no introduzca dependencias prohibidas."
- Uso de la respuesta: `specs/003-niebla-guerra/tasks.md` con 49 tareas en 9 fases y `specs/004-linea-de-tiempo/tasks.md` con 47 tareas en 9 fases. El análisis de consistencia (hecho con un script que expande los rangos del tipo «FR-008 a FR-012» y une las líneas envueltas) encontró dos huecos reales: `003-FR-020` y `004-FR-024` no estaban citados por ninguna tarea. Se corrigieron ampliando las tareas T016 de la 003 y T037 de la 004.

## Entrada 41
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai) con spec-kit (`/speckit-specify`, `/speckit-clarify` y `/speckit-plan` de la capacidad 004)
- Prompt: "Línea de tiempo (P2 §3.6, §5.5, §6.1, §6.3 y Apéndice B «Línea de tiempo»). El pergamino sigue limitado a 5 acciones; la línea de tiempo es independiente y permite consultar, sin modificar la partida, el estado en cualquier instante desde el inicio. El estado en el instante t es el de después de ejecutar todos los eventos con tiempo menor o igual que t, y si a t le corresponde una decisión del jugador es el estado justo antes de tomarla. En partida, `historia <t>` o `historia #k` muestra reloj, sala, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido en ese momento; la consulta no consume tiempo virtual, no se registra como acción y no altera el historial de retroceso. Sin interacción, `--replay partida.log --hasta <t>` imprime el mismo resumen sin instanciar la vista. Las acciones revertidas con un pergamino dejan de existir en la línea; consultar un instante posterior al reloj se rechaza. Se permiten puntos de control, pero no más de uno cada K acciones del jugador, con K configurable por `--checkpoint-cada` y un valor por defecto que el grupo justifica con mediciones; una consulta no puede requerir aplicar o deshacer más de K acciones; fuera de los puntos de control solo se almacena lo necesario para reconstruir los cambios; la memoria total no puede crecer como «acciones por tamaño del estado». Se puede reconstruir hacia adelante re-simulando o hacia atrás invirtiendo cambios, y si se re-simula el punto de control debe incluir el estado del generador random.Random: decide cuál y justifícalo. Guardar y cargar conserva la línea completa y un archivo de la primera parte debe detectarse como incompatible. La consulta debe tomar menos de 50 ms en una partida de al menos 5 000 acciones."
- Uso de la respuesta: `specs/004-linea-de-tiempo/spec.md` con 34 requisitos, 6 historias de usuario, los 6 casos del Apéndice B como escenarios y 11 criterios de éxito; `plan.md`, `research.md` con 10 decisiones y `data-model.md`. La decisión central fue reconstruir hacia adelante re-simulando, no por rendimiento (es comparable) sino porque las funciones de deshacer de P1 §4.6 son cierres en memoria y no datos, así que no se pueden persistir, y porque la re-simulación ocurre en una partida aparte y por tanto no toca el estado vivo.

## Entrada 42
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai) con spec-kit (`/speckit-implement` de las capacidades 003 y 004)
- Prompt: "Implementar las tareas de specs/003-niebla-guerra/tasks.md y specs/004-linea-de-tiempo/tasks.md con sus pruebas: el mapa conocido con los tres estados y la memoria de puertas, el efecto de la antorcha, el comando `mapa`, el viaje automático `ir a` con sus condiciones de parada, `ultimo_menor_o_igual` en busqueda_binaria.py, la línea de tiempo con puntos de control, el resumen de `historia`, el formato de guardado versión 3 con rechazo de los anteriores, el registro del cursor del inventario en la bitácora, los comandos `historia <t>` e `historia #k`, y las opciones `--hasta` y `--checkpoint-cada`. No pongas comentarios en el código."
- Uso de la respuesta: módulos nuevos `src/modelos/mapa_conocido.py`, `src/modelos/viaje.py`, `src/modelos/linea_tiempo.py`, `src/modelos/resumen_historia.py`, `src/servicios/banco_mapa.py` y `src/servicios/banco_linea_tiempo.py`; `ultimo_menor_o_igual` en `src/estructuras_datos/busqueda_binaria.py`; cambios en `partida.py`, `guardado.py` (versión 3 con mapa conocido, línea de tiempo, cursor, efectos activos y eventos pendientes), `bitacora.py`, `controlador_juego.py`, `vista_consola.py` y `main.py`; y 10 archivos de prueba nuevos. De 321 a 424 pruebas.
- Correcciones que la implementación obligó a hacer, en el orden que pide §2.6 (primero la especificación, después el código, en confirmaciones separadas):
  1. La R2 del `research.md` de la 003 decidía guardar la memoria de puertas por lado de la conexión. La prueba de `003-FR-017` demostró que está mal: el jugador observa la puerta A–B desde A y, si una ruta pasa después por B hacia A, ese lado seguiría «sin observar». El enunciado habla del estado de cada *puerta*, no de cada lado. Se corrigió la R2 y luego `observar_puerta` para escribir las dos entradas.
  2. `tests/test_restricciones.py` detectó una infracción real del Principio I en código nuevo: `mapa_conocido.py` usaba `.sort()` de la biblioteca. Se reemplazó por `ordenar()` del grupo.

## Entrada 43
- Fecha aproximada: 18 de noviembre de 2026
- Herramienta: Claude (claude.ai)
- Prompt: "Medir y fijar el K por defecto de los puntos de control con al menos tres valores, comparando memoria y tiempo de consulta contra la alternativa de una copia completa por acción y contra no usar puntos de control; volver a medir el ciclo de eventos con decenas de cazadores y la línea de tiempo activa; y medir el paso de «ir a» contra el límite de 5 ms con el mapa conocido completo. Documenta las decisiones en DECISIONES.md con la estructura de P1 §8."
- Uso de la respuesta: `banco_linea_tiempo.py` y `banco_mapa.py`, con `--bench` pasando de 15 a 22 secciones; secciones §P2 5.3 y §P2 5.5 de `DECISIONES.md`. Hallazgos:
  1. **K = 100.** El tiempo de consulta es casi plano entre K = 1 y K = 200 (0.9 a 5 ms, nunca más del 10 % del límite de 50 ms) porque lo que domina es restaurar un snapshot; lo que cambia dos órdenes de magnitud es la memoria (630 MB con copia por acción frente a 6.5 MB con K = 100 en una cripta de 400 salas). El criterio fue el K más grande que deje margen amplio de tiempo, no el más rápido. El plan anotaba 25 como provisional.
  2. **El `ms_max_bruto` del bench del cazador no mide el programa.** La variante que hace más trabajo (con línea de tiempo activa) dio 11.9 ms de máximo bruto y la que hace menos dio 32.4 ms. El número que vale es `ms_max`, el máximo de los mínimos entre repeticiones: 2.74 con línea y 2.99 sin ella, contra el límite de 20.
  3. **El paso de «ir a» es el margen más ajustado del proyecto.** La primera versión superaba el límite con la batería completa (6.43 ms), así que se optimizó el bucle interno sin cambiar el algoritmo (`examinadas_max` sigue siendo 1 396 y la prueba contra la referencia teórica sigue pasando): bajó a 1.83 ms de media y 3.02 ms de máximo con 1 600 salas. A la escala de referencia (400 salas) usa el 35 % del presupuesto; a 1 600 salas en el equipo del grupo no cumple, y la fila se reporta igual en `--bench` marcada como estrés fuera de la escala de referencia.
