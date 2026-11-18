# Quickstart: Validación de Verificación de Resolubilidad

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Contratos**: [interfaz-y-reporte.md](contracts/interfaz-y-reporte.md)

Este documento describe los comandos y pasos necesarios para validar y reproducir de extremo a extremo la capacidad de verificación de resolubilidad.

---

## Requisitos previos

- Python 3.11 o superior.
- Dependencias instaladas: `pip install -r requirements.txt`.
- Ejecutar todos los comandos desde la raíz del repositorio (`C:\Proyectos\proyecto-estructuras`).

---

## 1. Pruebas de aceptación obligatorias (Apéndice B)

Ejecutar la suite de pruebas unitarias y de aceptación de resolubilidad:

```bash
python -m unittest tests/test_resolubilidad.py -v
```

**Escenarios de aceptación verificados**:
- `test_caso_1_ciclo_llave_salida`: Verifica que si `llave_salida` está tras la única puerta que abre, la cripta es no resoluble y el reporte señala el ciclo `[llave_salida -> llave_salida]` (FR-015, Apéndice B Caso 1).
- `test_caso_2_llave_enemigo_errante`: Verifica que una llave portada por un enemigo errante es considerada obtenible en la sala inicial del enemigo (FR-006, Apéndice B Caso 2).
- `test_caso_3_orden_determinista_bifurcaciones`: Verifica que ante múltiples órdenes válidos, dos ejecuciones producen idéntico orden, desempatando alfanuméricamente por `id` (FR-009, FR-010, Apéndice B Caso 3).
- `test_caso_4_bloqueo_sin_forzar`: Verifica que una cripta irresoluble sin `--forzar` detiene la partida con reporte (FR-018, Apéndice B Caso 4).

---

## 2. Pruebas de integración CLI y códigos de terminación

```bash
python -m unittest tests/test_cli_verificar.py -v
```

**Comportamiento verificado**:
- `python main.py --verificar <cripta_resoluble>`: Emite reporte y finaliza con código de salida `0`.
- `python main.py --verificar <cripta_no_resoluble>`: Emite reporte y finaliza con código de salida `1`.
- `python main.py --cripta <cripta_no_resoluble>`: Detiene el inicio y finaliza con código `1`.
- `python main.py --cripta <cripta_no_resoluble> --forzar`: Imprime el reporte y permite continuar a la partida.

---

## 3. Pruebas de persistencia y presupuesto de red

```bash
python -m unittest tests/test_verificador_servicio.py -v
```

**Comportamiento verificado**:
- Primera consulta a `GET /criptas/<id>/llaves` descuenta 1 del presupuesto y persiste en disco `llaves.json`.
- Segunda consulta sobre la misma versión lee de disco con 0 solicitudes HTTP y 0 consumo de presupuesto.
- Modo `--offline` opera exclusivamente con el archivo local sin red.

---

## 4. Verificación de restricciones constitucionales (Principio I)

```bash
python -m unittest tests/test_restricciones.py -v
```

**Resultado esperado**:
- El escáner AST confirma que los nuevos módulos (`src/modelos/resolubilidad.py`, `src/servicios/verificador_servicio.py`, `src/servicios/banco_resolubilidad.py`, etc.) NO contienen `dict`, `set`, `heapq`, `bisect`, `collections` ni bibliotecas de grafos.

---

## 5. Medición de rendimiento empírico con `--bench`

```bash
python main.py --bench
```

**Métricas a verificar**:
1. **Límite de tiempo en cripta grande**: Cripta sintética de 1 000 salas y 40 llaves verificada en $< 200\text{ ms}$ (SC-003, FR-026).
2. **Escalamiento lineal vs. Alternativa ingenua**:
   - Para cadenas de 10, 25, 50, 100 y 500 llaves encadenadas, el algoritmo lineal reactivo $O(|V| + |E| + |K| \log |K|)$ con `MonticuloMin` crece de forma proporcional a $N$.
   - La alternativa ingenua (recorrido repetido por cada llave) muestra degradación cuadrática $O(N^2)$, justificando empíricamente la decisión de arquitectura (SC-004, FR-027).
3. **Robustez de detección iterativa de ciclos**: Cadenas profundas de dependencias cíclicas ($\ge 500$ llaves) procesadas sin desbordamiento de recursión en tiempo $O(|K| + |E_K|)$.
