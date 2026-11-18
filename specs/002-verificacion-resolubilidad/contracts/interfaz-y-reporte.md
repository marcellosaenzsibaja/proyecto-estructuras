# Contrato de Interfaz, Reporte y Servicio: Resolubilidad

**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

Este documento especifica los contratos formales para la interfaz de línea de comandos (CLI), los códigos de terminación del proceso, el formato del reporte impreso en consola y la integración con el servicio de red.

---

## 1. Contrato de Línea de Comandos (CLI)

### Opción `--verificar <cripta_id>`

- **Comportamiento**: Carga los datos, el esqueleto y las llaves de la cripta especificada, ejecuta la verificación estática de resolubilidad, imprime el reporte completo en `stdout` y finaliza la ejecución sin instanciar la vista interactiva (`VistaConsola`) ni iniciar el bucle de juego (FR-020).
- **Códigos de Salida del Proceso (`exit code`)**:
  - `0`: La cripta fue evaluada y el veredicto es **resoluble**.
  - `1`: La cripta fue evaluada y el veredicto es **no resoluble**.
  - `2`: La verificación no pudo completarse debido a un error técnico de red, formato de datos o presupuesto agotado (`ErrorCliente`, `ErrorDatos`, `PresupuestoAgotado`).

### Bandera `--forzar`

- **Comportamiento**: Modifica el arranque normal de una partida interactiva.
  - Sin `--forzar`: Si la cripta resulta **no resoluble**, el programa muestra el reporte de no resolubilidad y finaliza inmediatamente con código `1` sin iniciar la partida (FR-018, Apéndice B Caso 4).
  - Con `--forzar`: Si la cripta resulta **no resoluble**, el programa imprime el reporte diagnóstico y procede inmediatamente a iniciar la partida interactiva (FR-019).

### Arranque Normal

- Al invocar `python main.py --cripta <id>` (o seleccionarla desde la lista):
  1. Se descargan o leen de la caché el esqueleto y las llaves.
  2. Se ejecuta la verificación de resolubilidad.
  3. Se imprime el reporte en la consola (`stdout`).
  4. Si la cripta es resoluble, el juego continúa de inmediato a `mostrar_inicio()` y al bucle interactivo de la partida sin requerir pulsaciones de teclado ni pausas bloqueantes (Clarificación Q5).

---

## 2. Contrato de Servicio Web: `GET /criptas/<id>/llaves`

### Solicitud HTTP

- **Método**: `GET`
- **Ruta**: `/v1/criptas/<id>/llaves`
- **Encabezados requeridos**:
  - `X-Cripta-Client-Id`: Identificador único de sesión del cliente (UUID v4).
- **Control de Presupuesto**:
  - Cada solicitud cuenta exactamente como una unidad dentro del `presupuesto_solicitudes` de la cripta (FR-022).
  - Si el presupuesto está agotado antes de llamar al endpoint, se lanza `PresupuestoAgotado`.
- **Manejo de Tasa Límite (HTTP 429)**:
  - Si el servicio responde `429`, se lee `reintentar_en` del JSON y se espera antes de reintentar (contabilizando cada intento en el presupuesto).

### Respuesta HTTP 200 (JSON)

```json
{
  "llaves": [
    {
      "id": "itm_llave_hierro",
      "sala": 3,
      "enemigo_id": null
    },
    {
      "id": "itm_llave_salida",
      "sala": 8,
      "enemigo_id": "inst_cazador_01"
    }
  ]
}
```

- **Semántica de campos**:
  - `id` (`str`): Identificador único de la llave en la cripta.
  - `sala` (`int`): Sala donde se obtiene la llave. Para llaves que porta un enemigo, corresponde a la sala inicial donde aparece la instancia del enemigo (FR-006, Clarificación Q3).
  - `enemigo_id` (`str` o `null`): Identificador de la instancia de enemigo que la suelta, o `null` si la llave está en el suelo.

---

## 3. Contrato de Salida en Consola: Reporte de Resolubilidad

### Caso Cripta Resoluble

```text
================================================================
VERIFICACIÓN DE RESOLUBILIDAD: CRIPTA RESOLUBLE
================================================================
La cripta puede completarse exitosamente.

Orden de obtención de llaves (3 llaves):
  1. itm_llave_bronce (Sala 2)
  2. itm_llave_hierro (Sala 5)
  3. itm_llave_salida (Sala 12)
================================================================
```

### Caso Cripta No Resoluble

```text
================================================================
VERIFICACIÓN DE RESOLUBILIDAD: CRIPTA NO RESOLUBLE
================================================================
La cripta NO puede completarse bajo las reglas del juego.

Llaves inalcanzables (2):
  - itm_llave_oro (Sala 15)
  - itm_llave_salida (Sala 20)

Frontera bloqueada (2 puertas adyacentes a la región alcanzable):
  - Sala 10 [E] -> Sala 11 | Requiere: itm_llave_oro (ubicada en Sala 15)
  - Sala 14 [N] -> Sala 20 | Requiere: itm_llave_salida (ubicada en Sala 20)

Ciclos de dependencias detectados:
  - Ciclo 1: [itm_llave_salida -> itm_llave_salida]
================================================================
```

---

## 4. Contrato de Salida de `--bench` para Resolubilidad

Al ejecutar `python main.py --bench`, la sección de resolubilidad reporta las siguientes métricas reproducibles:

```text
Resolubilidad (specs/002-verificacion-resolubilidad):
  Cripta sintética grande (1000 salas, 40 llaves):
    recorrido lineal: 14.2 ms (< 200 ms límite constitucional)
  Escalamiento lineal vs. Alternativa ingenua:
    cadenas de llaves: 10 llaves -> lineal: 0.8 ms | ingenua: 2.1 ms
    cadenas de llaves: 25 llaves -> lineal: 1.9 ms | ingenua: 11.4 ms
    cadenas de llaves: 50 llaves -> lineal: 3.8 ms | ingenua: 43.7 ms
    cadenas de llaves: 100 llaves -> lineal: 7.6 ms | ingenua: 172.9 ms
    cadenas de llaves: 500 llaves -> lineal: 38.4 ms | ingenua: 4320.5 ms
  Detección de ciclos (DFS iterativo con pila propia):
    ciclo directo [llave_salida -> llave_salida]: detectado
    ciclos múltiples [k1 -> k2 -> k1], [k3 -> k4 -> k3]: orden canónico confirmado
    cadena profunda (500 llaves): validado sin desbordamiento de recursión
```
