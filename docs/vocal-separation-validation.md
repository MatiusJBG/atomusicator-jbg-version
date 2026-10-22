# Validación de separación vocal

## Ejecución local

- Motor: `python-audio-separator` 0.47.0, CPU.
- Entrada: fragmento de 30 s, estéreo, 48 kHz, derivado de la vista previa `mix-06.mp3`, número 06 de *Der Freischütz*.
- Transformación de entrada: recorte de 30 s desde el segundo 60 y conversión a WAV PCM estéreo de 48 kHz para la ejecución.
- Modelos: `UVR_MDXNET_Main.onnx` y `UVR_MDXNET_KARA_2.onnx`; ambos pesos se descargaron desde las URLs oficiales UVR y se verificaron mediante SHA-256 antes de la inferencia.
- Resultado: `voz_principal.wav`, `coros.wav` y `acompanamiento.wav`; cada archivo dura 30 s, es estéreo, 44.1 kHz y comienza en 0 s. Los tres ocupan 5,292,078 bytes.
- En la ejecución más reciente, las pasadas tardaron 20.384 s y 11.514 s en la CPU de este equipo; cada sesión guarda rutas relativas, dimensiones, URL/checksum/atribución de los modelos, parámetros explícitos del adaptador y tiempo de cada pasada.
- La mezcla fuente se conserva en su ubicación y los pesos y audios de referencia viven fuera del repositorio.

## Procedencia y límites de uso

La muestra proviene de las vistas previas MP3 del [Freischütz Digital Multitrack Dataset](https://www.audiolabs-erlangen.de/resources/MIR/FreiDi/MultitrackDataset). AudioLabs publica el conjunto bajo CC BY-NC-SA 4.0. Esta ejecución se hizo para validación local no comercial; el audio y sus stems no se redistribuyen con la aplicación. Para investigación, la página pide usar los WAV originales disponibles en Zenodo en vez de las vistas previas MP3.

Esta licencia no equivale a una referencia libre para uso comercial. La ejecución confirma que la tubería produce y registra tres WAV decodificables y alineados; no constituye evaluación de calidad por escucha, ni valida que el residuo vocal contenga únicamente coros. La validación de roles vocales sobre una mezcla con varias voces y licencia compatible sigue pendiente.

Los dos modelos aparecen en el catálogo oficial de UVR. Su README indica que el código es MIT y pide a integradores de modelos respetar MIT y atribuir a UVR y sus desarrolladores; la app registra esta base de atribución y verifica los hashes al descargar. No se redistribuyen los pesos.
