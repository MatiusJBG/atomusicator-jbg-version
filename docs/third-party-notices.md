# Atribuciones de componentes

## Ultimate Vocal Remover (UVR) y modelos

La aplicación ofrece `UVR_MDXNET_Main.onnx` y `UVR_MDXNET_KARA_2.onnx` bajo demanda, desde el catálogo público de UVR. El [README oficial de UVR](https://github.com/Anjok07/ultimatevocalremovergui#license) pide a las aplicaciones terceras que respeten MIT y den crédito a UVR, Anjok07 y aufr33; el catálogo identifica ambos archivos. El repositorio indica que sus desarrolladores entrenaron los modelos que provee salvo Demucs v3/v4.

UVR no adjunta un archivo de licencia individual a cada uno de esos dos pesos. Por eso, esta atribución refleja la solicitud publicada por UVR y no una revisión legal independiente de sus datos de entrenamiento o una autorización específica de redistribución comercial. Los pesos no se incluyen en el instalador ni en Git. Quien vaya a distribuir el programa con fines comerciales debe revisar el estado actual directamente con los titulares de derechos.

**Crédito solicitado por UVR:** Ultimate Vocal Remover (UVR), Anjok07 y aufr33.

Los pesos no se incluyen en el repositorio ni en el paquete de la aplicación. El [manifiesto local de modelos](../src/vocal_splitter/infrastructure/separation/model_license_manifest.json) guarda sus URLs, licencia, fuente de la suma SHA-256 y el checksum esperado; el programa verifica el archivo descargado contra ese checksum antes de la inferencia.

## `python-audio-separator`

Dependencia opcional de inferencia, publicada bajo MIT por karaokenerds: [repositorio y licencia](https://github.com/nomadkaraoke/python-audio-separator). La dependencia se obtiene del índice de paquetes Python cuando se instala el extra `separation-cpu`.

## FFmpeg

FFmpeg es un requisito externo del motor y no se incluye con Separador Vocal. Cada persona instala y usa una compilación independiente, cuyos términos dependen de las opciones de compilación; consulta el [proyecto FFmpeg](https://ffmpeg.org/legal.html). La app busca `ffmpeg.exe` en `PATH` y en WinGet Links del perfil de Windows. No modifica ni empaqueta esa instalación externa.

## Datos de audio de validación

Los archivos de audio descargados para validar el motor no forman parte del repositorio ni del instalador. Mantén junto a cada resultado de escucha la fuente, licencia, atribución, versión, transformación y propósito de uso. No uses una grabación si su licencia o autorización no se puede identificar.
