# Data Model: Verificación de resolubilidad de una cripta

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Este documento define las entidades, modelos de datos y estructuras en memoria empleadas para la verificación de resolubilidad y su diagnóstico.

---

## 1. Entidades de Dominio y Contrato

### LlaveInfo (`src/modelos/resolubilidad.py`)

Representa la información de una llave conocida en la cripta obtenida a partir del endpoint `GET /criptas/<id>/llaves`.

| Campo | Tipo | Descripción y Reglas |
|---|---|---|
| `id` | `str` | Identificador único de la llave (ej. `"itm_llave_salida"`). |
| `sala` | `int` | Identificador de la sala donde se ubica la llave o donde inicia el enemigo que la suelta (FR-005, FR-006). |
| `enemigo_id` | `str` o `None` | Identificador de la instancia de enemigo que suelta la llave si aplica, o `None` si la llave está suelta en el piso. |
| `indice` | `int` | Índice continuo compacto $0 \le \text{indice} < m$ asignado tras el ordenamiento lexicográfico canónico (R3). |

### PuertaBloqueada (`src/modelos/resolubilidad.py`)

Representa una puerta perteneciente a la frontera bloqueada (salida cerrada que conecta la región alcanzable con una región no accesible por falta de llave).

| Campo | Tipo | Descripción y Reglas |
|---|---|---|
| `sala_origen` | `int` | Identificador de la sala alcanzada desde la cual parte la salida. |
| `direccion` | `str` | Letra cardinal de la salida (`'N'`, `'S'`, `'E'`, `'O'`). |
| `sala_destino` | `int` | Identificador de la sala vecina a la que conduce la puerta. |
| `llave` | `str` | Identificador de la llave requerida para abrir la puerta. |
| `sala_llave` | `int` o `None` | Sala donde se ubica la llave requerida (o `None` si la llave no existe en la cripta). |

### ReporteResolubilidad (`src/modelos/resolubilidad.py`)

Objeto de valor inmutable que encapsula el resultado completo del análisis estático de resolubilidad.

| Campo | Tipo | Descripción y Reglas |
|---|---|---|
| `resoluble` | `bool` | `True` si el jugador puede obtener `llave_salida` y llegar a `sala_salida` a través de una puerta que la requiere; `False` en caso contrario. |
| `orden_llaves` | `list[str]` | Si es resoluble: secuencia ordenada determinista de llaves donde cada una aparece tras las necesarias para alcanzarla. Si no es resoluble: lista vacía. |
| `llaves_no_obtenidas` | `list[str]` | Lista de identificadores de llaves que no pudieron ser recolectadas desde la sala inicial. |
| `frontera_bloqueada` | `list[PuertaBloqueada]` | Lista de puertas de frontera bloqueada con sus salas y llaves asociadas (FR-013, FR-014). |
| `ciclos` | `list[list[str]]` | Lista de ciclos detectados, donde cada ciclo es una secuencia cerrada canónica `[L_min, ..., L_min]` iniciando en la llave lexicográficamente menor (FR-015, FR-016). |
| `mensaje` | `str` | Representación textual formateada lista para ser impresa en consola o mostrada al usuario. |

---

## 2. Estructuras de Soporte para el Recorrido (Infraestructura de Cálculo)

Estas estructuras no forman parte del estado mutable de la partida ni persisten en archivos de guardado; se instancian y consumen exclusivamente durante la verificación.

### IndexadorLlaves (`src/modelos/resolubilidad.py`) — R3

- **Propósito**: Mapear de forma determinista y sin diccionarios (`dict`) los identificadores de texto de las llaves a un espacio de índices continuo $0 \dots m-1$.
- **Almacenamiento**:
  - `claves_ordenadas`: `list[str]` con los identificadores únicos ordenados mediante `ordenar()`.
- **Operaciones**:
  - `obtener_indice(llave_id: str) -> int`: Ejecuta búsqueda binaria propia en $O(\log m)$. Lanza error si la llave no está indexada.
  - `obtener_id(indice: int) -> str`: Acceso por índice en $O(1)$.
  - `__len__() -> int`: Retorna la cantidad de llaves únicas $m$.

### RegistroEsperaPuertas (`src/modelos/resolubilidad.py`) — R4

- **Propósito**: Registrar qué puertas cerradas esperan por cada llave para reactivarlas inmediatamente cuando dicha llave sea obtenida.
- **Almacenamiento**:
  - `espera`: `list[list[tuple]]` de tamaño $m$, donde cada posición $j$ contiene una lista de `(sala_origen, sala_destino, salida)`.
- **Operaciones**:
  - `registrar_espera(indice_llave: int, entrada)`: Agrega la puerta a la lista en $O(1)$.
  - `extraer_en_espera(indice_llave: int) -> list`: Obtiene la lista de puertas reactivables y limpia la posición en $O(1)$.

### ColaLlavesDisponibles (`MonticuloMin` en `src/estructuras_datos/monticulo.py`) — R3b

- **Propósito**: Mantener las llaves que se han vuelto alcanzables durante la exploración pero que aún no han sido procesadas, permitiendo extraer siempre de forma determinista la de menor identificador lexicográfico (FR-010).
- **Almacenamiento**:
  - Instancia de `MonticuloMin` que almacena pares `(indice_llave, indice_llave)`.
- **Operaciones**:
  - `insertar(indice_llave, indice_llave)`: Inserta en el montículo en $O(\log k)$.
  - `extraer_minimo() -> (int, int)`: Extrae la llave con menor índice numérico (menor `id` alfanumérico) en $O(\log k)$.
  - `esta_vacio() -> bool`: Verifica si no hay llaves pendientes en $O(1)$.

### EstadoExploracion (`src/modelos/resolubilidad.py`) — R1, R2

- **Almacenamiento**:
  - `cola`: `list` continua de salas alcanzadas.
  - `cabeza`: `int` (puntero de extracción en $O(1)$).
  - `visitada`: `list[bool]` de tamaño $|V|$, indexada por `Sala.indice`.
  - `llave_obtenida`: `list[bool]` de tamaño $m$, indexada por índice de llave.
- **Invariante**: Cada sala se encola a lo sumo una vez; cada puerta se registra a lo sumo una vez en espera y se reactiva a lo sumo una vez.

### Estructuras de Detección de Ciclos (DFS Iterativo) (`src/modelos/resolubilidad.py`) — R5

- **Propósito**: Detectar y extraer ciclos de dependencias entre llaves de forma estrictamente determinista e iterativa, sin depender de la pila de llamadas del sistema (`sys.getrecursionlimit()`).
- **Almacenamiento**:
  - `pila`: `list` nativa utilizada en modo LIFO con tuplas `(nodo_llave, indice_arista)`.
  - `camino`: `list` nativa que mantiene la ruta activa del árbol de búsqueda para extraer el ciclo exacto al detectar un back-edge.
  - `estado`: `list[int]` de tamaño $m$, donde cada posición almacena `0` (NO_VISITADO), `1` (EN_PROCESO) o `2` (PROCESADO).
- **Garantía**: Ocupa $O(|K|)$ en memoria dinámica del heap y escala sin restricciones ante cadenas profundas de dependencias.

---

## 3. Modelo de Persistencia Local de Llaves

### CacheLlaves (`src/servicios/cache_persistente.py` / `ProveedorRed`)

Estructura de persistencia local en formato JSON:

```json
{
  "cripta_id": "cripta_ejemplo_01",
  "version_cripta": 3,
  "llaves": [
    {
      "id": "itm_llave_plata",
      "sala": 4,
      "enemigo_id": null
    },
    {
      "id": "itm_llave_salida",
      "sala": 12,
      "enemigo_id": "inst_errante_03"
    }
  ]
}
```

- **Validación de Vigencia**: Si `version_cripta` coincide con la versión provista por el catálogo/servidor, el archivo se carga directamente en memoria. Si no coincide, se invalida y se solicita nuevamente al servicio mediante `GET /criptas/<id>/llaves` (FR-023, FR-024).
