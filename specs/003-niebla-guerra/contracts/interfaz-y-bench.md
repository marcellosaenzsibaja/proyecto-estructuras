# Contrato de Interfaz, Bitácora y Mediciones: Niebla de guerra e «ir a»

**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

Este documento fija los contratos observables de la capacidad: los comandos nuevos de la interfaz,
el formato de las líneas que agrega a `partida.log`, la sección nueva del archivo de partida y el
formato de salida de `--bench`. Lo que aquí se fija es lo que las pruebas comprueban y lo que la
defensa puede exigir.

---

## 1. Comandos de la interfaz

### `mapa`

- **Sinónimos**: `mapa`, `mp`.
- **Argumentos**: ninguno.
- **Comportamiento**: imprime el mapa conocido y devuelve el control al jugador. NO consume tiempo
  virtual, NO se registra en `partida.log` y NO altera el historial de retroceso (FR-026).
- **Formato de salida**:

```
Mapa conocido (N salas exploradas, M avistadas)
  [id] Nombre de la sala
    N -> sala 12: abierta, costo 100
    E -> sala  7: cerrada, costo 250
    S -> sala  4: sin observar, costo 100
    O -> (sin salida)
  ...
Salas avistadas: 4, 7, 19
```

- El estado de cada salida es el **recordado**, nunca el real (FR-025). Los tres valores posibles se
  escriben `abierta`, `cerrada` y `sin observar`, y son distinguibles entre sí.
- Las salas exploradas se listan en el orden en que se exploraron.
- Las salas avistadas se listan solo por id, sin nombre ni salidas, porque es todo lo que el jugador
  conoce de ellas (FR-005).
- Una sala explorada cuyo destino es una sala avistada muestra la salida y su costo, porque eso lo
  conoce; lo que no muestra es nada del interior de la sala avistada.

### `ir a <sala>`

- **Sinónimos**: `ir a <sala>`, `ir <sala>`.
- **Argumento**: el id numérico de una sala explorada, o su nombre si ese nombre identifica a una
  sola sala explorada (FR-028). El nombre se compara sin distinguir mayúsculas ni acentos.
- **Rechazos** (ninguno consume tiempo virtual ni se registra como acción, FR-029):

| Situación | Mensaje |
| --- | --- |
| Destino no explorado | `No conoces esa sala todavía.` |
| Destino inexistente o argumento vacío | `No hay ninguna sala conocida con ese nombre o id.` |
| Nombre ambiguo entre salas exploradas | `Hay varias salas conocidas con ese nombre; usa el id (12, 19).` |
| Destino igual a la sala actual | `Ya estás en esa sala.` |
| Sin ruta conocida al empezar | `No conoces ninguna ruta hasta esa sala.` |

- **Ejecución**: da pasos mientras exista ruta conocida y no se cumpla ninguna condición de parada.
  Cada paso es una acción de mover ordinaria (FR-034), y entre pasos se despachan los eventos del
  reloj.
- **Mensaje final** (FR-042), uno por motivo de detención:

| Motivo | Mensaje |
| --- | --- |
| `LLEGADA` | `Llegas a Nombre de la sala (K pasos).` |
| `ENEMIGOS` | `El viaje se detiene en Nombre: hay enemigos en la sala (K pasos).` |
| `DANO` | `El viaje se detiene en Nombre: has recibido daño (K pasos).` |
| `SIN_RUTA` | `El viaje se detiene en Nombre: ya no conoces una ruta hasta el destino (K pasos).` |
| `FIN_PARTIDA` | no imprime mensaje de viaje: el final de la partida se informa por su propio camino. |

- `K` es la cantidad de pasos efectivamente dados, que puede ser 0 solo cuando la partida terminó en
  el primer paso.

---

## 2. Contrato de `partida.log`

La bitácora es un archivo de líneas JSON, una por registro, como en P1. Esta capacidad agrega un
tipo de registro.

### Registro de comentario

```json
{"tipo": "comentario", "texto": "ir a 12"}
```

- Se escribe **antes** del primer paso de un viaje (FR-043).
- `leer` lo descarta al construir la lista de acciones, de modo que `--replay` ejecuta solo los
  movimientos individuales grabados (FR-044). Un comentario nunca se traduce a una acción.
- Un archivo con comentarios sigue siendo válido para una versión del programa que los ignore, y un
  archivo sin comentarios sigue siendo válido para esta.

### Pasos de un viaje

Cada paso se graba con el mismo registro que un movimiento manual:

```json
{"tipo": "mover", "argumento": 0}
```

No hay forma de distinguir en la bitácora un paso de viaje de un movimiento manual, y eso es
deliberado: la reproducción debe llegar al mismo estado sin recalcular rutas y sin depender de que el
conocimiento del jugador se reconstruya antes de cada paso (clarificación de `spec.md`).

Un viaje de tres pasos produce entonces cuatro líneas: un comentario y tres movimientos.

---

## 3. Contrato del archivo de partida

- `FORMATO_VERSION` sube de **2** a **3** (FR-047). Un archivo de versión 1 (primera parte) o 2
  (capacidades 001 y 002) se rechaza con el mensaje de incompatibilidad que ya existe, y no se carga
  en silencio.
- Se agrega al encabezado una sección `mapa`, con una entrada por cada sala cuyo estado no sea
  desconocido:

| Campo | Contenido |
| --- | --- |
| `id` | id de la sala |
| `estado` | `1` avistada, `2` explorada |
| `puertas` | cuatro enteros, en el orden N, S, E, O: `0` sin observar, `1` recordada abierta, `2` recordada cerrada |

- El orden de las entradas es: primero las salas exploradas en su orden de exploración, después las
  avistadas. Cargar reconstruye la lista de exploradas en ese mismo orden, de modo que el mapa
  resultante es idéntico al guardado, incluido el orden en que la vista lo lista (FR-046, SC-007).
- Las salas exploradas sin contenido incorporado (las que reveló la antorcha) aparecen en esta
  sección aunque no aparezcan en la sección de salas, que solo existe para las salas con contenido.
- El viaje no se persiste: no hay viajes a medio terminar que reanudar al cargar.

---

## 4. Contrato de `--bench`

Formato de línea igual al de las capacidades 001 y 002: nombre del escenario, dos puntos, y pares
`clave=valor` separados por espacios. Toda sección es determinista por semilla y ninguna instancia
la vista (FR-056).

### `[mapa_consultas]`

```
mapa_consultas_100_exploradas: semilla=31 exploradas=100 consultas=200000 ms_total=... ns_por_consulta=...
mapa_consultas_400_exploradas: semilla=31 exploradas=400 consultas=200000 ms_total=... ns_por_consulta=...
mapa_consultas_1600_exploradas: semilla=31 exploradas=1600 consultas=200000 ms_total=... ns_por_consulta=...
```

Lo que respalda: `ns_por_consulta` no crece con `exploradas` (FR-050).

### `[mapa_exploracion]`

```
exploracion_antorcha_mapa_pequeno: semilla=31 exploradas_antes=... reveladas=K salas_tocadas=... puertas_tocadas=... ms_media=...
exploracion_antorcha_mapa_grande: semilla=31 exploradas_antes=... reveladas=K salas_tocadas=... puertas_tocadas=... ms_media=...
```

Lo que respalda: `salas_tocadas` y `puertas_tocadas` son iguales en las dos filas para el mismo `K`
(FR-051, SC-004). Los tiempos son evidencia complementaria.

### `[viaje_paso]`

```
viaje_paso_mapa_completo: semilla=31 salas=1600 exploradas=1600 ms_media=... ms_max=... limite_ms=5 resultado=CUMPLE
```

Lo que respalda: FR-053 y SC-003. `resultado` es `CUMPLE` si `ms_max` es menor que 5.

### `[viaje_vs_cazador]`

```
viaje_paso: semilla=31 salas=1600 ms_media=...
cazador_decision: semilla=31 salas=1600 ms_media=...
```

Lo que respalda: la decisión de `research.md` R4 de no compartir el recorrido entre las dos
búsquedas, mostrando que ninguna de las dos se degradó.

### `[mapa_reversion]`

```
reversion_registrada_k_salas: semilla=31 reveladas=K cambios=... ms_media=...
reversion_copia_completa_k_salas: semilla=31 reveladas=K copiado=... ms_media=...
```

Lo que respalda: FR-052, comparando registrar e invertir solo lo que cambió contra la alternativa de
copiar el mapa completo.

### `[mapa_determinismo]`

```
determinismo_mapa: semilla=31 salas=... acciones=... mismo_mapa=si mismas_rutas=si
```

Lo que respalda: FR-049 y FR-056.
