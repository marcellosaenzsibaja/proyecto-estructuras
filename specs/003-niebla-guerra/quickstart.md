# Quickstart: validar la niebla de guerra y el viaje automático

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Requisitos previos

- Python 3.11 o superior y las dependencias de `requirements.txt` instaladas.
- No hace falta red para nada de esta guía salvo el paso 4.

## 1. Pruebas de aceptación de la capacidad

```
python -m pytest tests/test_mapa_conocido.py tests/test_antorcha_exploracion.py tests/test_viaje.py tests/test_viaje_bitacora.py tests/test_mapa_guardado.py tests/test_equivalencia_viaje.py tests/test_rendimiento_mapa.py tests/test_restricciones.py -v
```

Cada prueba cita en su nombre o en su docstring el requisito que verifica (`003-FR-NNN`). Los seis
casos del Apéndice B de «Niebla de guerra e ir a» están en:

| Caso del Apéndice B | Prueba |
| --- | --- |
| `ir a` hacia una sala no explorada se rechaza y no consume tiempo | `test_viaje.py` |
| El mapa recuerda abierta una puerta cerrada: se corrige, se recalcula y si no queda ruta se detiene | `test_viaje.py` |
| `ir a` entra a una sala con enemigos dormidos: se activan y el viaje se detiene | `test_viaje.py` |
| Con antorcha encendida, entrar explora las vecinas sin activar enemigos ni trampas | `test_antorcha_exploracion.py` |
| Un pergamino revierte una entrada con antorcha encendida | `test_antorcha_exploracion.py` |
| Un pergamino durante un viaje revierte solo el último paso y el viaje no continúa | `test_viaje.py` |

## 2. Regresión de las capacidades anteriores

```
python -m pytest -q
```

Debe pasar la batería completa, incluidas las pruebas de 001 y 002 (SC-010). En particular
`tests/test_cazador.py` comprueba que el cazador sigue decidiendo con el estado real de las puertas y
no con el conocimiento del jugador (FR-023).

También con `unittest`, como indica el README:

```
python -m unittest discover -s tests
```

## 3. Mediciones

```
python main.py --bench
```

Secciones que agrega esta capacidad:

| Sección | Qué mirar |
| --- | --- |
| `[mapa_consultas]` | el tiempo por consulta no crece al pasar de 100 a 1 600 salas exploradas (FR-050) |
| `[mapa_exploracion]` | `salas_tocadas` y `puertas_tocadas` son iguales con mapa pequeño y grande (SC-004) |
| `[viaje_paso]` | `resultado=CUMPLE` contra el límite de 5 ms (FR-053, SC-003) |
| `[viaje_vs_cazador]` | respalda la decisión de R4 de no compartir el recorrido |
| `[mapa_reversion]` | registrar e invertir cuesta menos que copiar el mapa (FR-052) |
| `[mapa_determinismo]` | `mismo_mapa=si` en dos ejecuciones con la misma semilla (FR-049) |

`--bench` no instancia la vista y sus criptas sintéticas son deterministas por semilla (FR-056).

## 4. Prueba manual en partida

Con una cripta publicada:

```
python main.py --cripta <cripta> --semilla 42
```

1. Escribe `mapa`: la sala inicial aparece explorada y sus vecinas avistadas. El reloj no avanza
   (FR-026).
2. Muévete a una vecina y vuelve a escribir `mapa`: la sala nueva está explorada, con sus salidas y
   los estados recordados de sus puertas.
3. Escribe `ir a <sala inicial>` por su nombre o su id: el jugador vuelve paso a paso y al final se
   informa el motivo de detención (FR-042).
4. Escribe `ir a` hacia una sala avistada: se rechaza y el reloj no avanza (FR-029).
5. Con una antorcha en el inventario, `equipar` o `usar` la antorcha, muévete a una sala con varias
   salidas y escribe `mapa`: sus vecinas quedan exploradas con nombre y salidas, sin que nada haya
   despertado (FR-014 a FR-016).
6. Con un pergamino, úsalo justo después de esa entrada y vuelve a escribir `mapa`: las salas que la
   antorcha reveló volvieron a su estado anterior (FR-048).
7. `guardar prueba.bin`, `cargar prueba.bin` y `mapa`: el mapa es el mismo (FR-046).
8. Intenta cargar un archivo guardado con una versión anterior del programa: debe reportarse como
   incompatible y no cargarse (FR-047).

## 5. Reproducción

```
python main.py --cripta <cripta> --semilla 42 --bitacora viaje.log
python main.py --cripta <cripta> --replay viaje.log
```

La bitácora de una partida con viajes contiene un movimiento por cada paso más una línea de
comentario por cada orden `ir a`. La reproducción ejecuta solo los movimientos y llega al mismo
estado y al mismo mapa conocido (FR-043, FR-044, FR-049).
