# Contrato: presentación y salida de `--bench`

**Feature**: [../spec.md](../spec.md)

## Vista de consola (FR-023, FR-024)

La sintaxis exacta es decisión del grupo; el contrato mínimo es:

- Cada salida de la sala actual muestra su dirección y su costo. Ejemplo:
  `Salidas: N (100)  E (250, cerrada)  O (100)`.
- Cada enemigo cazador se distingue de los demás con una marca propia. Ejemplo:
  `Sabueso óseo #1 [cazador]  vida 18/18`.
- La vista no muestra distancias ni rutas de los cazadores, porque no son información del jugador.

## Salida de `--bench` (FR-032 a FR-035)

`--bench` imprime una sección por escenario de la tabla «Mediciones planificadas» del plan. Cada
fila incluye como mínimo:

| Campo | Significado |
|---|---|
| `escenario` | Nombre del escenario (por ejemplo `cazador_compartido_30_rango_pequeno`) |
| `semilla` | Semilla de la cripta sintética |
| `salas` | Tamaño de la cripta sintética |
| `cazadores` | Cantidad de cazadores activos |
| `examinadas_media` | Salas examinadas promedio por decisión (o por búsqueda en el modo compartido) |
| `ms_media` / `ms_max` | Tiempo medio y máximo |
| `reutilizaciones` | Veces que se reutilizó un cálculo (solo en escenarios de reutilización) |

Con la misma semilla, dos ejecuciones producen las mismas criptas sintéticas y los mismos valores de
`examinadas_media` y `reutilizaciones`. Los tiempos varían según la máquina.
