# Plan técnico: `vocal-separation`

## Alcance

Implementar la separación local en dos etapas aprobada en [SPEC-vocal-separation.md](../SPEC-vocal-separation.md), integrándola con las sesiones que crea `audio-ingest`. El resultado buscado son tres WAV alineados: voz principal estimada, coros/residuo vocal y acompañamiento. El motor se mantendrá intercambiable y no se copiará código, marca ni modelos privados de Moises.ai.

Este plan no abarca reproductor/mixer, cambio de pitch, EQ/limpieza, transcripción, mastering ni un instalador de producción.

## Componentes y dependencias

| Componente | Responsabilidad | Depende de |
|---|---|---|
| Dominio `SeparationJob` | Estados, avance, cancelación y errores recuperables del trabajo. | — |
| Dominio `Stem` / `SeparationResult` | Etiquetas propias (`LeadVocal`, `BackingVocals`, `Instrumental`), metadatos y rutas validadas. | — |
| Puerto `VocalSeparator` | Contrato independiente del motor concreto para ejecutar ambas etapas. | Dominio |
| Servicio `SeparateVocals` | Verificar sesión y espacio disponible, coordinar las etapas, validar resultados y registrar el motor/modelos. | Dominio, puerto, sesión |
| Adaptador `python-audio-separator` | Traducir perfiles/configuración a llamadas del paquete y normalizar sus stems de salida. | Puerto, biblioteca externa |
| Registro de modelos | Guardar nombre, versión, fuente, licencia, suma de comprobación y estado de revisión de cada peso usado. | — |
| `SeparationWorker` Qt | Ejecutar el servicio fuera del hilo de interfaz; entregar estados, avance, resultado y cancelación. | Servicio, UI |
| Integración con `MainWindow` | Mostrar acción de separación y estados; distinguir los resultados de primera etapa de los stems finales. | Worker, sesión |

La dirección de dependencia será UI → servicio de aplicación → interfaz del separador ← adaptador. El dominio no importará PySide6 ni `python-audio-separator`.

## Secuencia propuesta

1. Revisar las versiones del paquete, Python/Windows y los perfiles candidatos. Elegir pesos solo cuando la fuente y licencia de cada modelo estén documentadas; el permiso MIT del paquete no se tratará como licencia de sus pesos.
2. Definir estados del trabajo, errores tipados, perfiles de modelo y contrato del motor. Definir cómo identificar sin ambigüedad los stems vocal e instrumental que devuelve el adaptador.
3. Implementar el adaptador de primera etapa: mezcla → voz total + acompañamiento. Mantener la llamada de biblioteca detrás del puerto propio.
4. Implementar la segunda etapa sobre voz total: voz estimada → voz principal + residuo etiquetado coros. No afirmar que el residuo siempre contiene exclusivamente coros.
5. Guardar salidas temporales dentro de la sesión; validar decodificación, canales, inicio y duración; publicar los tres nombres finales solo si ambas etapas terminan correctamente. Si falla la segunda, preservar y etiquetar explícitamente solo la separación vocal/instrumental recuperable.
6. Integrar descarga/caché bajo demanda, progreso y cancelación en el worker Qt. Registrar en `session.json` la versión del motor, los perfiles/pesos, parámetros, tiempos y archivos resultantes. La entrada de audio permanece local.
7. Seleccionar pistas de referencia permisivas y registrar licencia, atribución, URL/DOI, versión y transformaciones. Evaluar Sanidha como primera opción por su CC BY 4.0 y stems de voz/instrumentos; comprobar acceso y atribución. MUSDB18 no es la base predeterminada porque su acceso es académico y reúne licencias distintas. Para los casos de coros, buscar una grabación multipista con varias voces y derechos compatibles o construir una mezcla derivada de fuentes CC BY y anotar el proceso; no presentar una voz duplicada sintéticamente como sustituto de una prueba real de coro.
8. Integrar la acción en la ventana principal, mostrar resultados/error y estados recuperables, y documentar los límites de calidad observados en escucha.

## Datos de validación y licencias

- No descargar automáticamente conjuntos de datos ni pesos durante la instalación. Cualquier descarga será explícita y separada de la importación de una canción del usuario.
- Mantener un manifiesto con los campos de licencia y procedencia requeridos por la especificación. Los elementos sin licencia identificable quedarán fuera del flujo de validación y de redistribución.
- Sanidha es una opción para mezcla con una voz e instrumentos: su sitio publica stems multipista y declara CC BY 4.0, pero el acceso requiere VPN de Georgia Tech. Confirmar disponibilidad efectiva antes de basar tareas en ella.
- MUSDB18 contiene stems pero su propia documentación señala acceso para uso académico y fuentes con licencias distintas; no asumir que sea permisivo para otros usos.
- Para la prueba específica de principal/coros se requiere referencia con stems vocales separados o mezcla derivada autorizada. Si no se encuentra un caso que satisfaga licencia y acceso, dejar esa validación pendiente y usar Sanidha únicamente para revisar separación voz/acompañamiento.

## Riesgos y decisiones

- **Derechos de los pesos:** el código del wrapper y los archivos ONNX/PTH pueden tener términos diferentes. Bloquear el perfil hasta documentar licencia, origen y hash; guardar los pesos en caché local, nunca en Git.
- **Separación principal/coros:** un modelo Karaoke puede estimar una voz prominente y dejar armonías/voz doblada en el residual, pero no garantiza separar roles vocales en todos los arreglos. Preservar el nombre “estimada” en la descripción y exponer la limitación.
- **Consumo de hardware:** medir memoria y tiempo en CPU antes de definir requisitos; ofrecer aceleración solo si el entorno local está soportado, sin impedir una ejecución CPU válida.
- **Descarga interrumpida o falta de disco:** no publicar artefactos parciales como stems finales; limpiar temporales propios sin borrar el audio de origen ni resultados recuperables.
- **Mapeo variable del motor:** comprobar nombres y existencia real de stems devueltos; nunca mapear una salida desconocida por posición de lista.
- **Duración/desfase:** normalizar únicamente lo necesario para que los tres WAV tengan comienzo y duración comunes; registrar cualquier recorte/relleno aplicado.
- **Interfaz/cancelación:** el trabajo no debe bloquear la ventana. Cancelar una operación de forma cooperativa y esperar su cierre antes de desechar el worker.

## Puntos de revisión

- Un flujo controlado produce exactamente las tres salidas esperadas, decodificables y alineadas con la mezcla.
- Los estados de ambas etapas son visibles y una falla de la segunda no etiqueta la voz total como “Voz principal”.
- Se puede cancelar/recuperar un trabajo fallido sin tocar el archivo original.
- Cada peso activo está registrado y pasa la revisión de licencia antes de ser descargado/usado.
- La atribución y licencia de cada pista usada para validación permanecen junto a sus resultados; la prueba de separación de coros no se declara validada con una referencia que solo tenga una voz.

## Fuera de alcance en esta iteración

- Separación de instrumentos individuales, pitch shifting, corrección tonal, efectos, ecualización y edición de formas de onda.
- Descargar desde URLs de música, iniciar sesión, subir audio del usuario a un servicio remoto o telemetría.
- Entrenar/ajustar pesos con grabaciones de usuarios o redistribuir pesos sin licencia revisada.
- Comprometer una calidad de aislamiento perfecta o asumir que toda voz residual son coros.
