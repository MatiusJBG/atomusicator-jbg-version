# Validación de cinco stems

## Entorno

- Windows 11, Python 3.13, `python-audio-separator` 0.47.0, CPU.
- Cuatro perfiles UVR/Kuielab descargados desde el host oficial y verificados con SHA-256 antes de cargar.
- Segmentos MDX de 256 para los modelos vocales y 512 para las pasadas Kuielab de batería/bajo; solapamiento 0.35, lote 1.

## Referencia y resultado

La entrada fue **“Anvil — Crypt Loop”**, de Oğuzhan Girgin, publicada bajo [CC BY 4.0](https://colorosse.com/assets/audio/music/anvil-music-loop). La página ofrece mezcla y cuatro stems independientes. El archivo de mezcla dura 15.483356 s.

La app publicó `voz_principal.wav`, `coros.wav`, `bateria.wav`, `bajo.wav` e `instrumental.wav`. Los cinco son estéreo, 44,100 Hz, 682,816 frames y 15.483356 s. Ninguno perdió duración al pasar por los cuatro modelos.

La forma de onda muestra que la separación de batería fue muy tenue en esta mezcla, cuya percusión está sintetizada. También sobre el stem aislado de percusión que acompaña a la referencia, ambos perfiles Kuielab evaluados produjeron una predicción de batería baja. Esto señala una limitación del modelo ante timbres sintetizados y no se corrige elevando la ganancia: hacerlo amplificaría fuga/artefactos. La prueba tampoco establece calidad sobre batería acústica.

## Alcance de la evidencia

Verificado: licencia y fuente de la referencia; carga y validación de cuatro pesos; nombres del motor; cinco WAV legibles; dimensiones, duración y alineación; controles de mezcla; publicación atómica y conservación parcial ante fallo simulado.

Pendiente: escucha comparativa de estilos variados, separación de batería acústica/bajo real y clasificación de voz principal frente a coros con una interpretación de varias voces. No se deben usar estos resultados como promesa de aislamiento perfecto.
