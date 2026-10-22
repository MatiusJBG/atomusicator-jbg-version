# Separador Vocal 0.2.0

## Incluye

- Mezclador local sincronizado para voz principal, coros/residuo y acompañamiento.
- Formas de onda, cursor común, búsqueda, Play/Pausa, Mute, Solo y ganancia por stem.
- Pitch de -12 a +12 semitonos con Rubber Band de FFmpeg. Renderiza copias y conserva el tempo.
- Mezcla protegida por un limitador de pico de muestra durante reproducción.
- Segmentación MDX con solapamiento configurado en 0.35 para combinar ventanas y reducir discontinuidades.
- Instalador Windows x64; no incluye FFmpeg, pesos ni audio del usuario.

## Requisitos

- Windows 10/11 x64.
- FFmpeg externo en PATH o instalado por WinGet. Para pitch, la compilación necesita el filtro `rubberband`.
- Internet en la primera descarga de los modelos UVR de voz/instrumental.

## Límites conocidos

- Los modelos de esta versión generan voz principal estimada, coros/residuo y acompañamiento. La separación de batería, bajo y otros queda pendiente de un modelo de cuatro stems con permisos de pesos compatibles.
- Las pruebas de audio del mezclador/pitch usaron tonos sintéticos. Falta evaluar auditivamente separación y solapamiento en una referencia musical con licencia permisiva.
- El instalador no está firmado digitalmente; Windows puede mostrar SmartScreen.
- El instalador usa Inno Setup. Distribución comercial requiere atender su solicitud de licencia comercial.
