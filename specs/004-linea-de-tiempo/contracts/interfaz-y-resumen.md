# Contrato de Interfaz, Resumen y Mediciones: Línea de tiempo

**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

---

## 1. Comando `historia`

- **Sinónimos**: `historia`, `hist`.
- **Formas del argumento**:
  - `historia <t>` con `t` entero, `0 ≤ t ≤ reloj actual`.
  - `historia #k` con `k` entero, `1 ≤ k ≤ acciones del jugador + 1`.
- **Comportamiento**: imprime el resumen y devuelve el control. NO consume tiempo virtual, NO se
  registra en `partida.log`, NO altera el historial de retroceso y NO emite solicitudes de red
  (FR-007, FR-011).
- **Rechazos** (ninguno consume tiempo ni altera nada, FR-010):

| Situación | Mensaje |
| --- | --- |
| `t` mayor que el reloj actual | `Ese instante todavía no ha ocurrido (el reloj va en <t_actual>).` |
| `t` negativo | `El instante debe estar entre 0 y <t_actual>.` |
| `#k` fuera de rango | `Solo hay <n> acciones del jugador; usa #1 a #<n+1>.` |
| Argumento ausente o mal formado | `Usa 'historia <t>' con un instante, o 'historia #k' con el número de una acción.` |

- **Formato de salida**:

```
Historia del instante 1850 (antes de la acción #19)
  Sala: [7] Galería inundada
  Vida: 23/40   ataque 8  defensa 3  velocidad 100
  Inventario (3/8): llave de bronce, *antorcha, pergamino de retroceso
  Efectos: antorcha (termina en 2100), veneno (4 por pulso, termina en 1920)
  Enemigos aquí: Sabueso óseo (e-1203) 18/18, Errante (e-1204) 5/12
  Mapa conocido: 6 exploradas, 4 avistadas
```

- El objeto seleccionado del inventario se marca con `*`.
- `Efectos` imprime `ninguno` si no hay.
- `Enemigos aquí` imprime `ninguno` si la sala no tiene enemigos en ese instante.
- `Mapa conocido` resume los conteos de la capacidad 003; el detalle se ve con el comando `mapa`.
- Si el instante pedido es posterior al final de la partida en un `--replay --hasta`, se agrega una
  última línea: `La partida terminó en el instante <t_final>, antes del instante pedido.` (FR-018).

---

## 2. Opciones de línea de comandos

### `--checkpoint-cada K`

- **Valor**: entero `K ≥ 1`. Un valor menor que 1 se rechaza al arrancar con
  `--checkpoint-cada debe ser un entero mayor o igual que 1.` y código de salida 2.
- **Efecto**: a lo sumo un punto de control cada `K` acciones del jugador (FR-020).
- **Por defecto**: el valor que fijan las mediciones de `[linea_tiempo]`, documentado en
  `DECISIONES.md` §P2 5.5 y en el README (FR-021).

### `--hasta <t>`

- **Válido solo junto con `--replay`.** Usado sin `--replay` se rechaza con
  `--hasta solo se puede usar junto con --replay.` y código de salida 2.
- **Efecto**: reproduce la bitácora hasta el instante `t`, imprime el mismo resumen que
  `historia <t>` y termina, sin instanciar la vista (FR-017).
- **`t` posterior al final de la partida grabada**: imprime el resumen del estado final más la línea
  de partida terminada antes (FR-018).

---

## 3. Contrato de `partida.log`

Esta capacidad agrega dos tipos de registro a los de P1 y de la capacidad 003.

```json
{"tipo": "cursor_sig"}
{"tipo": "cursor_ant"}
```

- Se escriben cuando el jugador mueve el cursor del inventario con `sig` o `ant`.
- NO son acciones del jugador: no consumen tiempo, no incrementan el contador de acciones y no
  generan punto de control.
- `reproducir` los aplica en su posición, para que una partida que usa un objeto no primero del
  inventario se reproduzca fielmente (research R5).
- Una bitácora grabada por las capacidades anteriores sigue siendo válida: solo faltan estos
  registros, y una reproducción sin ellos se comporta como antes.

---

## 4. Contrato del archivo de partida

- `FORMATO_VERSION` sube de **2** a **3**, compartido con la capacidad 003 (research R8). Las
  versiones 1 y 2 se rechazan con el mensaje de incompatibilidad existente (FR-029).
- Se agrega al encabezado una sección `linea`, con las entradas de la historia en orden:

| Campo | Contenido |
| --- | --- |
| `numero` | número de acción del jugador; `0` para un registro de cursor |
| `tiempo` | instante del reloj |
| `tipo` | tipo de acción, o `cursor_sig` / `cursor_ant` |
| `argumento` | argumento de la acción, o nulo |

- Los **puntos de control no se guardan** (research R2): se reconstruyen en la primera consulta de
  una partida cargada.
- Al tomar un punto de control en memoria se usa el mismo snapshot **sin** la sección `linea`: un
  punto de control no contiene la historia que lo contiene.

---

## 5. Contrato de `--bench`

### `[linea_tiempo]`

```
linea_k1_5000_acciones: semilla=47 acciones=5000 k=1 copias=5001 bytes_linea=... reaplicadas_max=0 ms_consulta_media=... ms_consulta_max=... limite_ms=50 resultado=CUMPLE
linea_k25_5000_acciones: semilla=47 acciones=5000 k=25 copias=201 bytes_linea=... reaplicadas_max=24 ms_consulta_media=... ms_consulta_max=... limite_ms=50 resultado=CUMPLE
linea_k200_5000_acciones: semilla=47 acciones=5000 k=200 copias=26 bytes_linea=... reaplicadas_max=199 ms_consulta_media=... ms_consulta_max=... limite_ms=50 resultado=...
linea_copia_por_accion: semilla=47 acciones=5000 k=1 copias=5001 bytes_linea=... nota=alternativa_descartada
linea_sin_puntos_control: semilla=47 acciones=5000 copias=1 reaplicadas_max=5000 ms_consulta_media=... ms_consulta_max=... nota=alternativa_descartada
```

Lo que respalda: FR-030 y FR-032. `copias` verifica SC-005 (`n/K + 1`), `reaplicadas_max` verifica
SC-004 (`≤ K`), y `bytes_linea` muestra el crecimiento de memoria de FR-024.

### `[linea_determinismo]`

```
determinismo_linea: semilla=47 acciones=... misma_historia=si mismos_resumenes=si
```

### `[ciclo_eventos]`

La sección de la capacidad 001 se repite con la línea activa y una fila más (FR-033, SC-006):

```
ciclo_eventos_30_cazadores_con_linea: semilla=7 salas=1600 cazadores=30 ms_media=... ms_max=... k=<K por defecto> limite_ms=20 resultado=CUMPLE
```

El valor que importa es `ms_max`, no `ms_media`: el pico es la acción que toma el punto de control
(research R10).
