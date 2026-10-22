# Verificación manual del mezclador y el pitch

Fecha: 2026-10-22. Entorno: Windows, Python 3.13, PySide6, FFmpeg 9.0.2 con filtro Rubber Band.

Se generaron tres tonos estéreo sintéticos de dos segundos en `.manual-check/` (carpeta ignorada por Git). Se cargaron como voz principal, coros y acompañamiento.

- El callback de mezcla produjo señal audible para stems sin silenciar.
- Al silenciar cada pista quedó silencio cuando las tres pistas estaban en Mute.
- El widget se creó con tres carriles de forma de onda en Qt offscreen.
- Pitch 0, +2 y -2 semitonos produjo WAV de 2.000 s. Con +2, el pico fue 0.226, por debajo del techo de reproducción de 0.98.
- La ventana principal abrió y cerró en modo Qt offscreen.
- El worker de exportación copió los tres stems sintéticos a la carpeta solicitada con nombres descriptivos.

Esta verificación comprueba el flujo de software, la duración y el nivel con tonos sintéticos. No mide calidad perceptual sobre música real, latencia del dispositivo de audio ni la mejora auditiva entre configuraciones de solapamiento. Esas comprobaciones permanecen pendientes.
