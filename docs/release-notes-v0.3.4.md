# Separador Vocal 0.3.4

## Correcciones

- Incluye las extensiones nativas de TorchVision que PyInstaller omitía. La versión 0.3.3 abría la ventana y pasaba el autodiagnóstico básico, pero el modelo UVR fallaba al ejecutar la operación torchvision::nms, así que no llegaba a producir los stems.
- Desactiva la barra de progreso de consola de MDX en el modo de escritorio; en Windows podía escribir en un controlador de consola inválido y detener la separación.
- El autodiagnóstico verifica FFmpeg, permisos de escritura local y la operación nativa nms antes de dar por lista una compilación.
- El progreso de descarga de modelos se mantiene monotónico; no aborta si una lectura reporta menos bytes. El proceso muestra un panel con la etapa activa: voz y acompañamiento, voz principal y coros, o validación de pistas. Al terminar correctamente abre el mezclador con formas de onda, mute, solo y volumen.
- Cuando el motor falla, la app muestra el modelo y el motivo técnico útil en vez del mensaje genérico «no produjo todas las pistas».

## Verificación

- 15 pruebas unitarias, incluida la ejecución local de torchvision.ops.nms y la regresión de progreso MDX.
- Build de PyInstaller e Inno Setup en Windows.
- Smoke test del EXE empaquetado con ambos modelos locales: FFmpeg, escritura local, operación nms, las dos etapas y arranque de la ventana Qt.
- Autoprueba de dos etapas con una mezcla sintética de 8 segundos. Comprueba los tres stems, que cada WAV se pueda leer y que conserve la duración de la fuente con tolerancia de 100 ms, a 44.1 kHz y en estéreo.

## Actualización

Cierra Separador Vocal e instala SeparadorVocal-Setup.exe desde [Releases](https://github.com/MatiusJBG/atomusicator-jbg-version/releases). Los modelos, proyectos y stems guardados en AppData local se conservan.
