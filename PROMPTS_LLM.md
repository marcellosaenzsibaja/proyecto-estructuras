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

