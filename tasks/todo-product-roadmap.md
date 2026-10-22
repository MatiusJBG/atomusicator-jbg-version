# Seguimiento de implementación del producto

## `audio-workbench`

- [x] Mostrar las cinco formas de onda (voz principal, coros, batería, bajo e instrumental) con cursor común.
- [x] Reproducir y pausar sincronizados; buscar al pulsar una forma de onda.
- [x] Mute, Solo y ganancia independientes; control de pico del bus durante reproducción.
- [x] Aplicar pitch de -12 a +12 semitonos en segundo plano con Rubber Band de FFmpeg y mantener los WAV originales.
- [x] Exportar copias WAV de los stems seleccionados a una carpeta elegida desde el mezclador, sin bloquear la UI.
- [x] Verificar con señal sintética 0, +2 y -2 semitonos, duración constante, callback de mezcla y UI PySide6 offscreen.

## Continuidad de separación

- [x] Mantener segmentación MDX del motor y configurar solapamiento 0.35 para la mezcla entre ventanas.
- [x] Registrar tamaño de segmento, solapamiento y lote en `session.json` a través de los parámetros del modelo.
- [x] Detectar FFmpeg en PATH o en WinGet Links y exponerlo también al proceso del motor.
- [ ] Validar escucha comparativa con canción con licencia permisiva; no declarar mejora auditiva hasta hacer esa escucha.

## Separación de cinco stems y exportación

- [x] Añadir batería, bajo e instrumental restante mediante modelos MDX-Net de UVR, con descarga local y hashes verificados.
- [x] Publicar los cinco WAV finales juntos; preservar pistas recuperables como resultado parcial si falla la separación instrumental.
- [x] Verificar la tubería con modelos reales, alineación a 44.1 kHz y duración conservada; validar controles M/S/ganancia y presentación de las cinco pistas.
- [ ] Evaluar la calidad auditiva con canciones de distintos estilos y voces reales; una mezcla sintetizada no valida la clasificación musical general.
- [ ] Añadir elección de formato y exportación de mezcla.
- [x] Mantener el procesamiento segmentado con solapamiento 0.35 y comprobar bordes y duración en una pista de referencia.

## Renovación visual

- [x] Aplicar paleta de grafito, pizarra y menta con colores semánticos por stem.
- [x] Compactar el mezclador para mostrar las cinco pistas juntas en 1280×800 y añadir scroll en ventanas menores.
- [x] Actualizar el flujo de importación, progreso de cuatro etapas y transporte de pitch/exportación.

## Windows / GitHub

- [x] README en español con instalación, configuración, uso y solución de problemas.
- [x] `.gitignore` cubre entornos, resultados, modelos y archivos de audio generados.
- [x] Definición PyInstaller/Inno Setup que excluye audio, modelos y FFmpeg.
- [x] Construir el instalador v0.2.0 e iniciar el ejecutable empaquetado.
- [x] Recompilar el instalador v0.3.0 y arrancar el ejecutable empaquetado.
- [x] Integrar ramas de funcionalidad/documentación a `develop` y subirlo.
- [x] Adjuntar el instalador v0.2.0 a una GitHub Release.
- [x] Adjuntar el instalador v0.3.0 a la GitHub Release `v0.3.0`.

## Flujo Git

- [x] Crear ramas feature/chore desde `develop`, commits atómicos y fast-forward de vuelta a `develop`.
- [x] Mantener `main` sin modificaciones; el mantenedor integrará `develop` cuando lo decida.
