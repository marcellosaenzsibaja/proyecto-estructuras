# Data Model: Terreno con costo y enemigo cazador

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Solo se describen los cambios respecto de la primera parte.

## Entidades modificadas

### Puerta (`src/modelos/entidades.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `costo` | int ≥ 1 | Nuevo. Costo de tránsito, compartido por los dos lados (FR-001, FR-002). 100 si no se declara. |
| `cerrada`, `llave`, `cierre_automatico`, `evento_cierre` | — | Sin cambios. |

**Validación al cargar** (R4): entero ≥ 1; si ambos lados lo declaran, deben coincidir. Si no se
cumple, `ErrorDatos` con sala y dirección (FR-008).

### Salida (`src/modelos/entidades.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `sala_destino` | Sala | Nuevo. Referencia directa a la sala vecina, asignada en `Cripta.enlazar_puertas` (R3). |

### Sala (`src/modelos/entidades.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `indice` | int 0..n-1 | Nuevo. Índice compacto asignado en `Cripta.agregar_sala`, en orden de carga y determinista (R2). |

### FichaEnemigo (`src/modelos/fichas.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `comportamiento` | str | Admite el valor nuevo `cazador`. |
| `rango` | int ≥ 0 o None | Nuevo. Obligatorio si `comportamiento == cazador`; si falta o no es válido, `ErrorDatos` con el id de la ficha (FR-009). |

### Partida (`src/modelos/partida.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `version_puertas` | int | Nuevo. Contador monotónico de infraestructura: aumenta con cada cambio de `Puerta.cerrada`, también al deshacer. No se revierte ni se guarda (R6). |
| `decisor_cazadores` | DecisorCazadores | Nuevo. Infraestructura: no se guarda ni se revierte (FR-021). |

## Estructuras nuevas (infraestructura de cálculo, no estado del juego)

### MonticuloMin (`src/estructuras_datos/monticulo.py`) — R1

- Almacenamiento: `list` de pares `(costo, indice)`. Orden: menor costo y, si empatan, menor
  índice, para que sea determinista.
- Operaciones: `insertar(costo, indice)` O(log k), `extraer_minimo()` O(log k), `minimo()` O(1)
  (consulta sin extraer, para pausar la búsqueda), `esta_vacio()` O(1), `vaciar()` (reutiliza la
  lista).

### RegistroBusqueda (`src/estructuras_datos/registro_busqueda.py`) — R2

- Listas de tamaño n indexadas por `Sala.indice`: `distancia`, `primer_paso`, `marca` (generación
  en que se registró una distancia tentativa) y `asentada` (generación en que se asentó).
- `generacion: int`. `nueva_busqueda()` incrementa la generación en O(1). `tiene(i)` es
  `marca[i] == generacion`.
- Contador `examinadas` de la búsqueda actual (R9): suma 1 la primera vez que una sala recibe
  `marca == generacion`.

### BuscadorRutas (`src/modelos/rutas.py`) — R5

- `distancias_desde(sala_origen, cota)`: inicia una búsqueda acotada que deja en el registro
  `dist(v)` para toda sala con distancia ≤ cota, usando solo salidas con puerta abierta en ese
  instante, y queda en pausa con `cota_alcanzada = cota`.
- `extender_hasta(cota_nueva)`: retoma la misma búsqueda (misma generación y mismo montículo) hasta
  `cota_nueva` si es mayor que `cota_alcanzada` (R5).
- `primer_paso_desde(sala_origen, sala_objetivo, cota)`: modo individual; devuelve `(d, vecina)` con
  el desempate de FR-014 y FR-015, o `None`.
- No conoce la niebla de guerra ni el contenido de las salas (FR-017).

### DecisorCazadores (`src/modelos/cazador.py`) — R5 y R6

- `decidir(cazador) -> Decision`: `ATACAR`, `ESPERAR` o `MOVER(salida)`, con el costo de la acción.
- Estado de reutilización: llave `(sala_jugador, cota, version_puertas)`, región examinada (vía
  generación del registro) y lista de puertas cambiadas desde la última búsqueda.
- `notificar_puerta(puerta)`: la llama `Partida` en cada cambio de puerta.
- `modo`: `compartido` (por defecto preliminar) o `individual`, seleccionable para `--bench`.

## Transiciones relevantes

- **Cazador**: dormido → activo al entrar el jugador a su sala (P1 §2.4, FR-018). Activo → muerto
  según P1. En cada turno activo: ATACAR (misma sala), ESPERAR (sin ruta o `d > rango`) o MOVER.
- **Puerta**: abierta ⇄ cerrada. Cada transición, también por deshacer, aumenta `version_puertas`
  y notifica al decisor.
