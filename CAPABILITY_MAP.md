# Mapa de capacidades: separador vocal

## Objetivo

Crear una aplicación propia para cargar audio, separar la voz principal de los coros y escuchar, limpiar y exportar la voz principal por separado. La referencia de Moises.ai sirve para orientar flujos de carga, reproducción y exportación; no se copiarán su marca, sus recursos visuales ni sus componentes privados.

## Módulos

| Módulo | Responsabilidad | Depende de |
|---|---|---|
| `audio-ingest` | Seleccionar/importar audio, validar formato y duración, mostrar el estado de cada procesamiento. | — |
| `vocal-separation` | Separar voz principal, coros y acompañamiento; definir el motor/modelo intercambiable y sus limitaciones de calidad. Es el núcleo del producto. | `audio-ingest` |
| `audio-workbench` | Escuchar stems sincronizados, formas de onda, búsqueda, solo/silencio/ganancia y transposición con tempo preservado. | `vocal-separation` |
| `export-library` | Organizar las sesiones y exportar voz principal, coros, acompañamiento o mezcla en formatos acordados. | `audio-workbench` |

## Orden de construcción propuesto

`audio-ingest` → `vocal-separation` → `audio-workbench` → `export-library`

## Estado de implementación

- `audio-ingest`: implementado para WAV, MP3, FLAC y M4A con sesiones locales.
- `vocal-separation`: implementado en dos pasadas UVR para voz principal estimada, residuo de coros y acompañamiento.
- `audio-workbench`: reproducción de stems alineados, formas de onda, Mute/Solo, ganancia por pista, búsqueda y pitch offline por semitonos.
- `export-library`: salidas WAV disponibles en la carpeta de cada sesión; falta una interfaz de exportación de mezcla y formatos seleccionables.
- Separación independiente de batería, bajo y otros instrumentos: falta integrar un perfil de cuatro stems con licencia de pesos apta para redistribución/uso previsto. El audio-separator acepta arquitecturas Demucs, pero no se habilitan sus pesos de investigación como opción general.

## Supuestos acordados o propuestos

- Primera entrega como aplicación de escritorio para Windows, ejecutándose localmente.
- El flujo principal recibe una mezcla terminada y produce stems; no requiere separar pistas multipista originales.
- La separación lead/coros se implementará con modelos públicos intercambiables y un flujo vocal de dos etapas; no se asumirá que el modelo base de Moises esté disponible.
- La prioridad es obtener una voz principal lo más limpia posible. Los artefactos residuales y la confusión entre voces serán una limitación que habrá que medir con audio de referencia.
- Los archivos se procesarán localmente. La búsqueda técnica encontró una vía experimental: separar primero voz/acompañamiento y volver a separar el stem vocal con un modelo de karaoke que intenta distinguir voz líder y coros. El resultado depende del contenido y no se puede garantizar perfecto.
- El candidato para envolver modelos es `python-audio-separator`, que documenta soporte para modelos UVR, Demucs y RoFormer y tiene licencia MIT; cada modelo descargado conserva sus propias condiciones y atribuciones.
