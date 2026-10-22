# Especificación: `audio-workbench`

## Objetivo

Reproducir los WAV de una sesión sincronizados y permitir balancear cada stem durante la reproducción. Aplicar transposición de pitch de forma offline conservando el tempo y la fuente original.

## Alcance implementado

- Carriles de forma de onda con un cursor temporal común y búsqueda al pulsar en la forma de onda.
- Reproducción en tiempo real, pausa y reinicio con un dispositivo predeterminado de Windows.
- Ganancia, Mute y Solo por stem.
- Cambio de -12 a +12 semitonos para el conjunto sincronizado de stems.
- Render de pitch con Rubber Band de FFmpeg, en un hilo de trabajo separado y guardado como copia bajo `outputs/pitch-renders/`.
- Limitador por bloque con techo de pico de muestra de 0.98 durante la reproducción para evitar clipping del mezclador.

## Decisiones técnicas

- Los stems se decodifican en memoria antes de abrir el dispositivo. El callback de `sounddevice` solo mezcla buffers existentes; no lee archivos ni actualiza la interfaz.
- Las pistas deben tener la misma frecuencia, número de canales y cantidad de frames. Una sesión con stems desalineados no se carga al mezclador.
- El pitch se renderiza fuera del callback con `rubberband=pitch=2^(semitones/12):tempo=1`. Si FFmpeg no contiene Rubber Band, se informa el requisito y se conserva la reproducción original.
- Los originales no se sobrescriben. Renderizar 0 semitonos crea una copia del original.

## Límites

- El limitador evita que el bus exceda -0.18 dBFS de pico de muestra, pero no realiza medición de true peak ni mastering.
- La reproducción mantiene todos los stems en memoria; sesiones muy largas o equipos con poca memoria pueden no ser aptos.
- La calidad de pitch depende de FFmpeg/Rubber Band local.
- Los stems de batería, bajo y otros requieren un modelo de cuatro fuentes con condiciones de pesos aprobadas. Los modelos Demucs v3/v4 se omiten de la descarga por defecto debido a su restricción declarada a fines científicos.
