# Atribuciones de componentes

## Ultimate Vocal Remover (UVR) y modelos

La aplicación ofrece los modelos `UVR_MDXNET_Main.onnx` y `UVR_MDXNET_KARA_2.onnx`, descargados bajo demanda desde el paquete público de modelos de UVR. El [README oficial de UVR](https://github.com/Anjok07/ultimatevocalremovergui#license) indica que UVR solicita a las aplicaciones de terceros respetar MIT y dar crédito a UVR y sus desarrolladores. El mismo repositorio identifica a Anjok07 y aufr33 como desarrolladores principales y dice que entrenaron los modelos proporcionados, con la excepción de los modelos Demucs v3/v4 de cuatro stems. Los dos perfiles usados aquí aparecen en el [catálogo oficial de modelos](https://github.com/Anjok07/ultimatevocalremovergui/blob/master/gui_data/model_manual_download.json).

**Crédito:** Ultimate Vocal Remover (UVR), Anjok07 y aufr33.

Los pesos no se incluyen en el repositorio ni en el paquete de la aplicación. El [manifiesto local de modelos](../src/vocal_splitter/infrastructure/separation/model_license_manifest.json) guarda sus URLs, licencia, fuente de la suma SHA-256 y el checksum esperado; el programa verifica el archivo descargado contra ese checksum antes de la inferencia.

## `python-audio-separator`

Dependencia opcional de inferencia, publicada bajo MIT por karaokenerds: [repositorio y licencia](https://github.com/nomadkaraoke/python-audio-separator). La dependencia se obtiene del índice de paquetes Python cuando se instala el extra `separation-cpu`.

## FFmpeg

FFmpeg es un requisito externo del motor y no se incluye con Separador Vocal. Cada persona instala y usa una compilación independiente, cuyos términos dependen de las opciones de compilación; consulta el [proyecto FFmpeg](https://ffmpeg.org/legal.html). La app solo verifica que `ffmpeg.exe` esté disponible en `PATH`.

## Datos de audio de validación

Los archivos de audio descargados para validar el motor no forman parte del repositorio ni del instalador. Mantén junto a cada resultado de escucha la fuente, licencia, atribución, versión, transformación y propósito de uso. No uses una grabación si su licencia o autorización no se puede identificar.
