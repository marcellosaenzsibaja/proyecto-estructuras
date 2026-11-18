# Feature Specification: Verificación de resolubilidad de una cripta

**Feature Branch**: `002-verificacion-resolubilidad`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Verificación de resolubilidad de una cripta (P2 §3.5, §4.2, §5.4, §6.1, §6.3 y Apéndice B «Resolubilidad»). Antes de iniciar una partida, el programa determina si la cripta puede ganarse, usando el esqueleto completo y la ubicación de las llaves que entrega el servicio en GET /criptas/<id>/llaves. Cada llave indica su sala y, si la suelta un enemigo, el id de esa instancia; en ese caso la llave se considera obtenible en la sala donde el enemigo inicia. Supuestos de la verificación: el jugador atraviesa cualquier salida abierta y cualquier salida cerrada cuya llave ya obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; las trampas y los cierres automáticos no bloquean porque una puerta puede volver a abrirse con la misma llave. Una cripta es resoluble si, partiendo de la sala inicial y bajo esos supuestos, el jugador puede obtener llave_salida y llegar a sala_salida a través de una puerta que la requiere. Si es resoluble, el resultado es un orden de obtención de llaves en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. Si hay varios órdenes válidos, cualquiera sirve, pero dos ejecuciones sobre la misma cripta producen el mismo orden. Si no es resoluble, el reporte indica: las llaves que no pueden obtenerse; las puertas de la frontera bloqueada (puertas cerradas adyacentes a la región alcanzable) con la llave que requiere cada una; y en qué sala está cada una de esas llaves. Si una llave está detrás de puertas que solo ella abre, directamente o mediante una cadena de llaves, el reporte señala el ciclo concreto, y esa detección es determinista. Interfaz: el reporte se muestra al iniciar una partida. Si la cripta no es resoluble y no se usa la bandera --forzar, la partida no inicia y se muestra el reporte. La opción --verificar <cripta> ejecuta únicamente la verificación sin instanciar la vista. La consulta de llaves cuenta dentro de presupuesto_solicitudes y su respuesta es válida mientras coincida la versión de la cripta, por lo que puede persistirse con el resto de los datos de la cripta. Ningún dato de una cripta concreta puede estar escrito en el código; el servicio publicará criptas no resolubles y en la revisión se usará una cripta nueva. Rendimiento: la verificación toma menos de 200 ms en la cripta publicada más grande, sin red ni renderizado. El costo total debe crecer aproximadamente de forma lineal con salas, salidas y llaves; no se acepta repetir el recorrido completo cada vez que se obtiene una llave. La información del reporte (frontera bloqueada y dependencias entre llaves) debe salir del mismo recorrido, sin recorridos adicionales por llave. La medición con criptas sintéticas deterministas por semilla, incluidas cadenas largas de llaves encadenadas, debe poder reproducirse con --bench. Casos que deben ser escenarios de aceptación (Apéndice B): (1) llave_salida detrás de la única puerta que ella misma abre: no resoluble y el reporte señala el ciclo; (2) una llave está en el campo suelta de un enemigo errante: la verificación la ubica en la sala inicial del enemigo; (3) existen varios órdenes válidos de obtención de llaves: dos ejecuciones producen el mismo orden; (4) cripta no resoluble sin --forzar: la partida no inicia y se muestra el reporte. Este documento describe solo reglas del juego, historias de usuario, escenarios de aceptación y requisitos funcionales y de rendimiento numerados. No nombres estructuras de datos, clases ni módulos: eso corresponde al plan."

## Contexto y alcance

Esta capacidad implementa la verificación estática previa al inicio de una partida para determinar si una cripta puede completarse con éxito (P2 §3.5, §4.2, §5.4, §6.1, §6.3 y Apéndice B «Resolubilidad»). Previene que un jugador intente resolver criptas inherentemente imposibles de ganar y proporciona diagnósticos deterministas precisos cuando existen bloqueos o dependencias circulares entre llaves y puertas.

**Dentro del alcance**:
- La regla formal de resolubilidad y sus supuestos ideales (llaves no consumibles, enemigos derrotables, puertas reabribles, atravesar salidas abiertas o con llave obtenida).
- La condición de victoria: obtener `llave_salida` y llegar a `sala_salida` a través de una puerta que requiere dicha llave.
- La determinación de un orden de obtención de llaves válido y determinista para criptas resolubles.
- El diagnóstico determinista para criptas no resolubles: llaves inalcanzables, frontera bloqueada con llaves requeridas y sus ubicaciones, y detección explícita de ciclos de dependencias entre llaves.
- La integración en línea de comandos: visualización del reporte al inicio, bloqueo de partida no resoluble salvo uso de `--forzar`, y modo independiente `--verificar <cripta>` sin instanciar la vista interactiva.
- Obtención del mapa de llaves mediante el servicio (`GET /criptas/<id>/llaves`), cómputo en el `presupuesto_solicitudes` y persistencia validada por versión de cripta.
- Medición de rendimiento y reproducibilidad mediante `--bench` sobre criptas sintéticas deterministas por semilla con escalabilidad lineal O(|V| + |E| + |llaves|) en < 200 ms en la cripta más grande.

**Fuera del alcance** (tienen sus propias especificaciones o pertenecen a otras capacidades):
- Simulación en tiempo real, combate, consumo de recursos y movimientos paso a paso durante el juego.
- Niebla de guerra e interacción con la orden «ir a» (especificación 003).
- Estructuras de datos concretas, algoritmos de bajo nivel, clases o módulos de implementación (corresponde a `plan.md` y `DECISIONES.md`).

## Clarifications

### Reglas de dominio fijadas

- **Ubicación de llaves**: Si la llave está en el suelo de una sala, su sala de obtención es esa misma sala. Si la llave la suelta un enemigo (`suelta`), se considera obtenible en la sala donde ese enemigo inicia su recorrido (su sala inicial en el esqueleto de la cripta), asumiendo que todo enemigo puede ser derrotado.
- **Determinismo ante múltiples órdenes válidos**: Si varias llaves pueden obtenerse en etapas independientes o en paralelo, dos ejecuciones sobre la misma cripta deben producir exactamente el mismo orden de obtención de llaves (por ejemplo, priorizando identificadores de llaves o salas en orden canónico).
- **Cierre y trampas automáticas**: Durante la verificación no se consideran los bloqueos dinámicos por trampas o puertas con autocierre, ya que el jugador puede volver a abrir cualquier puerta cerrada una vez que posee su llave.
- **Ciclos de llaves**: Un ciclo se produce cuando una llave se encuentra detrás de una o más puertas que requieren de la propia llave para ser abiertas (sea directamente o a través de una cadena de llaves dependientes). El reporte debe identificar la secuencia circular concreta de llaves involucradas de forma determinista.
- **Modo `--forzar`**: Permite al jugador iniciar y jugar una cripta no resoluble, mostrando siempre el reporte diagnóstico antes de ingresar a la vista interactiva.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificación previa y control de inicio de partida (Priority: P1)

Como jugador, antes de iniciar una partida quiero saber si la cripta seleccionada tiene solución; si no es resoluble, el juego debe advertírmelo con un reporte detallado y no iniciar la partida a menos que yo decida explícitamente forzarla, para evitar invertir tiempo en una cripta imposible.

**Why this priority**: Es la puerta de entrada funcional para el usuario y asegura que ninguna partida no resoluble comience por accidente sin advertencia previa.

**Independent Test**: Invocar la partida con criptas resolubles e irresolubles, comprobando la presentación del reporte y si el juego inicia o se detiene según el uso del parámetro `--forzar`.

**Acceptance Scenarios**:

1. **Given** una cripta resoluble, **When** el jugador inicia la partida normalmente, **Then** el sistema muestra el reporte de verificación confirmando que es resoluble y la partida inicia con normalidad.
2. **Given** una cripta no resoluble, **When** el jugador inicia la partida sin la opción `--forzar`, **Then** la partida no inicia, el sistema finaliza la ejecución y se muestra el reporte con el diagnóstico de no resolubilidad (Apéndice B, Caso 4).
3. **Given** una cripta no resoluble, **When** el jugador inicia la partida con la opción `--forzar`, **Then** el sistema muestra el reporte con el diagnóstico de no resolubilidad y procede a iniciar la partida interactiva.
4. **Given** una cripta cualquiera (resoluble o no resoluble), **When** se ejecuta el programa con `--verificar <cripta>`, **Then** se ejecuta únicamente la verificación, se presenta el reporte completo y el programa finaliza sin instanciar la vista interactiva ni iniciar la partida (P2 §3.5).

---

### User Story 2 - Secuencia determinista de obtención de llaves en criptas resolubles (Priority: P1)

Como jugador o evaluador, cuando una cripta es resoluble quiero conocer una secuencia válida en la que las llaves pueden ser recolectadas para alcanzar la salida, y esa secuencia debe ser estrictamente determinista entre distintas ejecuciones sobre la misma cripta.

**Why this priority**: Define el resultado afirmativo de la resolubilidad y garantiza la regla de oro de determinismo del sistema.

**Independent Test**: Verificar una cripta resoluble que contenga múltiples caminos o bifurcaciones para recoger llaves, comprobando que cada llave requerida aparezca antes de las puertas que abre y que dos ejecuciones independientes produzcan exactamente el mismo orden.

**Acceptance Scenarios**:

1. **Given** una cripta resoluble con una única cadena lineal de llaves (llave A abre puerta hacia llave B, y llave B abre puerta hacia llave_salida), **When** se verifica la cripta, **Then** el reporte entrega la secuencia ordenada [llave A, llave B, llave_salida] donde cada llave aparece después de todas las llaves necesarias para alcanzarla.
2. **Given** una cripta resoluble donde existen múltiples órdenes válidos para recolectar las llaves (bifurcaciones independientes), **When** se ejecutan dos o más verificaciones sobre la misma cripta, **Then** ambas ejecuciones producen exactamente el mismo orden de llaves (Apéndice B, Caso 3).
3. **Given** una cripta donde una llave está asignada en el campo `suelta` de un enemigo que se mueve (errante o cazador), **When** se realiza la verificación, **Then** la llave se ubica para la resolución en la sala inicial donde el enemigo aparece, asumiendo que es derrotado en su origen (Apéndice B, Caso 2).
4. **Given** una cripta donde una puerta cerrada con llave posee además mecanismo de autocierre o trampas en salas intermedias, **When** se evalúa la resolubilidad, **Then** se asume que las llaves no se consumen y que el jugador puede volver a abrir la puerta cuantas veces sea necesario sin quedar bloqueado.

---

### User Story 3 - Diagnóstico y reporte determinista de criptas irresolubles (Priority: P2)

Como jugador, analista o creador de criptas, cuando una cripta no es resoluble quiero un reporte exhaustivo que identifique exactamente qué llaves son inalcanzables, qué puertas forman la frontera bloqueada adyacente a la zona accesible, dónde se encuentra cada llave faltante, y qué ciclos de dependencias circulares impiden avanzar.

**Why this priority**: Proporciona el valor de diagnóstico del sistema y explica con precisión la causa de la imposibilidad de resolución, cumpliendo los requisitos estrictos de la evaluación.

**Independent Test**: Verificar criptas sintéticas con diversos patrones de irresolubilidad (llaves aisladas, puertas sin llave, ciclos directos y ciclos indirectos) y corroborar que el reporte liste con exactitud las llaves inalcanzables, las puertas de frontera con sus salas de llaves y los ciclos detectados.

**Acceptance Scenarios**:

1. **Given** una cripta donde `llave_salida` se encuentra ubicada detrás de la única puerta que ella misma abre, **When** se ejecuta la verificación, **Then** el sistema determina que la cripta no es resoluble y el reporte señala el ciclo concreto (Apéndice B, Caso 1).
2. **Given** una cripta con una dependencia circular indirecta (por ejemplo, llave A tras puerta B, llave B tras puerta C, y llave C tras puerta A), **When** se ejecuta la verificación, **Then** el sistema determina que la cripta no es resoluble y el reporte señala de forma determinista la cadena cíclica concreta formada por las llaves.
3. **Given** una cripta no resoluble donde el jugador solo puede alcanzar un subconjunto de salas antes de topar con puertas cerradas, **When** se emite el reporte, **Then** este enumera todas las puertas de la frontera bloqueada (puertas cerradas conectadas directamente a la región alcanzable) junto con el identificador de la llave que requiere cada una.
4. **Given** las puertas de la frontera bloqueada identificadas en el reporte, **When** se inspecciona la información de cada una, **Then** el reporte indica en qué sala se encuentra ubicada la llave requerida para cada una de esas puertas.
5. **Given** una cripta donde el jugador puede alcanzar la `sala_salida` pero no a través de una puerta que requiera `llave_salida` (o no existe `llave_salida`), **When** se verifica la cripta, **Then** la cripta se clasifica como no resoluble.

---

### User Story 4 - Consulta de llaves bajo presupuesto y persistencia por versión (Priority: P2)

Como administrador de recursos del sistema, quiero que la información de ubicación de llaves se consulte al servicio respetando el presupuesto de solicitudes y se persista localmente validada por versión de cripta, para no malgastar cuota de red.

**Why this priority**: Cumple con el Principio V de la constitución (presupuesto de red y uso responsable) y garantiza que el juego opere eficientemente en partidas repetidas y en modo desconectado.

**Independent Test**: Ejecutar verificaciones consecutivas sobre la misma versión de cripta y verificar que el presupuesto de solicitudes solo se consuma en la primera consulta, reutilizando la información persistida en las siguientes.

**Acceptance Scenarios**:

1. **Given** una partida en línea donde no se tiene persistida la información de llaves de la cripta, **When** se realiza la verificación, **Then** se efectúa la solicitud `GET /criptas/<id>/llaves` y esta consume exactamente una unidad del `presupuesto_solicitudes` asignado a la cripta.
2. **Given** datos de llaves ya persistidos localmente que coinciden con la versión actual de la cripta, **When** se ejecuta la verificación, **Then** la información se recupera del almacenamiento local sin realizar llamadas HTTP ni descontar unidades de `presupuesto_solicitudes`.
3. **Given** una ejecución con el parámetro `--offline`, **When** se verifica la cripta, **Then** se utiliza exclusivamente la información almacenada localmente y no se realiza ninguna petición de red.
4. **Given** una cripta cuya versión en el servidor es distinta a la versión de los datos persistidos localmente, **When** se ejecuta la verificación en línea, **Then** los datos obsoletos se invalidan automáticamente por control de versión y se solicita la nueva versión consumiendo del presupuesto.

---

### User Story 5 - Rendimiento lineal y reproducibilidad mediante pruebas de carga sintéticas (Priority: P3)

Como evaluador técnico, quiero comprobar con `--bench` que la verificación de resolubilidad toma menos de 200 ms en la cripta publicada más grande y que su costo crece linealmente con el tamaño de la cripta, asegurando que no se repitan recorridos completos por cada llave encontrada.

**Why this priority**: Requisito no funcional crítico exigido por P2 §6.1, §6.3 y el Principio VII de la constitución para demostrar que la implementación no recurre a soluciones ingenuas ineficientes.

**Independent Test**: Ejecutar `--bench` sobre familias de criptas sintéticas generadas deterministamente por semilla, variando la cantidad de salas, salidas y longitud de cadenas de llaves, comprobando tiempos de ejecución y escalabilidad.

**Acceptance Scenarios**:

1. **Given** la cripta publicada más grande del servicio, **When** se ejecuta la verificación de resolubilidad en el entorno local (sin red ni renderizado), **Then** el tiempo total de cómputo es estrictamente menor a 200 ms.
2. **Given** criptas sintéticas con cadenas largas de dependencias de llaves (por ejemplo, 50 o más llaves encadenadas secuencialmente), **When** se mide el costo computacional con `--bench`, **Then** el tiempo de procesamiento total crece de forma aproximadamente lineal O(|V| + |E| + |llaves|) respecto a la cantidad de salas, salidas y llaves, demostrando que no se reinicia el recorrido global tras descubrir cada llave.
3. **Given** una verificación de cripta irresoluble, **When** se genera el reporte diagnóstico, **Then** toda la información de la frontera bloqueada y las dependencias/ciclos entre llaves se deriva del mismo recorrido de exploración sin recorridos adicionales por llave.
4. **Given** una semilla aleatoria determinada, **When** se ejecuta `--bench` en momentos distintos, **Then** genera exactamente el mismo conjunto de criptas sintéticas deterministas y produce métricas reproducibles.

---

### Edge Cases

- **Llave en la sala inicial**: Una llave situada en la misma sala donde inicia el jugador se considera obtenida de inmediato al comenzar la verificación sin necesidad de atravesar ninguna salida.
- **Enemigo con llave en sala inalcanzable**: Si un enemigo posee una llave pero su sala inicial está en una región inaccesible, la llave se reporta como inalcanzable.
- **Múltiples puertas abiertas por la misma llave**: Una misma llave puede abrir varias puertas distintas en la cripta. Al obtenerse dicha llave, todas las puertas asociadas pasan a considerarse franqueables simultáneamente.
- **Puertas cerradas sin llave existente**: Si una puerta está cerrada pero ninguna llave de la cripta tiene asignado su código/identificador, la puerta nunca podrá abrirse; si es la única ruta a la salida, la cripta es no resoluble y dicha puerta forma parte de la frontera bloqueada indicando que su llave no existe en la cripta.
- **Llaves redundantes u huérfanas**: Llaves que no abren ninguna puerta de la cripta pueden ser recogidas si están en salas alcanzables, pero su obtención no desbloquea salidas adicionales y no afecta la resolubilidad.
- **Múltiples salidas entre las mismas dos salas**: Si dos salas están conectadas por más de una salida con diferentes requerimientos de llaves (por ejemplo, una abierta y una cerrada con llave), el jugador puede franquear la conexión usando la salida abierta sin esperar a obtener la llave.
- **Salida accesible sin llave_salida**: Si el jugador puede llegar a la `sala_salida` a través de una salida abierta pero las reglas exigen ingresar a través de una puerta que requiere `llave_salida`, la cripta no se considera resuelta hasta que `llave_salida` sea obtenida y se atraviese una puerta que la requiera.
- **Varios ciclos de dependencias disjuntos**: Si una cripta contiene múltiples regiones inaccesibles con ciclos independientes de llaves, el reporte debe identificar y desglosar deterministamente cada uno de los ciclos encontrados.
- **Presupuesto de solicitudes agotado**: Si antes de consultar las llaves el presupuesto de solicitudes de la cripta ya fue consumido por otras operaciones, la verificación debe reportar un error controlado de presupuesto sin causar caídas imprevistas del programa.

## Requirements *(mandatory)*

### Functional Requirements

**Reglas y supuestos de verificación**

- **FR-001**: El sistema DEBE determinar si una cripta es resoluble antes de iniciar la partida, basándose exclusivamente en el esqueleto completo de la cripta y en la información de llaves obtenida para esa cripta.
- **FR-002**: La verificación DEBE asumir que el jugador puede atravesar libremente cualquier salida abierta, así como cualquier salida cerrada cuya llave ya haya sido obtenida.
- **FR-003**: La verificación DEBE asumir que las llaves nunca se consumen al abrir puertas y permanecen en posesión permanente del jugador tras ser obtenidas.
- **FR-004**: La verificación DEBE asumir que cualquier enemigo puede ser derrotado por el jugador y que las trampas o mecanismos de autocierre de puertas no impiden el paso permanente, ya que toda puerta cerrada puede volver a abrirse si se posee la llave.
- **FR-005**: Si una llave se encuentra libre en una sala, su ubicación para la verificación DEBE ser esa sala.
- **FR-006**: Si una llave es soltada por un enemigo (campo `suelta` vinculado al id de la instancia del enemigo), su ubicación para la verificación DEBE ser la sala inicial donde dicho enemigo aparece en la cripta.
- **FR-007**: Una cripta DEBE considerarse resoluble si y solo si, partiendo de la sala inicial bajo los supuestos anteriores, el jugador puede obtener `llave_salida` y alcanzar `sala_salida` a través de una puerta que requiera dicha llave.

**Determinismo y orden de obtención**

- **FR-008**: Si la cripta es resoluble, el resultado DEBE incluir un orden de obtención de llaves en el que cada llave aparezca estrictamente después de todas las llaves requeridas para acceder a la sala donde se ubica.
- **FR-009**: Ante múltiples órdenes válidos de recolección de llaves, el sistema DEBE generar el mismo orden en cualquier ejecución sobre la misma cripta.
- **FR-010**: El desempate para fijar el orden determinista de obtención de llaves DEBE resolverse mediante un criterio canónico unívoco (como el identificador alfanumérico de la llave o de la sala) independiente del orden de almacenamiento interno o iteración en memoria.

**Diagnóstico de criptas no resolubles y ciclos**

- **FR-011**: Si la cripta no es resoluble, el sistema DEBE generar un reporte diagnóstico detallado.
- **FR-012**: El reporte de no resolubilidad DEBE listar todas las llaves de la cripta que no pueden ser obtenidas desde la sala inicial.
- **FR-013**: El reporte de no resolubilidad DEBE identificar todas las puertas pertenecientes a la «frontera bloqueada», definidas como las puertas cerradas inmediatamente adyacentes a la región de salas alcanzables por el jugador.
- **FR-014**: Para cada puerta de la frontera bloqueada, el reporte DEBE indicar la llave que dicha puerta requiere para ser abierta y la sala en la que se encuentra ubicada esa llave (o indicar si la llave no existe en la cripta).
- **FR-015**: Si una llave se encuentra detrás de una puerta que ella misma abre, o detrás de una cadena de puertas que requiere de llaves que dependen en última instancia de la primera, el sistema DEBE clasificarla como un ciclo de dependencias y señalar el ciclo concreto en el reporte.
- **FR-016**: La detección y reporte de ciclos DEBE ser estrictamente determinista entre ejecuciones.

**Interfaz de usuario e integración CLI**

- **FR-017**: Al intentar iniciar una partida normal, el sistema DEBE ejecutar la verificación de resolubilidad y mostrar su reporte en pantalla antes de entrar a la vista interactiva.
- **FR-018**: Si la cripta resulta no resoluble y el comando no incluye la bandera `--forzar`, la partida NO DEBE iniciar y el programa DEBE finalizar mostrando el reporte explicativo.
- **FR-019**: Si la cripta resulta no resoluble y el comando incluye la bandera `--forzar`, el sistema DEBE mostrar el reporte diagnóstico y proceder a iniciar la partida interactiva.
- **FR-020**: El sistema DEBE ofrecer la opción de línea de comandos `--verificar <cripta>`, la cual ejecuta únicamente la verificación de resolubilidad de la cripta indicada, imprime el reporte completo y termina sin instanciar la vista interactiva ni iniciar la partida.

**Servicio, red, persistencia y generalidad**

- **FR-021**: La ubicación de las llaves DEBE obtenerse mediante el endpoint del servicio `GET /criptas/<id>/llaves`.
- **FR-022**: Cada solicitud HTTP a `GET /criptas/<id>/llaves` DEBE contabilizarse como una consulta dentro del `presupuesto_solicitudes` de la cripta.
- **FR-023**: La respuesta de la ubicación de llaves DEBE persistirse en el almacenamiento local junto con los datos de la cripta y asociarse a la versión de la misma.
- **FR-024**: Mientras la versión de la cripta almacenada localmente coincida con la versión del servidor (o en modo `--offline`), el sistema DEBE utilizar los datos de llaves persistidos sin realizar peticiones de red ni descontar del `presupuesto_solicitudes`.
- **FR-025**: El código fuente NO DEBE contener datos grabados a fuego (hardcoded) de ninguna cripta específica (ni números de sala, ni nombres de llaves, ni salidas). El programa debe ser evaluable con criptas nuevas no publicadas provistas por el servicio.

**Rendimiento y verificación sintética**

- **FR-026**: La verificación de resolubilidad DEBE ejecutarse en un tiempo inferior a 200 milisegundos para la cripta más grande publicada por el servicio, medido en entorno local sin considerar tiempos de red ni de renderizado.
- **FR-027**: El tiempo computacional de la verificación DEBE crecer de forma aproximadamente lineal O(|V| + |E| + |llaves|) en función de la cantidad de salas (|V|), salidas (|E|) y llaves de la cripta.
- **FR-028**: La verificación NO DEBE repetir el recorrido completo de la región alcanzable cada vez que se obtiene una llave nueva.
- **FR-029**: Toda la información requerida por el reporte de no resolubilidad (frontera bloqueada, salas de llaves y ciclos de dependencias) DEBE generarse a partir del mismo recorrido de exploración, sin realizar búsquedas ni recorridos adicionales independientes por cada llave.
- **FR-030**: El comando `--bench` DEBE incorporar escenarios reproducibles para medir la verificación de resolubilidad utilizando criptas sintéticas deterministas por semilla, incluyendo casos con cadenas largas de llaves encadenadas.
- **FR-031**: La ejecución de `--bench` NO DEBE instanciar la interfaz visual interactiva.

### Key Entities

- **Llave**: Identificador de una llave en la cripta. Atributos conceptuales: identificador de llave, sala donde se encuentra, e identificador de la instancia de enemigo que la suelta (si aplica).
- **Puerta Cerrada / Salida Bloqueada**: Conexión orientada entre dos salas que requiere una llave específica para poder ser atravesada.
- **Frontera Bloqueada**: Conjunto de salidas cerradas cuya sala de origen pertenece a la región de salas alcanzables por el jugador pero cuya sala destino no puede ser visitada por falta de la llave requerida.
- **Ciclo de Dependencias**: Secuencia ordenada y circular de llaves y puertas `[L_1 -> P_1 -> L_2 -> ... -> P_k -> L_1]` donde cada llave `L_{i+1}` está bloqueada por una puerta `P_i` que solo puede abrirse poseyendo la llave anterior, formando un bloqueo mutuo irresoluble.
- **Reporte de Resolubilidad**: Resultado estructurado de la verificación. Para criptas resolubles: indicador de éxito y secuencia ordenada determinista de llaves. Para criptas no resolubles: indicador de fallo, lista de llaves no alcanzadas, listado de la frontera bloqueada con ubicación de llaves requeridas, y lista de ciclos detectados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 4 escenarios obligatorios de aceptación del Apéndice B («llave_salida tras puerta que ella misma abre», «llave en suelta de errante en sala inicial», «orden determinista ante múltiples caminos válidos» y «bloqueo de inicio sin --forzar») cuentan con pruebas automatizadas que citan sus respectivos requisitos y pasan exitosamente.
- **SC-002**: En el 100% de las ejecuciones repetidas sobre la misma cripta con múltiples órdenes válidos posibles de recolección de llaves, el orden resultante es idéntico carácter por carácter.
- **SC-003**: En la cripta más grande publicada por el servicio, la verificación completa toma estrictamente menos de 200 ms ejecutada en el equipo local sin red ni vista.
- **SC-004**: En criptas sintéticas con cadenas de 10, 20, 50 y 100 llaves encadenadas secuencialmente, el incremento en tiempo de ejecución medido con `--bench` demuestra un factor de crecimiento lineal O(|V| + |E| + |llaves|) sin degradación cuadrática.
- **SC-005**: Al iniciar una partida con una cripta no resoluble sin especificar `--forzar`, el juego finaliza en el 100% de los casos sin llegar a instanciar la pantalla de juego ni admitir comandos de acción del jugador.
- **SC-006**: La opción `--verificar <cripta>` completa su diagnóstico y emite el reporte en consola sin abrir ventanas gráficas ni bucles interactivos en menos de 250 ms en entorno local.
- **SC-007**: La consulta de llaves realiza a lo sumo una única llamada HTTP por versión de cripta, y no realiza llamadas adicionales en ejecuciones subsecuentes sobre la misma versión persistida ni en modo `--offline`.
- **SC-008**: Toda la suite existente de pruebas unitarias y de aceptación de etapas anteriores continúa ejecutándose y pasando al 100%.

## Assumptions

- **Información del servicio**: El servicio provee de manera confiable la ubicación de todas las llaves en `GET /criptas/<id>/llaves` con el identificador de la sala y, cuando corresponda, el identificador de instancia del enemigo portador.
- **Instancias de enemigos**: Los datos generales del esqueleto de la cripta contienen la asignación de salas iniciales para cada instancia de enemigo declarada.
- **Puerta de salida**: Se asume que toda cripta formalmente definida posee una `sala_salida` y una `llave_salida`. Si una cripta carece de dicha definición en sus metadatos, la verificación la reporta como no resoluble por defecto de datos.
- **Simplicidad del combate**: El supuesto de que "todo enemigo puede ser derrotado" es exclusivo del análisis estático de resolubilidad y no altera las probabilidades ni las reglas del combate real durante la partida interactiva.
- **Independencia de niebla de guerra**: La verificación de resolubilidad opera sobre el esqueleto completo y el mapa total de llaves, independiente del estado de exploración o niebla de guerra que experimentará el jugador en la partida.
