# Atribuciones de componentes

## Ultimate Vocal Remover (UVR) y modelos

La aplicación descarga bajo demanda `UVR_MDXNET_Main.onnx`, `UVR_MDXNET_KARA_2.onnx`, `kuielab_a_drums.onnx` y `kuielab_a_bass.onnx` desde los enlaces del catálogo público de UVR. Su README declara el código MIT, solicita a aplicaciones terceras respetar MIT y dar crédito a UVR y sus desarrolladores; también indica que sus desarrolladores entrenaron los modelos que provee salvo Demucs v3/v4. Los modelos Kuielab aparecen en el catálogo oficial y el proyecto upstream MDX-Net publica su código bajo MIT.

UVR no adjunta un archivo de licencia individual a cada peso. Esta atribución sigue la solicitud de UVR y la licencia upstream MDX-Net; no constituye una auditoría legal independiente de datos de entrenamiento. Los pesos se descargan directamente bajo demanda, no se incluyen en el instalador ni en Git y se validan con SHA-256 antes de inferencia.

**Crédito:** Ultimate Vocal Remover (UVR), Anjok07 y aufr33; KINoAI/Kuielab y Woosung Choi por MDX-Net.

Los pesos no se incluyen en el repositorio ni en el paquete de la aplicación. El [manifiesto local de modelos](../src/vocal_splitter/infrastructure/separation/model_license_manifest.json) guarda sus URLs, licencia, fuente de la suma SHA-256 y el checksum esperado; el programa verifica el archivo descargado contra ese checksum antes de la inferencia.

## `python-audio-separator`

Dependencia opcional de inferencia, publicada bajo MIT por karaokenerds: [repositorio y licencia](https://github.com/nomadkaraoke/python-audio-separator). La dependencia se obtiene del índice de paquetes Python cuando se instala el extra `separation-cpu`.

## FFmpeg

Desde la versión 0.5.0, el paquete Windows incluye FFmpeg y FFprobe 9.0.2 de la distribución estática full de Gyan, ejecutados como procesos independientes. Su procedencia y SHA-256 se fijan en `packaging/ffmpeg-runtime.json`. La preparación y la compilación rechazan herramientas incompletas o alteradas; el usuario final no necesita instalar FFmpeg ni modificar el PATH de Windows.

La compilación del proveedor declara GPL v3. Se conservan su `LICENSE`, `README.txt` con configuración y librerías, y el manifiesto de procedencia en `docs/ffmpeg` del instalador y dentro del runtime. Fuente de FFmpeg correspondiente: https://github.com/FFmpeg/FFmpeg/commit/946fcce07b. Distribución del proveedor: https://github.com/GyanD/codexffmpeg/releases/tag/9.0.2. Consulta los términos de cada componente y los [avisos del proyecto FFmpeg](https://ffmpeg.org/legal.html).

La Release 0.5.0 adjunta también el archivo de fuentes de FFmpeg correspondiente y los avisos/configuración del proveedor. Las versiones anteriores no incluían estas herramientas.

## Datos de audio de validación

Los archivos de audio descargados para validar el motor no forman parte del repositorio ni del instalador. Mantén junto a cada resultado de escucha la fuente, licencia, atribución, versión, transformación y propósito de uso. No uses una grabación si su licencia o autorización no se puede identificar.
