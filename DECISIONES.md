# Documento de Decisiones de Diseño — CRIPTA

Una sección por cada problema de §4 del enunciado. Las mediciones de
"Evidencia empírica" se obtuvieron ejecutando `python3 main.py --bench`
(ver `src/servicios/banco_pruebas.py`); los números concretos citados
corresponden a una corrida de referencia y pueden variar unos pocos
porcentos entre máquinas, pero las relaciones de orden entre alternativas
son estables.

---

## 4.1 Agenda de eventos (qué ocurre a continuación)

**Problema.** El bucle principal necesita, decenas de miles de veces por
partida, el evento pendiente con menor `tiempo_siguiente` (y, en caso de
empate, menor número de secuencia). Además debe poder cancelar un evento
cuando su actor muere o un efecto se cancela, y reprogramar un evento
cuando cambia la velocidad de un actor, sin recorrer todos los eventos
pendientes en ninguno de los tres casos.

**Alternativas consideradas.**
1. *Lista ordenada por inserción* (se inserta cada evento en su posición
   correcta con búsqueda lineal). Extraer el mínimo es O(1) (siempre está
   al frente), pero insertar es O(n) y, peor aún, cancelar un evento
   arbitrario exige encontrarlo primero recorriendo la lista: O(n) también.
2. *Montículo binario mínimo* (heap) representado como lista contigua,
   con cada `Evento` guardando su propio índice dentro del arreglo.

La alternativa 1 se descartó porque con "varios cientos de eventos
simultáneos" (enunciado §4.1) y decenas de miles de operaciones por
partida, un costo O(n) por inserción y por cancelación se vuelve el
cuello de botella dominante del bucle principal, justo la operación que
el enunciado señala como crítica.

**Decisión.** `Agenda`/`Evento` (`src/estructuras_datos/agenda.py`): un
montículo binario mínimo clásico sobre una lista, comparando por
`(tiempo, secuencia)` vía `Evento.__lt__`. Cada `Evento` guarda su propio
`indice` dentro del arreglo del montículo, actualizado en cada
intercambio; eso permite que `cancelar(evento)` y `reprogramar(evento,...)`
ubiquen el evento en O(1) y lo reacomoden en O(log n), sin ninguna
búsqueda. Cancelar no borra `tiempo`/`secuencia`: sólo pone `indice = -1`,
de modo que reinsertar el mismo objeto (usado por el pergamino de
retroceso, §4.6) restaura exactamente su posición original en la
simulación.

**Análisis de complejidad.** `insertar`: O(log n). `extraer_minimo`:
O(log n). `cancelar`: O(log n) (posición conocida, sólo hay que
reacomodar). `reprogramar`: O(log n). Ninguna de las cuatro operaciones
críticas recorre la colección completa.

**Evidencia empírica.** `--bench agenda` (n=2000 eventos):
- insertar 2000 eventos: ≈1.5 ms (≈0.0008 ms/operación)
- extraer los 2000 en orden: ≈7.5 ms (≈0.0038 ms/operación)

Ambos crecen de forma coherente con O(log n): log₂(2000) ≈ 11, y el costo
por operación es una pequeña constante multiplicada por esa magnitud, muy
lejos de un costo lineal en n.

**Límites conocidos.** Si la cripta creciera 50 veces (decenas de miles de
eventos simultáneos) el heap sigue siendo apropiado porque log(n) crece
muy lentamente. El punto donde esta decisión dejaría de ser apropiada es
si se necesitara *buscar* un evento por un criterio distinto a su
identidad de objeto (por ejemplo "todos los eventos de un actor dado"):
el heap no ofrece eso en menos de O(n), y haría falta un índice adicional.

---

## 4.2 Precarga anticipada del contenido de salas

**Problema.** Antes de confirmar que el jugador entra a una sala, su
contenido debe estar disponible; cada solicitud de red tarda ~400 ms
independientemente de si pide 1 o 10 salas, y el presupuesto de
solicitudes es limitado y propio de cada cripta (no se puede calcular con
una fórmula fija).

**Alternativas consideradas.**
1. *Precargar toda la cripta al iniciar* (la implementación original que
   se encontró en el código entregado: `ProveedorPrecargado`, ya
   eliminada). Es simple y nunca hay una sala sin contenido cuando se
   necesita, pero gasta solicitudes en salas que tal vez nunca se visiten
   y no tiene forma de respetar un `presupuesto_solicitudes` pequeño (el
   enunciado da un ejemplo de 9 solicitudes para una cripta de 20 salas).
2. *Carga perezosa estricta* (pedir sólo la sala exacta que se necesita,
   justo cuando se necesita). Respeta el presupuesto al mínimo posible,
   pero paga la espera de ~400 ms en casi cada puerta, violando el
   objetivo del enunciado de evitarla.
3. *Carga perezosa con precarga anticipada por lotes*: al pedir el
   contenido de una sala, se completa el mismo lote (hasta 10, igual de
   costoso que pedir 1) con las salas vecinas accesibles más cercanas
   (BFS sobre salidas abiertas) que todavía no se hayan solicitado.

La alternativa 1 se descartó porque no escala con el presupuesto por
cripta (es la razón de ser de la reescritura de esta parte del proyecto).
La alternativa 2 se descartó porque no amortiza el costo fijo de ~400 ms
por solicitud: pedir 1 sala o 10 cuesta prácticamente lo mismo, así que
desperdiciarlo pidiendo de una es ineficiente en tiempo real aunque sea
"óptimo" en solicitudes.

**Decisión.** `ProveedorRed` (`src/servicios/proveedor_red.py`):
`asegurar_disponible(id_sala)` sólo solicita red si la sala no está ya
disponible; cuando solicita, construye un lote de hasta 10 ids mediante
un recorrido en anchura (BFS) desde la sala pedida, siguiendo únicamente
salidas abiertas, y excluyendo salas ya solicitadas o ya resueltas. El
contenido de salas devueltas se incorpora en un orden determinista fijo
(el orden en que se construyó el lote), nunca en el orden en que
"llegaron" las respuestas, satisfaciendo el requisito de determinismo de
red del §2.4.

**Análisis de complejidad.** Construir un lote es O(k) donde k ≤ 10 es el
tamaño del lote (se explora la vecindad hasta agotar el cupo o quedarse
sin vecinos nuevos), independientemente del tamaño total de la cripta.
Verificar si una sala ya fue solicitada es O(1) amortizado (tabla hash
propia, `TablaHash`).

**Evidencia empírica.** `tests/test_servicios.py::test_precarga_anticipada_por_lotes_sin_repetir`
y `test_avanzar_mas_alla_del_horizonte_pide_otro_lote` verifican, con un
`FuenteFalsa` que cuenta solicitudes, que una cripta de 7 salas conectadas
en línea se resuelve con un único lote (y que una sala fuera de ese
horizonte dispara exactamente un lote adicional, no una solicitud por
sala). No se requirió `--bench` aquí porque la métrica relevante es
"número de solicitudes", no tiempo, y ya se mide con precisión en las
pruebas unitarias.

**Límites conocidos.** Si las salidas abiertas forman una vecindad muy
ramificada (muchas puertas abiertas desde la sala actual), el BFS puede
agotar el lote de 10 con salas que resultan estar en la dirección
equivocada a la que el jugador finalmente va. No se implementó
priorización por dirección de movimiento reciente; sería la siguiente
mejora si las métricas de un caso real lo justificaran.

---

## 4.3 Resolución de referencias del catálogo

**Problema.** El contenido de una sala referencia tipos de catálogo por
id (`"tipo": "ent_rata_gigante"`); antes de simular o mostrar la entidad
hace falta la ficha completa. Los ids se descubren sin orden, se repiten
entre salas y entre criptas, y pedir cada uno por separado desperdicia el
presupuesto.

**Alternativas consideradas.**
1. Pedir cada id por separado tan pronto se descubre (`GET /catalogo/<id>`).
2. Acumular todos los ids nuevos descubiertos al resolver un lote de
   contenido y pedirlos juntos, en sub-lotes de hasta 10, consultando
   primero la caché en memoria.

La alternativa 1 se descartó explícitamente por el propio enunciado
(§3.3: "tarda aproximadamente lo mismo [pedir una] que solicitar un lote
completo. Su uso repetido normalmente desperdicia presupuesto").

**Decisión.** `ProveedorRed._resolver_catalogo` (misma clase que §4.2):
tras resolver el contenido crudo de un lote de salas, se recolectan los
ids de catálogo referenciados (enemigos, objetos, trampas) sin
duplicados, usando una `TablaHash` como conjunto de "ya vistos" (nunca un
`set`/`dict` de Python). Se consulta primero `CacheFichas` (§4.4); sólo
los que faltan se piden a la red, en sub-lotes de hasta 10.

**Análisis de complejidad.** Recolectar referencias sin duplicados: O(m)
donde m es el número de referencias en el lote, con verificación de
duplicado O(1) amortizado por la tabla hash. Resolver m ids contra la
caché: O(m) búsquedas O(1) amortizado cada una. Las solicitudes de red
necesarias son ⌈(ids faltantes)/10⌉, el mínimo posible dado el límite de
lote del servicio.

**Evidencia empírica.** `test_catalogo_incompleto_se_reporta` y
`test_fijar_y_liberar_delegan_en_la_cache` cubren la resolución; el
`--bench cache_fichas` (ver §4.4) mide el costo de la búsqueda en caché
que esta resolución usa intensivamente: 2000 búsquedas con acierto en
≈0.6 ms, es decir, insignificante frente a una solicitud de red (~400 ms)
incluso para miles de resoluciones.

**Límites conocidos.** Si una sola sala referenciara más de 10 tipos de
catálogo nuevos y distintos (poco realista dado el tamaño típico de una
sala), igual se resolvería correctamente en varios sub-lotes, sólo que
sin poder amortizarlos junto con el contenido de otras salas del mismo
lote de §4.2.

---

## 4.4 Caché persistente de fichas de catálogo

**Problema.** Las fichas resueltas deben reutilizarse: en memoria hasta
un tope (`--cache-size`, 25 por defecto), y en disco indefinidamente
mientras la versión del catálogo siga vigente. Las búsquedas en caché son
mucho más frecuentes que las inserciones, así que su costo importa más
que el de insertar. Una ficha "en uso" (enemigo vivo, objeto en
inventario o en el suelo de la sala actual, trampa de la sala actual) no
puede desalojarse mientras lo esté.

**Alternativas consideradas.**
1. *Lista con búsqueda lineal* para saber si un id está en caché: simple,
   pero cada "¿está en caché?" es O(n) justo en la operación más
   frecuente del subsistema (enunciado §4.4: "Averiguar si una ficha está
   en caché es una de las operaciones más frecuentes").
2. *Tabla hash propia como índice + lista doblemente enlazada para el
   orden de uso* (política LRU): búsqueda O(1) amortizada, y mover una
   entrada "al frente" (más recientemente usada) o desalojar la del fondo
   es O(1) con referencia directa al nodo.

La alternativa 1 se descartó precisamente porque degrada la operación más
frecuente del subsistema a O(n), mientras que la 2 la deja en O(1)
amortizado sin sacrificar nada en las demás operaciones.

**Decisión.** `CacheFichas` (`src/estructuras_datos/cache_fichas.py`):
una `TablaHash` (id → nodo) para búsqueda O(1) amortizada, apuntando a
nodos de una `ListaDoble` que mantiene el orden de uso reciente (cabeza =
más reciente). `fijar`/`liberar` cuentan referencias por id en una
segunda `TablaHash`; al desalojar, se recorre la lista desde el nodo más
antiguo (`nodos_inversos`) y se salta cualquier id todavía en uso,
desalojando la primera que no lo esté. Persistencia en
`src/servicios/cache_persistente.py`: se serializa a JSON en el orden de
uso reciente (así una recarga con capacidad menor conserva las más
relevantes primero) junto con la versión del catálogo vigente al
guardar; al cargar, si la versión no coincide, se descarta por completo
en vez de arriesgar fichas obsoletas.

**Análisis de complejidad.** `obtener`/`poner`: O(1) amortizado (tabla
hash + mover un nodo ya conocido al frente de la lista). Desalojar: en el
peor caso recorre todas las entradas en uso antes de encontrar una
desalojable, O(k) donde k es el número de entradas protegidas — pero eso
sólo ocurre cuando casi toda la caché está en uso, que es exactamente la
situación en que no hay nada mejor que hacer.

**Evidencia empírica.** `--bench cache_fichas` (n=2000 inserciones,
capacidad 200): poner 2000 fichas (con sus desalojos) ≈20.8 ms;
2000 búsquedas con acierto garantizado ≈0.6 ms. Es decir, una búsqueda
con acierto cuesta del orden de 0.0003 ms, frente a ~400 ms de una
solicitud de red: incluso miles de búsquedas por partida son
insignificantes frente a evitar una sola solicitud innecesaria.
`tests/test_cache_fichas.py::test_fichas_en_uso_no_se_desalojan` y
`test_todas_en_uso_no_desaloja_ninguna` verifican empíricamente (no sólo
por inspección) que una ficha fijada sobrevive mientras otra, más
antigua pero no protegida, es la que se desaloja en su lugar.

**Límites conocidos.** Si `--cache-size` es menor que la cantidad de
fichas distintas que un solo lote de contenido puede necesitar fijar de
inmediato, puede ocurrir que una ficha recién insertada (todavía no
fijada por el modelo, porque `fijar` se llama después de resolver todo el
lote) sea la única candidata desalojable y se pierda de la caché antes de
usarse por primera vez; el programa sigue siendo correcto porque
`ProveedorRed.ficha()` puede recuperarla por su cuenta, pero esa
recuperación ya no es gratuita. Mitigación documentada, no implementada:
fijar cada ficha apenas se resuelve, antes de incorporar el contenido
completo del lote.

---

## 4.5 Inventario

**Problema.** El inventario debe recorrerse hacia adelante y atrás desde
una posición "actual", soltar el objeto que se está viendo en cualquier
posición sin que el costo dependa de dónde esté, mover un objeto
equipado al frente del orden real, y mostrar vistas ordenadas (por peso,
valor o nombre) sin alterar ese orden real.

**Alternativas consideradas.**
1. *Lista contigua con índice "actual"*: recorrer es O(1), pero soltar un
   elemento que no está al final implica desplazar todos los posteriores,
   O(n), justo lo que el enunciado pide evitar ("sin que el costo dependa
   de la posición").
2. *Lista doblemente enlazada con un puntero al nodo "actual"*: recorrer
   hacia delante/atrás es O(1) siguiendo enlaces; soltar el nodo actual
   (en cualquier posición) es O(1) porque sólo hace falta reconectar sus
   dos vecinos, sin desplazar nada más.

La alternativa 1 se descartó porque viola directamente el requisito de
costo independiente de la posición para soltar un objeto.

**Decisión.** `Inventario` (`src/estructuras_datos/inventario.py`) sobre
`ListaDoble` (`src/estructuras_datos/lista_doble.py`): cada objeto es un
`NodoLista`; `avanzar()`/`retroceder()` siguen `siguiente`/`anterior`;
`remover_nodo()`/`soltar_actual()` desenlazan el nodo actual en O(1) y
reajustan el cursor al vecino más cercano. `equipar` usa
`mover_al_frente`, también O(1) con el nodo ya conocido. Las vistas
ordenadas (`VistaConsola.mostrar_inventario_ordenado`) construyen una
lista aparte con `estructuras_datos.ordenamiento.ordenar` (§4.9) sobre
`list(inventario)`, sin tocar la lista enlazada real ni su cursor.

**Análisis de complejidad.** `avanzar`/`retroceder`: O(1). `soltar_actual`
/`remover_nodo`: O(1), independiente de la posición. `equipar`: O(1).
Vista ordenada: O(n log n) o O(n) según el tamaño (§4.9), pero sobre una
copia, nunca sobre la estructura real.

**Evidencia empírica.** `--bench inventario` (n=2000): agregar 2000
objetos ≈4.9–7.2 ms (~0.0025–0.0036 ms/op, dominado por la asignación de
cada nodo, no por ningún recorrido); recorrer los 2000 de principio a fin
≈0.2–0.3 ms totales (~0.0001 ms/op), consistente con un costo verdaderamente
O(1) por paso.

**Límites conocidos.** La lista doblemente enlazada no ofrece acceso
aleatorio por índice en O(1) (por ejemplo "ir directo a la posición 37");
el inventario del juego nunca lo necesita porque toda interacción parte
del objeto "actual", pero una interfaz que quisiera saltar directo a una
posición arbitraria tendría que recorrerla, O(posición).

---

## 4.6 Historial reversible y pergamino de retroceso

**Problema.** Un pergamino debe revertir exactamente la última acción del
jugador y todo lo ocurrido después de ella (acciones enemigas, efectos,
reloj, eventos, rastro, vida, inventario, puertas, trampas), sin guardar
copias completas del estado, hasta 5 veces hacia atrás, y sin que esa
reversión afecte la cantidad de pergaminos ni el estado de la caché.

**Alternativas consideradas.**
1. *Copias completas del estado* (snapshot de toda la partida antes de
   cada acción). Explícitamente prohibido por el enunciado, y además
   costoso en memoria y tiempo proporcional al tamaño completo del
   estado, no al tamaño real del cambio.
2. *Registro de deltas con clausura inversa*: cada mutación puntual
   (cambiar un atributo, programar/cancelar/reprogramar un evento,
   insertar/remover de una lista) se acompaña, en el momento en que
   ocurre, de una pequeña función que sabe revertir exactamente ese
   cambio. Un intervalo completo es la lista de esas funciones, en el
   orden en que ocurrieron; deshacer el intervalo significa llamarlas en
   orden inverso.

La alternativa 1 está prohibida por el enunciado y además escala mal: su
costo es O(tamaño total del estado) sin importar qué tan pequeño sea el
cambio real. La 2 cuesta sólo proporcional al número de cambios
realmente ocurridos en ese intervalo.

**Decisión.** `Partida` (`src/modelos/partida.py`) mantiene
`self._historial` (hasta 5 intervalos) y `self._intervalo_actual` (el que
se está construyendo). Helpers genéricos —`_set_atributo`,
`_lista_append`/`_lista_remove`/`_lista_pop`, `_programar_en`,
`_cancelar_en`, `_reprogramar`— envuelven cada mutación real y registran,
vía `_registrar`, una clausura que la invierte (capturando el valor
anterior o el objeto removido por cierre léxico, nunca copiando el
estado completo). `_confirmar_intervalo()`, llamado al cerrar cada acción
del jugador, archiva el intervalo completo y descarta el más antiguo si
se supera el límite de 5. `_usar_pergamino()` saca el último intervalo y
reproduce sus clausuras en orden inverso. Dos exclusiones explícitas del
enunciado se respetan por construcción: el descuento del pergamino usado
nunca pasa por `_registrar` (ocurre después de que el reemplazo termina,
con la grabación momentáneamente desactivada), y recoger/soltar un objeto
de clase `pergamino_retroceso` tampoco se registra, en ningún sentido.
Los cambios en la caché de fichas (`fijar`/`liberar`) tampoco se
registran nunca, porque el enunciado los declara "estado de
infraestructura".

**Análisis de complejidad.** Registrar una mutación: O(1) (una clausura
más en una lista). Cerrar un intervalo: O(1). Deshacer un intervalo: O(k)
donde k es el número de mutaciones reales ocurridas en ese intervalo —
nunca el tamaño del estado completo de la partida. El historial nunca
excede 5 intervalos simultáneos, así que su huella de memoria está
acotada independientemente de cuánto dure la partida.

**Evidencia empírica.** `--bench historial`: ejecutar 200 acciones
`esperar` (acumulando hasta el tope de 5 intervalos en el historial)
≈1.2–1.4 ms en total; deshacer los 5 intervalos acumulados ≈0.045–0.052
ms en total, es decir, revertir una acción completa (incluida toda la
simulación posterior hasta la siguiente decisión del jugador) cuesta una
fracción de milisegundo, muy por debajo del presupuesto de 20 ms de §5.2.
`tests/test_partida.py::PruebasPergamino` verifica, con partidas reales,
que un movimiento se revierte exactamente (el jugador vuelve a la sala
anterior), que soltar un objeto se revierte reinsertándolo en su posición
exacta del inventario, y que recoger un segundo pergamino no se "recupera"
al deshacer el intervalo en que se recogió el primero (la exclusión del
§2.11 en ambos sentidos).

**Límites conocidos.** Esta decisión asume que el número de mutaciones
por intervalo es pequeño (decenas, no miles): si una sola acción del
jugador disparara una cascada de miles de eventos encadenados antes de la
siguiente decisión, deshacer ese intervalo seguiría siendo correcto pero
proporcional a esa cascada, no instantáneo. El historial tampoco
sobrevive guardar/cargar la partida (§4.10): es, por diseño, estado de
una sesión en curso, no estado persistente del juego.

---

## 4.7 El rastro del jugador

**Problema.** Cada sala recuerda cuándo estuvo el jugador por última vez.
Un rastreador debe decidir su movimiento examinando únicamente sus salas
vecinas, con un costo proporcional al número de salidas de su sala (no al
tamaño de la cripta ni al recorrido del jugador), ignorando rastros de
400 o más unidades de antigüedad.

**Alternativas consideradas.**
1. *Mantener una cola/lista global de salas visitadas recientemente* y
   buscar en ella cuál vecina aparece más reciente. Requeriría recorrer
   una estructura potencialmente del tamaño de toda la cripta, o indexar
   por sala con una estructura prohibida (`dict`) para hacerlo O(1).
2. *Guardar el rastro directamente como un atributo de cada `Sala`*
   (`sala.rastro`, un entero o `None`), y que el rastreador sólo consulte
   sus hasta 4 vecinas directas (ya referenciadas por `sala.salidas`, sin
   ninguna búsqueda adicional).

La alternativa 1 se descartó porque, para cumplir "proporcional a las
salidas de la sala, no al tamaño de la cripta", necesitaría de todas
formas acceso O(1) por sala, que es exactamente lo que ya ofrece la
alternativa 2 sin estructura adicional.

**Decisión.** `Sala.rastro` (`src/modelos/entidades.py`) es un entero o
`None`, actualizado directamente al cerrar cada acción del jugador
(`Partida._cerrar_accion`, vía `_set_atributo` para que sea reversible,
§4.6). `Partida._vecino_con_rastro_fresco` recorre únicamente las hasta 4
salidas de la sala del enemigo (ya están ahí, en `sala.salidas`), filtra
las cerradas, descarta cualquier rastro con 400 o más unidades de
antigüedad respecto al reloj virtual actual, y elige el más fresco
desempatando por menor id de sala. No se eliminan activamente los rastros
caducados: se detecta su caducidad al consultarlos, porque un rastro
vencido no cuesta nada mantener (es un entero) y revisarlo cuesta lo
mismo que no tenerlo.

**Análisis de complejidad.** O(1) para actualizar el rastro de una sala.
O(d) para la decisión de un rastreador, donde d ≤ 4 es el número de
salidas de su sala — una constante acotada, independiente del tamaño de
la cripta. Con r rastreadores actuando en un ciclo, el trabajo total es
O(r), lineal en la cantidad de enemigos que realmente actúan, no en el
tamaño de la cripta.

**Evidencia empírica.**
`tests/test_partida.py::PruebasEnemigos::test_rastro_fresco`,
`test_rastro_se_refresca_con_cada_accion` y
`PruebasEnemigos::test_guardian_errante_y_rastreador` verifican el
comportamiento exacto (elección del vecino más fresco, desempate por id,
caducidad a los 400). No se requiere `--bench` adicional porque el costo
ya es una constante pequeña por diseño (d ≤ 4) y no depende de ningún
parámetro que valga la pena medir a escala.

**Límites conocidos.** Si el modelo del juego permitiera más de 4
direcciones (por ejemplo salidas diagonales), la constante d crecería
pero seguiría siendo acotada por el número de salidas de una sala, no por
el tamaño de la cripta; la decisión sigue siendo apropiada.

---

## 4.8 Bitácora en pantalla

**Problema.** Mostrar sólo los últimos 20 mensajes, con consumo de
memoria constante durante toda la partida, y sin desplazar físicamente
los 19 mensajes anteriores al agregar uno nuevo.

**Alternativas consideradas.**
1. *Lista de Python que se recorta* (`append` y luego `lista[-20:]` o
   `pop(0)`). `pop(0)` desplaza todos los elementos restantes, O(n) por
   inserción; mantener un slice nuevo en cada mensaje también copia hasta
   20 elementos cada vez.
2. *Buffer circular de tamaño fijo* sobre una lista preasignada de 20
   casillas, con un índice de inicio que avanza módulo 20.

La alternativa 1 se descartó porque "agregar un mensaje no debe implicar
desplazar físicamente los 19 anteriores" es un requisito explícito del
enunciado, y `pop(0)`/recortar hace exactamente eso.

**Decisión.** `BufferCircular` (`src/estructuras_datos/buffer_circular.py`,
ya presente en el código entregado y verificada): una lista de tamaño
fijo (`capacidad=20`) reservada una sola vez; `agregar` escribe en la
posición `(inicio + cantidad) % capacidad` mientras no esté llena, y
después sobrescribe la posición más antigua avanzando `inicio`. Ningún
mensaje mueve a los demás.

**Análisis de complejidad.** `agregar`: O(1), siempre — nunca copia ni
desplaza nada. Memoria: O(1) respecto a la duración de la partida (20
casillas fijas, nunca crece).

**Evidencia empírica.** `tests/test_buffer_circular.py::test_memoria_constante`
verifica exactamente esto: tras agregar miles de mensajes, la lista
interna sigue teniendo 20 casillas. No se requiere `--bench`: el costo ya
es una constante de un solo acceso a lista por índice.

**Límites conocidos.** Ninguno relevante a la escala del proyecto: al ser
O(1) y de memoria fija, esta decisión es apropiada para cualquier
duración de partida.

---

## 4.9 Ordenamiento

**Problema.** El programa ordena en varios contextos (tabla de puntajes,
vistas del inventario, índice del archivo de guardado, listas auxiliares
del catálogo). Debe haber al menos dos algoritmos con características
distintas, y el programa debe elegir automáticamente cuál usar según
propiedades medibles de los datos, sin usar `list.sort()`/`sorted()`.

**Alternativas consideradas.**
1. *Usar un solo algoritmo siempre* (por ejemplo, sólo mezcla): correcto
   y O(n log n) siempre, pero desperdicia la ventaja de los casos
   pequeños o casi ordenados, donde un algoritmo más simple es más
   rápido en la práctica.
2. *Dos algoritmos con selección automática*: inserción (estable, O(n²)
   peor caso pero O(n) real cuando la entrada ya está casi ordenada) y
   mezcla (estable, O(n log n) siempre). Esta es justamente la sección
   donde el enunciado exige medir directamente la alternativa descartada
   para una entrada grande y desordenada.

**Decisión.** `src/estructuras_datos/ordenamiento.py`: `insercion()` y
`mezcla()` como funciones independientes, y `ordenar()` como selector:
usa inserción si `len(lista) <= 24` o si la proporción de pares
adyacentes fuera de orden (una medida O(n), no una cuenta completa de
inversiones que sería O(n log n) y anularía la ventaja) es ≤ 15%; usa
mezcla en cualquier otro caso. Se aplica en `puntajes.mejores` (orden
descendente por puntaje), `VistaConsola.mostrar_inventario_ordenado`
(orden alfabético sin alterar el inventario real) y
`guardado.guardar_binario` (orden por id de sala, necesario para que el
índice de acceso aleatorio del §4.10 permita una futura búsqueda binaria
sobre él).

**Análisis de complejidad.** `insercion`: O(n²) peor caso, O(n+d) con d el
número de inversiones reales (óptimo cuando d es pequeño). `mezcla`:
O(n log n) siempre, independientemente del orden de entrada. `ordenar`:
el costo de decidir es O(n) (medir el desorden), más el costo del
algoritmo elegido.

**Evidencia empírica — incluye la alternativa descartada, medida
directamente (`--bench ordenamiento`, n=5000, datos aleatorios):**
- `insercion` sobre datos aleatorios: ≈873–982 ms
- `mezcla` sobre los mismos datos: ≈15.6–16.3 ms
- `ordenar` (selector automático) sobre los mismos datos aleatorios:
  ≈15.7–16.4 ms (elige mezcla correctamente)
- `ordenar` sobre una lista de 5000 elementos casi ordenada (un solo par
  adyacente fuera de lugar): ≈1.4 ms (elige inserción correctamente)

La diferencia entre inserción y mezcla sobre la misma entrada
desordenada es de casi dos órdenes de magnitud (≈56×), exactamente el
tipo de evidencia que el enunciado pide para no limitarse a justificar
con notación O() sin medir. `tests/test_ordenamiento.py` verifica además
que el selector realmente elige cada algoritmo en las condiciones
esperadas, no sólo que ambos ordenan correctamente.

**Límites conocidos.** El umbral de tamaño (24) y de desorden (15%) se
fijaron con datos sintéticos; una carga de trabajo real con un perfil muy
distinto (por ejemplo, datos siempre casi ordenados pero de miles de
elementos) podría beneficiarse de umbrales distintos. La medida de
desorden usada (pares adyacentes fuera de orden) es O(n) pero no detecta
todas las formas de "casi ordenado" (por ejemplo, una lista invertida
completa tiene proporción de desorden cercana a 1 aunque esté perfectamente
ordenada "al revés"); se aceptó esa imprecisión porque medir inversiones
exactas costaría tanto como ordenar.

---

## 4.10 Guardado binario de la partida

**Problema.** Guardar el estado en un formato binario propio, poder
recuperar una sola sala sin leer el archivo completo, detectar
incompatibilidad de versión, y comparar contra JSON en tamaño y tiempo de
carga.

**Alternativas consideradas.**
1. *Un único volcado binario secuencial* (escribir cada sala una tras
   otra y leer el archivo completo para reconstruir el estado). Cumple
   "formato propio" pero no "recuperar una sala específica sin leer el
   archivo completo": siempre habría que decodificar las salas
   anteriores para saber dónde empieza la que se busca.
2. *Encabezado + índice de desplazamientos (id de sala → posición y
   longitud en bytes) + registros de sala*: permite, tras leer sólo el
   índice (proporcional al número de salas, no a su contenido), un único
   `seek()`+`read()` de exactamente los bytes de la sala pedida.

La alternativa 1 se descartó porque no cumple el requisito explícito de
acceso aleatorio por sala, que es justamente la razón de pedir un formato
binario propio en vez de, por ejemplo, un volcado JSON secuencial.

**Decisión.** `src/servicios/guardado.py`: formato binario con
`struct` (big-endian): firma `CRPT`, versión del formato, encabezado de
tamaño variable (cripta, semilla, reloj, jugador, inventario), y un
índice de `(id_sala, desplazamiento, longitud)` de tamaño fijo por
entrada, ordenado por id con el ordenamiento propio del §4.9. Para leer
una sola sala (`leer_sala_binaria`), sólo se decodifica el encabezado y
el índice; luego un único `seek(desplazamiento)` + `read(longitud)`
obtiene exactamente esa sala, sin tocar ninguna otra. La incompatibilidad
de versión se detecta en dos niveles: la firma y versión del *formato*
binario (`FORMATO_VERSION`) al leer el preámbulo, y la versión de la
*cripta* (`version_compatible`) al restaurar una partida sobre una cripta
concreta. Se implementó también un volcado JSON equivalente
(`guardar_json`/`cargar_json`) exclusivamente para la comparación pedida.

**Análisis de complejidad.** Guardar: O(n) en el número total de salas
guardadas (cada una se serializa una vez). Leer la partida completa:
O(n). Leer una sola sala: O(1) para ubicarla en el índice (una vez leído,
que es O(número de salas), no O(contenido de todas las salas)) más
O(tamaño de esa sala) para decodificarla — nunca O(tamaño del archivo
completo).

**Evidencia empírica.** `--bench guardado` (partida pequeña de prueba):
guardar en binario ≈0.18–0.20 ms vs JSON ≈0.18–0.23 ms (comparables para
un estado tan pequeño); el tamaño en disco sí difiere claramente: 97
bytes en binario contra 357 en JSON (≈3.7× más compacto), porque el
formato binario no repite nombres de campos ni usa comillas/separadores
de texto. `tests/test_guardado.py::test_acceso_aleatorio_a_una_sola_sala`
verifica, leyendo directamente con `leer_sala_binaria`, que se recupera
el contenido exacto de una sala sin pasar por `cargar_binario` (que sí
decodificaría todas). `test_version_incompatible_se_rechaza` verifica que
cargar un guardado de una cripta distinta se rechaza explícitamente en
vez de restaurar silenciosamente un estado incorrecto.

**Límites conocidos (documentados explícitamente, por alcance).** No se
persisten: el historial de retroceso del §4.6 (es estado de una sesión en
curso, y además el propio enunciado excluye del alcance del retroceso
cualquier estado de infraestructura) ni los temporizadores exactos de
efectos transitorios en curso (veneno, cambio de velocidad, antorcha,
cierre automático de puertas, rearme de trampas): al cargar, cualquier
enemigo que haya quedado activo se reprograma con un turno nuevo, pero un
efecto transitorio del jugador no se restaura. Esto es una simplificación
deliberada, no un error: guardar/cargar reconstruye fielmente el estado
"estructural" del juego (mapa descubierto, inventario, vida, posición,
enemigos y su vida) pero no pretende ser un volcado binario exacto de
cada temporizador en vuelo.

---

## 4.11 Bitácora de partida y reproducción

**Problema.** Cada acción del jugador se registra en un archivo de sólo
anexado; el encabezado identifica cripta, versión de cripta, versión de
catálogo y semilla; `--replay` debe reproducir la partida completa sin
interacción, y debe rechazar una reproducción que no pueda garantizarse
fiel en vez de continuar silenciosamente contra datos distintos.

**Alternativas consideradas.**
1. *Guardar snapshots periódicos del estado* en vez de un registro de
   acciones. Permitiría "saltar" a un punto intermedio más rápido, pero
   viola el espíritu de append-only (habría que decidir cada cuánto
   snapshot-ear y reescribir estructura) y duplica el problema que el
   §4.6 ya resuelve con deltas: el estado completo no es la unidad
   correcta de registro en este proyecto.
2. *Registro de sólo las acciones del jugador, en JSON Lines*, con un
   encabezado de identificación, reproducidas contra `Partida.ejecutar()`
   tal cual se recibieron. Como toda la aleatoriedad pasa por
   `random.Random(semilla)` (§2.6), la misma cripta + semilla + secuencia
   de acciones basta para llegar exactamente al mismo estado.

La alternativa 1 se descartó porque el proyecto ya tiene, en el §4.6, la
infraestructura correcta para razonar sobre "cambios desde un punto",
y duplicarla en un formato de snapshots sería tanto más complejo como
contrario a la idea de bitácora de sólo anexado.

**Decisión.** `src/servicios/bitacora.py`: `Bitacora.iniciar` escribe una
primera línea JSON con `cripta_id`, `version_cripta`, `version_catalogo`
y `semilla`; cada acción ejecutada se anexa con `registrar`, abriendo el
archivo en modo `"a"` (apertura y escritura son siempre adición, nunca
reescritura). `reproducir(ruta, cripta, proveedor, version_catalogo)`
reconstruye una `Partida` nueva con la semilla registrada y ejecuta cada
acción leída, en orden, contra `Partida.ejecutar()` — exactamente el
mismo camino que usaría un jugador real, así que no hay dos
implementaciones de las reglas del juego que puedan desincronizarse.
`verificar_version` compara cripta, versión de cripta y, si se conoce,
versión de catálogo, y lanza un error explícito ante cualquier
incompatibilidad en vez de continuar con datos distintos.

**Análisis de complejidad.** Registrar una acción: O(1) (una línea más,
con `flush()` inmediato para que "append-only" sea real incluso si el
programa termina abruptamente). Reproducir: O(a) donde a es el número de
acciones registradas, cada una ejecutada con el mismo costo que tendría
en una partida interactiva real.

**Evidencia empírica.** `tests/test_bitacora.py::test_reproducir_llega_al_mismo_estado`
verifica, jugando una partida real y luego reproduciendo su bitácora
contra una cripta reconstruida desde cero, que la sala, el tamaño del
inventario, el reloj virtual y el contador de acciones coinciden
exactamente. `test_es_append_only` verifica que reabrir la bitácora y
seguir escribiendo conserva lo anterior. `tests/test_main.py::test_replay_reproduce_la_bitacora_grabada`
ejercita el camino completo `--replay` de `main.py`, incluyendo el modo
`--offline`. No se requirió medir tiempos aquí porque la métrica que
exige el enunciado es la fidelidad de la reproducción, no su velocidad.

**Límites conocidos.** Una partida retomada con `--cargar` y luego
continuada escribe una bitácora *nueva* cuyo encabezado no captura que
partió de un guardado (sólo cripta/semilla): reproducir esa bitácora por
sí sola, sin antes cargar el mismo guardado, no reconstruye fielmente la
sesión completa. Documentado como alcance no cubierto: la combinación
"cargar una partida y luego reproducir su continuación de forma
autocontenida" no forma parte de este entregable.

---

## Nota transversal: cumplimiento de §7

Ningún problema de §4 se resolvió con `dict` como índice, caché o tabla
de búsqueda: `TablaHash` (propia) cumple ese rol en `ProveedorRed`,
`CacheFichas`, `Cripta` y en los conjuntos de "ya visto" del §4.2/§4.3.
`list` se usa únicamente como almacenamiento contiguo de bajo nivel
(el arreglo interno del montículo de `Agenda`, el buffer fijo de
`BufferCircular`, listas temporales de resultados), nunca como índice o
caché. Las fichas de prueba en `tests/utilidades.py` sí usan `dict`/`set`
libremente porque son datos de prueba, no la estructura que resuelve un
problema evaluado.


---

# Segunda parte — Terreno y cazador

Secciones de los problemas de P2 §5 que atiende la capacidad
[001-terreno-cazador](specs/001-terreno-cazador/spec.md). Cada una sigue la
estructura de P1 §8 y enlaza a su especificación y a su plan
([plan.md](specs/001-terreno-cazador/plan.md),
[research.md](specs/001-terreno-cazador/research.md)). Las mediciones son de
una corrida de `python main.py --bench` en el equipo local (Windows, Python
3.14). Los tiempos varían entre máquinas; los conteos de salas examinadas,
búsquedas y reutilizaciones son deterministas por semilla.

---

## P2 5.1 La ruta más barata del cazador

**Problema.** En cada turno, un cazador necesita el costo mínimo `d` desde su
sala hasta la del jugador por puertas abiertas en ese instante, y dar un paso
por una ruta de costo `d` con el desempate de la vecina de menor id (FR-011 a
FR-015). Los costos no son uniformes, así que contar salas no sirve. En la
prueba de ciclo de `--bench` (30 cazadores, 150 acciones del jugador) hubo
5280 decisiones de cazador: unas 35 por acción del jugador. Es la operación
más frecuente de la capacidad.

**Alternativas consideradas.**
1. *Escoger la sala pendiente más barata con una lista y búsqueda lineal*,
   O(k) por extracción. Descartada por medición: con 10 000 operaciones tarda
   109 ms, frente a 9,8 ms del montículo (escenario `cola_*`).
2. *Una búsqueda individual desde cada cazador*, acotada por su rango, que
   propaga el primer paso de menor id (la estrategia de explorar hacia afuera
   y cortar la rama que supera el rango que propuso el grupo). Implementada y
   medida como alternativa.
3. *Una búsqueda compartida desde el jugador, siempre hasta el mayor rango
   activo.* Descartada en `/speckit-analyze` (hallazgo H1) antes de
   implementarla: hace pagar a un cazador de rango pequeño la región del
   cazador de rango mayor, lo que contradice FR-030.
4. *Búsqueda compartida incremental* (decisión final, ver abajo).

**Decisión.** Estructuras confirmadas por el grupo en el plan:
- `MonticuloMin` (`src/estructuras_datos/monticulo.py`): montículo binario de
  mínimos propio con **eliminación perezosa**. No hay «disminuir clave»: si
  una sala mejora, se inserta otra entrada, y al extraer se descarta la
  entrada de una sala ya asentada o cuyo costo no coincide con la distancia
  registrada. `minimo()` permite pausar sin extraer.
- `RegistroBusqueda` (`src/estructuras_datos/registro_busqueda.py`): listas
  indexadas por un índice compacto de sala con marca de generación. Empezar
  una búsqueda cuesta O(1) y no se limpia ninguna posición, así que solo se
  tocan las salas examinadas (FR-030). Sin `dict`, `set` ni hash.
- `BuscadorRutas` (`src/modelos/rutas.py`) y `DecisorCazadores`
  (`src/modelos/cazador.py`). **Modo por defecto: compartido incremental.**
  Una búsqueda desde la sala del jugador se expande solo hasta el rango del
  cazador que decide y queda en pausa (`extender_hasta`). Un cazador de rango
  mayor la retoma sin repetir trabajo. Cada cazador decide en O(4) con la
  clave D4 `(costo + dist(v), id(v), costo, dirección)`. Por la simetría de
  los costos (FR-002), `dist(v)` hasta el jugador es la misma distancia que
  calcula la búsqueda desde el jugador.

¿Coincide con el `plan.md` original? En parte. El plan original decía
«compartido desde el jugador hasta el mayor rango». `/speckit-analyze`
(hallazgo H1) lo cambió a «incremental» antes de escribir código, y la
medición final confirma ese plan corregido: no hubo cambios durante la
implementación.

**Análisis de complejidad.** Con `R` salas asentadas y hasta 4 salidas por
sala: búsqueda O(R log R), con a lo sumo `1 + 4R` entradas en el montículo
por la eliminación perezosa. Decisión local: O(4). Extender la búsqueda solo
procesa las salas nuevas. La memoria por búsqueda es proporcional a la región
examinada; las listas del registro, de tamaño n, se crean una sola vez por
cripta.

**Evidencia empírica** (`[cazador_decision]`, `[escala]`, `[cola_prioridad]`;
cripta sintética de 1600 salas):

| Escenario | Salas examinadas por decisión | ms por decisión |
|---|---|---|
| 1 cazador, rango 300, compartido / individual | 51 / 40 | 0,10 / 0,07 |
| 1 cazador, rango 5000, compartido / individual | 1600 / 636 | 4,27 / 1,44 |
| 30 cazadores, rango 5000, compartido sin reutilizar / individual | 1600 / 495 | 4,22 / 1,09 |
| **30 cazadores, compartido incremental con reutilización (ciclo)** | **53** | **0,135** |
| Escala x1 / x10, misma región en rango (compartido) | 40 / 40 | 0,057 / 0,051 |
| Escala x1 / x10 (individual) | 5 / 5 | 0,004 / 0,004 |

- **SC-004 (FR-030):** con la cripta 10 veces más grande y la misma región
  dentro del rango, el número de salas examinadas es exactamente el mismo
  (`tests/test_rendimiento_cazador.py`, en ambos modos y con rangos
  mezclados).
- **Correctitud:** 0 diferencias frente a la referencia teórica
  (`tests/referencia_cazador.py`) en más de 50 000 decisiones exhaustivas y
  10 400 decisiones aleatorias con puertas inestables.

**Por qué compartido incremental y no individual.** Para *un* cazador con
rango grande el individual examina menos salas (636 frente a 1600), porque
corta al asentar al jugador. Pero en la carga del enunciado, con decenas de
cazadores persiguiendo al mismo objetivo, la búsqueda compartida se hace una
vez y se reutiliza (29 de 30 decisiones reutilizan en el escenario de ciclo),
y el costo medio por cazador baja a 0,135 ms, unas 8 veces menos que el
individual.

**Límites conocidos.** Si hubiera uno o dos cazadores con rango muy grande en
una cripta enorme, el modo individual sería mejor, y se puede elegir con
`DecisorCazadores(..., modo=INDIVIDUAL)`. El modo individual no reutiliza
cálculos entre turnos. Todo el diseño compartido descansa en la simetría de
los costos (FR-002): si el enunciado la eliminara, habría que volver al modo
individual.

---

## P2 5.2 Rutas que dejan de ser válidas

**Problema.** Entre dos turnos de un cazador pueden abrirse o cerrarse
puertas, el jugador puede moverse y otros actores pueden moverse o morir. La
decisión debe ser siempre la de un cálculo desde cero (FR-019, FR-020), y
reutilizar solo vale si se demuestra que no cambia la respuesta.

**Alternativas consideradas.**
1. *Recalcular siempre.* Correcta por definición; es la alternativa medida.
2. *Invalidar todo ante cualquier cambio de puerta.* Simple, pero las
   puertas con cierre automático lejos de los cazadores invalidarían cálculos
   que siguen siendo válidos.
3. *Reutilización con invalidación selectiva* (decisión).

**Decisión** (research R6, `src/modelos/cazador.py`). Todo cambio de puerta
pasa por un único punto, `Partida._poner_cerrada` (abrir con llave, cierre
automático y deshacer con pergamino), que incrementa `version_puertas`
(nunca se revierte) y avisa al decisor. La búsqueda compartida se reutiliza
solo si:
1. el jugador sigue en la misma sala;
2. no se superó el umbral de 32 puertas cambiadas desde el cálculo;
3. todas las puertas cambiadas tienen sus dos salas fuera de la región
   asentada (`Puerta.extremos`).

Si se cumplen y el cazador pide un rango mayor, la búsqueda se *extiende*
en lugar de recalcularse.

**Demostración de la condición 3.** La búsqueda solo usó salidas de salas
asentadas. Una puerta con ambos extremos sin asentar no participó en ninguna
distancia asentada. Abrirla no crea un camino de costo ≤ la cota alcanzada,
porque para usarla habría que llegar a un extremo con costo ≤ esa cota, y ese
extremo estaría asentado. Cerrarla no quita ningún camino usado.

| Evento | ¿Invalida? |
|---|---|
| El jugador cambia de sala | Sí (otra sala de origen) |
| Puerta con alguna sala en la región asentada | Sí |
| Puerta con las dos salas fuera de la región (incluido el borde) | No |
| Más de 32 puertas cambiadas sin decidir | Sí (no se revisa la lista) |
| Cazador con rango mayor | No: extiende |
| Otros actores se mueven o mueren; cambios de velocidad | No: no cambian distancias |
| Retroceso con pergamino | Según lo restaurado: la sala del jugador o las puertas (que avisan al deshacer) |

¿Coincide con el `plan.md`? Sí, con el ajuste de `/speckit-analyze`
(«extender en lugar de recalcular» para rangos mayores).

**Análisis de complejidad.** Comprobar la reutilización: O(c), con c ≤ 32
puertas cambiadas. Reutilizar: O(1) más la decisión local O(4).

**Evidencia empírica** (`[reutilizacion]`, 1600 salas, 30 cazadores, 60
rondas):

| Escenario | Búsquedas | Reutilizaciones | ms por ronda (media / máx.) |
|---|---|---|---|
| Puertas estables, reutilizar | 31 | 1423 | 0,24 / 0,62 |
| Puertas estables, recalcular siempre | 1454 | 0 | 7,64 / 11,36 |
| Puertas inestables (cerca del jugador), reutilizar | 60 | 1533 | 0,45 / 0,76 |
| Puertas inestables, recalcular siempre | 1593 | 0 | 9,69 / 16,92 |

- **No recálculo demostrado:** en una cripta de 2000 salas, 100 cambios de
  puertas alejadas no aumentan ni las búsquedas ni las salas examinadas
  (`tests/test_reutilizacion_cazador.py`), y cada decisión coincide con la
  referencia.
- **Ciclo de eventos (FR-031, SC-003):** con 30 cazadores activos, el peor
  ciclo entre dos decisiones del jugador fue de **2,7 ms (CUMPLE el límite de
  20 ms)**, con 133 búsquedas y 5147 reutilizaciones. Se toma el mínimo de 3
  repeticiones por acción para descartar interrupciones del sistema operativo;
  el peor valor bruto observado en esa corrida fue de 3,8 ms. Durante el
  desarrollo se vieron picos brutos aislados de 20 a 100 ms en ciclos que,
  repetidos, tardan unos 3 ms; aparecían incluso con el recolector de basura
  desactivado, por lo que se atribuyen al sistema operativo y no al código.

**Límites conocidos.** Con puertas que cambian en cada evento justo al lado
del jugador, la condición 3 casi nunca se cumple: el sistema recalcula, pero
el costo de comprobar es despreciable (escenario inestable). El umbral de 32
es un valor elegido, no medido con precisión; por encima de él se recalcula
sin revisar la lista.

---

## P2 5.6 Revisión de decisiones de la primera parte (lo que toca 001)

**Agenda de eventos (P1 §4.1): sigue siendo adecuada.** Con eventos de 30
cazadores, intervalos variables por costo (1 a 300) y velocidades de 70 a 200
(`[revision_p1]`), 2000 extracciones con reinserción tardan 4,6 ms y 20 000
tardan 45,6 ms: unos 0,0023 ms por operación, el mismo orden que en P1
(0,0028 ms por extracción en `[agenda]`). El crecimiento es O(log n). No se
cambió.

**Historial de retroceso (P1 §4.6): sigue siendo adecuado.** Con 30 cazadores
persiguiendo, 50 acciones del jugador tardan 52,5 ms en total (1,05 ms por
acción, incluida toda la simulación) y deshacer los 5 intervalos tarda
0,43 ms. Los cazadores agregan deltas (cambios de sala y eventos), pero
siguen siendo pocos por intervalo. No se cambió.

**Decisiones de P1 que sí cambiaron** (antes y después):

| Qué | Antes (P1) | Después (P2) | Por qué |
|---|---|---|---|
| Costo de la acción del enemigo | Siempre 100 al programar su próxima acción | 100 al atacar o esperar; costo de la salida al moverse | FR-003 y FR-005 (research R8) |
| Formato binario de guardado | Versión 1, sin costo | Versión 2: costo de cada puerta e instante del próximo turno de cada enemigo; un archivo v1 se rechaza | FR-026, FR-029 |
| Restauración de una partida | Cada cara de una puerta quedaba como un objeto distinto; los enemigos se reprogramaban a 100 desde la carga | Las puertas se vuelven a unir con `Cripta.enlazar_puertas` y cada enemigo conserva el instante de su próximo turno | Al cerrar una cara, la otra seguía abierta; la partida cargada no continuaba igual (FR-029) |
| Rastreador con dos salidas hacia la misma vecina | Costo fijo de 100 | Salida abierta más barata; empate por N, S, E, O | FR-015 |

Las tres últimas filas son defectos de P1 que se descubrieron al implementar
001; se corrigieron con pruebas (`tests/test_guardado.py`).

---

## Nota transversal de la segunda parte: cumplimiento del Principio I

`tests/test_restricciones.py` verifica automáticamente con `ast` que los
módulos de la capacidad (montículo, registro, rutas, decisor, generador,
fuente en memoria, referencia teórica y utilidades de prueba) no importan
`heapq`, `bisect`, `collections`, `queue`, `networkx` ni `functools.lru_cache`,
ni usan diccionarios, conjuntos, `sorted` o `.sort`. El generador de criptas
escribe texto JSON y solo se leen los diccionarios que devuelve `json.loads`.
`src/servicios/banco_cazador.py` usa diccionarios únicamente para las filas
del reporte de `--bench`, que no resuelven ningún problema evaluado.
