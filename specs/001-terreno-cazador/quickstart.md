# Quickstart: validar terreno y cazador

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Requisitos previos

- Python 3.11+ y dependencias instaladas (`pip install -r requirements.txt`).
- Ejecutar desde la raíz del repositorio.

## 1. Pruebas de aceptación de la capacidad

```bash
python -m pytest tests/test_restricciones.py tests/test_generador_criptas.py tests/test_terreno.py tests/test_cazador.py tests/test_determinismo_cazador.py tests/test_equivalencia_cazador.py tests/test_reutilizacion_cazador.py tests/test_rendimiento_cazador.py -v
```

Resultado esperado: todas pasan. Cada prueba cita en su nombre o docstring el requisito que
verifica (por ejemplo `FR-014`), lo que permite recorrer la trazabilidad escenario → tarea →
código → prueba.

## 2. Regresión de la primera parte

```bash
python -m pytest -q
```

Resultado esperado: la batería completa pasa (SC-007).

## 3. Mediciones

```bash
python main.py --bench
```

Resultado esperado: aparecen las secciones del [contrato de `--bench`](contracts/interfaz-y-bench.md):
decisión del cazador (compartido frente a individual), cola de prioridad, reutilización con puertas
estables e inestables, escala ×1 frente a ×10 y ciclo de eventos con ≥ 30 cazadores con
`ms_max < 20`.

## 4. Prueba manual en partida

1. `python main.py --cripta <id> --semilla 42` con una cripta de la segunda parte.
2. Verificar que las salidas muestran su costo y que los cazadores llevan su marca.
3. Moverse por una salida de costo distinto de 100 y comprobar que el reloj avanza según
   `max(1, costo*100 // velocidad)`.
4. Guardar `partida.log` y reproducir con `python main.py --replay partida.log`: los cazadores
   toman las mismas decisiones (SC-005).
