# Atribuciones de componentes

## Ultimate Vocal Remover (UVR) y modelos

La aplicación descarga bajo demanda `UVR_MDXNET_Main.onnx`, `UVR_MDXNET_KARA_2.onnx`, `kuielab_a_drums.onnx` y `kuielab_a_bass.onnx` desde los enlaces del catálogo público de UVR. Su README declara el código MIT, solicita a aplicaciones terceras respetar MIT y dar crédito a UVR y sus desarrolladores; también indica que sus desarrolladores entrenaron los modelos que provee salvo Demucs v3/v4. Los modelos Kuielab aparecen en el catálogo oficial y el proyecto upstream MDX-Net publica su código bajo MIT.

UVR no adjunta un archivo de licencia individual a cada peso. Esta atribución sigue la solicitud de UVR y la licencia upstream MDX-Net; no constituye una auditoría legal independiente de datos de entrenamiento. Los pesos se descargan directamente bajo demanda, no se incluyen en el instalador ni en Git y se validan con SHA-256 antes de inferencia.

**Crédito:** Ultimate Vocal Remover (UVR), Anjok07 y aufr33; KINoAI/Kuielab y Woosung Choi por MDX-Net.

Los pesos no se incluyen en el repositorio ni en el paquete de la aplicación. El [manifiesto local de modelos](../src/vocal_splitter/infrastructure/separation/model_license_manifest.json) guarda sus URLs, licencia, fuente de la suma SHA-256 y el checksum esperado; el programa verifica el archivo descargado contra ese checksum antes de la inferencia.

## `python-audio-separator`

Dependencia opcional de inferencia, publicada bajo MIT por karaokenerds: [repositorio y licencia](https://github.com/nomadkaraoke/python-audio-separator). La dependencia se obtiene del índice de paquetes Python cuando se instala el extra `separation-cpu`.

## FFmpeg

FFmpeg es un requisito externo del motor y no se incluye con Separador Vocal. Cada persona instala y usa una compilación independiente, cuyos términos dependen de las opciones de compilación; consulta el [proyecto FFmpeg](https://ffmpeg.org/legal.html). La app busca `ffmpeg.exe` en `PATH` y en WinGet Links del perfil de Windows. No modifica ni empaqueta esa instalación externa.

## Datos de audio de validación

Los archivos de audio descargados para validar el motor no forman parte del repositorio ni del instalador. Mantén junto a cada resultado de escucha la fuente, licencia, atribución, versión, transformación y propósito de uso. No uses una grabación si su licencia o autorización no se puede identificar.
