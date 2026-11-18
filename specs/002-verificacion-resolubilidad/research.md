# Research: Verificación de resolubilidad de una cripta

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-17

Este documento consolida las decisiones de diseño técnico y selección de estructuras de datos para resolver la verificación de resolubilidad cumpliendo estrictamente con la Constitución del proyecto (Principio I: prohibición de `dict`, `set`, `heapq`, `bisect`, `collections` y bibliotecas de grafos; Principio II: determinismo absoluto; Principio III: MVC; Principio V: presupuesto de red; Principio VII: rendimiento demostrado).

---

## R1. Cola de salas para el recorrido de exploración (BFS / Flood-Fill)

- **Decisión**: Lista continua nativa de Python con puntero de lectura entero (`cola = [...]`, `cabeza = 0`). Al descubrir una sala alcanzable se agrega con `cola.append(sala)` ($O(1)$ amortizado), y al extraer la siguiente sala se toma `cola[cabeza]` y se incrementa `cabeza += 1` ($O(1)$ estricto sin corrimientos de memoria).
- **Justificación**: Cada sala $v \in V$ se encola a lo sumo una vez ($|V|$ elementos en total a lo largo de toda la verificación). Esta estructura garantiza acceso $O(1)$ exacto en memoria contigua, sobrecarga nula de punteros u objetos intermedios, y cero impacto sobre la recolección de basura. Es determinista y lineal.
- **Alternativas consideradas**:
  - *Alternativa 1 (`ListaDoble` propia de P1)*: Implementada en `src/estructuras_datos/lista_doble.py`. Ofrece inserción y extracción $O(1)$, pero asigna un objeto `NodoLista` por cada elemento, lo que introduce sobrecarga innecesaria de punteros y asignaciones en el heap para una cola cuyo tamaño total está acotado por $|V|$.
  - *Alternativa 2 (`BufferCircular` propio de P1)*: Implementado en `src/estructuras_datos/buffer_circular.py`. Tiene capacidad fija predefinida; requeriría predimensionar al número máximo de salas o redimensionar con copias intermedias.
  - *Alternativa 3 (`collections.deque`)*: **PROHIBIDA** categóricamente por el Principio I de la Constitución.

---

## R2. Registro de salas alcanzadas / visitadas

- **Decisión**: Arreglo de tamaño $n = |V|$ indexado por el índice compacto `Sala.indice` (`visitada = [False] * n`), reutilizando la indexación continua $0 \dots n-1$ que ya asigna `Cripta` durante la carga determinista del esqueleto.
- **Justificación**: Acceso, consulta y actualización en $O(1)$ estricto sin operaciones de hash ni resolución de colisiones. La memoria es contigua y proporcional a $|V|$ ($O(|V|)$ bits/enteros). Cumple al 100% con la prohibición constitucional de usar `set` o `dict` como registro de visitados.
- **Alternativas consideradas**:
  - *Alternativa 1 (`RegistroBusqueda` con marca de generación)*: Implementado en `src/estructuras_datos/registro_busqueda.py` para la capacidad 001. Permite reset en $O(1)$ para múltiples búsquedas sucesivas. Sin embargo, la verificación de resolubilidad es un análisis estático de una sola pasada al inicio, por lo que un arreglo directo de booleanos `[False] * n` es aún más liviano y específico.
  - *Alternativa 2 (`TablaHash` propia de P1)*: `src/estructuras_datos/tabla_hash.py`. Proporciona $O(1)$ promedio pero añade el costo del cómputo de dispersión, manejo de colisiones y mayor consumo de memoria, lo cual es innecesario teniendo ya un índice entero compacto $0 \dots n-1$.
  - *Alternativa 3 (`set` nativo de Python)*: **PROHIBIDO** por el Principio I de la Constitución.

---

## R3. Indexación y resolución de identificadores de llaves ($K$)

- **Decisión**: Tabla ordenada canónicamente de identificadores únicos de llaves `claves_llaves = ordenar(lista_ids_unicos)` mediante el algoritmo propio de ordenamiento (`src/estructuras_datos/ordenamiento.py`), asignando a cada llave un índice numérico continuo $0 \le j < m$ ($m = |K|$). La conversión de string de id a índice se realiza mediante una búsqueda binaria implementada a mano en $O(\log m)$.
- **Justificación**: Las llaves poseen identificadores textuales (como `"itm_llave_plata"` o `"llave_salida"`). Al mapear cada identificador a un índice entero $0 \dots m-1$ al iniciar la verificación, todas las estructuras de soporte subsecuentes (llaves obtenidas, puertas en espera, dependencias) se representan como arreglos indexados con operaciones $O(1)$. Ordenar los identificadores lexicográficamente asegura además que el desempate de llaves cumpla la regla determinista fijada en la sesión de clarificación (Q2).
- **Alternativas consideradas**:
  - *Alternativa 1 (`TablaHash` propia de P1 `str -> int`)*: $O(1)$ promedio, pero no provee orden canónico de iteración y tiene sobrecarga de colisiones.
  - *Alternativa 2 (Búsqueda lineal en lista)*: $O(m)$ por consulta. Si una cripta contiene 100 llaves y 500 puertas, el tiempo acumulado de resolución sería $O(|E| \cdot m)$, lo que introduciría un factor cuadrático indeseado.
  - *Alternativa 3 (`dict` o módulo `bisect`)*: **PROHIBIDOS** por el Principio I de la Constitución.

---

## R3b. Selección de la llave de menor id lexicográfico entre varias disponibles (FR-010)

- **Decisión**: Se reutiliza el montículo binario de mínimos propio `MonticuloMin` de `src/estructuras_datos/monticulo.py` como cola de prioridad para mantener el conjunto de llaves que se han vuelto alcanzables pero que aún no han sido procesadas. Al descubrir una llave disponible en una sala, se inserta en el montículo el par `(indice_llave, indice_llave)`. Para escoger la siguiente llave a obtener, se extrae el mínimo mediante `extraer_minimo()`.
- **Justificación de reutilización de `src/estructuras_datos/monticulo.py`**:
  `MonticuloMin` ya fue implementado y probado en el proyecto (capacidad 001). Almacena pares y los compara como tupla en tiempo $O(\log k)$. Como `claves_llaves` fue ordenado lexicográficamente al inicio (R3), el índice entero $0 \le j < m$ preserva de manera exacta el orden alfanumérico creciente de los identificadores (`id`). Por ende, insertar `(indice_llave, indice_llave)` garantiza que `extraer_minimo()` siempre entrega en $O(\log |K|)$ la llave de menor identificador lexicográfico disponible entre todas las alcanzadas, satisfaciendo estrictamente FR-010 de forma determinista y sin duplicar código.
  - *Complejidad*: Cada una de las $m = |K|$ llaves de la cripta se inserta a lo sumo una vez al alcanzarse su sala y se extrae a lo sumo una vez al procesarse. El costo acumulado total de todas las operaciones sobre el montículo es $O(|K| \log |K|)$.
  - *Mantenimiento del costo aproximadamente lineal*: Dado que en toda cripta $|K| \le |V|$, el costo de $O(|K| \log |K|)$ está dominado por la exploración de salas y salidas $O(|V| + |E|)$. El costo global total de la verificación permanece acotado por $O(|V| + |E| + |K| \log |K|) \approx O(|V| + |E| + |K|)$, estrictamente lineal respecto a la cantidad de salas y salidas y escalable a miles de elementos sin degradación cuadrática.
- **Alternativas consideradas**:
  - *Alternativa 1 (Arreglo booleano de disponibilidad y búsqueda lineal)*: Mantener `disponible = [False] * m` y buscar el mínimo escaneando el arreglo desde $j=0$ cada vez que se requiere una llave. En el peor caso (muchas llaves disponibles simultáneamente), cada extracción cuesta $O(|K|)$, totalizando $O(|K|^2)$ y degradando a cuadrático.
  - *Alternativa 2 (Acumulación en lista y ordenamiento periódico con `ordenar()`)*: Acumular llaves por etapas y ordenar la lista con mezcla/inserción. Requiere delimitar artificialmente las etapas y reordenar listas repetidamente, siendo menos eficiente y natural que la cola de prioridad continua.
  - *Alternativa 3 (`heapq` de biblioteca estándar)*: **PROHIBIDO** categóricamente por el Principio I de la Constitución.

---

## R4. Registro de puertas en espera de una llave (Frontera Bloqueada)

- **Decisión**: Arreglo de listas indexado por el índice de la llave: `puertas_en_espera = [[] for _ in range(m)]`. Cada posición $j$ almacena una lista de tuplas `(sala_origen, sala_destino, salida)` correspondientes a las salidas cerradas que requieren la llave $j$ para ser franqueadas.
- **Justificación**:
  1. Cuando el recorrido explora una sala y topa con una puerta cerrada cuya llave $j$ no se posee, la puerta se registra en $O(1)$ en `puertas_en_espera[j]`.
  2. Cuando la llave $j$ es descubierta y obtenida, se accede directamente a `puertas_en_espera[j]` en $O(1)$ y se activan únicamente las puertas que estaban esperando por ella, agregando sus salas destino a la cola de exploración.
  3. Cada puerta cerrada se procesa a lo sumo dos veces en toda la verificación (al topar con ella y al desbloquear su llave). Esto garantiza un tiempo global estrictamente lineal $O(|V| + |E| + |K|)$ sin volver a recorrer ninguna sala ya visitada (FR-028).
- **Alternativas consideradas**:
  - *Alternativa 1 (Alternativa ingenua / Naive)*: No llevar registro de espera indexado y reiniciar la exploración completa desde `sala_inicial` cada vez que se recolecta una llave nueva. Costo en el peor caso $O(|K| \cdot (|V| + |E|))$, el cual es inaceptablemente cuadrático ante cadenas largas de llaves encadenadas. Se implementa en `--bench` como línea base de comparación empírica (FR-027, FR-028).
  - *Alternativa 2 (Lista lineal única de puertas bloqueadas)*: Al obtener una llave, escanear toda la lista de puertas bloqueadas pendientes para filtrar las que coincidan. Costo $O(|K| \cdot |E_{\text{cerradas}}|)$, también cuadrático.

---

## R5. Construcción de dependencias y detección determinista de ciclos

- **Decisión**:
  1. Si la cripta no es resoluble al finalizar la fase de avance, la región de salas alcanzables $R$ queda acotada. Las puertas que quedaron en `puertas_en_espera` con llaves no obtenidas constituyen formalmente la **frontera bloqueada** (FR-013, FR-014).
  2. Desde cada puerta de la frontera bloqueada que conduce a una sala $v \notin R$, se explora la componente no alcanzada correspondiente para identificar qué llaves no obtenidas están situadas en esas salas. Si la llave $k'$ se encuentra en la región custodiada por la puerta que requiere $k$, se establece una dependencia dirigida $k \to k'$ ("poseer $k$ permite acceder a $k'$").
  3. Sobre el grafo de dependencias entre llaves no obtenidas ($|K_{\text{bloq}}| \le |K|$ nodos), se ejecuta un algoritmo de búsqueda en profundidad (DFS) **estrictamente iterativo con una pila propia** (`pila = [...]`, utilizando una lista nativa en modo LIFO con `append` y `pop` en $O(1)$) y un arreglo de estado de tres marcas (`0: NO_VISITADO`, `1: EN_PROCESO`, `2: PROCESADO`), evaluando los nodos en orden alfanumérico creciente de `id`.
  4. La pila propia almacena pares `(nodo_llave, indice_arista)` y una lista `camino` con la ruta activa en el árbol de exploración. Al encontrar una arista hacia un nodo marcado como `EN_PROCESO`, se ha detectado un ciclo de dependencias: se extrae la secuencia cíclica desde `camino`, se normaliza canónicamente rotándola para que inicie en la llave con menor `id` lexicográfico (ej. `[llave_a -> llave_b -> llave_a]`), y se registra. Si existen múltiples ciclos independientes, se presentan ordenados alfabéticamente por su llave inicial (Clarificación Q4).
- **Justificación**:
  - *Independencia del límite de recursión*: El límite de recursión predeterminado de Python (`sys.getrecursionlimit()`, típicamente 1 000) provocaría un fallo catastrófico (`RecursionError`) ante cadenas largas de dependencias de llaves (100 a más de 1 000 llaves encadenadas). Implementar el DFS de forma iterativa con una pila propia en memoria dinámica (heap) desvincula por completo la ejecución del call-stack del intérprete, soportando cadenas de profundidad arbitraria.
  - *Complejidad temporal*: $O(|K| + |E_K|)$, donde cada nodo de llave entra y sale de la pila a lo sumo una vez y cada dependencia dirigida se examina una sola vez.
  - *Complejidad espacial*: $O(|K|)$ en el heap para la pila y los arreglos de estado, acotada estrictamente por el número de llaves no obtenidas.
- **Alternativas consideradas**:
  - *Alternativa 1 (DFS recursivo convencional)*: Mucho más simple de escribir, pero totalmente dependiente de `sys.getrecursionlimit()`. Con criptas sintéticas de prueba que contienen cadenas largas de llaves encadenadas, causa desbordamiento de pila y no es apto para producción ni para `--bench`.
  - *Alternativa 2 (Algoritmo de Tarjan para Componentes Fuertemente Conexas - SCC)*: Encuentra las componentes cíclicas, pero requiere un post-procesamiento adicional para descomponer la SCC en ciclos elementales específicos y ordenarlos canónicamente, con mayor complejidad de código.
  - *Alternativa 3 (Búsqueda BFS hacia atrás por cada llave)*: Explorar hacia atrás desde cada llave no obtenida hasta encontrar si requiere de sí misma. Costo $O(|K| \cdot (|V| + |E|))$, violando el requisito de derivar el reporte a partir del mismo recorrido lineal (FR-029).

---

## R6. Consulta de llaves bajo presupuesto de red y persistencia por versión

- **Decisión**:
  - Extender el adaptador `ApiClient` con el método `obtener_llaves(cripta_id) -> dict`, el cual invoca directamente `self._get(f'/criptas/{cripta_id}/llaves', f'llaves de {cripta_id}')`.
  - Reutilizar el manejo existente de `ApiClient._get` para el código HTTP 429: si el servidor responde con 429, se extrae el tiempo exacto en segundos indicado en `reintentar_en` del JSON devuelto mediante `_segundos_reintento` y se espera ese tiempo con `self._esperar(segundos)` antes de reintentar. **Se elimina cualquier mención o uso de retroceso exponencial**, respetando la indicación estricta del servidor. Cada intento contabiliza 1 solicitud dentro de `presupuesto_solicitudes`.
  - Extender `FuenteSinConexion` para leer las llaves desde `<carpeta_offline>/<cripta_id>/llaves.json` sin realizar peticiones HTTP ni descontar presupuesto.
  - En `ProveedorRed`, incorporar la consulta de llaves con caché persistente en disco (`cache_llaves.json` o `<cache_dir>/<cripta_id>/llaves.json`), validada mediante la versión de la cripta (`GET /criptas/<id>/version`). Si la versión en disco coincide con la del servidor, se utiliza el archivo local con cero solicitudes HTTP (FR-022, FR-023, FR-024).
- **Justificación**: Cumple estrictamente con el Principio V de la Constitución (uso responsable de la red y persistencia por versión) y con el Principio III (adaptadores conmutables para `--offline`), reutilizando la lógica probada de `ApiClient._get` sin duplicar ni inventar políticas de reintento.
- **Alternativas consideradas**:
  - *Alternativa 1 (Implementar retroceso exponencial propio en el cliente)*: Descartada expresamente, ya que el servidor API de CRIPTA provee el encabezado y campo `reintentar_en` con el tiempo exacto a esperar; implementar retroceso exponencial violaría el protocolo del servicio y podría esperar más tiempo del necesario o reintentar antes de tiempo.
  - *Alternativa 2 (Consultar siempre por HTTP en cada ejecución)*: Desperdicia el presupuesto de red (Principio V) y falla en modo sin conexión.
  - *Alternativa 3 (Almacenar las llaves en el esqueleto)*: El servicio entrega las llaves en un endpoint independiente (`/llaves`), por lo que el contrato de red exige una consulta separada.

---

## R7. Integración en línea de comandos y control de flujo MVC

- **Decisión**:
  - **Modelo** (`src/modelos/resolubilidad.py`): Contiene la lógica pura de verificación (`VerificadorResolubilidad`, `ResultadoResolubilidad`). No realiza operaciones de E/S, red ni formateo de consola.
  - **Servicios** (`src/servicios/verificador_servicio.py`): Orquesta la carga del esqueleto y las llaves desde la fuente de datos (usando la persistencia validada) y ejecuta la verificación.
  - **Controlador / CLI** (`main.py` y `ControladorJuego`):
    - Si se especifica `--verificar <cripta>`: ejecuta la verificación mediante el servicio, imprime el reporte formateado en `stdout` y finaliza con código 0 si es resoluble, 1 si no es resoluble, o 2 si ocurre error técnico (Clarificación Q1). No instancia la vista ni el bucle de juego.
    - Al iniciar una partida interactiva normal: ejecuta la verificación antes de entrar al juego; imprime el reporte en consola y continúa inmediatamente sin pausas bloqueantes (Clarificación Q5). Si la cripta no es resoluble y no se suministró `--forzar`, no inicia la partida y finaliza con error. Si se incluye `--forzar`, emite advertencia y continúa a la partida.
- **Justificación**: Respeta escrupulosamente el Principio III (MVC y desacoplamiento de vista) y satisface todos los escenarios de CLI (FR-017 a FR-020).
- **Alternativas consideradas**:
  - *Alternativa 1 (Verificar dentro de `Partida.__init__`)*: Acoplaría la inicialización de la simulación del juego a la verificación previa, impidiendo ejecutar `--verificar` sin crear un estado completo de partida.
  - *Alternativa 2 (Verificar dentro de `VistaConsola`)*: Violación directa de MVC al delegar lógica de validación de reglas a la capa de presentación.

---

## R8. Diseño de mediciones en `--bench` y contraste empírico

- **Decisión**:
  - Incorporar en el banco de pruebas (`src/servicios/banco_pruebas.py`) un módulo especializado de medición de resolubilidad (`banco_resolubilidad.py`).
  - Utilizar un generador sintético determinista gobernado por semilla (`random.Random(semilla)`) para crear familias de criptas sintéticas:
    1. **Cripta de gran escala**: Red de salas y salidas comparable a la mayor cripta publicada (~1 000 salas, decenas de puertas) para validar que el tiempo total de verificación es < 200 ms (FR-026, SC-003).
    2. **Escalamiento lineal vs. Alternativa ingenua**: Familias de criptas con cadenas de llaves encadenadas crecientes ($K \in \{10, 25, 50, 100, 500\}$):
       - *Algoritmo lineal propuesto*: Recorrido único con lista de espera por llave y selección con `MonticuloMin`, con costo acotado por $O(|V| + |E| + |K| \log |K|)$.
       - *Algoritmo ingenuo*: Repetición completa del recorrido cada vez que se recolecta una llave $O(|K| \cdot (|V| + |E|))$.
       - Se mide el tiempo medio y se demuestra empíricamente el comportamiento lineal frente a la degradación cuadrática de la alternativa ingenua (SC-004, FR-027).
    3. **Determinismo de ciclos y robustez iterativa**: Medición sobre criptas con ciclo directo `[llave_salida -> llave_salida]`, ciclos múltiples disjuntos, y cadenas profundas de dependencias cíclicas ($\ge 500$ llaves), verificando que la búsqueda en profundidad iterativa con pila propia no sufre desbordamiento de recursión (`sys.getrecursionlimit()`), detecta el ciclo concreto deterministamente y opera en tiempo estrictamente lineal $O(|K| + |E_K|)$.
- **Justificación**: Cumple con el Principio VII de la Constitución (mediciones reproducibles contra alternativas medidas) y con las directivas del enunciado (P2 §6.1, §6.3).
- **Alternativas consideradas**:
  - *Alternativa 1 (Medir solo con criptas publicadas descargadas)*: No permite variar sistemáticamente la longitud de la cadena de llaves ni aislar el factor cuadrático de la solución ingenua.
