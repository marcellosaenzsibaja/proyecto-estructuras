# Bitácora de uso de LLM

## Entrada 1
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Este es el enunciado de un proyecto que necesito desarrollar. Necesito que lo analices completo y comprendas en qué consiste y cuál debe ser el resultado final. Te adjunto el avance que se tiene hasta el momento construido, necesito que lo revises y según lo que se pide y me digas si está correcto, además que me digas con qué se debe continuar y lo construyamos. Recuerda siempre regirte bajo las instrucciones del proyecto, sin inventar nada ni asumir decisiones que no se respalden en lo solicitado."
- Uso de la respuesta: revisar el avance contra el enunciado y definir las etapas de construcción.

## Entrada 2
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "No nos han dado el paquete de respuestas para --offline. Y sí, arranquemos, necesito corregir lo malo y avanzar con lo que se necesita para cumplir con la entrega como se debe"
- Uso de la respuesta: construir la etapa 1 (cliente de red corregido, interfaz de fuente de datos, README, .gitignore y pruebas).

## Entrada 3
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "ya esta versión se puede correr? Y si es así dime dónde y cómo"
- Uso de la respuesta: obtener las instrucciones para ejecutar la etapa 1.

## Entrada 4
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "como me ubico sobre la carpeta en la terminal"
- Uso de la respuesta: ubicar la terminal en la carpeta del proyecto.

## Entrada 5
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: [captura de pantalla de PowerShell con el error "Could not open requirements file"]
- Uso de la respuesta: corregir la carpeta desde la que se ejecutaban los comandos.

## Entrada 6
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Al correr salió esto" [dos capturas de pantalla de la ejecución de main.py]
- Uso de la respuesta: validar el cliente de red contra el servicio y señalar los defectos de reglas del avance anterior.

## Entrada 7
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Sí"
- Uso de la respuesta: construir la etapa 2 (tabla hash, agenda de eventos, lista doble, inventario y buffer circular, con pruebas).

## Entrada 8
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Sí"
- Uso de la respuesta: confirmar la etapa 2 y comenzar la etapa 3 (modelo del juego sin vista).

## Entrada 9
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "Continuar"
- Uso de la respuesta: terminar la etapa 3 (pruebas, cargador, controlador, vista y herramienta de muestra de datos).

## Entrada 10
- Fecha aproximada: 17 de octubre de 2026
- Herramienta: Claude (Anthropic)
- Prompt: "bueno ya tienes las instrucciones del proyecto y asi es como lo llevo, puedes terminarlo por favor y no hagas comentarios"
- Uso de la respuesta: completar de forma autónoma, contra el enunciado completo, todo lo que faltaba del proyecto: modo `--offline` y `herramientas/exportar_offline.py` (§3.4); ordenamiento propio con selección automática entre inserción y mezcla (§4.9); guardado binario con acceso aleatorio por sala, equivalente JSON de comparación y tabla de puntajes (§4.10); bitácora de sólo adición y `--replay` (§4.11); sistema de retroceso reversible por deltas e implementación completa del pergamino de retroceso, incluidas sus exclusiones de alcance (§2.11/§4.6); caché de fichas de catálogo con política LRU y protección de fichas en uso, y su persistencia en disco entre ejecuciones (§4.4); banco de pruebas de desempeño `--bench` (§5.3); reescritura del controlador y de `main.py` para integrar todos los comandos y opciones nuevos; ampliación de la batería de pruebas (`unittest`) para cada módulo nuevo; este documento de decisiones de diseño (`DECISIONES.md`, §8) y la actualización de `README.md` y de esta bitácora. Se verificaron además, en una relectura completa del enunciado, tres vacíos de cumplimiento que se corrigieron en el mismo trabajo: la versión del catálogo faltaba en el encabezado de la bitácora (§4.11), la caché de fichas no se conectaba a la persistencia en disco ya construida (§4.4), y el reporte final no incluía los aciertos/fallos de caché (§5.1).
