# Constitución de CRIPTA

Proyecto de Estructuras de Datos, II Ciclo 2026. Esta constitución gobierna las especificaciones,
planes, tareas e implementaciones de la segunda parte del proyecto. Se fundamenta en dos
enunciados: el de la primera parte (P1) y el de la segunda (P2). Todo lo que establece P1 sigue
vigente salvo que P2 lo modifique explícitamente. Ante una contradicción entre ambos, prevalece P2.

Regla editorial del proyecto: las reglas del juego están especificadas; las decisiones de
estructuras de datos no. Las especificaciones las escribe el grupo antes que el código.

## Principios fundamentales

### I. Estructuras de datos implementadas por el grupo (NO NEGOCIABLE)

- Las estructuras de datos que resuelven los problemas evaluados (P1 §4 y P2 §5) DEBEN
  implementarse a mano dentro del proyecto. Está prohibido sustituirlas por implementaciones
  equivalentes de bibliotecas (P1 §7).
- Para esos problemas está PROHIBIDO usar `dict` o `set` como índice, caché, tabla de búsqueda,
  registro de visitados o estructura propia. También están prohibidos `heapq`, `bisect`,
  `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), `networkx` y cualquier
  biblioteca de grafos o de búsqueda de rutas (P2 §6.2).
- En los ordenamientos evaluados (P1 §4.9) están PROHIBIDOS `list.sort()` y `sorted()`.
- SÍ se permite: `list` como almacenamiento contiguo de bajo nivel, `struct`, `json`, `requests`,
  bibliotecas de interfaz y los diccionarios que produce `respuesta.json()` únicamente para leer el
  JSON recibido (P1 §7).
- Toda estructura auxiliar que necesite una búsqueda (por ejemplo, para escoger el siguiente
  elemento a examinar o para registrar distancias) es de implementación propia. Se pueden
  reutilizar estructuras de la primera parte cuando sean adecuadas (P2 §5.1).
- spec-kit y el agente de programación son herramientas de proceso: no pueden introducir
  dependencias prohibidas. Un `plan.md` que las proponga es un defecto que se corrige en la fase
  de plan y que `/speckit-analyze` DEBE detectar antes de implementar (P2 §6.2).

*Justificación:* el curso evalúa la elección, la implementación y la defensa de cada estructura con
mediciones propias.

### II. Determinismo

- La misma versión de cripta, la misma semilla y la misma secuencia de acciones del jugador DEBEN
  producir la misma partida observable, incluida la misma secuencia de llamadas al generador
  aleatorio (P1 §2.6).
- Toda aleatoriedad del modelo usa una única instancia propia `random.Random(semilla)`. Está
  prohibido el generador global del módulo `random`. La semilla se guarda en el archivo de partida
  y en la bitácora de reproducción.
- Los eventos se ordenan por tiempo y, en caso de empate, por un número de secuencia creciente.
  Toda reprogramación asigna un número de secuencia nuevo. Nunca se usa la hora del sistema
  (P1 §2.3).
- Determinismo de red: la latencia real y el orden de llegada de las respuestas HTTP no pueden
  cambiar la simulación. Esperar una respuesta nunca avanza el reloj virtual, y las respuestas se
  incorporan en un orden fijado por el programa (P1 §2.4 y §4.2).
- Todo empate de reglas se resuelve con el criterio explícito que fija el enunciado (por ejemplo, la
  vecina de menor id para el cazador y para «ir a»), sin importar el algoritmo empleado (P2 §3.2).
- Ninguna decisión del juego puede depender del orden de iteración de una estructura sin orden
  definido ni de direcciones de memoria.
- Las criptas sintéticas que genera `--bench` son deterministas por semilla (P2 §6.3).

*Justificación:* `--replay`, la línea de tiempo y la evaluación comparan resultados exactos.

### III. Arquitectura Modelo–Vista–Controlador con adaptadores

- Modelo: reglas del juego, entidades y estructuras de datos. NO conoce HTTP, archivos ni la
  interfaz concreta (P1 §6).
- Vista: presenta el estado y recoge la interacción. Controlador: traduce las acciones del usuario
  en operaciones del modelo y coordina el flujo.
- Adaptadores: el acceso a red y a disco va detrás de interfaces. `--offline` sustituye la fuente de
  datos sin propagar condicionales por el modelo; el modelo no sabe si los datos llegaron por HTTP
  o desde archivos (P1 §3.4).
- `--replay`, `--replay … --hasta`, `--verificar` y `--bench` NO DEBEN instanciar la vista
  interactiva (P1 §6, P2 §3.5 y §3.6).
- Separación entre mapa y conocimiento: la infraestructura (descarga del esqueleto, precarga y
  caché) puede usar el esqueleto completo, pero todo lo que la vista muestra y lo que usa «ir a»
  DEBE derivarse exclusivamente del conocimiento del jugador (P2 §3.3).

### IV. Ningún dato de una cripta concreta en el código

- El código NO DEBE contener números de sala, ids de entidades o llaves, cantidad de páginas,
  presupuestos, costos ni estadísticas de una cripta específica (P1 §9). En la revisión se usará
  una cripta no publicada.
- Las estadísticas iniciales del jugador, `inventario_max` y `presupuesto_solicitudes` vienen
  siempre de los datos generales de la cripta.
- Lo persistido se valida con la versión de la cripta y la versión global del catálogo. Lo que
  persistió la primera parte se invalida con esa validación de versión, nunca borrando archivos a
  mano (P2 §4.3).

### V. Presupuesto de red y uso responsable del servicio

- Toda solicitud HTTP cuenta dentro de `presupuesto_solicitudes`: lista de criptas, datos generales,
  páginas, contenido, catálogo, versiones, ubicación de llaves (`GET /criptas/<id>/llaves`) y cada
  reintento después de un HTTP 429 (P1 §5.1 y P2 §4.3).
- Las lecturas de almacenamiento local y del modo `--offline` no cuentan como solicitudes.
- Se aprovechan los lotes (hasta 10 salas de contenido y hasta 10 ids de catálogo por solicitud) y
  la persistencia validada por versión. Un mismo dato vigente nunca se solicita dos veces.
- Todas las solicitudes de una ejecución usan el mismo encabezado `X-Cripta-Client-Id`, tienen un
  tiempo de espera explícito, manejan el HTTP 429 sin caerse y reportan cualquier otro error con el
  contexto de la operación que falló.
- La caché es estado de la infraestructura, no del juego: queda fuera del pergamino de retroceso y
  de la línea de tiempo (P1 §2.11).

### VI. Estado reversible sin copias completas

- El pergamino de retroceso NO DEBE guardar copias completas del estado. Solo almacena la
  información necesaria para invertir los cambios de cada intervalo entre decisiones del jugador,
  con un máximo de 5 acciones (P1 §2.11 y §4.6).
- La línea de tiempo solo puede guardar copias completas (puntos de control) como máximo una cada
  K acciones del jugador. Fuera de ellos solo guarda lo necesario para reconstruir los cambios, y
  ninguna consulta puede aplicar o deshacer más de K acciones. Si se reconstruye re-simulando, el
  punto de control incluye el estado del `random.Random` (P2 §3.6 y §5.5).
- La memoria total crece con la cantidad de cambios ocurridos más un punto de control cada K
  acciones; nunca con «acciones por tamaño del estado».
- El conocimiento del jugador (niebla de guerra) es estado del juego: se guarda en el archivo de
  partida, se revierte con el pergamino y forma parte de la línea de tiempo (P2 §3.3).
- Las consultas a la línea de tiempo (`historia`) no consumen tiempo virtual, no se registran como
  acción ni en `partida.log` y no alteran el estado del juego ni el historial de retroceso.

### VII. Rendimiento demostrado con mediciones

- Toda afirmación de rendimiento o complejidad en `plan.md`, `DECISIONES.md` o el README DEBE estar
  respaldada por un escenario reproducible de `--bench`.
- Límites que se verifican en el equipo local, sin red ni renderizado (P1 §5.2 y P2 §6.1):
  - ciclo de eventos entre dos decisiones del jugador: < 20 ms, con decenas de cazadores activos;
  - verificación de resolubilidad: < 200 ms en la cripta publicada más grande;
  - consulta `historia`: < 50 ms en una partida de al menos 5 000 acciones con el K por defecto;
  - cálculo de un paso de «ir a»: < 5 ms con el mapa conocido completo de la cripta de referencia.
- Cada decisión se compara con al menos una alternativa medida, incluida la alternativa ingenua
  cuando el enunciado la exige (recalcular siempre, recorrido repetido por llave, sin puntos de
  control, cálculo individual frente a compartido).
- Las decisiones de la primera parte se vuelven a medir con la carga nueva. Si dejan de ser
  adecuadas se cambian, y se documenta el antes y el después (P2 §5.6).

### VIII. La especificación precede a la implementación (NO NEGOCIABLE)

- Cada capacidad sigue el flujo `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
  `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`. Como mínimo hay una especificación
  para cada una de estas capacidades: terreno y cazador; niebla de guerra e «ir a»; resolubilidad;
  y línea de tiempo (P2 §2.2).
- El historial de Git DEBE mostrar la especificación de cada capacidad confirmada antes que el
  código que la implementa.
- Si la especificación resulta incorrecta durante la implementación, se corrige primero la
  especificación y después el código, en confirmaciones separadas. Una especificación desactualizada
  respecto del programa entregado es un defecto (P2 §2.6).
- Un programa que hace algo que ninguna especificación describe es un defecto del mismo tipo.

## Separación de artefactos y trazabilidad

- `spec.md` contiene reglas del juego, historias de usuario, escenarios de aceptación y requisitos
  funcionales y de rendimiento numerados. NO contiene nombres de estructuras de datos, clases ni
  módulos.
- `plan.md` contiene las estructuras elegidas, las alternativas consideradas, la complejidad
  esperada, los módulos afectados y las mediciones planificadas. NO introduce reglas que no estén en
  `spec.md`. Es el borrador de la sección correspondiente de `DECISIONES.md`.
- `tasks.md` contiene tareas pequeñas y verificables, con dependencias y la referencia a los
  requisitos que atienden. No existen tareas sin requisito asociado.
- Cada requisito funcional tiene un identificador estable (`FR-NNN`) que no se reutiliza.
- Cada caso del Apéndice B de P2 aparece como escenario de aceptación en alguna especificación. Los
  casos del Apéndice B de P1 siguen cubiertos por la batería de pruebas existente.
- Cada escenario de aceptación tiene al menos una prueba automatizada o un `partida.log` de
  reproducción que lo ejercita, y la prueba cita el identificador del requisito (P2 §2.5).

## Documentación y flujo de trabajo

- Lenguaje: Python 3.11 o superior. Pruebas con `unittest`, ejecutables también con `pytest`. Toda
  la batería existente DEBE seguir pasando después de cada cambio.
- `DECISIONES.md` mantiene, para cada problema, la estructura de P1 §8: problema, alternativas
  consideradas (al menos dos), decisión, análisis de complejidad, evidencia empírica con `--bench` y
  límites conocidos. Cada sección nueva enlaza a su especificación y a su plan, e indica si la
  decisión final coincide con la del `plan.md` y qué medición motivó un cambio (P2 §7.1).
- `README.md` indica la versión de spec-kit, el agente utilizado, cómo ejecutar el programa desde un
  entorno limpio, los comandos (`--offline`, `--replay`, `--replay … --hasta`, `--bench`,
  `--verificar`, `--forzar`, `--checkpoint-cada`) y cómo ejecutar las pruebas de aceptación.
- `PROMPTS_LLM.md` registra todo prompt enviado a un LLM, incluida cada invocación de un comando de
  spec-kit con texto propio, con fecha aproximada, herramienta, prompt textual y para qué se usó la
  respuesta (P1 §10.3 y P2 §2.6). No incluye credenciales ni datos personales.
- Los archivos que genera `specify init` (`.specify/`, `.claude/skills/`) se versionan.
- Un archivo de partida con un formato anterior se detecta como incompatible o se migra de forma
  explícita; nunca se carga en silencio (P1 §4.10 y P2 §3.6).
- Cada etapa del trabajo se desarrolla en su propia rama y se confirma al terminarla.

## Gobernanza

- Esta constitución prevalece sobre cualquier otra práctica del proyecto. Los agentes la leen en
  cada fase; si un plan o una tarea la contradice, el error es del grupo y se corrige antes de
  continuar.
- `/speckit-analyze` DEBE verificar el cumplimiento de esta constitución antes de cada
  `/speckit-implement`.
- Las enmiendas se hacen con `/speckit-constitution`, se registran en `PROMPTS_LLM.md` y se
  confirman por separado.
- Versionado semántico: MAYOR para eliminar o redefinir un principio; MENOR para agregar un
  principio o ampliar su alcance; PARCHE para aclaraciones de redacción.
- Las enmiendas al enunciado que comunique el profesor (P2 §2.7) se incorporan como enmienda de
  esta constitución o de la especificación afectada.
- Todo integrante del grupo debe poder explicar cualquier principio de esta constitución y
  cualquier especificación, no solo las de la capacidad que implementó (P1 §9 y P2 §7.4).

**Versión**: 1.0.0 | **Ratificada**: 2026-11-14 | **Última enmienda**: 2026-11-14
